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

from schematics.models import Model


PRIMARY_KEY_FIELD = "_id"


class PrimaryKey:

    def __init__(self, model_id=None):
        self._id = model_id or PRIMARY_KEY_FIELD

    def __get__(self, instance, owner):
        if instance is None:
            # It means that this method is called from class itself
            return getattr(owner, self._id)

        return getattr(instance, self._id)

    def __set__(self, instance, value):
        if instance is None:
            raise TypeError("'__set__' method is called when instance is None")
        setattr(instance, self._id, value)


class PrimaryKeyValue:

    def __init__(self, model_id=None):
        self._id = model_id or PRIMARY_KEY_FIELD

    def __get__(self, instance, owner):
        if instance is None:
            primary_key_field = getattr(owner, self._id)
            return getattr(owner, primary_key_field)

        primary_key_field = getattr(instance, self._id)
        return getattr(instance, primary_key_field)

    def __set__(self, instance, value):
        if instance is None:
            raise TypeError("'__set__' method is called when instance is None")

        primary_key_field = getattr(instance, self._id)
        setattr(instance, primary_key_field, value)


class BaseModel(Model):
    """
    Base model
    """

    _id = None  # This field used as Primary key of the Model
    primary_key = PrimaryKey()
    primary_key_val = PrimaryKeyValue()

    # TODO: based on primary key we can define compare operations for BaseModel instances
    # TODO: based on primary key we can define hashing of BaseModel instances
