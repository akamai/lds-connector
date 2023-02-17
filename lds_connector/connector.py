import logging
import os

from .config import Config
from .log_manager import LogManager, LogFile
from .splunk import Splunk


class Connector:
    def __init__(self, config: Config):
        self.config = config
        self.log_manager = LogManager(self.config)
        self.splunk = Splunk(self.config)

    def run(self):
        log_file = self.log_manager.get_next_log()

        if log_file is None:
            logging.info('No log files to process')
            return

        while log_file is not None:
            self._process_log_file(log_file)
            log_file = self.log_manager.get_next_log()

    def _process_log_file(self, log_file: LogFile):
        logging.info('Processing log file %s', log_file.local_path_txt)
        try:
            with open(log_file.local_path_txt, 'r', encoding='utf-8') as file:
                log_line = file.readline()
                line_number = 0
                while log_line:
                    line_number += 1
                    if line_number > log_file.last_processed_line:
                        # Only handle lines that haven't been processed already
                        self.splunk.add(log_line)
                        if self.splunk.publish():
                            log_file.last_processed_line = line_number

                    log_line = file.readline()

                # Publish remaining log lines
                if self.splunk.publish(force=True):
                    log_file.last_processed_line = line_number
                log_file.processed = True

            os.remove(log_file.local_path_txt)
        except Exception as exception:
            logging.error('An unexpected error has occurred processing log file. [%s]. Ignoring and moving on', exception)
        finally:
            if log_file.last_processed_line != -1:
                # Only update resume save file if some lines were processed
                # If multiple log files fail (say Splunk is down), we want to resume at the first failing log file
                self.log_manager.save_resume_data()
            self.splunk.clear()
            logging.info('Processed log file %s. Finished processing: %d. Last line processed: %d', \
                log_file.local_path_txt, log_file.processed, log_file.last_processed_line)
