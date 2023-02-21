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
from akamai.edgegrid import EdgeGridAuth

CONFIG_KEY_OPEN = "akamai_open_token"
CONFIG_KEY_OPEN_CLIENT_SECRET = "client_secret"
CONFIG_KEY_OPEN_HOST = "host"
CONFIG_KEY_OPEN_ACCESS_TOKEN = "access_token"
CONFIG_KEY_OPEN_CLIENT_TOKEN = "client_token"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog = 'open_auth_example',
        description = 'Authorize with Akamai using OPEN and fetch edge server locations')
    parser.add_argument('-c', '--config', required=True, type=argparse.FileType('r'))
    args = parser.parse_args()

    print('Parsing configuration from file')

    config = yaml.safe_load(args.config)

    open_client_secret = config[CONFIG_KEY_OPEN][CONFIG_KEY_OPEN_CLIENT_SECRET]
    open_host = config[CONFIG_KEY_OPEN][CONFIG_KEY_OPEN_HOST]
    open_access_token = config[CONFIG_KEY_OPEN][CONFIG_KEY_OPEN_ACCESS_TOKEN]
    open_client_token = config[CONFIG_KEY_OPEN][CONFIG_KEY_OPEN_CLIENT_TOKEN]

    open_session = requests.Session()
    open_session.auth = EdgeGridAuth(
        client_token=open_client_token,
        client_secret=open_client_secret,
        access_token=open_access_token
    )

    print('Fetching available edge locations')

    result = open_session.get(urljoin('https://' + open_host, '/edge-diagnostics/v1/edge-locations'))
    print('Result code ', result.status_code)
    print('Result: ', result.json())
