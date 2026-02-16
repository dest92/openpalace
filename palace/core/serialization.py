"""Fast JSON serialization using orjson when available."""

from typing import Any, Dict
import json

# Try to import orjson for 10x faster serialization
try:
    import orjson

    HAS_ORJSON = True

    def dumps(obj: Any, indent: bool = False) -> str:
        """
        Serialize object to JSON string using orjson.

        Args:
            obj: Object to serialize
            indent: Whether to format with indentation

        Returns:
            JSON string
        """
        if indent:
            # orjson doesn't support indent, use standard json for pretty printing
            return json.dumps(obj, indent=2)
        else:
            # orjson returns bytes, decode to str
            return orjson.dumps(obj).decode('utf-8')

    def loads(s: str) -> Any:
        """
        Deserialize JSON string to object using orjson.

        Args:
            s: JSON string

        Returns:
            Deserialized object
        """
        return orjson.loads(s)

except ImportError:
    # Fallback to standard json
    HAS_ORJSON = False

    def dumps(obj: Any, indent: bool = False) -> str:
        """
        Serialize object to JSON string using standard json.

        Args:
            obj: Object to serialize
            indent: Whether to format with indentation

        Returns:
            JSON string
        """
        if indent:
            return json.dumps(obj, indent=2)
        else:
            return json.dumps(obj)

    def loads(s: str) -> Any:
        """
        Deserialize JSON string to object using standard json.

        Args:
            s: JSON string

        Returns:
            Deserialized object
        """
        return json.loads(s)


def get_json_backend() -> str:
    """Get the name of the JSON backend being used."""
    return "orjson" if HAS_ORJSON else "json"
