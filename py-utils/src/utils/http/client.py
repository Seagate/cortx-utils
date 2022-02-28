# CORTX-Py-Utils: CORTX Python common library.
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

from aiohttp import ClientSession, ClientError
from http import HTTPStatus
import ssl
from time import gmtime, strftime
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from cortx.utils.http.exceptions import HttpClientException


class HttpClient:
    """
    Base HTTP client for CORTX utils.

    Enable user to asynchronously send HTTP requests.
    """

    def __init__(
        self, host: str = 'localhost', port: int = 8000,
        tls_enabled: bool = False, ca_bundle: str = '',
        timeout: int = 5
    ) -> None:
        """
        Initialize the client.

        :param host: hostname of the server.
        :param port: port of the server.
        :param tls_enabled: flag to use https.
        :param ca_bundle: path to the root CA certificate.
        :param timeout: connection timeout.
        :returns: None.
        """

        self._host = host
        self._port = port
        self._url = f"{'https' if tls_enabled else 'http'}://{host}:{port}"
        self._ssl_ctx = ssl.create_default_context(cafile=ca_bundle) if ca_bundle else False
        self._timeout = timeout

    def http_date(self) -> str:
        """
        Return the 'now' datetime in RFC 1123 format.

        :returns: string with datetime.
        """

        now = gmtime()
        return strftime("%a, %d %b %Y %H:%M:%S +0000", now)

    async def request(
        self, verb: str, path: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        request_params: Optional[Dict[str, Any]] = None
    ) -> Tuple[HTTPStatus, Optional[str]]:
        """
        Send the request to the server.

        :param verb: HTTP method of the request (GET, POST, etc.).
        :param path: server's URI to send the request to (e.g. /admin/user).
        :param headers: HTTP headers of the request.
        :param query_params: request parameters to be added into the query.
        :param request_params: request parameters to be added into the body.
        :returns: HTTP status and the body of the response.
        """

        final_url = self._url
        if path is not None:
            final_url += '/' if not path.startswith('/') else ""
            final_url += path
        if query_params is not None:
            final_url += "?" if "?" not in path else "&"
            final_url += urlencode(query_params)
        async with ClientSession() as http_session:
            try:
                async with http_session.request(method=verb, headers=headers, data=request_params,
                                                url=final_url, ssl=self._ssl_ctx,
                                                timeout=self._timeout) as resp:
                    status = resp.status
                    body = await resp.text()
                    return status, body
            except ClientError as e:
                raise HttpClientException(str(e)) from None
