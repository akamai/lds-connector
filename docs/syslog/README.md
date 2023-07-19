# Introduction

This document details how to configure log delivery using Syslog

This document covers the following
- Syslog implementation specifics
- How to configure the LDS Connector to deliver via Syslog


# Syslog Implementation

There are two syslog specifications in use today. The LDS Connector supports both.
- The [RFC 3164](https://www.rfc-editor.org/rfc/rfc3164.html) SysLog specification
- The [RFC 5424](https://www.rfc-editor.org/rfc/rfc5424) SysLog specification

Syslog messages can be sent over various transport protocols. The LDS Connector supports UDP, TCP, and TCP/TLS.

The RFC 3164 specification only allows sending syslog messages using UDP. Each syslog message is sent in a single UDP 
datagram. However, many applications send syslog messages over TCP streams anyways. The individual syslog messages
in the transport stream are differentiated using a delimiter character, typically a newline. 

The RFC 5424 specification allows sending syslog messages over UDP, TCP, and TCP/TLS. Each transport protocol has it's
own RFC. The individual syslog messages are differentiated using octet stuffing. Each messages is proceeded with the 
message length. However, many applications don't support this and still use the legacy delimiter approach.

The LDS Connector supports both octet stuffing and delimiter characters.


# LDS Connector Configuration

We need to configure the LDS connector script to deliver logs using Syslog.

Use the [config_template.yaml](../../config_template.yaml) file for reference.

- `syslog.host`: 
    - Required: Yes
    - The syslog server's hostname or IP address
- `syslog.port`: 
    - Required: Yes
    - The syslog server's port
- `syslog.protocol`: 
    - Required: No, default value `RFC3164`
    - Allowed values: `RFC3164`, `RFC5424`
    - The syslog protocol to use
- `syslog.transport`:
    - Required: Yes
    - Allowed values: `UDP`, `TCP`, `TCP_TLS`
    - The transport protocol to send the syslog messages over
- `syslog.lds_app_name`
    - Required: Yes
    - The syslog header's app name field to use when delivering LDS log messages
- `syslog.edgedns_app_name`
    - Required: No
    - The syslog header's app name field to use when delivering Edge DNS records.
    - Only configure this if you're using the Record Set Delivery feature
- `syslog.delimiter_method`
    - Required: No, default value `LF`
    - Allowed values: 
        - `LF`: Append a `\n` to each syslog message
        - `CRLF`: Append a `\r\n` to each syslog message
        - `NONE`: Do nothing
        - `NULL`: Append a `\x00` to each syslog message
        - `OCTET`: Prepend the message length followed by space to each syslog message. See RFC 6587.
    - How to delimit syslog messages. 
- `syslog.from_host`
    - Required: No, default value is output of `socket.gethostname()`.
    - The syslog header's hostname field. If this isn't set, the system's hostname will be used.
- `syslog.tls.ca_file`
    - Required: Only if `syslog.transport` is `TCP_TLS`
    - The certificate authority certificate to use during the TLS handshake. This should be a PEM file.
- `syslog.tls.verify`
    - Required: No, default value `true`
    - Whether or not to verify the syslog server's hostname against it's certificate.

