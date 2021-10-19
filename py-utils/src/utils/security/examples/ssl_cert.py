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

def ssl_cert_example():

        ssl_certificate_path = '/tmp/ssl/stx.pem'
        ssl_cert_configs = {"country" : "IN", "state" : "MH", "locality" : "Pune",
                            "organization" : "Seagate Technology", "CN" : "seagate.com"}
        ssl_dns_list = [u'*.seagate.com', u'localhost', u'*.localhost']
        expiry_days = 365
        ssl_cert_obj = Certificate.init('ssl')
        ssl_cert_obj.generate(cert_path = ssl_certificate_path, dns_list = ssl_dns_list,
                                expiry_days = expiry_days, **ssl_cert_configs)

if __name__ == "__main__":
    from cortx.utils.security.certificate import Certificate
    from cortx.utils.errors import SSLCertificateError

    try:
        ssl_cert_example()
    except SSLCertificateError as e:
        print(e)
