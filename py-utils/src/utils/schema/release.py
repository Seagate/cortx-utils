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
from cortx.utils.conf_store import Conf


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

    def version_check(self, deploy_version: str, release_version: str):
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
        deploy_digits = self._get_digits(deploy_version)
        release_digits = self._get_digits(release_version)
        for deploy_digit, release_digit in zip_longest(deploy_digits, release_digits, fillvalue=-1):
            if deploy_digit < release_digit:
                ret_code = -1
                break
            elif deploy_digit > release_digit:
                ret_code = 1
                break
        return ret_code

    def is_version_compatible(self, component:str):
        """
        Checks if version is compatible for upgrade/downgrade.

        Returns True if version is compatible for upgrade/downgrade else returns False.
        Parameters:
        upgrade_version - Deployed image version.
        component - Component to be checked for version compatibility.
        """
        upgrade_version = self._get_val('VERSION')
        min_compatible_versions = self._get_val('REQUIRES')
        try:
            min_compatible_version = [x.split('>=')[1].strip() for x in min_compatible_versions if component in x][0]
        except IndexError:
            raise Exception(f'Compatible version not found for {component}.')
        if self.version_check(upgrade_version, min_compatible_version) == -1:
            return False
        return True

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
