#!/bin/python3

# CORTX Python common library.
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
# please email opensource@seagate.com or cortx-questions@seagate.com

"""
 ***************************************************************************
  Description: Storage class to provide fru health and specific information
               through web service.
 ***************************************************************************
"""

import hashlib
import json
import time
import os

from cortx.utils.discovery.dm.webservices import WebServices


class Storage:
    """Provides health information of FRUs in storage"""

    name = "storage"

    # CLI APIs
    URI_CLIAPI_LOGIN = "/login/"
    URI_CLIAPI_SHOWCONTROLLERS = "/show/controllers"
    # CLI APIs Response status strings
    CLIAPI_RESP_INVSESSION = "Invalid sessionkey"
    CLIAPI_RESP_FAILURE = 2
    WEBSERVICE_TIMEOUT = 20

    def __init__(self):
        """Initialize storage"""
        # Read mc value from configuration file
        self.mc1 = "10.0.0.2"
        self.mc1_wsport = "80"
        self.mc2 = "10.0.0.3"
        self.mc2_wsport = "80"
        self.user = "manage"
        self.__passwd = "!manage"
        self.active_ip = self.mc1
        self.active_wsport = self.mc1_wsport
        # WS Request common headers
        self.ws = WebServices()
        self.common_reqheaders = {}

    def get_health_info(self, rid):
        """
        Fetch health information for given FRU
        rid: Resouce id (Example: hw>controllers)
        """
        _, fru = rid.split(">")[:2]
        info = None
        if fru == "controllers":
            info = self.build_controllers_cache()
        return info

    def build_controllers_cache(self):
        """Update and return controller information in specific format"""
        data = []
        controllers = self.get_realstor_show_data("controllers")
        for controller in controllers:
            controller_dict = {
              "uid": controller.get("durable-id"),
              "fru": "true",
              "last_updated": int(time.time()),
              "health": {
                "status": controller.get("health", "NA"),
                "description": controller.get("description"),
                "recommendation": controller.get("health-recommendation"),
                "specifics": [
                  {
                    "serial-number": controller.get("serial-number", "NA"),
                    "disks": controller.get("disks", "NA"),
                    "virtual-disks": controller.get("virtual-disks", "NA"),
                    "model": controller.get("model", "NA"),
                    "part-number": controller.get("part-number", "NA"),
                    "fw": controller.get("sc-fw", "NA"),
                    "location": controller.get("position", "NA")
                  }
                ]
              }
            }
            data.append(controller_dict)
        return data

    def get_realstor_show_data(self, fru: str):
        """Fetch fru information through webservice API"""
        # fru_data = []
        # if fru == "controllers":
        #     fru_uri = self.URI_CLIAPI_SHOWCONTROLLERS
        # else:
        #     return []
        # response = self.fetch_ws_request_data(fru_uri)
        # if response or response.status_code == self.ws.HTTP_OK:
        #     response_data = json.loads(response.text)
        #     fru_data = response_data.get(fru)

        # Mocked controller data
        fru_data = [{
            "object-name":"controllers",
            "durable-id":"controller_a",
            "serial-number":"DHSIFGD-2029512C4C",
            "disks":28,
            "virtual-disks":0,
            "sc-fw":"GNS265R14-01",
            "model":"5565",
            "description":"N/A",
            "part-number":"FRUKC82-01",
            "health":"OK",
            "health-reason":"",
            "health-recommendation":"",
            "position":"Left"
            },
            {
            "object-name":"controllers",
            "durable-id":"controller_b",
            "serial-number":"DHSIFGD-2029512C7C",
            "disks":28,
            "virtual-disks":0,
            "sc-fw":"GNS265R14-01",
            "model":"5565",
            "description":"N/A",
            "part-number":"FRUKC82-01",
            "health":"OK",
            "health-reason":"",
            "health-recommendation":"",
            "position":"Right"
        }]
        return fru_data

    def fetch_ws_request_data(self, fru_uri):
        """Return response for fru URI"""
        url = self.build_url(fru_uri)
        response = self.ws_request(url, self.ws.HTTP_GET)
        return response

    def build_url(self, uri):
        """
        Build request url
        Return URL in the format of "http://<host>/api/show/<fru>"
        """
        return "http://" + self.active_ip + ":" + self.active_wsport + "/api" + uri

    def switch_to_alt_mc(self):
        """
        When WS response for primary mc1 ip and port is not HTTP_OK,
        then switch to mc2.
        """
        # Set mc2 ip and port to active if mc1 is already tried
        if not (self.mc1 == self.mc2 and self.mc1_wsport == self.mc2_wsport):
            # Change active ip and port to secondary mc
            if self.active_ip == self.mc1:
                self.active_ip = self.mc2
                self.active_wsport = self.mc2_wsport
            elif self.active_ip == self.mc2:
                self.active_ip = self.mc1
                self.active_wsport = self.mc1_wsport
            self.login()

    def ws_request(self, url, method, post_data=""):
        """Make webservice requests using common utils"""
        timeout_sec = 20
        retry_count = 2
        response = None
        retried_login = False
        need_relogin = False
        tried_alt_ip = False

        while retry_count:
            if tried_alt_ip:
                url = self.build_url(url[url.index('/api/'):].replace('/api',''))
            response = self.ws.ws_request(
                method, url, self.common_reqheaders, post_data, timeout_sec)
            retry_count -= 1

            if response is None:
                continue

            # Return response if HTTP 200
            if response.status_code == self.ws.HTTP_OK:
                self.mc_timeout_counter = 0
                try:
                    jresponse = json.loads(response.content)
                except ValueError:
                    # Skip if corrupted or mal-formed json response received
                    pass
                if jresponse:
                    if jresponse['status'][0]['return-code'] == self.CLIAPI_RESP_FAILURE:
                        response_status = jresponse['status'][0]['response']
                        # if call fails with invalid session key request
                        # seen in G280 fw version
                        if self.CLIAPI_RESP_INVSESSION in response_status:
                            need_relogin = True

            # Retry login if http 403 forbidden request
            elif (response.status_code == self.ws.HTTP_FORBIDDEN or \
                need_relogin) and retried_login is False:
                self.login()
                retried_login = True
                need_relogin = False

            # Swith to alternative mc if connection timeout or refused
            elif response.status_code in [ \
                self.ws.HTTP_TIMEOUT, self.ws.HTTP_CONN_REFUSED, self.ws.HTTP_NO_ROUTE_TO_HOST \
                    ] and tried_alt_ip is False:
                self.switch_to_alt_mc()
                tried_alt_ip = True
                self.mc_timeout_counter += 1

        return response

    def login(self):
        """
        Perform realstor login to get session key & make it available
        in common request headers
        """
        cli_api_auth = self.user + '_' + self.__passwd
        url = self.build_url(self.URI_CLIAPI_LOGIN)
        auth_hash = hashlib.sha256(cli_api_auth.encode('utf-8')).hexdigest()
        headers = {'datatype':'json'}

        response = self.ws.ws_get(url + auth_hash, headers, self.WEBSERVICE_TIMEOUT)

        if not response:
            return

        if response.status_code == self.ws.HTTP_OK:
            try:
                jresponse = json.loads(response.content)
            except ValueError:
                # Skip if corrupted or mal-formed json response received
                pass
            if jresponse:
                if jresponse['status'][0]['return-code'] == 1:
                    sessionKey = jresponse['status'][0]['response']
                    self.add_request_headers(sessionKey)
        else:
            if response.status_code == self.ws.HTTP_TIMEOUT:
                self.mc_timeout_counter += 1

    def add_request_headers(self, sessionKey):
        """Add common request headers"""
        self.common_reqheaders['datatype'] = "json"
        self.common_reqheaders['sessionKey'] = sessionKey


if __name__ == "__main__":
    storage = Storage()
    storage.get_health_info(rid="hw>controllers")
