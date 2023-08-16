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
import argparse
import sys
import sched
import time

from lds_connector.config import read_yaml_config, Config
from lds_connector.connector import Connector, build_connector


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        prog = 'lds_connector.py',
        description = 'Script to move Akamai Log Delivery Service (LDS) logs from NetStorage into Splunk')
    parser.add_argument('--config',
        required=True,
        help='destination of the YAML configuration file',
        type=argparse.FileType('r'))
    parser.add_argument('--level',
        help='log level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO'
    )
    args = parser.parse_args()

    # Set log level
    logging.basicConfig(level=args.level)

    # Parse config from YAML file stream
    config = read_yaml_config(args.config)
    args.config.close()
    if not config:
        sys.exit(1)

    connector = build_connector(config)
    scheduler = sched.scheduler(time.time, time.sleep)
    if config.edgedns is not None and config.edgedns.send_records:
        scheduler.enter(delay=0,  priority=2, action=sched_process_dns_records, argument=(scheduler, connector, config))
    scheduler.enter(delay=0,  priority=1, action=sched_process_log_files, argument=(scheduler, connector, config))
    scheduler.run()


def sched_process_log_files(scheduler: sched.scheduler, connector: Connector, config: Config):
    connector.process_log_files()
    scheduler.enter(
        delay=config.lds.poll_period_sec,
        priority=1,
        action=sched_process_log_files,
        argument=(scheduler, connector, config))


def sched_process_dns_records(scheduler: sched.scheduler, connector: Connector, config: Config):
    assert config.edgedns is not None
    connector.process_dns_records()
    scheduler.enter(
        delay=config.edgedns.poll_period_sec,
        priority=1,
        action=sched_process_dns_records,
        argument=(scheduler, connector, config))


if __name__ == '__main__':
    main()
