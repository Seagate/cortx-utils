# CORTX Python common library.
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

from itertools import zip_longest
from cortx.utils.conf_store import Conf


class Manifest:

    @staticmethod
    def _get_val(index, key):
        """Get value for given key."""
        val = Conf.get(index, key, '')
        return val

    @staticmethod
    def _get_elem_from_list(sub_str: str, search_list: list):
        """Get elements from list which contain given sub_str."""
        matched_string = ''
        try:
            matched_string = [x for x in search_list if sub_str in x][0]
        except IndexError:
            raise Exception(f'Key not found for key {sub_str} in {search_list}.')
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


class Release(Manifest):

    _release_info_url = 'yaml:///opt/seagate/cortx/RELEASE.INFO'
    _release_index = 'release'

    def __init__(self):
        """Load RELEASE.INFO."""
        Conf.load(self._release_index, self._release_info_url)

    def get_release_version(self):
        """Return release version."""
        release_version = Manifest._get_val(self._release_index, 'VERSION')
        return release_version

    def get_component_version(self, component: str):
        """Return rpm version for given component.

            if build_version = False:
                return rpm_version with githash.
                e.g. - 2.0.0-459_git51f11338_3.10.0_1160
            if build_version = True:
                return only build_version from rpm.
                e.g - 2.0.0-459.
        """
        rpms = Manifest._get_val(self._release_index, 'COMPONENTS')
        component_rpm = Manifest._get_elem_from_list(component, rpms)
        version = Manifest._get_rpm_version(component_rpm)
        # Remove git_hash from rpm_version.
        while version.find('_') != -1:
                version = version.split('_')[0]
        return version

    def validate(self, release_spec: dict = {}):
        """Compare given release_spec with RELEASE.INFO file,
            and return correct release info define in RELEASE.INFO file."""
        release_info = {}
        is_valid = True
        keys = ['name', 'version']
        for key in keys:
            value = Manifest._get_val(self._release_index, key.upper())
            release_info[key] = value
            if not release_spec or release_spec.get(key) != value:
                is_valid = False
        return is_valid, release_info

    def version_check(self, deploy_version: str, release_version: str):
        """Compare deployed and release version and decide action based on result.
            e.g:
            deploy_version = 2.0.0-428
            release_version = 2.0.0-430
        """
        action = None
        ret_code = 0
        # If both versions are equal return 0 and action=None.
        # if deploy_version is null return 0, action=deploy.
        if not deploy_version:
            action = 'deploy'
            return ret_code, action
        elif deploy_version == release_version:
            return ret_code, action
        # Fetch all the digits present in string for comparison.
        deploy_digits = Manifest._get_digits(deploy_version)
        release_digits = Manifest._get_digits(release_version)
        for deploy_digit, release_digit in zip_longest(deploy_digits, release_digits, fillvalue=-1):
            if deploy_digit < release_digit:
                action = 'update'
                break
            elif deploy_digit > release_digit:
                ret_code = 1
                # TODO: action=degrade once the degrade is supported.
                break
        return ret_code, action
