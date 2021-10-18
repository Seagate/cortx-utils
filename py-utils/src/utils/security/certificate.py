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

import os
import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID
from cortx.utils.errors import SSLCertificateError

class Certificate:
    """Factory class for certificate"""

    @staticmethod
    def factory(cert_type):
        """
        This function returns the Class type of certificate that caller wants to generate.
        :returns : Class Type of certificate
        """
        cert = {
            "ssl": SSLCertificate,
            "domain": DomainCertificate,
            "device": DeviceCertificate,
        }
        return cert[cert_type]

class SSLCertificate:

    def __init__(self, cert_path, dns_list, expiry_days = 3650, **ssl_cert_configs):
        """
        Initialize SSLCertificate Object
        :param cert_path: File path at which certificate will be saved.
        :param dns_list: List of unicode dns names eg. [u"*.seagate.com", u"localhost"]
        :param expiry_days: Period in days for which certificate is valid, default: 10 yrs
        :kwargs ssl_cert_configs: ssl certificate general config eg. country_name, common_name etc.
        """
        self.cert_path = cert_path
        self.dns_list = dns_list
        self.expiry_days = expiry_days
        self.country = ssl_cert_configs.get("country", "IN")
        self.state = ssl_cert_configs.get("state", "MH")
        self.locality = ssl_cert_configs.get("locality", "Pune")
        self.organization = ssl_cert_configs.get("organization", "Seagate Technology")
        self.CN = ssl_cert_configs.get("CN", "seagate.com")

    def _prepare_private_key(self):
        """
        This function generates a private key
        :return: Private key
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        return private_key

    def _prepare_ssl_certificate(self, private_key:rsa.RSAPrivateKeyWithSerialization):
        """
        This functions generate a self-signed certificate
        :param private_key: Private_key
        :return: Self signed certificate
        """
        x509_dns_name_list = []
        for dns_name in self.dns_list:
            x509_dns_name_list.append(x509.DNSName(dns_name))

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, self.country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, self.locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.organization),
            x509.NameAttribute(NameOID.COMMON_NAME, self.CN)
        ])
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(issuer)
        builder = builder.not_valid_before(datetime.datetime.utcnow())
        builder = builder.not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=self.expiry_days))
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.public_key(private_key.public_key())
        builder = builder.add_extension(
            x509.SubjectAlternativeName(x509_dns_name_list),
            critical=False)
        builder = builder.add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)

        certificate = builder.sign(
            private_key=private_key, algorithm=hashes.SHA256(),
            backend=default_backend())
        return certificate

    def _create_dirs(self, file_path):
        """
        This function creates parent directories if not already present
        :param file_path: File path
        :return: None
        """
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def generate(self):
        """
        This function generate a self signed certificate and save it
        at specified location.
        :return: None
        """
        try:
            private_key = self._prepare_private_key()
            certificate = self._prepare_ssl_certificate(private_key)
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
            certificate_pem = certificate.public_bytes(serialization.Encoding.PEM)

            self._create_dirs(self.cert_path)

            with open(self.cert_path, "wb") as f:
                f.write(certificate_pem + private_key_pem)

        except Exception as e:
            raise SSLCertificateError(f"Unexpected error occured: {e}")

class DeviceCertificate:
    pass

class DomainCertificate:
    pass