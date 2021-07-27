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
import ldap
import ldap.modlist
import multiprocessing
from typing import Dict, List, Type

from cortx.utils.data.access import BaseModel, IDataBase, Query
from cortx.utils.data.access.filters import (IFilter, FilterOperationAnd, FilterOperationCompare,
                                             FilterOperationOr)
from cortx.utils.data.db import GenericDataBase, GenericQueryConverter
from cortx.utils.errors import DataAccessInternalError


class OpenLdapQueryConverter(GenericQueryConverter):
    def __init__(self, model: BaseModel) -> None:
        pass

    def handle_and(self, entry: FilterOperationAnd):
        pass

    def handle_or(self, entry: FilterOperationOr):
        pass

    def handle_compare(self, entry: FilterOperationCompare):
        pass


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
    def _generalize_field_name(field_name: str) -> str:
        """
        Converts the model field name to an LDAP attribute name.

        :param field_name: model field name.
        :returns: LDAP attribute name as a string.
        """

        return field_name.translate(str.maketrans('_', '-'))

    @staticmethod
    def _generalize_datetime(timestamp: datetime) -> str:
        """
        Converts the datetime to format stored in LDAP.

        :param timestamp: datetime object to generalize.
        :returns: generalized timestamp as a string.
        """

        return timestamp.strftime('%Y%m%d%H%M%SZ')

    @staticmethod
    def _generalize_field_value(value: object) -> str:
        """
        Converts a model field value into a format stored in LDAP.

        :param value: model field value to convert.
        :returns: generalized field value as a string.
        """

        default_converter = str
        special_converters = {
            datetime: OpenLdap._generalize_datetime,
            bool: lambda x: str(x).upper()
        }
        converter = special_converters.get(type(value), default_converter)
        # OpenLdap expects a list of bytes objects
        return [converter(value).encode('utf-8')]

    @staticmethod
    def _model_to_ldif(model: BaseModel) -> ldap.modlist.addModlist:
        """
        Converts the object model to LDIF.

        Object fields are converted into LDAP attributes in generalized format.

        :param model: object model.
        :returns: LDIF object to be added to LDAP.
        """

        attrs = {}
        attrs['objectclass'] = OpenLdap._generalize_field_value(type(model).__name__)
        for field, value in model.to_native().items():
            attr_name = OpenLdap._generalize_field_name(field)
            attr_value = OpenLdap._generalize_field_value(value)
            attrs[attr_name] = attr_value
        return ldap.modlist.addModlist(attrs)

    def _get_object_dn(self, obj: BaseModel) -> str:
        """
        Construct object DN.

        :param obj: object to be stored.
        :returns: object's DN as a string.
        """

        primary_key_name = OpenLdap._generalize_field_name(obj.primary_key)
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

    async def get(self, query: Query) -> List[BaseModel]:
        """
        Get object from OpenLdap by query.

        :param query: query object.
        :returns: list with objects that satisfy the query condition.
        """

        base_dn = self._collection
        base_scope = ldap.SCOPE_ONELEVEL
        items = await self._loop.run_in_executor(
            self._thread_pool, self._client.search_s, base_dn, base_scope)
        return items
        # TODO: convert list of dictionaries back to objects
        # objects = [self._model(attrs) for dn, attrs in items]
        # return objects

    async def update(self, filter_obj: IFilter, to_update: Dict) -> int:
        pass

    async def delete(self, filter_obj: IFilter) -> int:
        pass
