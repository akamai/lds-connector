Splunk - Akamai Log Delivery Service Connector 
==============================================

This script moves log data from Akamai's Log Delivery Service (LDS) into Splunk 
using an HTTP Event Collector (HEC).

This project has just started. The contents of this repository are incomplete and
not ready for customer use

Background
===========

Getting Started
==============

Prerequisites
-------------

Configure NetStorage 
- Create a Storage Group to contain the logs
- Create an Upload Account with an HTTP token

Configure Log Delivery Service 
- Create log delivery configuration into NetStorage

Configure Splunk 
- Enable HTTP Event Collector and create token

Configuration
-------------

Installation
------------

Create a virtual environment

Install modules in requirements.txt

Install Akamai's NetStorageKit For Python: https://github.com/akamai/NetStorageKit-Python

Running
-------

Monitoring
----------

Example Use Cases
=================

License
=======

References
==========

