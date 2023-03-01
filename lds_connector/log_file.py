from dataclasses import dataclass


@dataclass
class LogNameProps:
    customer_id: str
    cp_code: int
    format: str
    sorted: bool
    start_time: float
    part: int
    encoding: str


@dataclass
class LogFile:
    ns_path_gz: str
    filename_gz: str
    size: int
    md5: str
    name_props: LogNameProps
    local_path_gz: str
    local_path_txt: str
    last_processed_line: int
    processed: bool
