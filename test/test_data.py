import os
from os import path

from src.config import Config, SplunkConfig, NetStorageConfig
from src.log_manager import _LogFile, _LogNameProps


DATA_DIR = path.join(path.dirname(__file__), 'data')
TEMP_DIR = path.join(path.dirname(__file__), 'tmp')

NS_LIST_RESPONSE = """<?xml version="1.0" encoding="ISO-8859-1"?>
<list>
    <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030300-0400-0.gz" size="1234" md5="098f6bcd4621d373cade4e832627b4f6"/>
    <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030400-0500-0.gz" size="2345" md5="5d41402abc4b2a76b9719d911017c592"/>
    <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030400-0500-1.gz" size="3456" md5="d850f04cdb48312a9be171e214c0b4ee"/>
</list>"""


def create_config():
    return Config(
        splunk_config=SplunkConfig(
            hec_host="127.0.0.1",
            hec_port=8088,
            hec_token="test_hec_token",
            hec_use_ssl=False
        ),
        netstorage_config=NetStorageConfig(
            host="test_ns_host",
            account="test_ns_account",
            cp_code=123456,
            key="test_key",
            use_ssl=True,
            log_dir='logs1'
        ),
        log_download_dir=os.path.abspath('logs2')
    )


def get_ns_file1():
    return _LogFile(
        ns_path_gz='123456/cam/logs/cam_123456.edns_U.202301030300-0400-0.gz',
        filename_gz='cam_123456.edns_U.202301030300-0400-0.gz',
        size=1234,
        md5='098f6bcd4621d373cade4e832627b4f6',
        name_props= _LogNameProps(
            customer_id='cam',
            cp_code=123456,
            format='edns',
            sorted=False,
            start_time=1672714800.0,
            part=0,
            encoding='gz'
        ),
        local_path_gz='',
        local_path_txt=''
    )


def get_ns_file2():
    return _LogFile(
        ns_path_gz='123456/cam/logs/cam_123456.edns_U.202301030400-0500-0.gz',
        filename_gz='cam_123456.edns_U.202301030400-0500-0.gz',
        size=2345,
        md5='5d41402abc4b2a76b9719d911017c592',
        name_props=_LogNameProps(
            customer_id='cam',
            cp_code=123456,
            format='edns',
            sorted=False,
            start_time=1672718400.0,
            part=0,
            encoding='gz'
        ),
        local_path_gz='',
        local_path_txt=''
    )


def get_ns_file3():
    return _LogFile(
        ns_path_gz='123456/cam/logs/cam_123456.edns_U.202301030400-0500-1.gz',
        filename_gz='cam_123456.edns_U.202301030400-0500-1.gz',
        size=3456,
        md5='d850f04cdb48312a9be171e214c0b4ee',
        name_props= _LogNameProps(
            customer_id='cam',
            cp_code=123456,
            format='edns',
            sorted=False,
            start_time=1672718400.0,
            part=1,
            encoding='gz'
        ),
        local_path_gz='',
        local_path_txt=''
    )
