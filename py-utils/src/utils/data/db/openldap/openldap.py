#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2022 Seagate Technology LLC and/or its Affiliates
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

import ldap
import asyncio
import ldap.modlist
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Type

from cortx.utils.data.access.filters import IFilter
from cortx.utils.data.db.generic_storage import GenericDataBase
from cortx.utils.data.access import BaseModel, IDataBase, Query, SortOrder
from cortx.utils.errors import DataAccessExternalError, DataAccessInternalError
from cortx.utils.data.db.openldap.storage import OpenLdapQueryConverter, \
    OpenLdapSyntaxTools, field_to_str


class OpenLdap(GenericDataBase):
    """Open ldap."""

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
            try:
                cls._client.simple_bind_s(config.login, config.password)
            except ldap.LDAPError as le:
                err = f'Failed to bind to OpenLdap server: {le}'
                raise DataAccessExternalError(err) from None
            cls._loop = asyncio.get_event_loop()
            cls._thread_pool = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count())

        ldap_client = cls(cls._client, model, collection, cls._thread_pool, cls._loop)
        if create_schema:
            # Current OpenLdap implementaion in the framework does not support schema creation.
            # Make sure the schema and collections are created before using the framework.
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
        # Current OpenLdap implementation in the framework does not retrieve schema details
        # from the server.
        # Make sure the model corresponds to the pre-created collection before using the framework.
        # await super().store(obj)
        dn = self._get_object_dn(obj)
        ldif = OpenLdap._model_to_ldif(obj)
        try:
            await self._loop.run_in_executor(self._thread_pool, self._client.add_s, dn, ldif)
        except ldap.ALREADY_EXISTS:
            await self.update_by_id(obj.primary_key_val, obj.to_native())
        except ldap.LDAPError as le:
            err = f'Failed to execute add operation with OpenLdap server: {le}'
            raise DataAccessExternalError(err) from None

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
        try:
            raw_attributes = await self._loop.run_in_executor(
                self._thread_pool, self._client.search_s, base_dn, base_scope, ldap_filter)
        except ldap.LDAPError as le:
            err = f'Failed to execute search operation with OpenLdap server: {le}'
            raise DataAccessExternalError(err) from None
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
            from schematics.types import StringType
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

    async def _update_ldap(self, model: BaseModel, to_update: Dict) -> None:
        """
        Update the existing object in LDAP.

        :param model: object's model.
        :param to_update: fields to update.
        :returns: None.
        """
        obj_attrs = model.to_native()
        key_generalizer = OpenLdapSyntaxTools.generalize_field_name
        val_generalizer = OpenLdapSyntaxTools.generalize_field_value
        to_update_distinct = {
            key_generalizer(key): val_generalizer(val) for key, val in to_update.items()
            if val != obj_attrs[key]
        }
        old_attrs_distinct = {
            key_generalizer(key): val_generalizer(val) for key, val in obj_attrs.items()
            if key_generalizer(key) in to_update_distinct
        }

        if to_update_distinct:
            dn = self._get_object_dn(model)
            ldif = ldap.modlist.modifyModlist(old_attrs_distinct, to_update_distinct)
            try:
                await self._loop.run_in_executor(self._thread_pool, self._client.modify_s, dn, ldif)
            except ldap.LDAPError as le:
                err = (f'Failed to execute update operation with OpenLdap server: {le}')
                raise DataAccessExternalError(err) from None

    async def update(self, filter_obj: IFilter, to_update: Dict) -> int:
        """
        Update filtered objects in OpenLdap.

        :param filter_obj: filter.
        :param to_update: attributes with new values.
        :returns: number of updated entries.
        """
        models = await self._get_ldap(filter_obj)
        for model in models:
            await self._update_ldap(model, to_update)
        return len(models)

    async def delete(self, filter_obj: IFilter) -> int:
        """
        Delete objects from OpenLdap by filter.

        :param filter_obj: filter object.
        :returns: number of deleted entries.
        """
        models = await self._get_ldap(filter_obj)
        for model in models:
            dn = self._get_object_dn(model)
            try:
                await self._loop.run_in_executor(self._thread_pool, self._client.delete_s, dn)
            except ldap.LDAPError as le:
                err = (f'Failed to execute delete operation wtih OpenLdap server: {le}')
                raise DataAccessExternalError(err) from None
        return len(models)

    async def count(self, filter_obj: IFilter = None) -> int:
        """
        Count the number of entities matching the filter.

        :param filter_obj: filter object.
        :returns: number of entities.
        """
        models = await self._get_ldap(filter_obj)
        return len(models)
