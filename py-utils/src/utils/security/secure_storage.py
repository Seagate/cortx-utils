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

from schematics.types import StringType

from cortx.utils.security.cipher import Cipher
from cortx.utils.data.access.base_model import BaseModel
from cortx.utils.data.access.filters import Compare
from cortx.utils.data.access.queries import Query
from cortx.utils.data.access.storage import AbstractDataBaseProvider


class NamedEncryptedBytes(BaseModel):
    """Encrypted bytes model."""

    _id = "name"

    name = StringType()
    data = StringType()

    @staticmethod
    def instantiate(name: str, data: str):
        """Creates an NamedEncryptedBytes instance."""
        neb = NamedEncryptedBytes()
        neb.name = name
        neb.data = data
        return neb


class SecureStorage:
    """Storage of explicitly CORTX cipher encrypted objects upon Consul KVS."""

    def __init__(self, storage: AbstractDataBaseProvider, key: bytes) -> None:
        self._storage = storage
        self._key = key

    async def _get_item(self, name: str) -> NamedEncryptedBytes:
        """
        Gets NamedEncryptedBytes object with encrypted payload from the storage.

        Returns NamedEncryptedBytes object if the item with provided name exists or None
        """
        query = Query().filter_by(Compare(NamedEncryptedBytes.name, '=', name))
        neb = next(iter(await self._storage(NamedEncryptedBytes).get(query)), None)
        return neb

    async def store(self, name: str, data: bytes, force=False) -> None:
        """
        Saves the data to the encrypted storage.

        Data is AES encrypted with the default CORTX cipher and stored
        as Base64 encoded string with the provided name.
        Raises KeyError if an item with the provided name exists and "force" flag
        is not set.
        """
        if not force:
            neb = await self._get_item(name)
            if neb is not None:
                raise KeyError(f'{name} already exists in the secure storage')

        encrypted_bytes = Cipher.encrypt(self._key, data)
        # Encrypted token is base64 encoded, thus there won't be a problem with storing it in String
        neb = NamedEncryptedBytes.instantiate(name, encrypted_bytes.decode('ascii'))
        await self._storage(NamedEncryptedBytes).store(neb)

    async def get(self, name: str) -> bytes:
        """
        Gets bytes from the encrypted storage.

        Acquires the data from the storage and decrypts it with the default CORTX cipher
        Raises CipherInvalidToken if decryption fails.
        """
        neb = await self._get_item(name)
        if neb is None:
            return None

        decrypted_bytes = Cipher.decrypt(self._key, neb.data.encode('ascii'))
        return decrypted_bytes

    async def delete(self, name: str) -> None:
        """Removes the data from the encrypted storage."""
        neb = await self._get_item(name)
        if neb is None:
            raise KeyError(f'Item "{name}" was not found in secure storage')
        await self._storage(NamedEncryptedBytes).delete(Compare(NamedEncryptedBytes.name, '=', name))
