Akamai Log Delivery Service Connector 
=====================================

This script moves log data from Akamai's Log Delivery Service (LDS) into a Splunk instance. Support for additional
destinations may be added in the future.

This project is in early development. 


Background
===========


Akamai
------

Akamai's infrastructure continuously collects logs from thousands of edge servers around the globe. Akamai's 
Log Delivery Service (LDS) delivers these logs to customers.

LDS supports log delivery by email, FTP server, or NetStorage. It supports several log formats, compression, and 
encryption. The delivery period is configurable, with a minimum period of 1 day. 

NetStorage is Akamai's distributed cloud storage solution. It supports API access, automatic purge policies, 
and permissions.

A **storage group** is the basic unit in a NetStorage instance where content is stored. It contains one/more root
**upload directories**. Each upload directory has a **content provider (CP) code** used for billing/reporting. The
upload directory name is the CP code.

An **upload account** is an account used to access a specific upload directory in a storage group. It can be configured
with different **access methods**, such as HTTP API or FTP. An upload directory can be accessed by multiple upload 
accounts.


Splunk
------

Splunk is a data platform that allows you to search, analyze, and visualize data gathered from a variety of sources.

Splunk receives **raw data** from a variety of sources. It indexes this raw data, converting it to events and storing 
them under an index.

An **event** is a single unit of data in Splunk. Each event consists of a timestamp, the data, metadata (host, 
source type, source), and any fields extracted from the data.

A **source type** defines how raw data is converted into events. A **field extraction** can be defined for a source 
type, defining how fields are extracted from the data. The source type also contains configuration on how to parse the timestamp from the raw data.

Splunk Web is a web interface used for interacting with Splunk data. Users can submit 
**SPL (Search Processing Language)** commands to find, analyze, and visualize data. Users can create dashboards backed 
by these commands.

The **Splunk HTTP Event Collector (HEC)** is an HTTP endpoint hosted by the Splunk instance. Applications can send data
into Splunk by POST-ing it to this endpoint. It uses token-based authentication. A default source-type is associated 
with each token.


This Solution
-------------

This solution moves Akamai log data into a Splunk instance. So how does this work?

1. Log Delivery Service periodically delivers compressed log files to NetStorage.
2. NetStorage stores and automatically purges the log files. It provides an API for downloading log files
3. Splunk receives events using the HTTP Event Collector (HEC). A source type and field extraction is added for the log 
   files. Splunk parses the log lines into fields.
3. The Splunk-LDS connector script downloads log files from NetStorage, parses out events, and sends them to the Splunk 
   HEC

This solution will continuously move log data into Splunk without user intervention


Getting Started
===============


NetStorage Configuration
------------------------

We need to configure NetStorage to store the log files, implement an automatic purge policy, and provide API access
to the log files (for the script). 

First, we'll create a storage group. You can use an existing storage group. Otherwise, create a new storage group 
by following [these instructions](https://techdocs.akamai.com/netstorage/docs/create-a-storage-group).

**Take note** of the following
- `Storage Group Details -> Storage Group Name`: This is the human-readable storage group name. 
- `Storage Group Details -> HTTP Domain Name`: This is the host the API requests will be sent to.
- `Upload Directories -> Upload Directory`: This is the CP code that identifies the upload directory. A storage group 
  can have multiple upload directories.

Next, we'll configure an automatic purge policy for the upload directory.

1. Find the storage group under NetStorage -> Storage Groups. Click the "Edit" button.
2. Scroll down to the Automatic Purge section. Click the "+Automatic Purge" button.
3. Configure the automatic purge
    - `Upload Account`: The CP code noted above.
    - `Upload Directory`: The directory where the logs will be stored. Choose this name now and **take note**.
    - `Purge When The Directory Reaches`: The log directory's maximum size. 
    - `Only Purge Content Older Than (in days)`: The minimum number of days to keep files for. Files newer than this 
      time will not be purged, even if the directory file size exceeds the maximum

NetStorage only needs to store the log files long enough for the script to move them into Splunk. If there's an issue 
ingesting log data into Splunk, the unprocessed log files in NetStorage may be automatically purged before the issue is 
resolved. This means that log data is lost. 

You'll want to choose automatic purge settings to balance storage cost and your need for log retention. Some things to 
consider
- LDS delivers logs to NetStorage every X hours. How much log data is generated every X hours on average? Will my
  automatic purge settings accomodate this much data?
- Is it possible for log data generation rate to dramatically increase? For example during a DDoS attack?
- If Splunk goes down, do I need the log data delivered during this time? 

When developing this application, I used DNS logs for a relatively quiet zone. I set
`Only Purge Content Older Than` to 2 days and `Purge When The Directory` to 1MB.

Next, we'll configure an upload account to access the upload directory.
1. Go to NetStorage -> Upload Accounts. Click "+Add Upload Account".
2. Configure the upload account
  - `Id`: Choose this name. Take note
  - `Upload Directory Association`: The CP code noted above.
  - `Access Methods`: Add a `Netstorage HTTP CMS API` key. *Take note* of the key 
5. Done!

Great job! NetStorage is configured. It can take a few minutes for the upload account permissions to propagate.


Log Delivery Service Configuration
---------------------------------

We need to configure LDS to deliver logs into our NetStorage log directory.

Follow these steps.
1. Go to Common Services -> Log Delivery
2. Find the object you want to enable log delivery for. 
    - Use the "View by" selector and search feature.
3. Click Action -> Start a log delivery -> New
4. Configure logs
  - `Start date`: When you want the delivery to start
  - `Indefinite end date`: Leave this checked
  - `Log format`: Choose this
  - `Log identifier string`: Choose this. It's added to the log filenames
  - `Aggregation type`: Aggregate by log arrival time ever 1 hour
5. Configure the delivery
    - `Type`: Akamai NetStorage 4
    - `NetStorage`: The CP code noted above
    - `Directory`: Log directory noted above
    - `Encoding`: GZip
    - `Approximate message size`: 5MB
6. Enter contact details
7. Done!

Great job! LDS is configured. It can take a few hours for log delivery to start


Splunk Configuration
--------------------

We need to configure Splunk to define a source type and enable HEC

First, we'll create a source type. 
1. Go to Settings -> Data -> Source Types. Click "New Source Type" button 
2. Configure the source type
    - `Name`: Choose this name now and **take note**. (ex: lds_logs_dns)
    - `Event Breaks`: Every line
    - `Timestamp`: This depends on the [LDS log format](https://techdocs.akamai.com/log-delivery/docs/log-deliv-opt).
      I'll eventually add either settings/config files for each format to this repo.
3. Save

Next, we'll add an HTTP Event Collector token
1. Go to Settings -> Data -> Data Inputs -> HTTP Event Collector. Click "New Token" button
2. Choose a token name and **take note**
3. Set the source type to that noted above
4. Add indexes to the allowed list. Consider using a sandbox index
3. Done! **Take note** of the token value

Finally, we'll enable the HTTP Event Collector endpoint
1. Go to Settings -> Data -> Data Inputs -> HTTP Event Collector. Click "Global Settings " button
2. Enable all tokens
3. **Take note** of the port number
4. Enable SSL if you'd like. The Splunk certificate needs to be signed correctly. 
3. Done!

Great job! Splunk is configured.


Connector Script
======


Configuration
-------------

The script is configured using a YAML file. The `config_template.yaml` file shows what this should look like and
has a comment description for each field.

Most of these config values come from the above **take note**. See `img/yaml_examples` for where some of these values
come from in Akamai Control Center / Splunk.

Timestamp Configuration
-----------------------

The connector script converts each log line to an event and sends it to Splunk HEC. The event must contain the 
timetamp, otherwise Splunk uses the current time of ingestion for each event. 

How the connector script extracts the timestamp from the log lines is defined by two YAML configuration parameters.
This allows the connector script to support any LDS format without us having to maintain parsing logic for each. 
We'll try to provide values for each LDS format, so you don't need to think too much about this. See the
`timestamp_configs.md` document.
- The `connector.timestamp_parse` value specifies where the timestamp is in the log line. It's backed by the 
  [parse](https://pypi.org/project/parse/) package; you can read about the formatting specifics here. The format string 
  should contain a named field called `timestamp`.
- The `connector.timestamp_strptime` value specifies how the timestamp is formatted. It's backed by the 
  [datetime strptime()](https://docs.python.org/3/library/datetime.html) function.


Installation
------------

This package will eventually be ported to PyPI and installable via pip. 

Note that I've only tested this script on macOS so far.

First, create a virtual environment and activate it. 

```sh
splunk-lds-connector % python3 -m venv env
splunk-lds-connector % source env/bin/activate
```

Next, install the required packages.

```sh
splunk-lds-connector % python3 -m pip install -r requirements.txt
```

Optionally, run the unit tests. Make sure the last line says `OK` and not `FAILED`. Ignore the errors above the dashed 
line; these are intentionally omitted during unit tests.

```sh
splunk-lds-connector % python3 -m unittest discover -vb
... Test output
----------------------------------------------------------------------
Ran 21 tests in 0.018s

OK
```

Great job! The script is ready.


Running
-------

Run the script with the following command. Use the `-h` flag for the help message. 

``` sh
$ python3 lds_connector.py --config config.yaml
```


Monitoring
----------

The LDS connector script emits logs. We're working on improving this and are considering integration with monitoring 
services like Grafana


Script Features
===============

At the highest-level, the script moves log data from NetStorage into Splunk.

Let's dig into how it works a bit.

- The script is configured using a YAML file. This is passed as a command line argument. The script must be restarted
  to process any changes to the YAML file.
- The script process the log files chronologically. The log files are named using 
  [a standard format](https://techdocs.akamai.com/log-delivery/docs/file-names) that contains the time range. 
  The script fetches the listing of available log files and sorts them by the start time. 
- The script is able to resume processing where it left off. The script saves the current/last log file's metadata to 
  disk. When the script is first run, it checks the saved metadata and resumes where it left off.


Example Use Case
=================

An example use case of this script is to improve visibility into NXDOMAIN spikes. 

The script periodically delivers Edge DNS log events into Splunk. 

The following Splunk dashboard shows some simple DNS traffic visualizations
- A chart of NXDOMAIN count over time
- A geo map showing where DNS queries originated from and what proportion were NXDOMAINs. Splunk converts the source IP in 
  the Edge DNS log lines into geographic data.

![NXDOMAIN Dashboard Example](/img/splunk_nxdomain_dashboard.jpg?raw=true)

Notice the NXDOMAIN spike. We use Splunk Search to narrow in on the spike and investigate. The traffic mostly came from Portland and Yekaterinburg. Most from Portland were not NXDOMAINs. Most from Yekaterinburg were NXDOMAINs.

![NXDOMAIN Dashboard Example](/img/splunk_nxdomain_invest.jpg?raw=true)


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


References
==========

[NetStorage Overview](https://techdocs.akamai.com/netstorage/docs)

[NetStorage Key Terms](https://techdocs.akamai.com/netstorage/docs/key-concepts-and-terms)

[NetStorage Usage API](https://techdocs.akamai.com/netstorage-usage/reference/api)

[LDS Overview](https://techdocs.akamai.com/log-delivery/docs)

[LDS Log Formats](https://techdocs.akamai.com/log-delivery/docs/log-deliv-opt)

[LDS File Name Format](https://techdocs.akamai.com/log-delivery/docs/file-names)

[Splunk HEC Format](https://docs.splunk.com/Documentation/Splunk/9.0.3/Data/FormateventsforHTTPEventCollector)



