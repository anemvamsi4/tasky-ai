from datetime import datetime
from typing import Dict, Any

def get_datetime_now() -> Dict[str, Any]:
    """
    Returns the current date and time in ISO 8601 format and weekday.

    Returns:
        Dict[str, Any]: Dictionary containing the current date and time.
    """

    datetime_now = datetime.now().isoformat()
    weekday = datetime.now().strftime("%A")
    return {"current_datetime": datetime_now, "weekday": weekday}