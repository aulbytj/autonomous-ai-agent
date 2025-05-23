import json
from datetime import datetime
from typing import Any

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def dumps(obj: Any) -> str:
    """Serialize obj to a JSON formatted string with datetime support."""
    return json.dumps(obj, cls=DateTimeEncoder)

def loads(s: str) -> Any:
    """Deserialize s to a Python object."""
    return json.loads(s)
