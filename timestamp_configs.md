
Timestamp Configuration Examples
================================


This document provides example config values for each LDS format for parsing timestamps from log lines

DNS 
---

This is for the `dns` log format

Recommended configuration. 
``` YAML
connector.timestamp_parse: '{} - {timestamp} {}'
timestamp_strptime: '%s'
```

Another possible configuration.
``` YAML
connector.timestamp_parse: '{} - {} {timestamp},{}'
timestamp_strptime: '%d/%m/%Y %H:%M:%S'
```

Example log line
```
416458 - 1672716996 03/01/2023 03:36:36,34.217.7.8,55972,2ww-nigiro.edgedns.zone,IN,A,E,4096,D,,3:NXDOMAIN 
```


License
=======

Copyright 2023 Akamai Technologies, Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an 
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the 
specific language governing permissions and limitations under the License.

