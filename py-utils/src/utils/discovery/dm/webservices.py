# Copyright (c) 2019-2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>. For any questions
# about this software or licensing, please email opensource@seagate.com or
# cortx-questions@seagate.com.

"""
 ****************************************************************************
  Description: Webservice Class to abstract over actual python lib or web
               framework used to handle generic web services
 ****************************************************************************
"""

import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError


class WebServices(object):
    # Http Methods
    HTTP_GET  = "GET"
    HTTP_POST = "POST"
    HTTP_PUT  = "PUT"
    HTTP_DELETE = "DELETE"

    # HTTP Response codes
    HTTP_CONN_REFUSED = 111
    HTTP_OK = 200
    HTTP_BADRQ = 400
    HTTP_FORBIDDEN = 403
    HTTP_NOTFOUND = 404
    HTTP_TIMEOUT = 408
    HTTP_NO_ROUTE_TO_HOST = 113
    SERVICE_UNAVIALABLE = 503

    LOOPBACK = "127.0.0.1"

    def __init__(self):
        """Initialize webservice"""
        super(WebServices, self).__init__()
        self.http_methods = [self.HTTP_GET, self.HTTP_POST]

    def ws_request(self, method, url, hdrs, postdata, tout):
        """Make webservice request"""
        wsresponse = None
        try:
            if method == self.HTTP_GET:
                wsresponse = requests.get(url, headers=hdrs, timeout=tout)
            elif method == self.HTTP_POST:
                wsresponse = requests.post(url, headers=hdrs, data=postdata,
                                           timeout=tout)
            wsresponse.raise_for_status()
        except (ConnectionError, HTTPError, Timeout, Exception) as err:
            errstr = str(err)
            if not wsresponse:
                wsresponse = requests.Response()
            # Extract error code from exception obj and set in response
            if isinstance(err, ConnectionError):
                if errstr.find("error:") != -1:
                    wsresponse.status_code = \
                        int(errstr[errstr.find("error(") + 6:].split(",")[0])
                else:
                    wsresponse.status_code = self.HTTP_CONN_REFUSED
            elif isinstance(err, HTTPError):
                # HttpError exception example "403 Client Error: Forbidden"
                if errstr.find("Client Error") != -1:
                    wsresponse.status_code = int(errstr.split(" ")[0])
                else:
                    wsresponse.status_code = self.HTTP_CONN_REFUSED
            elif isinstance(err, Timeout):
                if url.find(self.LOOPBACK) == -1:
                    wsresponse.status_code = self.HTTP_TIMEOUT
            else:
                # Default to an error code
                wsresponse.status_code = self.SERVICE_UNAVIALABLE
        return wsresponse

    def ws_get(self, url, headers, timeout):
        """Webservice GET request"""
        return self.ws_request(self.HTTP_GET, url, headers, None, timeout)

    def ws_post(self, url, headers, postdata, timeout):
        """Webservice POST request"""
        return self.ws_request(self.HTTP_POST, url, headers, postdata, timeout)
