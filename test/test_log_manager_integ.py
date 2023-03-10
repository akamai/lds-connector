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
import shutil

from lds_connector.config import read_yaml_config
from lds_connector.log_manager import LogManager

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog = 'test_log_manager_integ',
        description = 'Integration test the LogManager -> NetStorage interaction')
    parser.add_argument('-c', '--config', required=True, type=argparse.FileType('r'))
    args = parser.parse_args()

    config = read_yaml_config(args.config)
    args.config.close()
    assert config is not None

    log_manager = LogManager(config)

    log_file = log_manager.get_next_log()

    print(log_file)

    shutil.rmtree(config.log_download_dir)
