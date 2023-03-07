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
import requests
import yaml
import json
from akamai.edgegrid import EdgeGridAuth

KEY_AKAMAI = 'akamai'
KEY_OPEN = 'open'
KEY_OPEN_CLIENT_SECRET = 'client_secret'
KEY_OPEN_HOST = 'host'
KEY_OPEN_ACCESS_TOKEN = 'access_token'
KEY_OPEN_CLIENT_TOKEN = 'client_token'
KEY_OPEN_ACCOUNT_SWITCH = 'account_switch_key'
KEY_EDGEDNS = 'edgedns'
KEY_EDGEDNS_ZONE = 'zone_name'

def main():
    parser = argparse.ArgumentParser(
        prog = 'dns_zone_example',
        description = 'Fetch Akamai Edge DNS zone data')
    parser.add_argument('-c', '--config', required=True, type=argparse.FileType('r'))
    args = parser.parse_args()

    print('Parsing configuration from file')
    config = yaml.safe_load(args.config)

    akamai_open_config = config[KEY_AKAMAI][KEY_OPEN]
    open_client_secret = akamai_open_config[KEY_OPEN_CLIENT_SECRET]
    open_host = akamai_open_config[KEY_OPEN_HOST]
    open_access_token = akamai_open_config[KEY_OPEN_ACCESS_TOKEN]
    open_client_token = akamai_open_config[KEY_OPEN_CLIENT_TOKEN]
    open_account_switch_key = akamai_open_config[KEY_OPEN_ACCOUNT_SWITCH]

    akamai_edgedns_config = config[KEY_AKAMAI][KEY_EDGEDNS]
    edgedns_zone = akamai_edgedns_config[KEY_EDGEDNS_ZONE]
    print('Parsed configuration from file')


    open_session = requests.Session()
    open_session.auth = EdgeGridAuth(
        client_token=open_client_token,
        client_secret=open_client_secret,
        access_token=open_access_token
    )


    # print('Fetching zone settings')
    # url = f'https://{open_host}/config-dns/v2/zones/{edgedns_zone}'
    # query_params = {'accountSwitchKey': open_account_switch_key}
    # result = open_session.get(url=url, params=query_params)
    # print('Result code ', result.status_code)
    # print('Result: ', result.json())
    # print()

    # print('Fetching available names in zone')
    # url = f'https://{open_host}/config-dns/v2/zones/{edgedns_zone}/names'
    # query_params = {'accountSwitchKey': open_account_switch_key}
    # result = open_session.get(url=url, params=query_params)
    # names_json = result.json()
    # print('Result code ', result.status_code)
    # print('Result: ', names_json)
    # print()

    # print('Fetching master zone file')
    # url = f'https://{open_host}/config-dns/v2/zones/{edgedns_zone}/zone-file'
    # query_params = {'accountSwitchKey': open_account_switch_key}
    # headers = {'Accept': 'text/dns'}
    # result = open_session.get(url=url, params=query_params, headers=headers)
    # print('Result code ', result.status_code)
    # print('Result: ', result.text)
    # print()

    print('Fetching zone resource records')
    url = f'https://{open_host}/config-dns/v2/zones/{edgedns_zone}/recordsets'
    query_params = {'accountSwitchKey': open_account_switch_key}
    result = open_session.get(url=url, params=query_params)
    print('Result code ', result.status_code)
    print('Result: ', json.dumps(result.json(), indent=4))
    print()

    print('Fetching any remaining zone resource records...')
    print()

    while True:
        next_page = result.json()['metadata']['page'] + 1
        if result.status_code != 200 or next_page > result.json()['metadata']['lastPage']:
            break
        query_params = {'accountSwitchKey': open_account_switch_key, 'page': next_page}
        result = open_session.get(url=url, params=query_params)
        print('Result code ', result.status_code)
        print('Result: ', json.dumps(result.json(), indent=4))
        print()


if __name__ == '__main__':
    main()
