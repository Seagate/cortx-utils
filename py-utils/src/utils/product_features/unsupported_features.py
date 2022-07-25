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

from cortx.utils.common import DbConf
from cortx.utils.data.access import Query
from cortx.utils.data.access.filters import Compare, And
from cortx.utils.data.db.db_provider import DataBaseProvider, GeneralConfig
from cortx.utils import const
from cortx.utils.product_features.model import UnsupportedFeaturesModel

class UnsupportedFeaturesDB:
    def __init__(self) -> None:
        """Init load consul db for storing key in db."""
        DbConf.init(const.CLUSTER_CONF)
        dict_conf = DbConf.export_database_conf()
        conf = GeneralConfig(dict_conf)
        self.storage = DataBaseProvider(conf)

    async def store_unsupported_feature(self, component_name, feature_name):
        """
        Store un-supported features in db.

        :param component_name: Name of Component :type :String.
        :param feature_name: Name of Feature :type: String.
        :return:
        """
        # Generate Key
        feature_id = UnsupportedFeaturesModel.create_feature_id(component_name,
                                                                const.UNSUPPORTED_FEATURE,
                                                                feature_name)
        # Generate unsupported_features DB Object.
        feature = UnsupportedFeaturesModel.instantiate_decision(feature_id,
                                                                feature_name,
                                                                component_name)
        # Save Data.
        await self.storage(UnsupportedFeaturesModel).store(feature)

    async def get_unsupported_features(self, component_name = "",
        feature_name = ""):
        """
        Get Unsupported Features in Following Formats.

            1) No Component Name : Return All Features List.
            2) No Feature Name : Return All the Features Related to Components Provided.
        :param component_name: Name of Component :type: String
        :param feature_name: Name of Feature :type: String
        :return: List of Features Found.
        """
        query = Query()
        # Generate Key
        if component_name:
            query.filter_by(Compare(
                UnsupportedFeaturesModel.component_name, "=", component_name))
            if feature_name:
                query.filter_by(And(Compare(
                    UnsupportedFeaturesModel.feature_name, "=", feature_name)))

        feature_details = await self.storage(UnsupportedFeaturesModel).get(
            query)
        if not feature_details:
            return []
        return [each_feature.to_primitive() for each_feature in feature_details]

    async def is_feature_supported(self, component_name, feature_name):
        """
        Check whether the feature supported or not.

        :param component_name: Name of Component :type: String
        :param feature_name: Name of Feature :type: String
        :return: Supported -> True/Not-Supported -> False
        """
        feature_id = UnsupportedFeaturesModel.create_feature_id(
            *(component_name, const.UNSUPPORTED_FEATURE, feature_name))
        # Create Query
        query = Query().filter_by(
            Compare(UnsupportedFeaturesModel.feature_id, '=', feature_id))
        feature = await self.storage(UnsupportedFeaturesModel).get(query)
        if feature:
            return False
        return True

    async def store_unsupported_features(self, component_name, features):
        """
        Store Multiple un-supported features for a single component in db.

        :param component_name: Name of Component :type :String.
        :param features: List of Features :type: List.
        :return:
        """
        if not isinstance(features, list):
            raise TypeError("Unsupported Type for features.")

        for each_feature in features:
            await self.store_unsupported_feature(component_name, each_feature)
