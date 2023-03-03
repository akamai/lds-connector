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
import time
from typing import Optional

import requests
from akamai.edgegrid import EdgeGridAuth

from .config import Config
from .dns_record import DnsRecord


class EdgeDnsManager():
    def __init__(self, config: Config):
        assert config.edgedns is not None
        assert config.edgedns.send_records
        assert config.open is not None

        self.records_url = f'https://{config.open.host}/config-dns/v2/zones/{config.edgedns.zone_name}/recordsets'

        self.open_session = requests.Session()
        self.open_session.auth = EdgeGridAuth(
            client_token=config.open.client_token,
            client_secret=config.open.client_secret,
            access_token=config.open.access_token
        )

        self.config = config

    def get_records(self) -> list[DnsRecord]:
        assert self.config.edgedns is not None
        assert self.config.open is not None

        record_set = []
        query_params = {}

        if self.config.open.account_switch_key is not None:
            query_params['accountSwitchKey'] = self.config.open.account_switch_key

        # Fetch first page of DNS records
        response = self.open_session.get(url=self.records_url, params=query_params)
        if response.status_code != 200:
            logging.error('Failed fetching Edge DNS records')
            return []
        try:
            last_page = response.json()['metadata']['lastPage']
            next_page = response.json()['metadata']['page'] + 1
        except (KeyError, TypeError) as key_error:
            logging.error('Edge DNS API returned unexpected response [%s]: [%s]', key_error, response.json)
            return []
        record_set.extend(self._parse_records(response.json()))

        # Fetch remaining pages of DNS records
        while next_page <= last_page:
            query_params['page'] = next_page
            response = self.open_session.get(url=self.records_url, params=query_params)
            if response.status_code != 200:
                logging.error('Failed fetching Edge DNS records')
                break
            record_set.extend(self._parse_records(response.json()))
            next_page += 1

        return record_set

    def _parse_records(self, json_response) -> list[DnsRecord]:
        assert self.config.edgedns is not None
        assert self.config.edgedns.zone_name is not None

        records = []
        time_fetched_sec = time.time()
        for json_record in json_response['recordsets']:
            try:
                records.append(DnsRecord(
                    zone=self.config.edgedns.zone_name,
                    time_fetched_sec=time_fetched_sec,
                    name=json_record['name'],
                    type=json_record['type'],
                    ttl_sec=json_record['ttl'],
                    rdata=json_record['rdata']
                ))
            except (KeyError, TypeError) as key_error:
                logging.warning('Edge DNS API returned record missing key [%s]: [%s]', key_error, json_record)

        return records


def create_edgedns_manager(config: Config) -> Optional[EdgeDnsManager]:
    if config.edgedns is None or not config.edgedns.send_records:
        return None
    return EdgeDnsManager(config)
