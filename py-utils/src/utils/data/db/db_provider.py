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

from asyncio import coroutine
from pydoc import locate
from enum import Enum
from typing import Type

from schematics import Model
from schematics.types import DictType, StringType, ListType, ModelType, IntType

from cortx.utils.data.access import BaseModel
from cortx.utils.log import Log
from cortx.utils.errors import MalformedConfigurationError, DataAccessInternalError, DataAccessError
from cortx.utils.data.access import AbstractDataBaseProvider

import cortx.utils.data.db as db_module
from cortx.utils.synchronization import ThreadSafeEvent


DEFAULT_HOST = "127.0.0.1"


class ServiceStatus(Enum):
    NOT_CREATED = "Not created"
    IN_PROGRESS = "In progress"
    READY = "Ready"


class DBSettings(Model):
    """
    Settings for database server
    """

    host = StringType(required=True, default=DEFAULT_HOST)
    port = IntType(required=True, default=None)
    login = StringType()
    password = StringType()
    replication = IntType(required=False, default=0)


class DBConfig(Model):
    """
    Database driver configuration description
    """

    import_path = StringType(required=True)
    config = ModelType(DBSettings)  # db-specific configuration


class ModelSettings(Model):
    """
    Configuration for base model like collection as example
    """
    collection = StringType(required=True)


class DBModelConfig(Model):
    """
    Description of how a specific model is expected to be stored
    """

    import_path = StringType(required=True)
    database = StringType(required=True)
    # this configuration is specific for each supported by model db driver
    config = DictType(ModelType(ModelSettings), str)


class GeneralConfig(Model):
    """
    Layout of full database configuration
    """

    databases = DictType(ModelType(DBConfig), str)
    models = ListType(ModelType(DBModelConfig))


class ProxyStorageCallDecorator:
    """Class to decorate proxy call"""

    def __init__(self, async_storage, model: Type[BaseModel], attr_name: str, event: ThreadSafeEvent):
        self._async_storage = async_storage
        self._model = model
        self._attr_name = attr_name
        self._event = event
        self._proxy_call_coroutine = None

    def __call__(self, *args, **kwargs) -> coroutine:
        async def async_wrapper():
            async def _wait_db_creation():
                while self._async_storage.storage_status != ServiceStatus.READY:
                    if self._async_storage.storage_status == ServiceStatus.NOT_CREATED:
                        # Note: Call create_database one time per Model
                        await self._async_storage.create_database()
                    elif self._async_storage.storage_status == ServiceStatus.IN_PROGRESS:
                        await self._event.wait()
                        self._event.clear()

            await _wait_db_creation()  # Wait until db will be created
            database = self._async_storage.get_database()
            if database is None:
                raise DataAccessInternalError("Database is not created")
            attr = database.__getattribute__(self._attr_name)
            if callable(attr):
                # may be, first call the function and then check whether we need to await it
                # DD: I think, we assume that all storage API are async
                return await attr(*args, **kwargs)
            else:
                return attr

        self._proxy_call_coroutine = async_wrapper()
        return self._proxy_call_coroutine

    def __del__(self):
        """
        Close proxy call coroutine if it was never awaited

        :return:
        """
        if self._proxy_call_coroutine is not None:
            self._proxy_call_coroutine.close()


# TODO: class can't be inherited from IDataBase
class AsyncDataBase:
    """
    Decorates all storage async calls and async db drivers and db storages initializations
    """

    def __init__(self, model: Type[BaseModel], model_config: DBModelConfig,
                 db_config: GeneralConfig):
        self._event = ThreadSafeEvent()
        self._model = model
        self._model_settings = model_config.config.get(model_config.database)
        self._db_config = db_config.databases.get(model_config.database)
        Log.info(f'Connect to DB {self._db_config.config.host}:{self._db_config.config.port}')
        self._database_status = ServiceStatus.NOT_CREATED
        self._database_module = getattr(db_module, self._db_config.import_path)
        self._database = None

    def __getattr__(self, attr_name: str) -> coroutine:
        _proxy_call = ProxyStorageCallDecorator(self, self._model, attr_name, self._event)
        return _proxy_call

    async def create_database(self) -> None:
        self._database_status = ServiceStatus.IN_PROGRESS
        try:
            self._database = await self._database_module.create_database(self._db_config.config,
                                                                         self._model_settings.collection,
                                                                         self._model)
        except DataAccessError:
            raise
        except Exception as e:
            raise DataAccessError(f"Unexpected message happened: {e}")
        else:
            self._database_status = ServiceStatus.READY
        finally:
            if not self._database_status == ServiceStatus.READY:
                # attempt to create database was unsuccessful. Setup initial state
                self._database_status = ServiceStatus.NOT_CREATED
            self._event.set()  # weak up other waiting coroutines

    def get_database(self):
        # Note: database can be None
        return self._database

    @property
    def storage_status(self):
        return self._database_status


class DataBaseProvider(AbstractDataBaseProvider):

    _cached_async_decorators = dict()  # Global for all DbStorageProvider instances

    def __init__(self, config: GeneralConfig):
        self.general_config = config
        self.model_settings = {}

        for model in config.models:
            # TODO: improve model loading
            model_class = locate(model.import_path)

            if not model_class:
                raise MalformedConfigurationError(f"Couldn't import '{model.import_path}'")

            if not issubclass(model_class, BaseModel):
                raise MalformedConfigurationError(f"'{model.import_path}'"
                                                  f" must be a subclass of BaseModel")

            self.model_settings[model_class] = model

    def get_storage(self, model: Type[BaseModel]):
        if model not in self.model_settings:
            raise MalformedConfigurationError(f"No configuration for {model}")

        model_settings = self.model_settings[model].config.get(
            self.model_settings[model].database, None)
        if model_settings is None:
            raise MalformedConfigurationError(f"No model settings for '{model}' and database "
                                              f"'{self.model_settings[model].database}'")

        if model in self._cached_async_decorators:
            return self._cached_async_decorators[model]

        self._cached_async_decorators[model] = AsyncDataBase(model, self.model_settings[model],
                                                             self.general_config)
        return self._cached_async_decorators[model]
