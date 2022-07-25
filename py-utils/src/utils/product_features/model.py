#!/usr/bin/env python3

# CORTX-Utils: CORTX Python common library.
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

from cortx.utils.data.access.base_model import BaseModel
from schematics.types import StringType

class UnsupportedFeaturesModel(BaseModel):
    _id = "feature_id"

    feature_id = StringType()
    feature_name = StringType()
    component_name = StringType()

    @staticmethod
    def create_feature_id(*key_data):
        """
        This method creates the key for saving feature in DB.

        Format:
            /cortx/base/config/obj/<component_name>/UNSUPPORTED_FEATURE/<feature_name>
        :param key_data: Parameters for Feature Consul Key. :type: Tuple
        :return:
        """
        key_data = [str(each_key).upper() for each_key in key_data]
        return "/".join(key_data)

    @staticmethod
    def instantiate_decision(feature_id, feature_name, component_name):
        """
        Generate the unsupported feature DB model object.

        :param feature_id: Created Key for Feature. :type: String.
        :param feature_name: Name of Feature Not Supported in the System. :type: String.
        :param component_name: Name of Component :type: String.
        :return: Model Object.
        """
        unsupported_feature = UnsupportedFeaturesModel()
        unsupported_feature.feature_id = feature_id
        unsupported_feature.feature_name = feature_name
        unsupported_feature.component_name = component_name

        return unsupported_feature
