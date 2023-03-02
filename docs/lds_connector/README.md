
Log Download Directory 
======================

The log files are downloaded from NetStorage into the directory configured at `lds.log_download_dir`. This is an
absolute path, or relative path from the current working directory.

The LDS connector will download compressed log files here, uncompress them, and delete them when done.

The LDS connector will also create a file in this directory containing metadata on the last processed log file. This
allows the LDS connector to resume where it left off if restarted.


Timestamp Extraction
====================

Splunk receives logs from the LDS connector using the HTTP Event Collector. The events must include the timestamp,
otherwise Splunk sets the timestamp to the current time. 

Wazuh receives logs from the LDS connector using SysLog messages. The SysLog messages must include the timestamp.

As a result, the LDS connector must extract the timestamp from each log line, before sending it to Splunk/Wazuh.

This timestamp extraction is defined by two YAML configuration parameteters. This allows the connector script to
support any LDS format.

The `lds.timestamp_parse` value specifies where the timestamp is in the log line. This is a 
[parse](https://pypi.org/project/parse/) format string. It should contain a named field called `timestamp`.

The `lds.timestamp_strptime` value specifies how the timestamp is formatted. This is a 
[datetime strptime()](https://docs.python.org/3/library/datetime.html) format string. It supports the additional 
format string "%s" to handle epoch times in seconds.


DNS Example
------------

This is for the `dns` log format. An example log line is as follows
```
416458 - 1672716996 03/01/2023 03:36:36,34.217.7.8,55972,2ww-nigiro.edgedns.zone,IN,A,E,4096,D,,3:NXDOMAIN 
```

Recommended configuration. 
``` YAML
lds.timestamp_parse: '{} - {timestamp} {}'
lds.timestamp_strptime: '%s'
```
The LDS connector will parse the log line into several fields
- Unnamed field: `416458`
- timestamp: `1672716996` 
- Unnamed field: `03/01/2023 03:36:36,34.217.7.8,55972,2ww-nigiro.edgedns.zone,IN,A,E,4096,D,,3:NXDOMAIN `

The LDS connector will then parse the timestamp field `1672716996` into a datetime.


Another possible configuration.
``` YAML
lds.timestamp_parse: '{} - {} {timestamp},{}'
lds.timestamp_strptime: '%d/%m/%Y %H:%M:%S'
```
The LDS connector will parse the log line into several fields
- Unnamed field: `416458`
- Unnamed field: `1672716996` 
- timestamp: `03/01/2023 03:36:36`
- Unnamed field: `34.217.7.8,55972,2ww-nigiro.edgedns.zone,IN,A,E,4096,D,,3:NXDOMAIN `

The LDS connector will then parse the timestamp field `03/01/2023 03:36:36` into a datetime.


Delivering Edge DNS Records
===========================

The LDS connector can be configured to deliver Edge DNS records for a given zone. This is useful when delivered along 
side Edge DNS LDS logs.

When delivering to Splunk, the HEC token configured at `splunk.edgedns_hec` is used.

When delivering to SysLog, the app name configured at `syslog.edgedns_app_name` is used.



References
==========

https://techdocs.akamai.com/netstorage/docs

https://techdocs.akamai.com/netstorage/docs/key-concepts-and-terms

https://techdocs.akamai.com/netstorage-usage/reference/api

https://techdocs.akamai.com/log-delivery/docs

https://techdocs.akamai.com/log-delivery/docs/log-deliv-opt

https://techdocs.akamai.com/log-delivery/docs/file-names