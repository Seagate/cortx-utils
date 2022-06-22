#!/usr/bin/env python3

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

header_template = """
                <!DOCTYPE html>
                <html>
                <head>
                <style>
                    #result {
                    font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
                    border-collapse: collapse;
                    width: 80%;
                    }
                    #result td, #result th {
                    border: 1px solid #ddd;
                    padding: 8px;
                    }
                    #result tr:nth-child(even){background-color: #f2f2f2;}
                    #result tr:hover {background-color: #ddd;}
                    #result th {
                    padding-top: 12px;
                    padding-bottom: 12px;
                    text-align: left;
                    background-color: #4CAF50;
                    color: white;
                    }
                </style>
                </head>
                <body>
                <table id="result">
                    <tr>
                        <th>Test Suite</th>
                        <th>Status</th>
                        <th>Duration</th>
                    </tr>"""

result_template = """
                <tr>
                    <td>{testsuite}</td>
                    <td>{status}</td>
                    <td>{duration}s</td>
                </tr>"""

footer_template = """
                </table><br>
                Overall Status: {}<br>
                Total Test Suites: {}<br>
                Passed: {}<br>
                Failed: {}<br>
                Time Taken: {}s<br>
                </body></html>"""

def generate_html_report(test_result):
    """Generates HTML test_report under /tmp."""
    result_table = ''
    overall_status = 'Passed'
    total_ts = 0
    total_failed = 0
    time_taken=0
    for ts, value in test_result.items():
        status = list(value.keys())[0]
        duration = int(list(value.values())[0])
        if status.lower() == 'fail':
            overall_status = 'Failed'
            total_failed += 1
            st_style = "<p style='color:red'>"
            st_end = "</p>"
            status = st_style + status + st_end
        result_table += result_template.format(testsuite=ts, status=status,\
            duration=duration)
        total_ts += 1
        time_taken += duration
    footer = footer_template.format(overall_status, total_ts,\
        total_ts-total_failed, total_failed, time_taken)
    test_data = header_template + result_table + footer
    with open('/tmp/py_utils_test_report.html', 'w') as test_report:
        test_report.write(test_data)
