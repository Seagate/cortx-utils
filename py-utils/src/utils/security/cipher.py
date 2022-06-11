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

import os
import subprocess

from base64 import urlsafe_b64encode
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidSignature, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

cortxsec_cmd = '/opt/seagate/cortx/extension/cortxsec'


class Cipher:
    """
    Wrapper around actual actual AES implementation (Fernet)

    Serves a single purpose: wraps the actual implementation in order to be able
    to change it in the future.
    """

    @staticmethod
    def encrypt(key: bytes, data: bytes) -> bytes:
        """
        Performs a symmetric encryption of the provided data with
        the provided key.
        """

        return Fernet(key).encrypt(data)

    @staticmethod
    def decrypt(key: bytes, data: bytes) -> bytes:
        """
        Performs a symmetric decryption of the provided data with
        the provided key.
        """

        try:
            decrypted = Fernet(key).decrypt(data)
        except (InvalidSignature, InvalidToken):
            raise CipherInvalidToken(f'Decryption failed')
        return decrypted

    @staticmethod
    def generate_key(str1: str, str2: str, *strs) -> bytes:
        if os.path.exists(cortxsec_cmd):
            args = ' '.join(['getkey', str1, str2] + list(strs))
            getkey_cmd = f'{cortxsec_cmd} {args}'
            try:
                resp = subprocess.check_output(getkey_cmd.split(), stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                raise Exception(f'Command "{getkey_cmd}" failed with the output: {e.output}') from e
            return resp
        else:
            return Cipher.gen_key(str1, str2, *strs)

    @staticmethod
    def gen_key(str1: str, str2: str, *strs):
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                         length=32,
                         salt=str1.encode('utf-8'),
                         iterations=100000,
                         backend=default_backend())
        passwd = str2 + ''.join(strs)
        key = urlsafe_b64encode(kdf.derive(passwd.encode('utf-8')))
        return key


class CipherInvalidToken(Exception):
    """Wrapper around actual implementation's decryption exceptions."""
    pass
