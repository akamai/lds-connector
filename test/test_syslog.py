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

import socket
import unittest
import json
from unittest.mock import patch, MagicMock, call

from test import test_data
from lds_connector.syslog import SysLog
from lds_connector.json import CustomJsonEncoder
from lds_connector.config import Config

class SysLogTest(unittest.TestCase):
    LOG_EMIT_TIME = 1647651600.0

    @patch('lds_connector.syslog.logging.handlers.socket.socket')
    @patch('time.time', MagicMock(return_value=LOG_EMIT_TIME))
    def test_publish_udp_log(self, mock_socket: MagicMock):
        config = test_data.create_syslog_config()
        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst
        syslog_handler = SysLog(config)

        syslog_handler.add_log_line(test_data.DNS_LOG_EVENTS[0])
        syslog_handler.publish_log_lines()

        expected_message = SysLogTest.create_syslog_message_log(config, test_data.DNS_LOG_LINES[0])
        assert config.syslog is not None
        mock_socket_inst.sendto.assert_called_once_with(expected_message, (config.syslog.host, config.syslog.port))

    @patch('lds_connector.syslog.logging.handlers.socket.socket')
    @patch('time.time', MagicMock(return_value=LOG_EMIT_TIME))
    def test_publish_udp_dns_record(self, mock_socket: MagicMock):
        config = test_data.create_syslog_config()
        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst
        syslog_handler = SysLog(config)
        dns_record = test_data.create_dns_record1()

        syslog_handler.add_dns_record(dns_record)
        syslog_handler.publish_dns_records()

        expected_message = SysLogTest.create_syslog_message_dns(config, dns_record)
        assert config.syslog is not None
        mock_socket_inst.sendto.assert_called_once_with(expected_message, (config.syslog.host, config.syslog.port))

    @patch('lds_connector.syslog.logging.handlers.socket.socket')
    @patch('time.time', MagicMock(return_value=LOG_EMIT_TIME))
    def test_publish_tcp_log(self, mock_socket: MagicMock):
        config = test_data.create_syslog_config()
        assert config.syslog is not None
        config.syslog.use_tcp = True
        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst
        syslog_handler = SysLog(config)

        syslog_handler.add_log_line(test_data.DNS_LOG_EVENTS[0])
        syslog_handler.publish_log_lines()

        expected_message = SysLogTest.create_syslog_message_log(config, test_data.DNS_LOG_LINES[0])
        mock_socket_inst.connect.assert_called_once()
        mock_socket_inst.sendall.assert_called_once_with(expected_message)

    @patch('lds_connector.syslog.logging.handlers.socket.socket')
    @patch('time.time', MagicMock(return_value=LOG_EMIT_TIME))
    def test_publish_tcp_dns_record(self, mock_socket: MagicMock):
        config = test_data.create_syslog_config()
        assert config.syslog is not None
        config.syslog.use_tcp = True
        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst
        syslog_handler = SysLog(config)
        dns_record = test_data.create_dns_record1()

        syslog_handler.add_dns_record(dns_record)
        syslog_handler.publish_dns_records()

        expected_message = SysLogTest.create_syslog_message_dns(config, dns_record)
        mock_socket_inst.connect.assert_called_once()
        mock_socket_inst.sendall.assert_called_once_with(expected_message)

    def test_publish_logs_no_events(self):
        config = test_data.create_syslog_config()
        syslog_handler = SysLog(config)
        syslog_handler.syslogger = MagicMock()

        syslog_handler.publish_log_lines()

        syslog_handler.syslogger.info.assert_not_called()

    def test_publish_dns_records_no_events(self):
        config = test_data.create_syslog_config()
        syslog_handler = SysLog(config)
        syslog_handler.syslogger = MagicMock()

        syslog_handler.publish_dns_records()

        syslog_handler.syslogger.info.assert_not_called()

    @patch('lds_connector.syslog.logging.handlers.socket.socket')
    @patch('time.time', MagicMock(return_value=LOG_EMIT_TIME))
    def test_publish_multiple_logs(self, mock_socket: MagicMock):
        config = test_data.create_syslog_config()

        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst

        syslog_handler = SysLog(config)
        syslog_handler.add_log_line(test_data.DNS_LOG_EVENTS[0])
        syslog_handler.add_log_line(test_data.DNS_LOG_EVENTS[1])
        syslog_handler.add_log_line(test_data.DNS_LOG_EVENTS[2])
        syslog_handler.publish_log_lines()

        assert config.syslog is not None
        expected_message1 = SysLogTest.create_syslog_message_log(config, test_data.DNS_LOG_LINES[0])
        expected_message2 = SysLogTest.create_syslog_message_log(config, test_data.DNS_LOG_LINES[1])
        expected_message3 = SysLogTest.create_syslog_message_log(config, test_data.DNS_LOG_LINES[2])
        self.assertEqual(mock_socket_inst.sendto.call_count, 3)
        mock_socket_inst.sendto.assert_has_calls([
            call(expected_message1, (config.syslog.host, config.syslog.port)),
            call(expected_message2, (config.syslog.host, config.syslog.port)),
            call(expected_message3, (config.syslog.host, config.syslog.port))
        ])

    @patch('lds_connector.syslog.logging.handlers.socket.socket')
    @patch('time.time', MagicMock(return_value=LOG_EMIT_TIME))
    def test_publish_multiple_dns_records(self, mock_socket: MagicMock):
        config = test_data.create_syslog_config()

        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst

        syslog_handler = SysLog(config)
        syslog_handler.add_dns_record(test_data.create_dns_record1())
        syslog_handler.add_dns_record(test_data.create_dns_record2())
        syslog_handler.add_dns_record(test_data.create_dns_record3())
        syslog_handler.publish_dns_records()

        assert config.syslog is not None
        expected_message1 = SysLogTest.create_syslog_message_dns(config, test_data.create_dns_record1())
        expected_message2 = SysLogTest.create_syslog_message_dns(config, test_data.create_dns_record2())
        expected_message3 = SysLogTest.create_syslog_message_dns(config, test_data.create_dns_record3())
        self.assertEqual(mock_socket_inst.sendto.call_count, 3)
        mock_socket_inst.sendto.assert_has_calls([
            call(expected_message1, (config.syslog.host, config.syslog.port)),
            call(expected_message2, (config.syslog.host, config.syslog.port)),
            call(expected_message3, (config.syslog.host, config.syslog.port))
        ])

    def test_clear_logs(self):
        config = test_data.create_syslog_config()
        syslog_handler = SysLog(config)
        syslog_handler.syslogger = MagicMock()

        syslog_handler.add_log_line(test_data.DNS_LOG_EVENTS[0])
        syslog_handler.add_log_line(test_data.DNS_LOG_EVENTS[1])
        syslog_handler.clear()
        syslog_handler.publish_log_lines()

        syslog_handler.syslogger.info.assert_not_called()

    @staticmethod
    def create_syslog_message_dns(config: Config, json_object):
        json_message = json.dumps(json_object, cls=CustomJsonEncoder)
        assert config.syslog is not None
        return f'<14>Mar 18 18:00:00 {socket.gethostname()} {config.syslog.edgedns_app_name}: {json_message}'.encode('utf-8')

    @staticmethod
    def create_syslog_message_log(config: Config, message: str):
        assert config.syslog is not None
        return f'<14>Mar 18 18:00:00 {socket.gethostname()} {config.syslog.lds_app_name}: {message}'.encode('utf-8')


if __name__ == '__main__':
    unittest.main()
