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

import logging
import os
from dataclasses import dataclass
from typing import Optional

import yaml


@dataclass
class HecConfig:
    source_type: Optional[str]
    index: Optional[str]
    token: str
    event_batch_size: int


@dataclass
class SplunkConfig:
    host: str
    hec_port: int
    hec_use_ssl: bool
    lds_hec: HecConfig
    edgedns_hec: Optional[HecConfig]


@dataclass
class SysLogTlsConfig:
    ca_file: str
    verify: bool


@dataclass
class SysLogConfig:
    host: str
    port: int
    protocol: str
    tls: Optional[SysLogTlsConfig]
    lds_app_name: str
    edgedns_app_name: Optional[str]
    append_null: bool
    from_host: Optional[str]


@dataclass
class NetStorageConfig:
    host: str
    account: str
    cp_code: int
    key: str
    use_ssl: bool
    log_dir: str


@dataclass
class EdgeDnsConfig:
    send_records: bool
    zone_name: str
    poll_period_sec: int

@dataclass
class AkamaiOpenConfig:
    client_secret: str
    host : str
    access_token : str
    client_token : str
    account_switch_key : Optional[str]


@dataclass
class LdsConfig:
    ns: NetStorageConfig
    log_download_dir: str
    timestamp_strptime: str
    timestamp_parse: str
    poll_period_sec: int


@dataclass
class Config:
    splunk: Optional[SplunkConfig]
    syslog: Optional[SysLogConfig]
    lds: LdsConfig
    edgedns: Optional[EdgeDnsConfig]
    open: Optional[AkamaiOpenConfig]


_KEY_EDGEDNS = 'edgedns'
_KEY_EDGEDNS_ZONE = 'zone_name'
_KEY_EDGEDNS_SEND_RECORDS = 'send_records'
_KEY_EDGEDNS_POLL_PERIOD = 'poll_period_sec'

_KEY_OPEN = 'open'
_KEY_OPEN_CLIENT_SECRET = 'client_secret'
_KEY_OPEN_HOST = 'host'
_KEY_OPEN_ACCESS_TOKEN = 'access_token'
_KEY_OPEN_CLIENT_TOKEN = 'client_token'
_KEY_OPEN_ACCOUNT_SWITCH_KEY = 'account_switch_key'

_KEY_SPLUNK = 'splunk'
_KEY_SPLUNK_HOST = 'host'
_KEY_SPLUNK_HEC_PORT = 'hec_port'
_KEY_SPLUNK_HEC_SSL = 'hec_use_ssl'
_KEY_SPLUNK_HEC_LDS = 'lds_hec'
_KEY_SPLUNK_HEC_EDGEDNS = 'edgedns_hec'
_KEY_SPLUNK_HEC_BATCH_SIZE = 'batch_size'
_KEY_SPLUNK_HEC_TOKEN = 'token'
_KEY_SPLUNK_HEC_SOURCE_TYPE = 'source_type'
_KEY_SPLUNK_HEC_INDEX = 'index'

_KEY_SYSLOG = 'syslog'
_KEY_SYSLOG_HOST = 'host'
_KEY_SYSLOG_PORT = 'port'
_KEY_SYSLOG_USE_TCP = 'use_tcp' # Deprecated
_KEY_SYSLOG_PROTOCOL = 'protocol'
_KEY_SYSLOG_LDS_APP_NAME = 'lds_app_name'
_KEY_SYSLOG_EDGEDNS_APP_NAME = 'edgedns_app_name'
_KEY_SYSLOG_APPEND_NULL = 'append_null'
_KEY_SYSLOG_FROM_HOST = 'from_host'
SYSLOG_PROTOCOL_UDP = 'UDP'
SYSLOG_PROTOCOL_TCP = 'TCP'
SYSLOG_PROTOCOL_TCP_TLS = 'TCP_TLS'

_KEY_SYSLOG_TLS = 'tls'
_KEY_SYSLOG_TLS_CA_FILE = 'ca_file'
_KEY_SYSLOG_TLS_VERIFY = 'verify'

_KEY_LDS = 'lds'
_KEY_LDS_LOG_DIR = 'log_download_dir'
_KEY_LDS_TIMESTAMP_PARSE = 'timestamp_parse'
_KEY_LDS_TIMESTAMP_STRPTIME = 'timestamp_strptime'
_KEY_LDS_LOG_POLL_PERIOD_SEC = 'log_poll_period_sec'

_KEY_NS = 'ns'
_KEY_NS_HOST = 'host'
_KEY_NS_ACCOUNT = 'upload_account'
_KEY_NS_CP_CODE = 'cp_code'
_KEY_NS_KEY = 'key'
_KEY_NS_SSL = 'use_ssl'
_KEY_NS_LOG_DIR = 'log_dir'


def is_config_valid(config: Config) -> bool:
    if config.splunk is None and config.syslog is None:
        logging.error('Invalid config. No destinations configured')
        return False

    if config.splunk is not None and config.syslog is not None:
        logging.error('Invalid config. Only one destination (Splunk or SysLog) can be configured')
        return False

    if config.edgedns is not None and config.edgedns.send_records:
        if config.open is None:
            logging.error('Invalid config. DNS record sending enabled but Akamai OPEN credentials not provided')
            return False
        if config.edgedns.zone_name is None:
            logging.error('Invalid config. DNS record sending enabled but no zone provided')
            return False
        if config.splunk is not None and config.splunk.edgedns_hec is None:
            logging.error('Invalid config. DNS record sending enabled but Splunk HEC token not provided')
            return False
        if config.syslog is not None and config.syslog.edgedns_app_name is None:
            logging.error('Invalid config. DNS record sending enabled by SysLog app name not provided')
            return False

    if config.syslog is not None:
        if config.syslog.protocol not in {SYSLOG_PROTOCOL_UDP, SYSLOG_PROTOCOL_TCP, SYSLOG_PROTOCOL_TCP_TLS}:
            logging.error('Invalid config. Syslog protocol is not supported: %s', config.syslog.protocol)
            return False
        if config.syslog.protocol == SYSLOG_PROTOCOL_TCP_TLS and config.syslog.tls is None:
            logging.error('Invalid config. Protocol is TCP_TLS but TLS config is missing')
            return False

    return True


def _get_syslog_protocol(syslog_yaml) -> str:
    protocol = syslog_yaml.get(_KEY_SYSLOG_PROTOCOL, None)

    if protocol is None:
        logging.warning('Config parameter "syslog.protocol" was not specified. Falling back to deprecated "syslog.use_tcp". The program will sill work as expected.')
        if syslog_yaml[_KEY_SYSLOG_USE_TCP]:
            protocol = SYSLOG_PROTOCOL_TCP
        else:
            protocol = SYSLOG_PROTOCOL_UDP

    return protocol


def read_yaml_config(yaml_stream) -> Optional[Config]:
    """
    Parses configuration from a YAML file

    Parameters:
        yaml_stream (_ReadStream): YAML file stream

    Returns 
        Optional[Config]: Config instance. If required value missing, None.

    """
    logging.info('Parsing configuration from YAML file')

    yaml_config = yaml.safe_load(yaml_stream)

    try:
        # Akamai Edge DNS Config
        edgedns_yaml = yaml_config.get(_KEY_EDGEDNS, None)
        edgedns_config = None
        if edgedns_yaml is not None:
            edgedns_config = EdgeDnsConfig(
                send_records=edgedns_yaml[_KEY_EDGEDNS_SEND_RECORDS],
                zone_name=edgedns_yaml[_KEY_EDGEDNS_ZONE],
                poll_period_sec=edgedns_yaml.get(_KEY_EDGEDNS_POLL_PERIOD, 7200)
            )

        # Akamai OPEN Config
        open_yaml = yaml_config.get(_KEY_OPEN, None)
        open_config = None
        if open_yaml is not None:
            open_config = AkamaiOpenConfig(
                client_secret=open_yaml[_KEY_OPEN_CLIENT_SECRET],
                host=open_yaml[_KEY_OPEN_HOST],
                access_token=open_yaml[_KEY_OPEN_ACCESS_TOKEN],
                client_token=open_yaml[_KEY_OPEN_CLIENT_TOKEN],
                account_switch_key=open_yaml.get(_KEY_OPEN_ACCOUNT_SWITCH_KEY, None)
            )

        # Splunk Config
        splunk_yaml = yaml_config.get(_KEY_SPLUNK, None)
        splunk_config = None
        if splunk_yaml is not None:
            splunk_lds_yaml = splunk_yaml[_KEY_SPLUNK_HEC_LDS]
            splunk_config = SplunkConfig(
                host=splunk_yaml[_KEY_SPLUNK_HOST],
                hec_port=splunk_yaml[_KEY_SPLUNK_HEC_PORT],
                hec_use_ssl=splunk_yaml[_KEY_SPLUNK_HEC_SSL],
                lds_hec=HecConfig(
                    source_type=splunk_lds_yaml.get(_KEY_SPLUNK_HEC_SOURCE_TYPE, None),
                    index=splunk_lds_yaml.get(_KEY_SPLUNK_HEC_INDEX, None),
                    token=splunk_lds_yaml[_KEY_SPLUNK_HEC_TOKEN],
                    event_batch_size=splunk_lds_yaml.get(_KEY_SPLUNK_HEC_BATCH_SIZE, 10)
                ),
                edgedns_hec=None
            )

            # Splunk Edge DNS HEC Config 
            splunk_edgedns_yaml = splunk_yaml.get(_KEY_SPLUNK_HEC_EDGEDNS)
            if splunk_edgedns_yaml is not None:
                splunk_config.edgedns_hec = HecConfig(
                    source_type=splunk_edgedns_yaml.get(_KEY_SPLUNK_HEC_SOURCE_TYPE, None),
                    index=splunk_edgedns_yaml.get(_KEY_SPLUNK_HEC_INDEX, None),
                    token=splunk_edgedns_yaml[_KEY_SPLUNK_HEC_TOKEN],
                    event_batch_size=splunk_edgedns_yaml.get(_KEY_SPLUNK_HEC_BATCH_SIZE, 10)
                )

        # LDS Config
        lds_yaml = yaml_config[_KEY_LDS]
        ns_yaml = lds_yaml[_KEY_NS]
        lds_config = LdsConfig(
            ns=NetStorageConfig(
                host=ns_yaml[_KEY_NS_HOST],
                account=ns_yaml[_KEY_NS_ACCOUNT],
                cp_code=ns_yaml[_KEY_NS_CP_CODE],
                key=ns_yaml[_KEY_NS_KEY],
                use_ssl=ns_yaml[_KEY_NS_SSL],
                log_dir=ns_yaml[_KEY_NS_LOG_DIR]
            ),
            log_download_dir=os.path.abspath(lds_yaml[_KEY_LDS_LOG_DIR]),
            timestamp_parse=lds_yaml[_KEY_LDS_TIMESTAMP_PARSE],
            timestamp_strptime=lds_yaml[_KEY_LDS_TIMESTAMP_STRPTIME],
            poll_period_sec=lds_yaml.get(_KEY_LDS_LOG_POLL_PERIOD_SEC, 60)
        )

        # SysLog Config
        syslog_yaml = yaml_config.get(_KEY_SYSLOG, None)
        syslog_config = None
        if syslog_yaml is not None:
            syslog_tls_yaml = syslog_yaml.get(_KEY_SYSLOG_TLS, None)
            syslog_tls_config = None
            if syslog_tls_yaml is not None:
                syslog_tls_config = SysLogTlsConfig(
                    ca_file=syslog_tls_yaml.get(_KEY_SYSLOG_TLS_CA_FILE),
                    verify=syslog_tls_yaml.get(_KEY_SYSLOG_TLS_VERIFY, True)
                )
            syslog_config = SysLogConfig(
                host=syslog_yaml[_KEY_SYSLOG_HOST],
                port=syslog_yaml[_KEY_SYSLOG_PORT],
                protocol=_get_syslog_protocol(syslog_yaml),
                tls=syslog_tls_config,
                lds_app_name=syslog_yaml[_KEY_SYSLOG_LDS_APP_NAME],
                edgedns_app_name=syslog_yaml.get(_KEY_SYSLOG_EDGEDNS_APP_NAME, None),
                append_null=syslog_yaml.get(_KEY_SYSLOG_APPEND_NULL, True),
                from_host=syslog_yaml.get(_KEY_SYSLOG_FROM_HOST, None)
            )

        config = Config(
            splunk=splunk_config,
            syslog=syslog_config,
            lds=lds_config,
            edgedns=edgedns_config,
            open=open_config
        )

        if not is_config_valid(config):
            return None

        logging.info('Parsed configuration from file')
        return config
    except KeyError as key_error:
        logging.error('Configuration file missing key %s', key_error.args[0])
        return None

