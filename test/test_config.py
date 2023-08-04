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

from lds_connector.config import read_yaml_config, is_config_valid, SysLogTransport, SysLogProtocol, SysLogTlsConfig


class ConfigTest(unittest.TestCase):

    def test_splunk_no_records(self):
        expected_config = test_data.create_splunk_config()
        expected_config.open = None
        expected_config.edgedns = None
        assert expected_config.splunk is not None
        expected_config.splunk.edgedns_hec = None

        config_filename = path.join(test_data.DATA_DIR, 'test_config_splunk_no_records.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)


    def test_splunk_records(self):
        expected_config = test_data.create_splunk_config()

        config_filename = path.join(test_data.DATA_DIR, 'test_config_splunk_records.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)


    def test_splunk_records_defaults(self):
        expected_config = test_data.create_splunk_config()
        assert expected_config.splunk is not None
        assert expected_config.splunk.edgedns_hec is not None
        expected_config.splunk.edgedns_hec.source_type = None
        expected_config.splunk.edgedns_hec.index = None
        expected_config.splunk.edgedns_hec.event_batch_size = 10
        expected_config.splunk.lds_hec.source_type = None
        expected_config.splunk.lds_hec.index = None
        expected_config.splunk.lds_hec.event_batch_size = 10
        assert expected_config.edgedns is not None
        expected_config.edgedns.poll_period_sec = 7200

        config_filename = path.join(test_data.DATA_DIR, 'test_config_splunk_records_defaults.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)


    def test_syslog_no_records(self):
        expected_config = test_data.create_syslog_config()
        expected_config.open = None
        expected_config.edgedns = None
        assert expected_config.syslog is not None
        expected_config.syslog.edgedns_app_name = None

        config_filename = path.join(test_data.DATA_DIR, 'test_config_syslog_no_records.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)


    def test_syslog_records(self):
        expected_config = test_data.create_syslog_config()

        config_filename = path.join(test_data.DATA_DIR, 'test_config_syslog_records.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)


    def test_lds_defaults(self):
        expected_config = test_data.create_splunk_config()
        expected_config.lds.poll_period_sec = 60

        config_filename = path.join(test_data.DATA_DIR, 'test_config_lds_defaults.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)


    def test_open_defaults(self):
        expected_config = test_data.create_splunk_config()
        assert expected_config.open is not None
        expected_config.open.account_switch_key = None

        config_filename = path.join(test_data.DATA_DIR, 'test_config_open_defaults.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)


    def test_syslog_tls(self):
        expected_config = test_data.create_syslog_config()
        expected_config.open = None
        expected_config.edgedns = None
        expected_config.syslog.edgedns_app_name = None
        expected_config.syslog.transport = SysLogTransport.TCP_TLS
        expected_config.syslog.protocol = SysLogProtocol.RFC5424
        expected_config.syslog.tls = SysLogTlsConfig(
            ca_file='ca.pem',
            verify=True
        )

        config_filename = path.join(test_data.DATA_DIR, 'test_config_syslog_tls.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)


    def test_neither_syslog_or_splunk(self):
        # Neither syslog or splunk is configured
        parsed_config = test_data.create_syslog_config()
        parsed_config.syslog = None
        parsed_config.splunk = None

        self.assertFalse(is_config_valid(parsed_config))

    def test_both_syslog_and_splunk(self):
        # Both syslog and splunk are configured
        parsed_config = test_data.create_syslog_config()
        parsed_config.splunk = test_data.create_splunk_config().splunk

        self.assertFalse(is_config_valid(parsed_config))


    def test_syslog_missing_edns_app_name(self):
        # edgedns.send_records is true, but syslog.edgedns_app_name is not set
        parsed_config = test_data.create_syslog_config()
        assert parsed_config.syslog is not None
        parsed_config.syslog.edgedns_app_name = None

        self.assertFalse(is_config_valid(parsed_config))

   
    def test_syslog_missing_edns_zone_name(self):
        # edgedns.send_records is true, but syslog.edgedns.zone_name is not set
        parsed_config = test_data.create_syslog_config()
        parsed_config.edgedns.zone_name = None

        self.assertFalse(is_config_valid(parsed_config))


    def test_splunk_missing_edns_hec(self):
        # edgedns.send_records is true, but splunk.edgedns_hec is not set

        parsed_config = test_data.create_splunk_config()
        assert parsed_config.splunk is not None
        parsed_config.splunk.edgedns_hec = None

        self.assertFalse(is_config_valid(parsed_config))


    def test_splunk_missing_open(self):
        # edgedns.send_records is true, but open is not set
        parsed_config = test_data.create_splunk_config()
        parsed_config.open = None

        self.assertFalse(is_config_valid(parsed_config))


    def test_syslog_missing_tls(self):
        parsed_config = test_data.create_syslog_config()
        parsed_config.open = None
        parsed_config.edgedns = None
        parsed_config.syslog.edgedns_app_name = None
        parsed_config.syslog.transport = SysLogTransport.TCP_TLS
        parsed_config.syslog.protocol = SysLogProtocol.RFC5424

        self.assertFalse(is_config_valid(parsed_config))


if __name__ == '__main__':
    unittest.main()
