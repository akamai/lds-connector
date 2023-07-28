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

import json
import socket
import unittest
from datetime import datetime, timezone
from test import test_data
from unittest.mock import MagicMock, call, patch

from freezegun import freeze_time

from lds_connector.config import Config, SysLogTransport, SysLogTlsConfig, SysLogProtocol, SysLogDelimiter
from lds_connector.json import CustomJsonEncoder
from lds_connector.log_file import LogEvent
from lds_connector.syslog import SysLog


class SysLogTest(unittest.TestCase):
    LOG_EMIT_TIME = 1647651600.0

    EXPECTED_TIMES_RFC3164 = [
        'Jan 03 03:06:39',
        'Jan 03 03:06:39',
        'Jan 03 03:36:36',
    ]

    EXPECTED_TIMES_RFC5424 = [
        '2023-01-03T03:06:39Z',
        '2023-01-03T03:06:39Z',
        '2023-01-03T03:36:36Z',
    ]


    @patch('lds_connector.syslogger.socket.socket')
    def test_publish_udp_log(self, mock_socket: MagicMock):
        config = test_data.create_syslog_config()
        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst
        syslog_handler = SysLog(config)

        log_event = test_data.get_dns_log_events()[0]
        syslog_handler.add_log_line(log_event)
        syslog_handler.publish_log_lines()

        expected_message = SysLogTest.create_rfc3164_log(config, log_event, SysLogTest.EXPECTED_TIMES_RFC3164[0])
        assert config.syslog is not None
        mock_socket_inst.sendto.assert_called_once_with(expected_message, (config.syslog.host, config.syslog.port))


    @patch('lds_connector.syslogger.socket.socket')
    @freeze_time(datetime.fromtimestamp(LOG_EMIT_TIME, tz=timezone.utc))
    def test_publish_udp_dns_record(self, mock_socket: MagicMock):
        config = test_data.create_syslog_config()
        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst
        syslog_handler = SysLog(config)
        dns_record = test_data.create_dns_record1()

        syslog_handler.add_dns_record(dns_record)
        syslog_handler.publish_dns_records()

        expected_message = SysLogTest.create_rfc3164_dns(config, dns_record)
        assert config.syslog is not None
        mock_socket_inst.sendto.assert_called_once_with(expected_message, (config.syslog.host, config.syslog.port))


    @patch('lds_connector.syslogger.socket.socket')
    @freeze_time(datetime.fromtimestamp(LOG_EMIT_TIME))
    def test_publish_tcp_log(self, mock_socket: MagicMock):
        config = test_data.create_syslog_config()
        assert config.syslog is not None
        config.syslog.transport = SysLogTransport.TCP
        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst
        syslog_handler = SysLog(config)

        log_event = test_data.get_dns_log_events()[0]
        syslog_handler.add_log_line(log_event)
        syslog_handler.publish_log_lines()

        expected_message = SysLogTest.create_rfc3164_log(config, log_event, SysLogTest.EXPECTED_TIMES_RFC3164[0])
        mock_socket_inst.connect.assert_called_once()
        mock_socket_inst.sendall.assert_called_once_with(expected_message)


    @patch('lds_connector.syslogger.socket.socket')
    @freeze_time(datetime.fromtimestamp(LOG_EMIT_TIME))
    def test_publish_tcp_log_delims(self, mock_socket: MagicMock):

        for delim in SysLogDelimiter:
            config = test_data.create_syslog_config()
            assert config.syslog is not None
            config.syslog.transport = SysLogTransport.TCP
            config.syslog.delimiter_method = delim
            mock_socket_inst = MagicMock()
            mock_socket.return_value = mock_socket_inst
            syslog_handler = SysLog(config)

            log_event = test_data.get_dns_log_events()[0]
            syslog_handler.add_log_line(log_event)
            syslog_handler.publish_log_lines()

            expected_message = SysLogTest.create_rfc3164_log(config, log_event, SysLogTest.EXPECTED_TIMES_RFC3164[0], delim)
            mock_socket_inst.connect.assert_called_once()
            mock_socket_inst.sendall.assert_called_once_with(expected_message)



    @patch('lds_connector.syslogger.socket.socket')
    @freeze_time(datetime.fromtimestamp(LOG_EMIT_TIME))
    def test_publish_tcp_log_rfc5424(self, mock_socket: MagicMock):
        config = test_data.create_syslog_config()
        assert config.syslog is not None
        config.syslog.transport = SysLogTransport.TCP
        config.syslog.protocol = SysLogProtocol.RFC5424
        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst
        syslog_handler = SysLog(config)

        log_event = test_data.get_dns_log_events()[0]
        syslog_handler.add_log_line(log_event)
        syslog_handler.publish_log_lines()

        expected_message = SysLogTest.create_rfc5424_log(config, log_event, SysLogTest.EXPECTED_TIMES_RFC5424[0])
        mock_socket_inst.connect.assert_called_once()
        mock_socket_inst.sendall.assert_called_once_with(expected_message)


    @patch('lds_connector.syslogger.ssl.SSLContext.wrap_socket')
    @patch('lds_connector.syslogger.socket.socket')
    @freeze_time(datetime.fromtimestamp(LOG_EMIT_TIME))
    def test_publish_tls_log(self, mock_socket: MagicMock, mock_wrap_socket: MagicMock):
        config = test_data.create_syslog_config()
        assert config.syslog is not None
        config.syslog.transport = SysLogTransport.TCP_TLS
        config.syslog.tls = SysLogTlsConfig(
            ca_file=test_data.CA_FILE,
            verify=False
        )
        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst
        mock_wrap_socket.side_effect = lambda socket: socket
        syslog_handler = SysLog(config)

        log_event = test_data.get_dns_log_events()[0]
        syslog_handler.add_log_line(log_event)
        syslog_handler.publish_log_lines()

        expected_message = SysLogTest.create_rfc3164_log(config, log_event, SysLogTest.EXPECTED_TIMES_RFC3164[0])
        mock_socket_inst.connect.assert_called_once()
        mock_socket_inst.sendall.assert_called_once_with(expected_message)
        mock_wrap_socket.assert_called_once()


    @patch('lds_connector.syslogger.ssl.SSLContext.wrap_socket')
    @patch('lds_connector.syslogger.socket.socket')
    @freeze_time(datetime.fromtimestamp(LOG_EMIT_TIME))
    def test_publish_tls_log_verify(self, mock_socket: MagicMock, mock_wrap_socket: MagicMock):
        config = test_data.create_syslog_config()
        assert config.syslog is not None
        config.syslog.transport = SysLogTransport.TCP_TLS
        config.syslog.tls = SysLogTlsConfig(
            ca_file=test_data.CA_FILE,
            verify=True
        )
        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst
        mock_wrap_socket.side_effect = lambda socket, server_hostname: socket
        syslog_handler = SysLog(config)

        log_event = test_data.get_dns_log_events()[0]
        syslog_handler.add_log_line(log_event)
        syslog_handler.publish_log_lines()

        expected_message = SysLogTest.create_rfc3164_log(config, log_event, SysLogTest.EXPECTED_TIMES_RFC3164[0])
        mock_socket_inst.connect.assert_called_once()
        mock_socket_inst.sendall.assert_called_once_with(expected_message)
        mock_wrap_socket.assert_called_once()


    @patch('lds_connector.syslogger.socket.socket')
    @freeze_time(datetime.fromtimestamp(LOG_EMIT_TIME, tz=timezone.utc))
    def test_publish_tcp_dns_record(self, mock_socket: MagicMock):
        config = test_data.create_syslog_config()
        assert config.syslog is not None
        config.syslog.transport = SysLogTransport.TCP
        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst
        syslog_handler = SysLog(config)
        dns_record = test_data.create_dns_record1()

        syslog_handler.add_dns_record(dns_record)
        syslog_handler.publish_dns_records()

        expected_message = SysLogTest.create_rfc3164_dns(config, dns_record)
        mock_socket_inst.connect.assert_called_once()
        mock_socket_inst.sendall.assert_called_once_with(expected_message)


    def test_publish_logs_no_events(self):
        config = test_data.create_syslog_config()
        syslog_handler = SysLog(config)
        syslog_handler.syslogger = MagicMock()

        syslog_handler.publish_log_lines()

        syslog_handler.syslogger.log_info.assert_not_called()


    def test_publish_dns_records_no_events(self):
        config = test_data.create_syslog_config()
        syslog_handler = SysLog(config)
        syslog_handler.syslogger = MagicMock()

        syslog_handler.publish_dns_records()

        syslog_handler.syslogger.log_info.assert_not_called()


    @patch('lds_connector.syslogger.socket.socket')
    @patch('time.time', MagicMock(return_value=LOG_EMIT_TIME))
    def test_publish_multiple_logs(self, mock_socket: MagicMock):
        config = test_data.create_syslog_config()

        mock_socket_inst = MagicMock()
        mock_socket.return_value = mock_socket_inst

        syslog_handler = SysLog(config)
        log_events = test_data.get_dns_log_events()
        syslog_handler.add_log_line(log_events[0])
        syslog_handler.add_log_line(log_events[1])
        syslog_handler.add_log_line(log_events[2])
        syslog_handler.publish_log_lines()

        assert config.syslog is not None
        expected_message1 = SysLogTest.create_rfc3164_log(config, log_events[0], SysLogTest.EXPECTED_TIMES_RFC3164[0])
        expected_message2 = SysLogTest.create_rfc3164_log(config, log_events[1], SysLogTest.EXPECTED_TIMES_RFC3164[1])
        expected_message3 = SysLogTest.create_rfc3164_log(config, log_events[2], SysLogTest.EXPECTED_TIMES_RFC3164[2])
        self.assertEqual(mock_socket_inst.sendto.call_count, 3)
        mock_socket_inst.sendto.assert_has_calls([
            call(expected_message1, (config.syslog.host, config.syslog.port)),
            call(expected_message2, (config.syslog.host, config.syslog.port)),
            call(expected_message3, (config.syslog.host, config.syslog.port))
        ])


    @patch('lds_connector.syslogger.socket.socket')
    @freeze_time(datetime.fromtimestamp(LOG_EMIT_TIME, tz=timezone.utc))
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
        expected_message1 = SysLogTest.create_rfc3164_dns(config, test_data.create_dns_record1())
        expected_message2 = SysLogTest.create_rfc3164_dns(config, test_data.create_dns_record2())
        expected_message3 = SysLogTest.create_rfc3164_dns(config, test_data.create_dns_record3())
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

        log_events = test_data.get_dns_log_events()
        syslog_handler.add_log_line(log_events[0])
        syslog_handler.add_log_line(log_events[1])
        syslog_handler.clear()
        syslog_handler.publish_log_lines()

        syslog_handler.syslogger.log_info.assert_not_called()


    @staticmethod
    def create_rfc3164_dns(config: Config, json_object):
        json_message = json.dumps(json_object, cls=CustomJsonEncoder)
        assert config.syslog is not None
        return f'<14>Mar 19 01:00:00 {socket.gethostname()} {config.syslog.edgedns_app_name}: {json_message}\n'.encode('utf-8')


    @staticmethod
    def create_rfc3164_log(config: Config, log_event: LogEvent, timestamp: str, delim = SysLogDelimiter.LF):
        assert config.syslog is not None
        message = f'<14>{timestamp} {socket.gethostname()} {config.syslog.lds_app_name}: {log_event.log_line}'

        if delim == SysLogDelimiter.LF:
            message += '\n'
        elif delim == SysLogDelimiter.NULL:
            message += str('\x00')
        elif delim == SysLogDelimiter.CRLF:
            message += '\r\n'
        elif delim == SysLogDelimiter.NONE:
            pass
        elif delim == SysLogDelimiter.OCTET:
            message = str(len(message))+ ' ' + message

        return message.encode('utf-8')
    

    @staticmethod
    def create_rfc5424_log(config: Config, log_event: LogEvent, timestamp: str):
        assert config.syslog is not None
        return f'<14>1 {timestamp} {socket.gethostname()} {config.syslog.lds_app_name} - - - {log_event.log_line}\n'.encode('utf-8')
    

if __name__ == '__main__':
    unittest.main()
