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
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from distutils.util import strtobool
import ldap
import ldap.modlist
import multiprocessing
from schematics.exceptions import ConversionError
from schematics.types import BaseType, BooleanType, DateTimeType, StringType
from typing import Dict, List, Optional, Type, Union

from cortx.utils.data.access import BaseModel, IDataBase, Query, SortOrder
from cortx.utils.data.access.filters import (ComparisonOperation, IFilter, FilterOperationAnd,
                                             FilterOperationCompare, FilterOperationOr)
from cortx.utils.data.db import GenericDataBase, GenericQueryConverter
from cortx.utils.errors import DataAccessInternalError


class OpenLdapSyntaxTools:
    @staticmethod
    def generalize_field_name(field_name: str) -> str:
        """
        Converts the model field name to an LDAP attribute name.

        :param field_name: model field name.
        :returns: LDAP attribute name as a string.
        """

        return field_name.translate(str.maketrans('_', '-'))

    @staticmethod
    def pythonize_attr_name(attr_name: str) -> str:
        """
        Converts the LDAP attribute's name to an field name of a Python model.

        :param attr_name: attribute name.
        :returns: field name as a string.
        """

        return attr_name.translate(str.maketrans('-', '_'))

    @staticmethod
    def _generalize_datetime(timestamp: datetime) -> str:
        """
        Converts the datetime to format stored in LDAP.

        :param timestamp: datetime object to generalize.
        :returns: generalized timestamp as a string.
        """

        return timestamp.strftime('%Y%m%d%H%M%SZ')

    @staticmethod
    def _pythonize_datetime(attr_timestamp: str) -> datetime:
        """
        Converts an OpenLdap's timestamp to Python datetime.

        :param attr_timestamp: timestamp from OpenLdap's attribute.
        :returns: datetime object.
        """

        return datetime.strptime(attr_timestamp, '%Y%m%d%H%M%SZ')

    @staticmethod
    def _pythonize_bool(attr_bool: str) -> bool:
        """
        Converts an OpenLdap's boolean string to Python bool.

        :param attr_bool: Boolean string from OpenLdap's attribute.
        :returns: bool object.
        """

        return bool(strtobool(attr_bool))

    @staticmethod
    def generalize_field_value(value: object, to_bytes: bool = True) -> str:
        """
        Converts a model field value into a format stored in LDAP.

        :param value: model field value to convert.
        :param to_bytes: flag to convert the resulting string to bytes object.
        :returns: generalized field value as a string.
        """

        default_converter = str
        special_converters = {
            datetime: OpenLdapSyntaxTools._generalize_datetime,
            bool: lambda x: str(x).upper()
        }
        converter = special_converters.get(type(value), default_converter)
        ret = converter(value)
        if to_bytes:
            # OpenLdap expects a list of bytes objects for addition and update
            ret = [ret.encode('utf-8')]
        return ret

    @staticmethod
    def pythonize_attr_value(model: BaseModel, attr_name: str, attr_value: str) -> object:
        """
        Converts an OpenLdap attribute's value to Python model's field value.

        :param model: objects's model.
        :param value: attribute value.
        :returns: object for model's field.
        """

        special_converters = {
            DateTimeType: OpenLdapSyntaxTools._pythonize_datetime,
            BooleanType: OpenLdapSyntaxTools._pythonize_bool,
        }

        model_field = getattr(model, attr_name)
        converter = special_converters.get(type(model_field), lambda x: x)
        # OpenLdap returns attributes as lists of bytes objects
        attr_value = attr_value[0].decode('utf-8')
        return converter(attr_value)


# TODO: to some generic db helper
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


class OpenLdapQueryConverter(GenericQueryConverter):
    def __init__(self, model: BaseModel) -> None:
        """
        Initialize OpenLdapQueryConverter.

        :param model: object model to query.
        :returns: None.
        """

        self._model = model

    def _handle_composite(self, op: str, conditions: IFilter) -> str:
        """
        Handle filter that includes a list of conditions.

        :param op: filter operation.
        :param conditions: a list of conditions.
        :returns: compiled filter as a string.
        """

        conditions_filter_list = [f'({condition.accept_visitor(self)})' for condition in conditions]
        conditions_filter_str = ''.join(conditions_filter_list)
        return f'{op}{conditions_filter_str}'

    def handle_and(self, entry: FilterOperationAnd) -> str:
        """
        Handle the 'AND' filter.

        :param entry: filter object.
        :returns: compiled filter as a string.
        """

        operands = entry.get_operands()
        return self._handle_composite('&', operands)

    def handle_or(self, entry: FilterOperationOr) -> str:
        """
        Handle the 'OR' filter.

        :param entry: filter object.
        :returns: compiled filter as a string.
        """
        operands = entry.get_operands()
        return self._handle_composite('|', operands)

    def handle_compare(self, entry: FilterOperationCompare) -> str:
        """
        Handle all kinds of comparison filters: '<', '<=', '>', '>=', '==', '!=', 'LIKE'

        :param entry: filter object.
        :returns: compiled filter as a string.
        """

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
        field_str = OpenLdapSyntaxTools.generalize_field_name(field_str)
        right_operand = OpenLdapSyntaxTools.generalize_field_value(right_operand, to_bytes=False)
        if op == ComparisonOperation.OPERATION_LIKE:
            op = ComparisonOperation.OPERATION_EQ
            right_operand = f'*{right_operand}*'
        return f'{field_str}{op.value}{right_operand}'

    def build(self, root: IFilter) -> str:
        """
        Builds a filter for OpenLdap.

        :param root: filter object.
        :returns: filter for OpenLdap as a string.
        """

        filter_str = root.accept_visitor(self)
        return f'({filter_str})'


class OpenLdap(GenericDataBase):
    _client: ldap.ldapobject.LDAPObject = None
    _loop: asyncio.AbstractEventLoop = None
    _thread_pool: ThreadPoolExecutor = None

    def __init__(
        self, ldap_client: ldap.ldapobject.LDAPObject, model: Type[BaseModel], collection: str,
        thread_pool: ThreadPoolExecutor, loop: asyncio.AbstractEventLoop = None
    ) -> None:
        """
        Initialize openldap client.

        :param ldap_client: ldap client.
        :param model (class object) to be stored in ldap.
        :param collection: base DN for stored object.
        :param thread_pool: thread pool executor.
        :param loop: asyncio event loop.
        :returns: None
        """

        self._client = ldap_client
        self._collection = collection
        self._query_converter = OpenLdapQueryConverter(model)

        if not isinstance(model, type) or not issubclass(model, BaseModel):
            raise DataAccessInternalError(
                "Model parameter is not a Class object or not inherited "
                "from cortx.utils.data.access.BaseModel")

        self._model = model
        self._thread_pool = thread_pool
        self._loop = loop

    @staticmethod
    def _ldap_init(host: str, port: int) -> ldap.ldapobject.LDAPObject:
        """
        Initialize the internal LDAP client.

        :param host: LDAP server host.
        :param port: LDAP server port.
        :returns: internal LDAP client object.
        """

        LDAP_PROTO = 'ldap'
        ldap_url = f'{LDAP_PROTO}://{host}:{port}'
        ldap_obj = ldap.initialize(ldap_url, bytes_mode=False)
        return ldap_obj

    @staticmethod
    def _ldap_object_to_modlist(obj: BaseModel) -> ldap.modlist.addModlist:
        """
        Convert object to the LDIF.

        :param obj: object to be stored in OpenLdap.
        :returns: LDIF to store the object.
        """

        attrs = obj.to_native()
        attrs['objectclass'] = type(obj).__name__
        ldif = ldap.modlist.addModlist(attrs)
        return ldif

    @classmethod
    async def create_database(
        cls, config: Dict, collection: str, model: Type[BaseModel], create_schema: bool = False
    ) -> IDataBase:
        """
        Creates new instance of OpenLdap client and performs necessary initializations.

        :param DBSettings config: configuration for OpenLdap server.
        :param str collection: base DN for stored model.
        :param Type[BaseModel] model: model which instances will be stored.
        :param bool create_schema: if the flag is True, the base DN will be created.
        :returns: OpenLdap client instanse
        """

        if not all((cls._client, cls._thread_pool, cls._loop)):
            cls._client = OpenLdap._ldap_init(config.hosts[0], config.port)
            # TODO: bind & unbind immediately after every operation
            cls._client.simple_bind_s(config.login, config.password)
            cls._loop = asyncio.get_event_loop()
            cls._thread_pool = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count())

        ldap_client = cls(cls._client, model, collection, cls._thread_pool, cls._loop)
        if create_schema:
            # TODO: handle schema creation
            pass

        return ldap_client


    @staticmethod
    def _model_to_ldif(model: BaseModel) -> ldap.modlist.addModlist:
        """
        Converts the object model to LDIF.

        Object fields are converted into LDAP attributes in generalized format.

        :param model: object model.
        :returns: LDIF object to be added to LDAP.
        """

        attrs = {}
        attrs['objectClass'] = OpenLdapSyntaxTools.generalize_field_value(type(model).__name__)
        for field, value in model.to_native().items():
            attr_name = OpenLdapSyntaxTools.generalize_field_name(field)
            attr_value = OpenLdapSyntaxTools.generalize_field_value(value)
            attrs[attr_name] = attr_value
        return ldap.modlist.addModlist(attrs)

    def _ldif_to_model(self, attrs: Dict[str, str]) -> BaseModel:
        """
        Converts LDIF from OpenLdap to Model object.

        :param attrs: object attributes from OpenLdap.
        :returns: BaseModel object.
        """

        model_attrs = {}
        del(attrs['objectClass'])
        for attr_name, attr_value in attrs.items():
            model_attr_name = OpenLdapSyntaxTools.pythonize_attr_name(attr_name)
            model_attr_value = OpenLdapSyntaxTools.pythonize_attr_value(
                self._model, model_attr_name, attr_value)
            model_attrs[model_attr_name] = model_attr_value
        return self._model(model_attrs)

    def _get_object_dn(self, obj: BaseModel) -> str:
        """
        Construct object DN.

        :param obj: object to be stored.
        :returns: object's DN as a string.
        """

        primary_key_name = OpenLdapSyntaxTools.generalize_field_name(obj.primary_key)
        dn = f'{primary_key_name}={obj.primary_key_val},{self._collection}'
        return dn

    async def store(self, obj: BaseModel) -> None:
        """
        Stores the provided object in OpenLdap.

        :param obj: object to store.
        :returns: None.
        """

        # TODO: implement self._model_schema to enable validation
        # await super().store(obj)
        dn = self._get_object_dn(obj)
        ldif = OpenLdap._model_to_ldif(obj)
        await self._loop.run_in_executor(self._thread_pool, self._client.add_s, dn, ldif)

    async def _get_ldap(self, filter_obj: Optional[IFilter]) -> List[Dict[str, str]]:
        """
        Gets filtered objects from OpenLdap.

        Includes the Get logic that is empowered by OpenLdap itself.

        :param filter_obj: filter.
        :returns: list of dictionaries.
        """

        # Prepare the filter string
        ldap_filter = self._query_converter.build(filter_obj) if filter_obj else None
        # Query the OpenLdap
        base_dn = self._collection
        base_scope = ldap.SCOPE_ONELEVEL
        raw_attributes = await self._loop.run_in_executor(
            self._thread_pool, self._client.search_s, base_dn, base_scope, ldap_filter)
        models = [self._ldif_to_model(attrs) for _, attrs in raw_attributes]
        return models

    async def get(self, query: Query) -> List[BaseModel]:
        """
        Get object from OpenLdap by query.

        :param query: query object.
        :returns: list with objects that satisfy the query condition.
        """

        def _sorted_key_func(_by_field, _field_type):
            """
            Generates key function for built-in sorted function to perform correct sorting
            of get results

            :param _by_field: field which will be used for sorting (ordering by)
            :param _field_type: type of the field which will be used for sorting
            :return:
            """
            # TODO: for other types we can define other wrapper-functions
            wrapper = str.lower if _field_type is StringType else lambda x: x
            return lambda x: wrapper(getattr(x, _by_field))

        query = query.data
        models = await self._get_ldap(query.filter_by)

        # Sort the result
        if any((query.order_by, query.offset)):
            field = query.order_by.field if query.order_by else getattr(
                self._model,
                self._model.primary_key)
            field_str = field_to_str(field)

            field_type = type(getattr(self._model, field_str))

            reverse = SortOrder.DESC == query.order_by.order if query.order_by else False
            key = _sorted_key_func(field_str, field_type)
            models = sorted(models, key=key, reverse=reverse)

        # Paginate the result
        offset = query.offset or 0
        limit = offset + query.limit if query.limit is not None else len(models)
        # NOTE: if query.limit is None then slice will be from offset to the end of array
        #  slice(0, None) means that start is 0 and stop is not specified
        if offset < 0 or limit < 0:
            raise DataAccessInternalError(
                "Wrong offset and limit parameters of Query object: "
                f"offset={query.offset}, limit={query.limit}")
        model_slice = slice(offset, limit)

        return models[model_slice]

    async def update(self, filter_obj: IFilter, to_update: Dict) -> int:
        pass

    async def delete(self, filter_obj: IFilter) -> int:
        pass
