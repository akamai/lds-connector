Introduction
============

This document details how to configure log delivery into SysLog

This document covers the following
- SysLog implementation specifics
- How to configure the LDS Connector to deliver via SysLog


SysLog Implementation
=====================

The LDS Connector delivers log events to Wazuh using SysLog messages. This should work for any other data platform
capable of ingesting SysLog. However, I haven't tested any.

However, there are a few specifics to note.

There are two SysLog specifications. 
The 2001 SysLog specification is defined in [RFC 3164](https://www.rfc-editor.org/rfc/rfc3164.html). 
The 2009 SysLog specification is defined in [RFC 5424](https://www.rfc-editor.org/rfc/rfc5424).
The LDS Connector uses the 2001 SysLog specification since that's what Wazuh uses. 

The LDS Connector supports sending SysLog messages over either TCP or UDP. Your data platform may only support UDP 
SysLog messages, as that's what's defined in RFC 3164.

The SysLog messages take the following format, encoded as UTF-8. 
- The hostname is populated automatically. 
- The program name is populated using `syslog.lds_app_name` (for LDS log events) and `syslog.edgedns_app_name` (for Edge DNS
records).
- The facility is hard-coded as user (1). The severity is hard-coded as informational (6)

```
<14> Jan 03 03:06:39 hostname program_name: log_event\n
```

LDS Connector Configuration
============================

In your LDS connector YAML configuration file
- Remove the `splunk` configuration 
- Add the `syslog` configuration 
- Use the [config_template.yaml](../../config_template.yaml) file for reference

