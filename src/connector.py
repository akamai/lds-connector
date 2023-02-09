from config import Config
from log_manager import LogManager

class Connector:
    def __init__(self, config: Config):
        self.config = config
        self.log_manager = LogManager(self.config)
    
    def run(self):
        log_filename = self.log_manager.get_next_log()
