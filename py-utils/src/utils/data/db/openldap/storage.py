#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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
import multiprocessing
from schematics.exceptions import ConversionError
from schematics.types import BaseType, BooleanType, DateTimeType, StringType
from typing import Dict, List, Optional, Type, Union

from cortx.utils.data.access import BaseModel, IDataBase, Query, SortOrder
from cortx.utils.data.access.filters import (ComparisonOperation, IFilter, FilterOperationAnd,
                                             FilterOperationCompare, FilterOperationOr)
from cortx.utils.data.db import GenericQueryConverter
from cortx.utils.errors import DataAccessExternalError, DataAccessInternalError


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