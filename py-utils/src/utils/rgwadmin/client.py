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

import asyncio
import base64
from hashlib import sha1
import hmac
from http import HTTPStatus
from typing import Any, Dict, Optional, Tuple

from cortx.utils.http import HTTPClient, HTTPClientException
from cortx.utils.rgwadmin.exceptions import RGWAdminClientException


class RGWAdminClient(HTTPClient):
    """
    Low level RGW admin client.

    Enable user to send signed HTTP requests to the RADOS Gateway REST API.
    """

    def __init__(
        self, access_key_id: str, secret_access_key: str,
        host: str = 'localhost', port: int = 8000,
        tls_enabled: bool = False, ca_bundle: str = '',
        timeout: int = 5
    ) -> None:
        """
        Initialize the client.

        :param access_key_id: access key id of the admin user.
        :param secret_access_key: secret access key of the admin user.
        :param host: hostname of the RGW server.
        :param port: port of the RGW server.
        :param tls_enabled: flag to use https.
        :param ca_bundle: path to the root CA certificate.
        :param timeout: connection timeout.
        :returns: None.
        """

        super(RGWAdminClient, self).__init__(host, port, tls_enabled, ca_bundle, timeout)
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key

    def _generate_signature(self, verb: str, headers: Dict[str, str], path: str) -> str:
        """
        Generate an S3 compatible authorization signature.

        :param verb: HTTP method of the request (GET, POST, etc.).
        :param headers: HTTP headers of the request.
        :param path: server's URI to send the request to (e.g. /admin/user).
        :returns: signature string.
        """

        required_headers = ["content-md5", "content-type", "date"]
        string_to_sign = f"{verb}\n"
        for key in sorted(required_headers):
            val = headers.get(key, "")
            string_to_sign += f"{val}\n"
        string_to_sign += path.split('?')[0]
        string_to_sign_bytes = string_to_sign.encode("UTF-8")
        secret_access_key_bytes = self._secret_access_key.encode("UTF-8")
        secret_key_hmac = hmac.new(secret_access_key_bytes, string_to_sign_bytes, sha1).digest()
        signature_bytes = base64.encodestring(secret_key_hmac).strip()
        signature = f"AWS {self._access_key_id}:{signature_bytes.decode('UTF-8')}"
        return signature

    async def signed_http_request(
        self, verb: str, path: str, headers: Dict[str, str] = None,
        query_params: Dict[str, Any] = None, request_params: Dict[str, Any] = None
    ) -> Tuple[HTTPStatus, Optional[str]]:
        """
        Send an S3-signed request to the RGW.

        :param verb: HTTP method of the request (GET, POST, etc.).
        :param path: server's URI to send the request to (e.g. /admin/user).
        :param headers: HTTP headers of the request.
        :param query_params: request parameters to be added into the query.
        :param request_params: request parameters to be added into the body.
        :returns: HTTP status and the body of the response.
        """

        # 'content-type' and 'date' headers need to be signed.
        # If not provided by the user they might be attached by the HTTP framework
        # at the time of sending making the signature incorrect.
        # Here headers are manually added in a proper format.
        if headers is None:
            headers = {}
        if 'content-type' not in headers:
            headers['content-type'] = 'application/x-www-form-urlencoded'
        headers['date'] = self.http_date()
        # 'Authorization' header provides the required signature
        headers['authorization'] = self._generate_signature(verb, headers, path)
        try:
            status, body = await self.request(verb, path, headers, query_params, request_params)
            return status, body
        except (HTTPClientException, asyncio.TimeoutError) as e:
            reason = str(e)
            if isinstance(e, asyncio.TimeoutError):
                reason = "Request timeout"
            raise RGWAdminClientException(reason) from None
