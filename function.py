#functions

import datetime
import datetime
import pytz


def get_time(country):
    try:
        if not country:
            current_time = datetime.datetime.now()
            return current_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            timezone = pytz.timezone(country)
            current_time = datetime.datetime.now(timezone)
            return current_time.strftime("%Y-%m-%d %H:%M:%S")
    except pytz.UnknownTimeZoneError:
        return "Invalid country or timezone not found."
