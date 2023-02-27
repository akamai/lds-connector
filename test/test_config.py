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

    def test_read_yaml_no_optionals1(self):
        expected_config = test_data.create_config()
        assert expected_config.splunk is not None
        expected_config.splunk.lds_hec.index = None
        expected_config.splunk.lds_hec.source_type = None
        expected_config.splunk.lds_hec.event_batch_size = 10
        assert expected_config.splunk.edgedns_hec is not None
        expected_config.splunk.edgedns_hec.index = None
        expected_config.splunk.edgedns_hec.source_type = None
        expected_config.splunk.edgedns_hec.event_batch_size = 10
        assert expected_config.edgedns is not None
        expected_config.edgedns.poll_period_sec = 7200
        expected_config.edgedns.send_records = False
        assert expected_config.open is not None
        expected_config.open.account_switch_key = None
        expected_config.lds.poll_period_sec = 60
        assert expected_config.syslog is not None
        expected_config.syslog.edgedns_app_name = None

        config_filename = path.join(test_data.DATA_DIR, 'test_config_no_opts.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)

    def test_read_yaml_no_edgedns(self):
        expected_config = test_data.create_config()

        assert expected_config.splunk is not None
        expected_config.splunk.edgedns_hec = None

        assert expected_config.syslog is not None
        expected_config.syslog.edgedns_app_name = None

        expected_config.open = None
        expected_config.edgedns = None
        
        config_filename = path.join(test_data.DATA_DIR, 'test_config_no_edgedns.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)

    def test_read_yaml_edgedns_no_open(self):
        config_filename = path.join(test_data.DATA_DIR, 'test_config_missing_open.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertIsNone(config)

    def test_read_yaml_edgedns_no_hec_token(self):
        config_filename = path.join(test_data.DATA_DIR, 'test_config_missing_hec_token.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertIsNone(config)

    def test_read_yaml_edgedns_no_syslog_appname(self):
        config_filename = path.join(test_data.DATA_DIR, 'test_config_missing_syslog_appname.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertIsNone(config)


    def test_read_yaml_only_splunk(self):
        expected_config = test_data.create_config()
        expected_config.syslog = None

        config_filename = path.join(test_data.DATA_DIR, 'test_config_only_splunk.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)

    def test_read_yaml_only_syslog(self):
        expected_config = test_data.create_config()
        expected_config.splunk = None

        config_filename = path.join(test_data.DATA_DIR, 'test_config_only_syslog.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)

if __name__ == '__main__':
    unittest.main()
