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
from string import Template
from typing import List, Type, Union, Dict
from datetime import datetime
import json
import operator

from aiohttp import ClientConnectorError
from consul.aio import Consul
from schematics.types import BaseType, StringType
from schematics.exceptions import ConversionError

from cortx.utils.data.access import Query, SortOrder, IDataBase
from cortx.utils.data.access import ExtQuery
from cortx.utils.data.db import GenericDataBase, GenericQueryConverter
from cortx.utils.data.access import BaseModel
from cortx.utils.errors import DataAccessExternalError, DataAccessInternalError, \
    DataAccessError
from cortx.utils.data.access.filters import FilterOperationCompare
from cortx.utils.data.access.filters import ComparisonOperation, IFilter

CONSUL_ROOT = "cortx/base"
OBJECT_DIR = "obj"
PROPERTY_DIR = "prop"

class ConsulWords:
    """Consul service words."""

    VALUE = "Value"
    KEY = "Key"

def field_to_str(field: Union[str, BaseType]) -> str:
    """
    Convert model field to its string representation.

    :param Union[str, BaseType] field:
    :return: model field string representation
    """
    if isinstance(field, str):
        return field
    elif isinstance(field, BaseType):
        return field.name
    else:
        raise DataAccessInternalError(
            "Failed to convert field to string representation")

class ConsulQueryConverterWithData(GenericQueryConverter):
    """
    Implementation of filter tree visitor which performs query tree traversal in parallel with.

    data filtering based on given filter logical and comparison operations.
    Usage:
    converter = ConsulQueryConverter()
    q_obj = converter.build(filter_root)
    """

    def __init__(self, model):
        # Needed to perform for type casting if field name is pure string,
        # not of format Model.field
        self._model = model
        self._operator = {
            ComparisonOperation.OPERATION_EQ: operator.eq,
            ComparisonOperation.OPERATION_NE: operator.ne,
            ComparisonOperation.OPERATION_GEQ: operator.ge,
            ComparisonOperation.OPERATION_LEQ: operator.le,
            ComparisonOperation.OPERATION_GT: operator.gt,
            ComparisonOperation.OPERATION_LT: operator.lt,
            ComparisonOperation.OPERATION_LIKE: operator.contains
        }
        self._raw_data = None
        self._object_data = None

    def _filter(self, suitable_keys: List[str]):
        return filter(lambda x: x[ConsulWords.KEY] in suitable_keys,
                      self._raw_data)

    def build(self, root: IFilter, raw_data: List[Dict]):
        # TODO: may be, we should move this method to the entity that processes
        # Query objects
        self._raw_data = raw_data
        self._object_data = {
            entry[ConsulWords.KEY]: self._model(
                json.loads(entry[ConsulWords.VALUE])) for entry in
            self._raw_data}
        return self._filter(root.accept_visitor(self))

    def handle_compare(self, entry: FilterOperationCompare):
        super().handle_compare(entry)  # Call the generic code

        field = entry.get_left_operand()

        field_str = field_to_str(field)

        op = entry.get_operation()
        try:
            right_operand = getattr(self._model, field_str).to_native(
                entry.get_right_operand())
        except ConversionError as e:
            raise DataAccessInternalError(f"{e}")
        if not entry.get_operation() != ComparisonOperation.OPERATION_LIKE:
            return set(entry_key for entry_key in filter(lambda x: self._operator[op](
            getattr(self._object_data[x], field_str),right_operand),
                                                         self._object_data.keys()))
        else:
            return set(entry_key for entry_key in filter(lambda x: self._operator[op](
                right_operand, getattr(self._object_data[x], field_str)),
                                                         self._object_data.keys()))

def query_converter_build(model: BaseModel, filter_obj: IFilter,
                          raw_data: List[Dict]):
    query_converter = ConsulQueryConverterWithData(model)
    return query_converter.build(filter_obj, raw_data)

class ConsulKeyTemplate:
    """Class-helper for storing consul key structure."""

    _OBJECT_ROOT = f"{CONSUL_ROOT}/$OBJECT_TYPE"
    _OBJECT_DIR = _OBJECT_ROOT + f"/{OBJECT_DIR}"
    _OBJECT_PATH = _OBJECT_DIR + "/$OBJECT_UUID"
    _PROPERTY_DIR = _OBJECT_ROOT + f"/{PROPERTY_DIR}/$PROPERTY_NAME/$PROPERTY_VALUE"

    def __init__(self):
        self._object_root = Template(self._OBJECT_ROOT)
        self._object_dir = Template(self._OBJECT_DIR)
        self._object_path = Template(self._OBJECT_PATH)
        self._property_dir = Template(self._PROPERTY_DIR)
        self._object_type_is_set = False

    def set_object_type(self, object_type: str) -> None:
        """
        Render templates using given object_type.

        :param str object_type: BaseModel type or collection
        :return:
        """
        self._object_root = Template(
            self._object_root.substitute(OBJECT_TYPE=object_type))
        self._object_dir = Template(
            self._object_dir.substitute(OBJECT_TYPE=object_type))
        self._object_path = Template(
            self._object_path.safe_substitute(OBJECT_TYPE=object_type))
        self._property_dir = Template(
            self._property_dir.safe_substitute(OBJECT_TYPE=object_type))
        self._object_type_is_set = True

    def _render_template(self, template: Union[Template, str],
                         object_type: str = None, **kwargs):
        if not self._object_type_is_set and object_type is None:
            raise DataAccessInternalError("Need to set object type")
        elif object_type is not None:
            template.substitute(OBJECT_TYPE=object_type, **kwargs)

        return template.substitute(**kwargs)

    def get_object_root(self, object_type: str = None):
        return self._render_template(self._object_root, object_type=object_type)

    def get_object_dir(self, object_type: str = None):
        return self._render_template(self._object_dir, object_type=object_type)

    def get_object_path(self, object_uuid: str, object_type: str = None):
        return self._render_template(self._object_path, object_type=object_type,
                                     OBJECT_UUID=object_uuid)

    def get_property_dir(self, property_name: str, property_value: str,
                         object_type: str = None):
        return self._render_template(self._property_dir, object_type=object_type,
                                     PROPERTY_NAME=property_name,
                                     PROPERTY_VALUE=property_value)

class ConsulDB(GenericDataBase):
    """Consul Storage Interface Implementation."""

    consul_client = None
    thread_pool = None
    loop = None

    def __init__(self, consul_client: Consul, model: Type[BaseModel],
                 collection: str,
                 process_pool: ThreadPoolExecutor,
                 loop: asyncio.AbstractEventLoop = None):
        """
        Constructor method.

        :param Consul consul_client: consul client
        :param Type[BaseModel] model: model (class object) to associate it with consul storage
        :param str collection: string represented collection for `model`
        :param ThreadPoolExecutor process_pool: thread pool executor
        :param AbstractEventLoop loop: asyncio event loop
        """
        self._consul_client = consul_client
        self._collection = collection.lower()

        self._query_converter = ConsulQueryConverterWithData(model)

        if not isinstance(model, type) or not issubclass(model, BaseModel):
            raise DataAccessInternalError(
                "Model parameter is not a Class object or not inherited "
                "from cortx.utils.data.access.BaseModel")
        self._model = model  # Needed to build returning objects

        # self._query_service = ConsulQueryService(self._collection, self._consul_client,
        #                                          self._query_converter)

        # TODO: there is problems with process pool switched to thread pool
        self._process_pool = process_pool
        self._loop = loop

        self._templates = ConsulKeyTemplate()
        self._templates.set_object_type(self._collection)
        self._model_scheme = dict()

    @classmethod
    async def create_database(cls, config, collection: str,
                              model: Type[BaseModel],
                              create_schema: bool=True) -> IDataBase:
        """
        Creates new instance of Consul KV DB and performs necessary initializations.

        :param DBSettings config: configuration for consul kv server
        :param str collection: collection for storing model onto db
        :param Type[BaseModel] model: model which instances will be stored in DB
        :param bool create_schema: if the flag is true, the collection will be created.
        :return:
        """
        # NOTE: please, be sure that you avoid using this method twice (or more times) for the same
        # model
        if not all((cls.consul_client, cls.thread_pool, cls.loop)):
            cls.loop = asyncio.get_event_loop()
            try:
                cls.consul_client = Consul(host=config.hosts[0], port=config.port,
                                           loop=cls.loop)
            except ConnectionRefusedError as e:
                raise DataAccessExternalError(f"{e}")
            # needed to perform tree traversal in non-blocking mode
            cls.thread_pool = ThreadPoolExecutor(
                max_workers=multiprocessing.cpu_count())

        consul_db = cls(cls.consul_client, model, collection, cls.thread_pool,
                        cls.loop)

        try:
            if create_schema:
                await consul_db.create_object_root()
        except ClientConnectorError as e:
            raise DataAccessExternalError(f"{e}")
        except Exception as e:
            raise DataAccessError(
                f"Some unknown exception occurred in Consul module: {e}")

        return consul_db

    async def create_object_root(self) -> None:
        """
        Provides async method to initialize key structure for given object type.

        :return:
        """
        async def _create_obj_dir():
            """
            Create obj dir if it does not exist and load model_scheme.

            :return:
            """
            _index, _data = await self._consul_client.kv.get(obj_dir)
            if _data is None:
                self._model_scheme = dict.fromkeys(self._model.fields.keys())
                _response = await self._consul_client.kv.put(obj_dir,
                                                             json.dumps(
                                                                 self._model_scheme))
                if not _response:
                    raise DataAccessExternalError(f"Can't put key={obj_root} and "
                                                  f"value={str(creation_time)}")
            else:
                self._model_scheme = json.loads(_data[ConsulWords.VALUE])

        obj_root = self._templates.get_object_root()
        obj_dir = self._templates.get_object_dir()
        _, data = await self._consul_client.kv.get(obj_root)
        if data is None:
            # maybe need to post creation time
            creation_time = datetime.now()
            response = await self._consul_client.kv.put(obj_root,
                                                        str(creation_time))
            if not response:
                raise DataAccessExternalError(f"Can't put key={obj_root} and "
                                              f"value={str(creation_time)}")

        await _create_obj_dir()  # create if it is not exists

    async def store(self, obj: BaseModel):
        """
        Store object into Storage.

        :param Model obj: Arbitrary base object for storing into DB

        """
        await super().store(obj)  # Call the generic code

        obj_path = self._templates.get_object_path(obj.primary_key_val)
        obj_path = obj_path.lower()

        obj_val = json.dumps(obj.to_primitive())
        response = await self._consul_client.kv.put(obj_path, obj_val)
        if not response:
            raise DataAccessExternalError(
                f"Can't put key={obj_path} and value={obj_val}")

    async def _get_all_raw(self) -> List[Dict]:
        obj_dir = self._templates.get_object_dir()
        obj_dir = obj_dir.lower() + "/"  # exclude key cortx/base/type/obj without trailing "/"
        _, data = await self._consul_client.kv.get(obj_dir, recurse=True,
                                                       consistency=True)
        if data is None:
            return list()
        return data

    async def get(self, query: Query) -> List[BaseModel]:
        """
        Get object from Storage by Query.

        :param query:
        :return: empty list or list with objects which satisfy the passed query condition.
        """
        def _sorted_key_func(_by_field, _field_type):
            """
            Generates key function for built-in sorted function to perform correct sorting of get results.

            :param _by_field: field which will be used for sorting (ordering by)
            :param _field_type: type of the field which will be used for sorting
            :return:
            """
            # TODO: for other types we can define other wrapper-functions
            wrapper = str.lower if _field_type is StringType else lambda x: x
            return lambda x: wrapper(getattr(x, _by_field))

        query = query.data

        suitable_models = await self._get_all_raw()

        if not suitable_models:
            return list()

        # NOTE: use processes for parallel data calculations and make true asynchronous work
        if query.filter_by is not None:
            suitable_models = await self._loop.run_in_executor(self._process_pool,
                                                               query_converter_build,
                                                               self._model,
                                                               query.filter_by,
                                                               suitable_models)

        base_models = [self._model(json.loads(entry[ConsulWords.VALUE]))
                       for entry in suitable_models]

        # NOTE: if offset parameter is set in Query then order_by option is enabled automatically
        if any((query.order_by, query.offset)):
            field = query.order_by.field if query.order_by else getattr(
                self._model,
                self._model.primary_key)
            field_str = field_to_str(field)

            field_type = type(getattr(self._model, field_str))

            reverse = SortOrder.DESC == query.order_by.order if query.order_by else False
            key = _sorted_key_func(field_str, field_type)
            base_models = sorted(base_models, key=key, reverse=reverse)

        offset = query.offset or 0
        limit = offset + query.limit if query.limit is not None else len(
            base_models)
        # NOTE: if query.limit is None then slice will be from offset to the end of array
        #  slice(0, None) means that start is 0 and stop is not specified
        if offset < 0 or limit < 0:
            raise DataAccessInternalError(
                "Wrong offset and limit parameters of Query object: "
                f"offset={query.offset}, limit={query.limit}")
        model_slice = slice(offset, limit)
        return base_models[model_slice]

    async def update(self, filter_obj: IFilter, to_update: dict) -> int:
        """
        Update object in Storage by filter.

        :param IFilter filter_obj: filter which specifies what objects need to update
        :param dict to_update: dictionary with fields and values which should be updated
        :return: number of entries updated
        """
        await super().update(filter_obj, to_update)  # Call the generic code

        raw_data = await self._get_all_raw()

        if not raw_data:
            return 0

        # NOTE: use processes for parallel data calculations and make true asynchronous work
        suitable_models = await self._loop.run_in_executor(self._process_pool,
                                                           query_converter_build,
                                                           self._model,
                                                           filter_obj,
                                                           raw_data)
        base_models = [self._model(json.loads(entry[ConsulWords.VALUE]))
                       for entry in suitable_models]

        for model in base_models:
            # use any to invoke map over each parameter
            any(map(setattr, (model for _i in range(len(to_update))),
                    to_update.keys(),
                    to_update.values()))
            await self.store(model)

        return len(base_models)  # return number of entries updated

    async def delete(self, filter_obj: IFilter) -> int:
        """
        Delete objects in DB by Query.

        :param IFilter filter_obj: filter object to perform delete operation
        :return: number of deleted entries
        """
        raw_data = await self._get_all_raw()

        if not raw_data:
            return 0

        # NOTE: use processes for parallel data calculations and make true asynchronous work
        suitable_models = await self._loop.run_in_executor(self._process_pool,
                                                           query_converter_build,
                                                           self._model,
                                                           filter_obj,
                                                           raw_data)
        suitable_models = list(suitable_models)
        if not suitable_models:
            return 0  # No models are deleted

        tasks = [asyncio.ensure_future(
            self._consul_client.kv.delete(model[ConsulWords.KEY])) for
                 model in suitable_models]

        done, _ = await asyncio.wait(tasks)

        for task in done:
            if not task.result():
                raise DataAccessInternalError(
                    f"Error happens during object deleting")

        return len(suitable_models)

    async def delete_by_id(self, obj_id: Union[int, str]) -> None:
        obj_path = self._templates.get_object_path(str(obj_id))
        obj_path = obj_path.lower()
        response = await self._consul_client.kv.delete(obj_path)
        if not response:
            raise DataAccessExternalError(
                f"Error happens during object deleting with id={obj_id}")

    async def count(self, filter_obj: IFilter = None) -> int:
        """
        Returns count of entities for given filter_obj.

        :param IFilter filter_obj: filter to perform count aggregation
        :return: count of entries which satisfy the `filter_obj`
        """
        raw_data = await self._get_all_raw()

        if not raw_data:
            return 0

        if filter_obj is None:
            return len(raw_data)

        # NOTE: use processes for parallel data calculations and make true asynchronous work
        suitable_models = await self._loop.run_in_executor(self._process_pool,
                                                           query_converter_build,
                                                           self._model,
                                                           filter_obj,
                                                           raw_data)

        return len(list(suitable_models))

    async def count_by_query(self, ext_query: ExtQuery):
        """
        Count Aggregation function.

        :param ExtQuery ext_query: Extended query which describes to perform count aggregation.
        """
        pass

    async def get_by_prefix(self):
        """Get by prefix."""
