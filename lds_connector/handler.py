from abc import ABCMeta, abstractmethod

from .dns_record import DnsRecord

class Handler(metaclass = ABCMeta):

    @abstractmethod
    def add_log_line(self, log_line: str) -> None:
        pass

    @abstractmethod
    def add_dns_record(self, dns_record: DnsRecord) -> None:
        pass

    @abstractmethod
    def publish_log_lines(self, force=False) -> bool:
        return False

    @abstractmethod
    def publish_dns_records(self, force=False) -> bool:
        return False

    @abstractmethod
    def clear(self):
        pass
