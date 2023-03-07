
Overview
========

This document includes field extraction regular expressions for LDS formats.


DNS Format
==========

```
^(?P<cp_code>\d+)\s\-\s(?P<timestamp_epoch>\d+)\s(?P<timestamp_human>[^,]+),(?P<source_ip>[^,]+),(?P<source_port>[^,]+),(?P<domain>[^,]+),(?P<dns_class>\w+),(?P<record_type>[^,]+),(?P<edns0_flag>E?),(?P<edns0_size>\d*),(?P<dnssec_flag>D?),(?P<tcp_flag>T?),(?P<answer>.*)
```

Edge DNS Records
================

Not necessary, as Edge DNS records are sent as JSON. Splunk is able to extract the fields automatically.
