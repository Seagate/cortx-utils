#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
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

import unittest
from cortx.utils.event_framework.health import HealthEvent, HealthAttr

class TestHealthEvent(unittest.TestCase):
    """Test health event message schema handling"""

    def test_health_event_set(self):
        """Create of object HealthEvent, Test set attributes value."""
        he = HealthEvent()
        self.assertTrue('header>version' in he.get_keys())
        self.assertTrue('payload>source' in he.get_keys())
        he.set(f'{HealthAttr.STORAGESET_ID}', '1')
        he.set(f'{HealthAttr.NODE_ID}', '3')
        self.assertEqual(he.get(f'payload>{HealthAttr.STORAGESET_ID}'), '1')
        self.assertEqual(he.get(f'payload>{HealthAttr.NODE_ID}'), '3')
        # Other attributes remain empty strings if not set
        self.assertEqual(he.get(f'payload>{HealthAttr.RESOURCE_ID}'), '')

    def test_health_event_create(self):
        """Check by passing values of attributes during creation of object."""
        health_attrs = {
        f'{HealthAttr.SOURCE}': 's1',
        f'{HealthAttr.CLUSTER_ID}': '1234',
        f'{HealthAttr.SITE_ID}': '1',
        f'{HealthAttr.RACK_ID}': '1' }

        he = HealthEvent(**health_attrs)

        self.assertEqual(he.get(f'payload>{HealthAttr.SOURCE}'), 's1')
        self.assertEqual(he.get(f'payload>{HealthAttr.CLUSTER_ID}'), '1234')
        self.assertEqual(he.get(f'payload>{HealthAttr.SITE_ID}'), '1')
        self.assertEqual(he.get(f'payload>{HealthAttr.RACK_ID}'), '1')
    
        # Way to set specific info
        he.set_specific_info({'a': 'a1'})
        self.assertEqual(he.get(f'payload>{HealthAttr.SPECIFIC_INFO}>a'), 'a1')
        # One more way to set specific attr
        he.set_specific_attr('a', 'a2')
        self.assertEqual(he.get(f'payload>{HealthAttr.SPECIFIC_INFO}>a'), 'a2')
       
        # Other attributes remain empty strings if not set
        self.assertEqual(he.get(f'payload>{HealthAttr.RESOURCE_ID}'), '')

if __name__ == '__main__':
    unittest.main()
