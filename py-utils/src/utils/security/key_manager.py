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

from os import stat, umask
from pathlib import Path, PosixPath
from types import TracebackType
from typing import Optional, Type


class KeyMaterialStore:
    """Context manager for safe access to key material store."""
    _old_umask: int
    _store_path: Path

    def __init__(self, store_path: str) -> None:
        self._store_path = PosixPath(store_path)

    def __enter__(self) -> 'KeyMaterialStore':
        self._old_umask = umask(0o077)
        self._store_path.mkdir(parents=True, exist_ok=True)
        if stat(self._store_path).st_mode & 0o077:
            umask(self._old_umask)
            raise Exception(f'Key store "{self._store_path}" has lax permissions')
        umask(0o177)
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        umask(self._old_umask)

    def path(self) -> Path:
        """
        Returns the path to the key material store.

        :return: Path to the key material store
        """
        return self._store_path

    def resolve_path(self, relative_path: str, lax: bool = False) -> Path:
        """
        Resolves paths in the key material store, checking for lax permissions.

        :param relative_path: Relative path inside the key material store
        :param lax: Check for lax permissions if `False`
        :return: Resolved path
        """
        path = PosixPath(self._store_path) / relative_path
        path.resolve(strict=True)
        if not lax and stat(path).st_mode & 0o177:
            raise Exception(f'Key material "{relative_path}" has lax permissions.')
        return path
