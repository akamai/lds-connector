
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