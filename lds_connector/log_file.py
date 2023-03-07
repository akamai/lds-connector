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

from dataclasses import dataclass
from datetime import datetime

@dataclass
class LogNameProps:
    customer_id: str
    cp_code: int
    format: str
    sorted: bool
    start_time: float
    part: int
    encoding: str


@dataclass
class LogFile:
    ns_path_gz: str
    filename_gz: str
    size: int
    md5: str
    name_props: LogNameProps
    local_path_gz: str
    local_path_txt: str
    last_processed_line: int
    processed: bool


@dataclass
class LogEvent:
    log_line: str
    timestamp: datetime
