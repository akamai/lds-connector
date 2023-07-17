import logging
from dataclasses import dataclass
from datetime import datetime
import socket
import ssl

@dataclass
class SysLogRecord:
    severity: int
    facility: int
    time: datetime
    hostname: str
    app_name: str
    process_id: str | None          # Not yet supported
    message_id: str | None          # Not yet supported
    structured_data: str | None     # Not yet supported
    message: str

class SysLogger:
    # Severity codes
    SEV_EMERG     = 0       #  System is unusable
    SEV_ALERT     = 1       #  Action must be taken immediately
    SEV_CRIT      = 2       #  Critical conditions
    SEV_ERR       = 3       #  Error conditions
    SEV_WARNING   = 4       #  Warning conditions
    SEV_NOTICE    = 5       #  Normal but significant condition
    SEV_INFO      = 6       #  Informational
    SEV_DEBUG     = 7       #  Debug-level messages

    # Facility codes
    FAC_KERN      = 0       #  Kernel messages
    FAC_USER      = 1       #  Random user-level messages
    FAC_MAIL      = 2       #  Mail system
    FAC_DAEMON    = 3       #  System daemons
    FAC_AUTH      = 4       #  Security / authorization messages
    FAC_SYSLOG    = 5       #  Messages generated internally by syslogd
    FAC_LPR       = 6       #  Line printer subsystem
    FAC_NEWS      = 7       #  Network news subsystem
    FAC_UUCP      = 8       #  UUCP subsystem
    FAC_CRON      = 9       #  Clock daemon
    FAC_AUTHPRIV  = 10      #  Security/authorization messages (private)
    FAC_FTP       = 11      #  FTP daemon
    FAC_NTP       = 12      #  NTP subsystem
    FAC_SECURITY  = 13      #  Log audit
    FAC_CONSOLE   = 14      #  Log alert
    FAC_SOLCRON   = 15      #  Scheduling daemon (Solaris)

    # Transport types
    PROTOCOL_UDP       = 0
    PROTOCOL_TCP       = 1
    PROTOCOL_TCP_TLS   = 2

    # Syslog formats
    SYSLOG_RFC3164 = 0
    SYSLOG_RFC5424 = 1

    # Delimiting methods
    DELIM_NONE = 0
    DELIM_LF = 1
    DELIM_CRLF = 2
    DELIM_NULL = 3
    DELIM_OCTET = 4

    _SYSLOG_RFC3164_TIME_FORMAT = '%b %d %H:%M:%S'
    _SYSLOG_RFC5424_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

    def __init__(
            self,
            protocol: int,
            address: tuple[str, int],
            syslog_flavor: int,
            facility: int,
            delimiter_method: int,
            from_host: str | None = None,
            tls_ca_file: str | None = None,
            tls_check_hostname: bool = True
    ):
        self.protocol = protocol
        self.address = address
        self.syslog_flavor = syslog_flavor
        self.facility = facility
        self.from_address = from_host
        self.delimiter_method = delimiter_method
        self.tls_check_hostname = tls_check_hostname

        self.socket = None

        self.ssl_context = None
        if self.protocol == SysLogger.PROTOCOL_TCP_TLS:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            self.ssl_context.load_verify_locations(tls_ca_file)
            self.ssl_context.verify_mode = ssl.CERT_REQUIRED
            self.ssl_context.check_hostname = tls_check_hostname


    def __del__(self):
        if self.socket is not None:
            if self.protocol == SysLogger.PROTOCOL_TCP_TLS:
                self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()


    def log_info(self, app_name: str, time: datetime, message: str):
        try:
            record = SysLogRecord(
                severity = SysLogger.SEV_INFO,
                facility = self.facility,
                time = time,
                hostname = self.from_address if self.from_address else socket.gethostname(),
                app_name = app_name,
                process_id = None,
                message_id = None,
                structured_data = None,
                message = message
            )

            event = None
            if self.syslog_flavor == SysLogger.SYSLOG_RFC3164:
                event = self._format_rfc3164(record)
            elif self.syslog_flavor == SysLogger.SYSLOG_RFC5424:
                event = self._format_rfc5424(record)
            else:
                logging.error('Invalid syslog flavor: %s', self.syslog_flavor)
                return

            if self.delimiter_method == SysLogger.DELIM_LF:
                event += '\n'
            elif self.delimiter_method == SysLogger.DELIM_CRLF:
                event += '\r\n'
            elif self.delimiter_method == SysLogger.DELIM_NULL:
                event += '\x00'
            elif self.delimiter_method == SysLogger.DELIM_OCTET:
                event = f'{len(event)} {event}'

            event_bytes = event.encode('utf-8')

            self._send(event_bytes)

        except Exception as exception:
            logging.error('Failed sending syslog message: %s', exception)


    def _send(self, event: bytes):
        if not self.socket:
            self._create_socket()

        assert self.socket is not None, 'Unexpected state. Socket was not created'
        if self.protocol == SysLogger.PROTOCOL_UDP:
            self.socket.sendto(event, self.address)
        elif self.protocol == SysLogger.PROTOCOL_TCP or SysLogger.PROTOCOL_TCP_TLS:
            self.socket.sendall(event)


    def _create_socket(self):
        socktype = socket.SOCK_DGRAM
        if self.protocol == SysLogger.PROTOCOL_UDP:
            socktype = socket.SOCK_DGRAM
        elif self.protocol == SysLogger.PROTOCOL_TCP or self.protocol == SysLogger.PROTOCOL_TCP_TLS:
            socktype = socket.SOCK_STREAM

        host, port = self.address
        results = socket.getaddrinfo(host, port, 0, socktype)
        if not results:
            raise OSError("getaddrinfo returned an empty list")

        # Open a socket using each result until successful
        err = None
        sock = None
        for result in results:
            address_fam, socktype, proto, _, sockaddr = result
            try:
                sock = socket.socket(address_fam, socktype, proto)
                if socktype == socket.SOCK_STREAM:
                    sock.connect(sockaddr)
                break
            except OSError as os_error:
                err = os_error
                if sock is not None:
                    sock.close()

        # None of sockets were successful
        if err is not None:
            raise err
        assert sock is not None, 'Unexpected state. Socket was not created'

        if self.protocol == SysLogger.PROTOCOL_TCP_TLS:
            assert self.ssl_context is not None, 'Unexpected state. SSL context was not created'
            if self.tls_check_hostname:
                sock = self.ssl_context.wrap_socket(sock, server_hostname=host)
            else:
                sock = self.ssl_context.wrap_socket(sock)

        self.socket = sock


    def _format_rfc3164(self, record: SysLogRecord) -> str:
        pri_str = self._encode_prio(record.severity)
        timestamp_str = record.time.strftime(SysLogger._SYSLOG_RFC3164_TIME_FORMAT)
        return f'<{pri_str}>{timestamp_str} {record.hostname} {record.app_name}: {record.message}'
    

    def _format_rfc5424(self, record: SysLogRecord) -> str:
        pri_str = self._encode_prio(record.severity)
        timestamp_str = record.time.strftime(SysLogger._SYSLOG_RFC5424_TIME_FORMAT)
        return f'<{pri_str}>1 {timestamp_str} {record.hostname} {record.app_name} - - - {record.message}'


    def _encode_prio(self, severity: int) -> int:
        return (self.facility << 3) | severity
