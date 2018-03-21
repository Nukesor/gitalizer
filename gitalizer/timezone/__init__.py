"""Helper for time zone handling."""
from pytz import country_timezones


timezone_country = {}
for countrycode in country_timezones:
    timezones = country_timezones[countrycode]
    for timezone in timezones:
        timezone_country[timezone] = countrycode


def map_timezone_to_utc(name):
    """Convert a timezone like GMT or MET to an utc offset timezone name."""
    # Check if we have GMT
    if 'GMT' in name:
        # If we have GMT, get the offset, invert it and create proper utc name
        offset = name.split('GMT')[1]
        if '-' in offset:
            offset.replace('-', '+')
        elif '+' in offset:
            offset.replace('+', '-')
        else:
            offset = 0
        return offset

    # No compatible zone found. Go back to default name
    else:
        return name
