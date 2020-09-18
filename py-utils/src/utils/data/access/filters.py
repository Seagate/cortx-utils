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

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Any
from cortx.utils.errors import MalformedQueryError


class IFilter(ABC):
    """
    Abstract class for IFilter
    """

    @abstractmethod
    def accept_visitor(self, visitor) -> Any:
        pass


class FilterOperationAnd(IFilter):
    """
    Class representing AND condition
    :param *args: List of nested filter conditions (each must be of type IFilterQuery)
    """

    def __init__(self, *args):
        if len(args) < 2 or not all(isinstance(x, IFilter) for x in args):
            raise MalformedQueryError("AND operation takes >= 2 arguments of filter type")

        self._operands = args

    def accept_visitor(self, visitor):
        return visitor.handle_and(self)

    def get_operands(self) -> List[IFilter]:
        return self._operands


class FilterOperationOr(IFilter):
    """
    Class representing OR condition
    :param *args: List of nested filter conditions (each must be of type IFilterQuery)
    """

    def __init__(self, *args):
        if len(args) < 2 or not all(isinstance(x, IFilter) for x in args):
            raise MalformedQueryError("OR operation takes >= 2 arguments of filter type")

        self._operands = args

    def accept_visitor(self, visitor):
        return visitor.handle_or(self)

    def get_operands(self) -> List[IFilter]:
        return self._operands


class ComparisonOperation(Enum):
    """
    Enumeration that represents possible comparison operations
    """

    OPERATION_GT = '>'
    OPERATION_LT = '<'
    OPERATION_EQ = '='
    OPERATION_LEQ = '<='
    OPERATION_GEQ = '>='
    OPERATION_NE = "!="  # TODO: Add support to elasticsearch
    OPERATION_LIKE = "like" # TODO: Add support to elasticsearch

    @classmethod
    def from_standard_representation(cls, op: str):
        mapping = {
            '=': cls.OPERATION_EQ,
            '>': cls.OPERATION_GT,
            '<': cls.OPERATION_LT,
            '>=': cls.OPERATION_GEQ,
            '<=': cls.OPERATION_LEQ,
            "!=": cls.OPERATION_NE,
            "like": cls.OPERATION_LIKE
        }

        if op in mapping:
            return mapping[op]
        else:
            raise MalformedQueryError("Invalid comparison operation: {}".format(op))


class FilterOperationCompare(IFilter):
    """
    Class representing a comparison operation.
    """

    def __init__(self, left_operand, operation: ComparisonOperation, right_operand):
        self.left_operand = left_operand
        self.operation = operation
        self.right_operand = right_operand

    def accept_visitor(self, visitor):
        return visitor.handle_compare(self)

    def get_left_operand(self):
        return self.left_operand

    def get_right_operand(self):
        return self.right_operand

    def get_operation(self) -> ComparisonOperation:
        return self.operation


class IFilterTreeVisitor(ABC):
    """
    Descendants of this class are supposed to be used for filter tree traversal.
    Application of "visitor" design pattern allows to:
    1) Avoid switch'ing over possible filter types
    2) Not to forget to add handers for new filter types as they are added to the system
    """

    @abstractmethod
    def handle_and(self, entry: FilterOperationAnd):
        pass

    @abstractmethod
    def handle_or(self, entry: FilterOperationOr):
        pass

    @abstractmethod
    def handle_compare(self, entry: FilterOperationCompare):
        pass


def And(*args):
    """
    Adds a condition that demands that all the nested conditions are satisfied.
    :param *args: List of nested conditions (each must be an instance of IFilterQuery)
    :returns: a FilterOperationAnd object
    """
    if not args:
        raise MalformedQueryError("AND operation must take at least 1 argument")

    if len(args) == 1:
        return args[0]

    return FilterOperationAnd(*args)


def Or(*args):
    """
    Adds a condition that demands that at least one of the nested conditions is true.
    :param args: List of nested conditions (each must be an instance of IFilterQuery)
    :returns: a FilterOperationOr object
    """
    if not args:
        raise MalformedQueryError("OR operation must take at least 1 argument")

    if len(args) == 1:
        return args[0]

    return FilterOperationOr(*args)


def Compare(left, operation: str, right):
    """
    Adds a condition that demands some order relation between two items.
    :param left: Left operand. Either a field or a value.
    :param operation: a string corresponding to the required operation, e.g. '=' or '>'
    :param right: Right operand. Either a field or a value.
    :returns: a FilterOperationCompare object
    """
    op = ComparisonOperation.from_standard_representation(operation)
    return FilterOperationCompare(left, op, right)
