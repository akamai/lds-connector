# Original author: Cam Mackintosh <cmackint@akamai.com>
# For more information visit https://developer.akamai.com

# Copyright 2023 Akamai Technologies, Inc. All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from test import test_data
from unittest.mock import MagicMock
import json

import requests

from lds_connector.edgedns_manager import EdgeDnsManager
from lds_connector.json import CustomJsonEncoder


class MockResponse(requests.Response):
    def __init__(self, status_code: int, json_data):
        self.status_code = status_code
        self.json_data = json_data

    def json(self):
        return self.json_data

class EdgeDnsManagerTest(unittest.TestCase):

    def test_get_records_single_page(self):
        config = test_data.create_config()
        edgedns_manager = EdgeDnsManager(config)

        edgedns_manager.open_session.get = MagicMock(
            return_value = MockResponse(200, test_data.read_json('test_recordset1.json'))
        )

        expected_records = [
            test_data.create_dns_record1(),
            test_data.create_dns_record2(),
            test_data.create_dns_record3()
        ]

        actual_records = edgedns_manager.get_records()
        for record in actual_records:
            record.time_fetched_sec=0

        self.assertEqual(actual_records, expected_records)

    def test_get_records_multiple_pages(self):
        config = test_data.create_config()
        edgedns_manager = EdgeDnsManager(config)

        edgedns_manager.open_session.get = MagicMock(
            side_effect = [
                MockResponse(200, test_data.read_json('test_recordset2_page1.json')),
                MockResponse(200, test_data.read_json('test_recordset2_page2.json'))
            ]
        )

        expected_records = [
            test_data.create_dns_record1(),
            test_data.create_dns_record2(),
            test_data.create_dns_record3()
        ]

        actual_records = edgedns_manager.get_records()
        for record in actual_records:
            record.time_fetched_sec=0

        self.assertEqual(actual_records, expected_records)

    def test_dns_record_json(self):
        dns_record = test_data.create_dns_record1()

        actual_json = json.dumps(dns_record, cls=CustomJsonEncoder)

        self.assertEqual(actual_json, test_data.DNS_RECORD1_JSON)
        

if __name__ == '__main__':
    unittest.main()
