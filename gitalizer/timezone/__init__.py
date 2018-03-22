"""Helper for time zone handling."""
from pytz import country_timezones
from geopy.geocoders import Nominatim


timezone_country = {}
for countrycode in country_timezones:
    timezones = country_timezones[countrycode]
    for timezone in timezones:
        timezone_country[timezone] = countrycode


def map_timezone_to_state(name):
    """Map a timezone to a state."""
    components = name.split('/')

    # If there are three components, the middle component is the state
    if len(components) == 3:
        return components[1]

    try:
        search_string = components[1].replace('_', ' ')
        geolocator = Nominatim()
        location = geolocator.geocode(search_string)
        location = geolocator.reverse([location.raw['lat'], location.raw['lon']])

        state = location.raw['address']['state']
        return state

    except BaseException:
        return None


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
