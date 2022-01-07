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
    def init(cert_type):
        """
        This function creates a object of desired certificate type
        :param: cert_type: Certificate type
        :returns: Object of desired certificate type
        """
        cert = {
            "ssl": SSLCertificate,
            "domain": DomainCertificate,
            "device": DeviceCertificate,
        }
        return cert[cert_type]()

class SSLCertificate:
    """Class to generate self signed SSL Certificate"""

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

    def _prepare_ssl_certificate(self, private_key:rsa.RSAPrivateKeyWithSerialization,
                                dns_list, expiry_days, **ssl_cert_configs):
        """
        This function generates a self-signed certificate
        :param private_key: Private_key
        :param dns_list: List of unicode dns names eg. [u"*.seagate.com", u"localhost"]
        :param expiry_days: Period in days for which certificate will be valid, default: 10 yrs
        :kwargs ssl_cert_configs: ssl certificate general configs as below
            country: Country Name
            state: State Name
            locality: Locality Name
            organization: Organization Name
            CN: Common Name
        :return: Self signed certificate
        """
        x509_dns_name_list = []
        for dns_name in dns_list:
            x509_dns_name_list.append(x509.DNSName(dns_name))

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, ssl_cert_configs.get("country", "IN")),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, ssl_cert_configs.get("state", "MH")),
            x509.NameAttribute(NameOID.LOCALITY_NAME, ssl_cert_configs.get("locality", "Pune")),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME,
                                ssl_cert_configs.get("organization", "Seagate Technology")),
            x509.NameAttribute(NameOID.COMMON_NAME, ssl_cert_configs.get("CN", "seagate.com"))
        ])
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(issuer)
        builder = builder.not_valid_before(datetime.datetime.utcnow())
        builder = builder.not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=expiry_days))
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

    def generate(self, cert_path, dns_list, expiry_days = 3650, **ssl_cert_configs):
        """
        This function generate a self signed certificate and save it
        at specified location.
        :param cert_path: File path at which certificate will be saved.
        :param dns_list: List of unicode dns names eg. [u"*.seagate.com", u"localhost"]
        :param expiry_days: Period in days for which certificate will be valid, default: 10 yrs
        :kwargs ssl_cert_configs: ssl certificate general configs as below
        country: Country Name
        state: State Name
        locality: Locality Name
        organization: Organization Name
        CN: Common Name
        :return: None
        """
        try:
            private_key = self._prepare_private_key()
            certificate = self._prepare_ssl_certificate(
                private_key, dns_list, expiry_days, **ssl_cert_configs)
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
            certificate_pem = certificate.public_bytes(serialization.Encoding.PEM)

            self._create_dirs(cert_path)

            with open(cert_path, "wb") as f:
                f.write(certificate_pem + private_key_pem)

        except Exception as e:
            raise SSLCertificateError(f"Unexpected error occurred: {e}")

class DeviceCertificate:
    pass

class DomainCertificate:
    pass
