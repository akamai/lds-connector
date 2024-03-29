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

import os
from os import path
from datetime import datetime, timezone
from typing import List

from lds_connector.config import *
from lds_connector.log_manager import LogFile, LogNameProps, LogManager
from lds_connector.edgedns_manager import DnsRecord
from lds_connector.log_file import LogEvent

from test import test_util


DATA_DIR = path.join(path.dirname(__file__), 'data')
TEMP_DIR = path.join(path.dirname(__file__), 'tmp')
RESUME_DATA_PATH = path.join(TEMP_DIR, LogManager._RESUME_DATA_PICKLE_FILE_NAME)

NS_LIST_RESPONSE = """<?xml version="1.0" encoding="ISO-8859-1"?>
<list>
    <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030300-0400-0.gz" size="1234" md5="098f6bcd4621d373cade4e832627b4f6"/>
    <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030400-0500-0.gz" size="2345" md5="5d41402abc4b2a76b9719d911017c592"/>
    <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030400-0500-1.gz" size="3456" md5="d850f04cdb48312a9be171e214c0b4ee"/>
</list>"""

DNS_LOG_EVENTS_PATH = 'test_log_events.json'
def get_dns_log_events() -> List[LogEvent]:
    log_events: List[LogEvent]= []
    log_events_json = test_util.read_json(DNS_LOG_EVENTS_PATH)
    for log_event_json in log_events_json['log_events']:
        log_events.append(LogEvent(
            timestamp=datetime.fromtimestamp(log_event_json['timestamp'], timezone.utc),
            log_line=log_event_json['log_line']
        ))

    return log_events

def get_dns_log_lines() -> List[str]:
    log_events: List[LogEvent] = get_dns_log_events()
    return map(lambda le: le.log_line, log_events)


CA_FILE = path.join(DATA_DIR, 'ca.pem')

def create_splunk_config():
    return Config(
        splunk=SplunkConfig(
            host="127.0.0.1",
            hec_port=8088,
            hec_use_ssl=False,
            hec_ssl_verify=True,
            lds_hec=HecConfig(
                source_type='lds_log_dns',
                index='sandbox',
                token="test_lds_hec_token",
                event_batch_size=8
            ),
            edgedns_hec=HecConfig(
                source_type='edgedns_record',
                index='sandbox',
                token="test_edgedns_hec_token",
                event_batch_size=10
            )
        ),
        syslog=None,
        edgedns=EdgeDnsConfig(
            send_records=True,
            zone_name='edgedns.zone',
            poll_period_sec=3600
        ),
        open=AkamaiOpenConfig(
            client_secret='test_client_secret',
            host='test_host',
            access_token='test_access_token',
            client_token='test_client_token',
            account_switch_key='test_account_switch_key'
        ),
        lds=LdsConfig(
            ns=NetStorageConfig(
                host="test_ns_host",
                account="test_ns_account",
                cp_code=123456,
                key="test_key",
                use_ssl=True,
                log_dir='cam/logs/'
            ),
            log_download_dir=os.path.abspath('logs2'),
            timestamp_parse='{} - {} {timestamp},{}',
            timestamp_strptime='%d/%m/%Y %H:%M:%S',
            poll_period_sec=60
        )
    )


def create_syslog_config():
    config = create_splunk_config()

    config.splunk = None
    config.syslog = SysLogConfig(
        host='192.168.0.1',
        port=514,
        protocol=SysLogProtocol.RFC3164,
        transport=SysLogTransport.UDP,
        tls=None,
        lds_app_name='test_lds_app_name',
        edgedns_app_name='test_edgedns_app_name',
        delimiter_method=SysLogDelimiter.LF,
        from_host=None
    )

    return config


def get_ns_file1():
    return LogFile(
        ns_path_gz='/123456/cam/logs/cam_123456.edns_U.202301030300-0400-0.gz',
        filename_gz='cam_123456.edns_U.202301030300-0400-0.gz',
        size=1234,
        md5='098f6bcd4621d373cade4e832627b4f6',
        name_props= LogNameProps(
            customer_id='cam',
            cp_code=123456,
            format='edns',
            sorted=False,
            start_time=1672714800.0,
            part=0,
            encoding='gz'
        ),
        local_path_gz='',
        local_path_txt='',
        processed=False,
        last_processed_line=-1
    )
NS_FILE1_LINES = 15


def get_ns_file2():
    return LogFile(
        ns_path_gz='/123456/cam/logs/cam_123456.edns_U.202301030400-0500-0.gz',
        filename_gz='cam_123456.edns_U.202301030400-0500-0.gz',
        size=2345,
        md5='5d41402abc4b2a76b9719d911017c592',
        name_props=LogNameProps(
            customer_id='cam',
            cp_code=123456,
            format='edns',
            sorted=False,
            start_time=1672718400.0,
            part=0,
            encoding='gz'
        ),
        local_path_gz='',
        local_path_txt='',
        processed=False,
        last_processed_line=-1
    )
NS_FILE2_LINES = 15


def get_ns_file3():
    return LogFile(
        ns_path_gz='/123456/cam/logs/cam_123456.edns_U.202301030400-0500-1.gz',
        filename_gz='cam_123456.edns_U.202301030400-0500-1.gz',
        size=3456,
        md5='d850f04cdb48312a9be171e214c0b4ee',
        name_props= LogNameProps(
            customer_id='cam',
            cp_code=123456,
            format='edns',
            sorted=False,
            start_time=1672718400.0,
            part=1,
            encoding='gz'
        ),
        local_path_gz='',
        local_path_txt='',
        processed=False,
        last_processed_line=-1
    )
NS_FILE3_LINES = 15


def get_ns_file4():
    return LogFile(
        ns_path_gz='/123456/cam/logs/cam_123456.edns_U.202301030500-0600-0.gz',
        filename_gz='cam_123456.edns_U.202301030500-0600-0.gz',
        size=3456,
        md5='d850f04cdb48312a9be171e214c0b4ee',
        name_props= LogNameProps(
            customer_id='cam',
            cp_code=123456,
            format='edns',
            sorted=False,
            start_time=1672718400.0,
            part=0,
            encoding='gz'
        ),
        local_path_gz='',
        local_path_txt='',
        processed=False,
        last_processed_line=-1
    )
NS_FILE4_LINES = 16

def get_ns_file5():
    return LogFile(
        ns_path_gz='/123456/cam/logs/yaac_123456.edns_U.202301030300-0400-0.gz',
        filename_gz='yaac_123456.edns_U.202301030300-0400-0.gz',
        size=1234,
        md5='098f6bcd4621d373cade4e832627b4f6',
        name_props= LogNameProps(
            customer_id='yaac',
            cp_code=123456,
            format='edns',
            sorted=False,
            start_time=1672714800.0,
            part=0,
            encoding='gz'
        ),
        local_path_gz='',
        local_path_txt='',
        processed=False,
        last_processed_line=-1
    )
NS_FILE5_LINES = 16


DNS_RECORD1_JSON = '{"time_fetched_sec": 0, "zone": "edgedns.zone", "name": "edgedns.zone", "type": "CAA", ' \
    + '"ttl_sec": 300, "rdata": ["0 issue \\"ca.sectigo.com\\"", "0 issue \\"ca.digicert.com\\""]}'
def create_dns_record1():
    return DnsRecord(
        zone='edgedns.zone',
        time_fetched_sec=0,
        name='edgedns.zone',
        type='CAA',
        ttl_sec=300,
        rdata=['0 issue \"ca.sectigo.com\"', '0 issue \"ca.digicert.com\"']
    )

def create_dns_record2():
    return DnsRecord(
        zone='edgedns.zone',
        time_fetched_sec=0,
        name='edgedns.zone',
        type='SOA',
        ttl_sec=86400,
        rdata=['a1-247.akam.net. hostmaster.edgedns.zone. 2019102601 3600 600 604800 300']
    )

def create_dns_record3():
    return DnsRecord(
        zone='edgedns.zone',
        time_fetched_sec=0,
        name='cam.edgedns.zone',
        type='A',
        ttl_sec=300,
        rdata=['192.0.2.2']
    )

