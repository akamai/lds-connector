Akamai Log Delivery Service Connector 
=====================================

Version 2.1 - June 14, 2023

Introduction
------------

The LDS Connector is a solution to periodically deliver Akamai log events into third-party data platforms. 
We currently support delivering logs to Splunk, Wazuh, and any platform that can receive Syslog messages.

The Log Delivery Service (LDS) is an Akamai service that periodically delivers Akamai log files via email, FTP storage, 
or Akamai NetStorage. 

The LDS Connector is a script that monitors a NetStorage location for LDS logs, parses them into log events, and sends
them to your data platform.

The LDS Connector's **Log Delivery** feature monitors NetStorage for LDS logs, parses them into log events, and delivers
them to your data platform.

The LDS Connector's **Record Set Delivery** add-on feature periodically fetches an Edge DNS record set using the 
Akamai APIs, parses them into log events, and delivers them to your data platform. This currently only suports a 
single zone.

This document will show you
1. How to configure Log Delivery Service to send your Akamai logs to NetStorage
2. How to configure your third-party data platform to receive Akamai logs
  - For Splunk users: How to enable event receiving, add a source type, and add field extraction
  - For Wazuh users: How to enable Syslog receiving, add a custom decoder, add a custom rule
  - For SysLog users: How to enable Syslog receiving
3. How to install, configure, and run the LDS Connector script

The LDS Connector works with any Log Delivery Service log format. However, it's only been tested with Edge DNS logs.


How It Works
============

The LDS Connector is configured using a YAML file. In this file you'll configure...
- Your NetStorage credentials
- Where to download logs from in NetStorage
- Where you want to deliver logs to. This is either Splunk or Syslog.

The LDS Connector performs the following steps when launched...
1. Parse the YAML configuration file. Fail if there's any invalid settings
2. Fetch the list of available log files from NetStorage.
3. Determine the next log file to process chronologically. Download and uncompress it.
4. For each log line in the log file, send it to Splunk or Syslog
5. Repeat

The LDS Connector will eventually process all available log files. After this, it'll periodically check NetStorage
for new log files to process.

The LDS Connector stores which log files have already been processed for each LDS object. If the LDS Connector
is restarted, then it can resume where it left off. This file is stored in the `resume_data.picke` in the log
download directory. If you need to reset LDS, then delete this file.

The LDS Connector will continuously retry if communication to Splunk / Syslog fails. 


Getting Started
===============

Prerequisites
-------------

See the [Akamai documentation](docs/akamai/README.md) to configure NetStorage and the Log Delivery Service. 

If you want to deliver logs to Splunk, then see the [Splunk documentation](docs/splunk/README.md).

If you want to deliver logs via SysLog, then see the [SysLog documentation](docs/syslog/README.md).

If you want to deliver logs to Wazuh, then see the [Wazuh documentation](docs/wazuh/README.md).


Configuration
-------------

The script is configured using a YAML file passed as a command line argument. 

Use `config_template.yaml` as a template. It includes a comment describing each field. Optional fields can be 
deleted if they're not needed. 

The documents linked in the above Prerequisites section detail how to set each of these fields. They include 
annotated screenshots. Please consult this documentation.


Installation
------------

The LDS Connector requires Python >= 3.6, PIP, and virtualenv installed. Install these from your package manager
or a python version management tool like `pyenv`.

I've tested this script on both macOS and Ubuntu. 

First, create a virtual environment and activate it. 
```sh
lds-connector % python3 -m venv env
lds-connector % source env/bin/activate
```

Next, ensure PIP is up-to-date and install the required packages. 
```sh
lds-connector % python3 -m pip install --upgrade pip
lds-connector % python3 -m pip install -r requirements.txt
```

Great job! The script is ready.


Running
-------

Run the script with the following command. Use the `-h` flag for the help message. 

``` sh
lds-connector % python3 lds_connector.py --config config.yaml
```


Monitoring
----------

The LDS connector script emits logs. We're working on improving this and are considering integration with monitoring 
services like Grafana


Example Use Case
=================

An example use case of this script is to improve visibility into NXDOMAIN spikes. 

The script periodically delivers Edge DNS log events into Splunk or Wazuh

The following Splunk dashboard shows some simple DNS traffic visualizations
- A chart of NXDOMAIN count over time
- A geo map showing where DNS queries originated from and what proportion were NXDOMAINs. Splunk converts the source IP 
  in the Edge DNS log lines into geographic data.

![](EXAMPLES/splunk_example1.jpg)

Notice the NXDOMAIN spike. We use Splunk Search to narrow in on the spike and investigate. The traffic mostly came from 
Portland and Yekaterinburg. Most from Portland were not NXDOMAINs. Most from Yekaterinburg were NXDOMAINs.

![](EXAMPLES/splunk_example2.jpg)

We can produce similar visualizations in Wazuh as well.

![](EXAMPLES/wazuh_example.jpg)

A more detailed example is included at [EXAMPLES/](./EXAMPLES/dns_logs/README.md)


Developer Notes
===============

You can run the unit tests using the following command
```sh
lds-connector % python3 -m unittest discover -vb
... Test output
----------------------------------------------------------------------
Ran 21 tests in 0.018s

OK
```


You can run the coverage analysis using the following commands
```sh
lds-connector % coverage run -m unittest discover
lds-connector % coverage report
lds-connector % coverage html
```

Authors
=======

This project is maintained by Akamai's Security Technology Group.

The original author is Cam Mackintosh. Her email is `cmackint@akamai.com`


License
=======

Copyright 2023 Akamai Technologies, Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an 
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the 
specific language governing permissions and limitations under the License.

