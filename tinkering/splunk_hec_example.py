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

import argparse
from urllib.parse import urljoin

import requests
import yaml

KEY_SPLUNK = 'splunk'
KEY_SPLUNK_HEC = 'hec'
KEY_SPLUNK_HEC_HOST = 'host'
KEY_SPLUNK_HEC_PORT = 'port'
KEY_SPLUNK_HEC_SSL = 'use_ssl'
KEY_SPLUNK_HEC_TOKEN = 'token'

HEC_ENDPOINT = '/services/collector/event'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog = 'splunk_hec_example',
        description = 'Send an example HEC event to Splunk')
    parser.add_argument('-c', '--config', required=True, type=argparse.FileType('r'))
    args = parser.parse_args()

    print('Parsing configuration from file')

    config = yaml.safe_load(args.config)

    hec_host = config[KEY_SPLUNK][KEY_SPLUNK_HEC][KEY_SPLUNK_HEC_HOST]
    hec_port = config[KEY_SPLUNK][KEY_SPLUNK_HEC][KEY_SPLUNK_HEC_PORT]
    hec_use_ssl = config[KEY_SPLUNK][KEY_SPLUNK_HEC][KEY_SPLUNK_HEC_SSL]
    hec_token = config[KEY_SPLUNK][KEY_SPLUNK_HEC][KEY_SPLUNK_HEC_TOKEN]

    baseurl = ('https://' if hec_use_ssl else 'http://') + hec_host + ':' + str(hec_port)
    url = urljoin(baseurl, HEC_ENDPOINT)
    headers = {'Authorization': 'Splunk ' + hec_token}

    payload = {
        'time': 1672716997,
        'host': 'localhost',
        'source': 'Akamai Splunk - LDS Connector',
        'sourcetype': 'edgedns_logs',
        'index': 'sandbox',
        'event':  '416458 - 1672716996 03/01/2023 03:36:37,34.217.7.8,38661,2ww-nigiro.edgedns.zone,IN,AAAA,E,4096,D,,3:NXDOMAIN'
    }

    print('Sending event to Splunk HEC')
    result = requests.post(url, headers=headers, json=payload, timeout=2)
    print(result)
