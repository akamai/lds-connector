import logging

from config import Config
from log_manager import LogManager
from splunk import Splunk

class Connector:
    def __init__(self, config: Config):
        self.config = config
        self.log_manager = LogManager(self.config)
        self.splunk = Splunk(self.config)
    
    def run(self):
        log_filename = self.log_manager.get_next_log()

        if not log_filename:
            logging.info('No log files to process')
            return

        while not log_filename:
            self._process_log_file(log_filename)
            log_filename = self.log_manager.get_next_log()

    def _process_log_file(self, filename):
        # TODO: Track the last successfully processed log line
        with open(filename, 'r') as log_file:
            log_line = log_file.readline()
            while log_line:
                self.splunk.handle_logline(log_line)
                log_line = log_file.readline()