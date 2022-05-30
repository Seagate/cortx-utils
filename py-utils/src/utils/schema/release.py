# CORTX Python common library.
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

from itertools import zip_longest
from cortx.utils.conf_store import Conf, MappedConf
from cortx.utils import const
from cortx.utils.schema.payload import Text

import errno

class Manifest:

    def __init__(self, manifest_url: str):
        """Load conf url."""
        self._index = 'manifest_conf'
        Conf.load(self._index, manifest_url)

    def _get_val(self, key: str):
        """Get value for given key."""
        val = Conf.get(self._index, key, '')
        return val


class Release(Manifest):

    def __init__(self, release_info_url: str):
        """Load RELEASE.INFO file url."""
        super().__init__(release_info_url)

    def get_release_version(self):
        """Return release version."""
        release_version = self._get_val('VERSION')
        return release_version

    def get_component_version(self, component: str):
        """Return component version."""
        rpms = self._get_val('COMPONENTS')
        component_rpm = self._get_rpm_from_list(component, rpms)
        version = self._get_rpm_version(component_rpm)
        # Remove git_hash from rpm_version.
        while version.find('_') != -1:
            version = version.split('_')[0]
        return version

    def validate(self, release_spec: dict = None):
        """Compare given release_spec with RELEASE.INFO file.

            Return correct release info define in RELEASE.INFO file."""
        release_info = {}
        is_valid = True
        keys = ['name', 'version']
        for key in keys:
            value = self._get_val(key.upper())
            if release_spec is None or release_spec.get(key) != value:
                is_valid = False
                release_info[key] = value
        return is_valid, release_info

    @staticmethod
    def version_check(deploy_version: str, release_version: str):
        """Compare deployed and release version.

            e.g:
            deploy_version = 2.0.0-428
            release_version = 2.0.0-430
            Return code:
            0 - If both versions are equal.
            1 - If deployed_version > release_version.
            -1 - If deployed_version < release_version.
        """
        ret_code = 0
        if deploy_version == release_version:
            return ret_code
        # Fetch all the digits present in string for comparison.
        deploy_digits = Release._get_digits(deploy_version)
        release_digits = Release._get_digits(release_version)
        for deploy_digit, release_digit in zip_longest(deploy_digits, release_digits, fillvalue=-1):
            if deploy_digit < release_digit:
                ret_code = -1
                break
            elif deploy_digit > release_digit:
                ret_code = 1
                break
        return ret_code

    @staticmethod
    def is_version_compatible(resource_type:str, resource_id:str, version_clauses:list):
        """
        Validates whether a version is compatible for update.

        Parameters:
        resource_type: Resource type like node, cluster (currently supports only node).
        resource_id - Name/Id of the node/cluster (as in gconf).
        version_clauses - Version compatibilty rules. example: ['cortx-csm_agent >= 2.0.0-5255'].

        Returns:
        status - True if version is compatible for upgrade else returns False.
        reason - Reason why the given version is not compatible for update.
        """
        #TODO: Decide on cluster version compatibilty design and add support
        if resource_type == 'cluster':
            raise NotImplementedError("Compatibilty check at cluster level is not yet supported")

        if not Release._validate_clauses(version_clauses):
            raise ReleaseError(errno.EINVAL, "Invalid compatibility rules %s" % version_clauses)

        # Get version details of all the components
        consul_conf = Text(const.CONSUL_CONF)
        conf_url = str(consul_conf.load()).strip()
        installed_versions = Release.get_installed_version(resource_id, conf_url)
        if not installed_versions:
            raise ReleaseError(ReleaseError.INTERNAL_ERROR, "Installed versions not found")

        validation_count =  0
        # Determine if the new version is compatible with the deployed version.
        for component, version in installed_versions.items():
            for clause in version_clauses:
                name, new_version = Release._parse_version(clause, const.VERSION_UPGRADE)
                if component == const.COMPONENT_NAME_MAP[name]:
                    validation_count += 1
                    if Release.version_check(version, new_version) == -1:
                        reason = f"{component} deployed version {version} is older " + \
                                f"than the compatible version {new_version}."
                        return False, reason
                    break

        if validation_count != len(installed_versions):
            raise ReleaseError(errno.EINVAL, "Incomplete compatibilty rules %s" % version_clauses)

        return True, "Versions are Compatible"

    @staticmethod
    def _validate_clauses(version_clauses:list):
        """Validate compatibility rules for component name and version operator."""
        for clause in version_clauses:
            # Validate clause for valid component name.
            if not clause.split('>=')[0].strip() in const.COMPONENT_NAME_MAP:
                return 0

            # Validate clause for version operator '>='.
            if len(clause.split('>=')) < 1:
                return 0
        return 1

    @staticmethod
    def _parse_version(clause:str, operation:str):
        """
        Parse the compatibility rule and get the new version.

        Parameters:
        clause: Compatibilty condition ex. cortx-prvsnr >= 2.0.0-0.
        operation: Version operation like UPGRADE or DOWNGRADE.
        """
        name = ""
        version = 0
        # get upgrade compatible version
        if operation.upper() == const.VERSION_UPGRADE:
            name = clause.split('>=')[0].strip()
            version = clause.split('>=')[1].split('<=')[0].strip()
        return name, version

    @staticmethod
    def get_installed_version(resource_id:str, conf_url:str):
        """
        Get current deployed versions on the node.

        Parameters:
        resource_id - Name of the node (as in gconf).
        conf_url - Global Configuration URL.
        """
        node_id = None
        version_info = {}
        version_conf = MappedConf(conf_url)

        # Get list of all the nodes in the cluster.
        node_list = Release._get_node_list(version_conf)
        for node in node_list:
            if resource_id == version_conf.get(const.NODE_NAME_KEY % node):
                node_id = node
        if node_id is None:
            raise ReleaseError(errno.EINVAL, "Invalid Resource Id %s." % resource_id)

        # Get version details of all the components of a node
        num_components = int(version_conf.get(const.NUM_COMPONENTS_KEY % node_id))
        for component in range(0, num_components):
            _name = version_conf.get(const.COMPONENT_NAME_KEY % (node_id, component))
            _version = version_conf.get(const.COMPONENT_VERSION_KEY % (node_id, component))
            if _version is not None:
                version_info[_name] = _version
            else:
                raise ReleaseError(ReleaseError.INTERNAL_ERROR,
                "No installed version found for component %s" % _name)

        # get cluster release version
        release_name =  version_conf.get(const.RELEASE_NAME_KEY)
        release_version = version_conf.get(const.RELEASE_VERSION_KEY)
        version_info[release_name] = release_version

        return version_info if len(version_info) > 1 else 0

    @staticmethod
    def _get_node_list(version_conf:MappedConf):
        """
        Get list of node Id.

        Parameters:
        version_conf - ConfStore instance of Gconf.
        """
        node_list = []
        num_storage_set = int(version_conf.get(const.NUM_STORAGESET_KEY))
        for storage_set_idx in range(0, num_storage_set):
            num_nodes = int(version_conf.get(const.NUM_NODES_KEY % storage_set_idx))
            for node_idx in range(0, num_nodes):
                # Add node id to node list. ex: cluster>storage_set[storage_set_idx]>nodes[node_idx].
                # node list: [ '0cdf725015124cbbbc578114dbc51982' ].
                node_list.append(version_conf.get(const.NODE_ID_KEY % (storage_set_idx, node_idx)))
        return node_list

    @staticmethod
    def _get_rpm_from_list(component: str, search_list: list):
        """Search rpm name for given component in rpm list."""
        matched_string = ''
        try:
            matched_string = [x for x in search_list if component in x][0]
        except IndexError:
            raise Exception(f'RPM not found for {component} component.')
        return matched_string

    @staticmethod
    def _get_rpm_version(rpm_name: str):
        """Get version from rpm-name."""
        version = ''
        temp_list = []
        try:
            for element in rpm_name.split('-'):
                if element[0].isdigit():
                    temp_list.append(element)
            # Now num_list contains version and githash number
            # e.g ['2.0.0', '438_b3c80e82.x86_64.rpm']
            # Remove .noarch.rpm,.x86_64.rpm, .el7.x86_64, _e17.x86_64 from version string.
            if '.el7' in temp_list[1]:
                temp_list[1] = temp_list[1].split(str('.el7'))[0]
            elif '_el7' in temp_list[1]:
                temp_list[1] = temp_list[1].split('_el7')[0]
            elif '.noarch' in temp_list[1]:
                temp_list[1] = temp_list[1].split('.noarch')[0]
            elif '.x86_64' in temp_list[1]:
                temp_list[1] = temp_list[1].split('.x86_64')[0]
            version = temp_list[0] + '-' + temp_list[1]
        except IndexError as e:
            raise Exception(f'Exception occurred {e}.')
        return version

    @staticmethod
    def _get_digits(version_str: str):
        """Get digit from the given string."""
        digits = []
        for elem in list(version_str):
            if elem.isdigit():
                digits.append(int(elem))
        return digits

class ReleaseError(Exception):
    
    """ Generic Exception with error code and output """

    INTERNAL_ERROR = 0x1005

    def __init__(self, rc, message, *args):
        """Initialize self."""
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        """Return str(self)."""
        if self._rc == 0: return self._desc
        return "error(%d): %s" % (self._rc, self._desc)
