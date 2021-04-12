#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

import asyncio
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Type, Union, Any
from string import Template

from elasticsearch_dsl import Q, Search, UpdateByQuery
from elasticsearch_dsl.response import UpdateByQueryResponse
from elasticsearch import Elasticsearch
from elasticsearch import ConflictError, ConnectionError
from schematics.types import (StringType, DecimalType, DateType, IntType, BaseType, BooleanType,
                              DateTimeType, UTCDateTimeType, FloatType, LongType, NumberType,
                              ListType)
from schematics.exceptions import ConversionError

from cortx.utils.errors import InternalError
from cortx.utils.data.access import Query, SortOrder, IDataBase
from cortx.utils.data.access import ExtQuery
from cortx.utils.data.db import GenericDataBase, GenericQueryConverter
from cortx.utils.data.access import BaseModel
from cortx.utils.errors import DataAccessExternalError, DataAccessInternalError
from cortx.utils.data.access.filters import FilterOperationCompare
from cortx.utils.data.access.filters import ComparisonOperation, IFilter


__all__ = ["ElasticSearchDB"]


class ESWords:
    """ElasticSearch service words"""

    MAPPINGS = "mappings"
    PROPERTIES = "properties"
    DATA_TYPE = "type"
    ALIASES = "aliases"
    SETTINGS = "settings"
    SOURCE = "_source"
    ASC = "asc"
    DESC = "desc"
    MODE = "mode"
    ORDER = "order"
    COUNT = "count"
    DELETED = "deleted"
    PAINLESS = "painless"
    FIELD_DATA = "fielddata"
    INDEX_SETTINGS = "settings"


class ESDataType:
    """Enumeration for ElasticSearch data types"""

    TEXT = "text"
    KEYWORD = "keyword"
    INTEGER = "integer"
    DATE = "date"
    BOOLEAN = "boolean"
    FLOAT = "float"
    LONG = "long"
    SHORT = "short"


LOWERCASE_NORMALIZER = "lowercase_normalizer"

# Specific for ElasticSearch setting to perform case insensitive search
INDEX_SETTINGS = {
    "analysis": {
        "normalizer": {
            LOWERCASE_NORMALIZER: {
                "type": "custom",
                "char_filter": [],
                "filter": ["lowercase"]
            }
        }
    }
}


# TODO: Add remaining schematics data types
DATA_MAP = {
    StringType: "keyword",  # TODO: keyword
    IntType: "integer",
    DateType: "date",
    BooleanType: "boolean",
    DateTimeType: "date",
    UTCDateTimeType: "date",
    DecimalType: "keyword",  # TODO: maybe a poor text?
    FloatType: "float",  # TODO: it is possible to increase type to elasticsearch's double
    LongType: "long",
    NumberType: "short",  # TODO: Size of ES's type can be increased to 'integer'
    ListType: "nested"   # TODO: This will serialize only one level of nested objects. Need to implement for multi-level
    # DictType: "nested"
}


def field_to_str(field: Union[str, BaseType]) -> str:
    """
    Convert model field to its string representation

    :param Union[str, BaseType] field:
    :return: model field string representation
    """
    if isinstance(field, str):
        return field
    elif isinstance(field, BaseType):
        return field.name
    else:
        raise DataAccessInternalError("Failed to convert field to string representation")


class ElasticSearchQueryConverter(GenericQueryConverter):
    """
    Implementation of filter tree visitor that converts the tree into the Query
    object of ElasticSearch-dsl library.

    Usage:
    converter = ElasticSearchQueryConverter()
    q_obj = converter.build(filter_root)
    """

    def __init__(self, model):
        self.comparison_conversion = {
            ComparisonOperation.OPERATION_EQ: self._match_query,
            ComparisonOperation.OPERATION_LT: self._range_generator('lt'),
            ComparisonOperation.OPERATION_GT: self._range_generator('gt'),
            ComparisonOperation.OPERATION_LEQ: self._range_generator('lte'),
            ComparisonOperation.OPERATION_GEQ: self._range_generator('gte')
        }
        # Needed to perform for type casting if field name is pure string,
        # not of format Model.field
        self._model = model

    @staticmethod
    def _match_query(field: str, target):
        obj = {
            field: target
        }

        return Q("match", **obj)

    @staticmethod
    def _range_generator(op_string: str):
        def _make_query(field: str, target):
            obj = {
                field: {
                    op_string: target
                }
            }

            return Q("range", **obj)

        return _make_query

    def build(self, root: IFilter):
        # TODO: may be, we should move this method to the entity that processes
        # Query objects
        return root.accept_visitor(self)

    def handle_compare(self, entry: FilterOperationCompare):
        super().handle_compare(entry)  # Call generic code

        field = entry.get_left_operand()

        field_str = field_to_str(field)

        op = entry.get_operation()
        try:
            if isinstance(field, str):
                right_operand = getattr(self._model, field_str).to_native(entry.get_right_operand())
            else:
                right_operand = field.to_native(entry.get_right_operand())
        except ConversionError as e:
            raise DataAccessInternalError(f"{e}")

        return self.comparison_conversion[op](field_str, right_operand)


class ElasticSearchDataMapper:
    """ElasticSearch data mappings helper"""

    def __init__(self, model: Type[BaseModel]):
        """

        :param Type[BaseModel] model: model for constructing data mapping for index in ElasticSearch
        """
        self._model = model
        self._mapping = {
            ESWords.MAPPINGS: {
                ESWords.PROPERTIES: {
                }
            }
        }

    def _add_property(self, name: str, property_type: Type[BaseType]):
        """
        Add property to mappings

        :param str name: property name
        :param Type[BaseType] property_type: type of property for given property `name`
        :return:
        """
        properties = self._mapping[ESWords.MAPPINGS][ESWords.PROPERTIES]

        if name in properties:
            raise InternalError(f"Repeated property name in model: {name}")

        properties[name] = dict()
        properties[name][ESWords.DATA_TYPE] = DATA_MAP[property_type]
        # NOTE: to perform case insensitive search we need to use custom normalizer for keywords
        if properties[name][ESWords.DATA_TYPE] == ESDataType.KEYWORD:
            properties[name]["normalizer"] = LOWERCASE_NORMALIZER

    def build_index_mappings(self, replication: int) -> dict:
        """
        Build ElasticSearch index data mapping

        :return: elasticsearch data mappings dict
        """
        for name, property_type in self._model.fields.items():
            self._add_property(name, type(property_type))
        self._mapping[ESWords.INDEX_SETTINGS] = INDEX_SETTINGS
        if replication > 0:
            self._mapping[ESWords.INDEX_SETTINGS].update({
                "number_of_replicas": str(replication),
                "auto_expand_replicas": f"{replication}-all"})
        return self._mapping


class ElasticSearchQueryService:
    """Query service-helper for Elasticsearch"""

    def __init__(self, index: str, es_client: Elasticsearch,
                 query_converter: ElasticSearchQueryConverter):
        self._index = index
        self._es_client = es_client
        self._query_converter = query_converter

    def search_by_query(self, query: Query) -> Search:
        """
        Get Elasticsearch Search instance by given query object

        :param Query query: query object to construct ES's Search object
        :return: Search object constructed by given `query` param
        """
        def convert(name):
            return ESWords.ASC if name == SortOrder.ASC else ESWords.DESC

        extra_params = dict()
        sort_by = dict()
        search = Search(index=self._index, using=self._es_client)

        q = query.data

        if q.filter_by is not None:
            filter_by = self._query_converter.build(q.filter_by)
            search = search.query(filter_by)

        if q.offset is not None:
            extra_params["from_"] = q.offset
        if q.limit is not None:
            extra_params["size"] = q.limit

        if any((i is not None for i in (q.offset, q.limit))):
            search = search.extra(**extra_params)

        if q.order_by is not None:
            sort_by[field_to_str(q.order_by.field)] = {ESWords.ORDER: convert(q.order_by.order)}
            search = search.sort(sort_by)

        return search


class ElasticSearchDB(GenericDataBase):
    """ElasticSearch Storage Interface Implementation"""

    elastic_instance = None
    thread_pool = None
    loop = None

    _default_template = Template("ctx._source.$FIELD_NAME = '$FIELD_VALUE';")
    _inline_templates = {
        bool: Template("ctx._source.$FIELD_NAME = $FIELD_VALUE;"),
        int: Template("ctx._source.$FIELD_NAME = $FIELD_VALUE;"),
        float: Template("ctx._source.$FIELD_NAME = $FIELD_VALUE;"),
    }
    _default_date_format = '%Y-%m-%dT%H:%M:%S.%fZ'

    def __init__(self, es_client: Elasticsearch, model: Type[BaseModel], collection: str,
                 thread_pool_exec: ThreadPoolExecutor, loop: asyncio.AbstractEventLoop = None):
        """

        :param Elasticsearch es_client: elasticsearch client
        :param Type[BaseModel] model: model (class object) to associate it with elasticsearch storage
        :param str collection: string represented collection for `model`
        :param ThreadPoolExecutor thread_pool_exec: thread pool executor
        :param BaseEventLoop loop: asyncio event loop
        """
        self._es_client = es_client
        self._tread_pool_exec = thread_pool_exec
        self._loop = loop or asyncio.get_event_loop()
        self._collection = collection

        self._query_converter = ElasticSearchQueryConverter(model)

        # We are associating index name in ElasticSearch with given collection
        self._index = self._collection

        if not isinstance(model, type) or not issubclass(model, BaseModel):
            raise DataAccessInternalError("Model parameter is not a Class object or not inherited "
                                          "from cortx.utils.data.access.BaseModel")
        self._model = model  # Needed to build returning objects

        self._index_info = None
        self._model_scheme = None

        self._query_service = ElasticSearchQueryService(self._index, self._es_client,
                                                        self._query_converter)

    @classmethod
    async def create_database(cls, config, collection, model: Type[BaseModel]) -> IDataBase:
        """
        Creates new instance of ElasticSearch DB and performs necessary initializations

        :param DBSettings config: configuration for elasticsearch server
        :param str collection: collection for storing model onto db
        :param Type[BaseModel] model: model which instances will be stored in DB
        :return:
        """
        # NOTE: please, be sure that you avoid using this method twice (or more times) for the same
        # model
        if not all((cls.elastic_instance, cls.thread_pool, cls.loop)):
            auth = None
            if config.login:
                auth = (config.login, config.password)

            node = {"host": config.host, "port": config.port}
            cls.elastic_instance = Elasticsearch(hosts=[node], http_auth=auth)
            cls.pool = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count())
            cls.loop = asyncio.get_event_loop()

        es_db = cls(cls.elastic_instance, model, collection, cls.thread_pool, cls.loop)

        try:
            await es_db.attach_to_index(config.replication)
        except DataAccessExternalError:
            raise  # forward error to upper caller
        except Exception as e:
            raise DataAccessExternalError("Some unknown exception occurred in "
                                          f"ElasticSearch module: {e}")

        return es_db

    async def attach_to_index(self, replication: int) -> None:
        """
        Provides async method to connect storage to index bound to provided model and collection
        :return:
        """
        def _get_alias(_index):
            return self._es_client.indices.get_alias(self._index, ignore_unavailable=True)

        def _create(_index, _body):
            self._es_client.indices.create(index=_index, body=_body)

        def _get(_index):
            return self._es_client.indices.get(self._index)

        try:
            indices = await self._loop.run_in_executor(self._tread_pool_exec, _get_alias, self._index)
        except ConnectionError as e:
            raise DataAccessExternalError(f"Failed to establish connection to ElasticSearch: {e}")

        # self._obj_index = self._es_client.indices.get_alias("*")
        if indices.get(self._index, None) is None:
            data_mappings = ElasticSearchDataMapper(self._model)
            mappings_dict = data_mappings.build_index_mappings(replication)
            # self._es_client.indices.create(index=model.__name__, ignore=400, body=mappings_dict)
            await self._loop.run_in_executor(self._tread_pool_exec,
                                             _create, self._index, mappings_dict)

        self._index_info = await self._loop.run_in_executor(self._tread_pool_exec,
                                                            _get, self._index)
        self._model_scheme = self._index_info[self._index][ESWords.MAPPINGS][ESWords.PROPERTIES]
        self._model_scheme = {k.lower(): v for k, v in self._model_scheme.items()}

    async def store(self, obj: BaseModel):
        """
        Store object into Storage

        :param BaseModel obj: Arbitrary base object for storing into DB

        """
        def _store(_id, _doc: dict):
            """
            Store particular object into elasticsearch index

            :param dict _doc: dict representation of the object
            :return: elastic search server response
            """
            # TODO: is it needed to use id?
            _result = self._es_client.index(index=self._index, id=_id, body=_doc)
            return _result

        await super().store(obj)  # Call generic code

        doc = dict()
        for key in self._model_scheme:
            doc[key] = getattr(obj, key)
            #  TODO: This will serialize only one level of nested objects. Need to implement for multi-level
            if type(doc[key]) is list:
                list_nested = []
                for item in doc[key]:
                    nested_obj = dict()
                    for k, v in item.items():
                        nested_obj[k] = v
                    list_nested.append(nested_obj)
                doc[key] = list_nested

        obj_id = str(obj.primary_key_val)  # convert primary key value into string

        # TODO: check future for the error and result
        # future = self._tread_pool_exec.submit(_store, doc)
        # result = self._loop.run_until_complete(future)

        result = await self._loop.run_in_executor(self._tread_pool_exec, _store, obj_id, doc)
        # TODO: discuss that. May be better avoid this to increase store performance
        # NOTE: make refresh to ensure that updated results will be available quickly
        await self._refresh_index()
        return result

    async def get(self, query: Query) -> List[BaseModel]:
        """
        Get object from Storage by Query

        :param query:
        :return: empty list or list with objects which satisfy the passed query condition
        """
        def _get(_query):
            search = self._query_service.search_by_query(_query)
            return search.execute()

        result = await self._loop.run_in_executor(self._tread_pool_exec, _get, query)
        return [self._model(hit.to_dict()) for hit in result]

    async def update(self, filter_obj: IFilter, to_update: dict) -> int:
        """
        Update object in Storage by Query

        :param IFilter filter_obj: filter object which describes what objects need to update
        :param dict to_update: dictionary with fields and values which should be updated
        :return: number of updated entries
        """
        def dict_to_source(__to_update: dict) -> str:
            """
            Convert __to_update dict into elasticsearch source representation
            :param __to_update: dictionary with fields and values which should be updated
            :return: elasticsearch inline representation
            """

            def _value_converter(_value: Any) -> Any:
                """
                Convert value if it is necessary
                :param _value:
                :return:
                """
                if isinstance(_value, bool):
                    return str(_value).lower()
                elif isinstance(_value, datetime):
                    return _value.strftime(self._default_date_format)

                return _value

            return " ".join(
                (self._inline_templates.get(type(value), self._default_template).substitute(
                    FIELD_NAME=key, FIELD_VALUE=_value_converter(value))
                 for key, value in __to_update.items()))

        def _update(_ubq) -> UpdateByQueryResponse:
            """
            Perform Update by Query in separate thread
            :param UpdateByQuery _ubq: UpdateByQuery instance
            :return: Response object of ElasticSearch DSL module
            """
            return _ubq.execute()

        _to_update = to_update.copy()  # Copy because it will be change below

        # NOTE: Important: call of the parent update method changes _to_update dict!
        await super().update(filter_obj, _to_update)  # Call the generic code

        ubq = UpdateByQuery(index=self._index, using=self._es_client)

        filter_by = self._query_converter.build(filter_obj)
        ubq = ubq.query(filter_by)

        source = dict_to_source(_to_update)
        ubq = ubq.script(source=source, lang=ESWords.PAINLESS)

        result = await self._loop.run_in_executor(self._tread_pool_exec, _update, ubq)

        await self._refresh_index()  # ensure that updated results will be ready immediately
        return result.updated

    async def _refresh_index(self):
        """
        Refresh index

        :return:
        """
        def _refresh():
            self._es_client.indices.refresh(index=self._index)

        await self._loop.run_in_executor(self._tread_pool_exec, _refresh)

    async def delete(self, filter_obj: IFilter) -> int:
        """
        Delete objects in DB by Query

        :param IFilter filter_obj: filter object to perform delete operation
        :return: number of deleted entries
        """
        def _delete(_by_filter):
            search = Search(index=self._index, using=self._es_client)
            search = search.query(_by_filter)
            return search.delete()

        filter_by = self._query_converter.build(filter_obj)
        # NOTE: Needed to avoid elasticsearch.ConflictError when we perform delete quickly
        #       after store operation
        await self._refresh_index()
        try:
            result = await self._loop.run_in_executor(self._tread_pool_exec, _delete, filter_by)
        except ConflictError as e:
            raise DataAccessExternalError(f"{e}")

        return result[ESWords.DELETED]

    async def count(self, filter_obj: IFilter = None) -> int:
        """
        Returns count of entities for given filter_obj

        :param IFilter filter_obj: filter to perform count aggregation
        :return: count of entries which satisfy the `filter_obj`
        """

        def _count(_body):
            return self._es_client.count(index=self._index, body=_body)

        search = Search(index=self._index, using=self._es_client)
        if filter_obj is not None:
            filter_by = self._query_converter.build(filter_obj)
            search = search.query(filter_by)
        else:
            search = search.query()

        result = await self._loop.run_in_executor(self._tread_pool_exec, _count, search.to_dict())
        return result.get(ESWords.COUNT)

    async def count_by_query(self, ext_query: ExtQuery):
        """
        Count Aggregation function

        :param ExtQuery ext_query: Extended query which describes to perform count aggregation
        :return:
        """
        pass
