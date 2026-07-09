from datetime import datetime, timedelta
import re


def parse_time(text: str):
    text = text.lower().strip()

    patterns = [
        (r"(\d+)\s*мин", "minutes"),
        (r"(\d+)\s*час", "hours"),
        (r"(\d+)\s*дн", "days"),
        (r"(\d+)\s*нед", "weeks")
    ]

    for pattern, unit in patterns:
        match = re.search(pattern, text)

        if match:
            value = int(match.group(1))

            if unit == "minutes":
                return datetime.now() + timedelta(
                    minutes=value
                )

            if unit == "hours":
                return datetime.now() + timedelta(
                    hours=value
                )

            if unit == "days":
                return datetime.now() + timedelta(
                    days=value
                )

            if unit == "weeks":
                return datetime.now() + timedelta(
                    weeks=value
                )

    return None