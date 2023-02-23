import json
import dataclasses

class CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return json.JSONEncoder.default(self, o)
