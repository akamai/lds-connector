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
from os import path
from test import test_data

from lds_connector.config import read_yaml_config


class ConfigTest(unittest.TestCase):

    def test_read_yaml_config(self):
        expected_config = test_data.create_config()

        config_filename = path.join(test_data.DATA_DIR, 'test_config1.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)

    def test_read_yaml_missing_optional(self):
        expected_config = test_data.create_config()
        expected_config.splunk.lds_hec.index = None
        expected_config.splunk.lds_hec.source_type = None
        expected_config.splunk.lds_hec.event_batch_size = 10
        expected_config.splunk.edgedns_hec = None
        expected_config.lds.poll_period_sec = 60
        expected_config.edgedns = None
        expected_config.open = None

        config_filename = path.join(test_data.DATA_DIR, 'test_config2.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)

    def test_read_yaml_missing_nested_optional(self):
        expected_config = test_data.create_config()
        assert expected_config.open is not None
        expected_config.open.account_switch_key = None

        config_filename = path.join(test_data.DATA_DIR, 'test_config3.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)

    def test_read_yaml_edgedns_records_requires_open(self):
        config_filename = path.join(test_data.DATA_DIR, 'test_config4.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertIsNone(config)

    def test_read_yaml_edgedns_records_requires_token(self):
        config_filename = path.join(test_data.DATA_DIR, 'test_config5.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertIsNone(config)


if __name__ == '__main__':
    unittest.main()
