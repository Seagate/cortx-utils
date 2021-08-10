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

import datetime
from enum import Enum
from typing import Optional
from schematics.types import BaseType
from cortx.utils.data.access.filters import IFilter

class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"

class SortBy:
    def __init__(self, field, order: SortOrder):
        self.field = field
        self.order = order

class QueryLimits:
    def __init__(self, limit: Optional[int], offset: Optional[int]):
        self.limit = limit
        self.offset = offset

class DateTimeRange:
    def __init__(self, start, end):
        self.start = start
        self.end = end

class OrderBy:

    """Class to represent order by parameters for DB"""

    def __init__(self, field, order: SortOrder = SortOrder.ASC, **kwargs):
        self.field = field
        self.order = order
        self.kwargs = kwargs


class Query:

    """Storage Query API"""

    class Data:

        """Data storage class for Query parameters"""

        # TODO: it can be a schematics model
        def __init__(self, order_by: OrderBy = None, filter_by: IFilter = None, limit: int = None,
                     offset: int = None):

            self.order_by = order_by
            self.filter_by = filter_by
            self.limit = limit
            self.offset = offset

    def __init__(self, order_by: OrderBy = None, filter_by: IFilter = None, limit: int = None,
                 offset: int = None):

        self.data = self.Data(order_by, filter_by, limit, offset)

    # TODO: order_by can be chained and we can store an array of fields to sort by them
    def order_by(self, by_field: BaseType, by_order: SortOrder = SortOrder.ASC, **kwargs):
        """
        Set Query order_by parameter

        :param BaseType by_field: particular field to perform ordering
        :param int by_order: direction of ordering

        """
        self.data.order_by = OrderBy(by_field, by_order, **kwargs)
        return self

    def filter_by(self, by_filter: IFilter):
        """
        Set Query filter parameter

        :param IFilter by_filter: filter parameter for Query
        :return:
        """
        self.data.filter_by = by_filter
        return self

    def limit(self, limit: int):
        """
        Set Query limit parameter

        :param int limit: limit for Query operation
        :return:

        """
        self.data.limit = limit
        return self

    def offset(self, offset: int):
        """
        Set Query offset parameter

        :param int offset: offset for Query
        :return:
        """
        self.data.offset = offset
        return self

    # TODO: having functionality


class ExtQuery(Query):

    """Storage Extended Query API used by Storage aggregation functions"""

    class Data:

        """Data storage class for Query parameters"""

        # TODO: it can be a schematics model
        def __init__(self, order_by: OrderBy = None, group_by: BaseType = None,
                     filter_by: IFilter = None, limit: int = None, offset: int = None):

            self.order_by = order_by
            self.group_by = group_by
            self.filter_by = filter_by
            self.limit = limit
            self.offset = offset

    def __init__(self):
        super().__init__()

    def group_by(self, by_field: BaseType):
        """
        Set Query group_by parameter

        :param BaseType by_field: field for grouping

        """
        self.data.group_by = by_field
        return self
