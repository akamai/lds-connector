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
import shutil
import json
from datetime import datetime, timezone

from lds_connector.config import *
from lds_connector.log_manager import LogFile, LogNameProps, LogManager
from lds_connector.edgedns_manager import DnsRecord
from lds_connector.log_file import LogEvent


DATA_DIR = path.join(path.dirname(__file__), 'data')
TEMP_DIR = path.join(path.dirname(__file__), 'tmp')
RESUME_PATH = path.join(TEMP_DIR, LogManager._RESUME_PICKLE_FILE_NAME)

NS_LIST_RESPONSE = """<?xml version="1.0" encoding="ISO-8859-1"?>
<list>
    <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030300-0400-0.gz" size="1234" md5="098f6bcd4621d373cade4e832627b4f6"/>
    <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030400-0500-0.gz" size="2345" md5="5d41402abc4b2a76b9719d911017c592"/>
    <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030400-0500-1.gz" size="3456" md5="d850f04cdb48312a9be171e214c0b4ee"/>
</list>"""

DNS_LOG_LINES = [
    '416458 - 1672715199 03/01/2023 03:06:39,52.37.159.152,52149,edgedns.zone,IN,CAA,E,4096,D,,300:0 issue "ca.sectigo.com" 300:0 issue "ca.digicert.com" SIGNx1 \n',
    '416458 - 1672715199 03/01/2023 03:06:39,52.37.159.152,64062,2ww-nigiro.edgedns.zone,IN,A,E,4096,D,,3:NXDOMAIN \n',
    '416458 - 1672715199 03/01/2023 03:06:39,52.37.159.152,43215,edgedns.zone,IN,NS,E,4096,D,,86400:a13-67.akam.net 86400:a11-66.akam.net 86400:a22-64.akam.net 86400:a24-65.akam.net 86400:a28-66.akam.net 86400:a1-247.akam.net SIGNx1 \n',
    '416458 - 1672713883 03/01/2023 02:44:43,2600:1406:1a00:2::687d:da8c,44473,edgedns.zone,IN,SOA,,,,,86400:a1-247.akam.net hostmaster.edgedns.zone 2019102599 3600 600 604800 300 \n'
]

DNS_LOG_TIMESTAMPS = [1672715199.0, 1672715199.0, 1672715199.0, 1672713883.0]

DNS_LOG_EVENTS = [
    LogEvent(DNS_LOG_LINES[0], datetime.fromtimestamp(DNS_LOG_TIMESTAMPS[0]).astimezone(timezone.utc)),
    LogEvent(DNS_LOG_LINES[1], datetime.fromtimestamp(DNS_LOG_TIMESTAMPS[1]).astimezone(timezone.utc)),
    LogEvent(DNS_LOG_LINES[2], datetime.fromtimestamp(DNS_LOG_TIMESTAMPS[2]).astimezone(timezone.utc)),
    LogEvent(DNS_LOG_LINES[3], datetime.fromtimestamp(DNS_LOG_TIMESTAMPS[3]).astimezone(timezone.utc))
]


def create_splunk_config():
    return Config(
        splunk=SplunkConfig(
            host="127.0.0.1",
            hec_port=8088,
            hec_use_ssl=False,
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
                log_dir='logs1'
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
        use_tcp=False,
        lds_app_name='test_lds_app_name',
        edgedns_app_name='test_edgedns_app_name'
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


def read_json(filename: str):
    json_path = path.join(path.dirname(__file__), 'data/', filename)
    json_data = {}
    with open(json_path, 'r', encoding='utf-8') as json_file:
        json_data = json.load(json_file)

    return json_data


def download_file(log_file: LogFile):
    """
    Mock method of downloading a file

    The desired log file is assumed to exist in data/ directory. 
    It's copied into the tmp/ download directory.
    This allows unit testing the Gzip deletion.
    """
    source_path: str = path.join(DATA_DIR, log_file.filename_gz)
    dest_path: str = path.join(TEMP_DIR, log_file.filename_gz)
    shutil.copyfile(source_path, dest_path)

    log_file.local_path_gz = dest_path


def download_uncompress_file(log_file: LogFile):
    download_file(log_file)
    LogManager._uncompress(log_file)
    os.remove(log_file.local_path_gz)
