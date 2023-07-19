
History
=======

# 2.2 (2023-07-19)

Improvements
- Add support for delivering logs using RFC-5424 syslog
- Add support for delivering logs using syslog over TLS/TCP 
- Add configuration for syslog message delimters and RFC-6587 octet-counting
- Extend Python support from 3.9+ to 3.6+. Unsupported language features were removed.
- Improve documentation


# 2.1 (2023-06-14)

Improvements
- Add support for LDS to deliver logs for multiple products (i.e. Edge DNS zones) to the same NetStorage upload directory
- Reduce unnecessary calls to NetStorage by caching the list of available log files
- Add retry behavior when publishing log events to Splunk fails
- Improve documentation

Bug fixes
- Delete downloaded log files from local file system on processing failure.


# 2.0 (2023-03-07)

Improvements:
- Add support for delivering LDS logs using SysLog
- Increase unit test coverage
- Improve documentation by...
    - Splitting into multiple documents
    - Adding more screenshots showing how to populate config YAML
    - Adding Wazuh and SysLog documentation
    - Adding example for delivering Edge DNS logs to Wazuh and Splunk, including Splunk field extraction and Wazuh
      decoder definition

1.0 (2023-02-24)
----------------

First version
