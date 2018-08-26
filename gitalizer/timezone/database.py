"""Create a timezone database to reverse map timestamps to a timezone."""
import pendulum

from pendulum import timezones
from pendulum.tz.loader import Loader

from gitalizer.models import TimezoneInterval


def create_timezone_database(session):
    """Create new utc offset history for all timezones."""
    timezone_intervals = []
    for name in timezones:
        timezone = create_timezone(name)
        timezone_intervals += timezone

    for interval in timezone_intervals:
        new = TimezoneInterval(
            interval['name'],
            interval['utc-offset'],
            interval['start'],
            interval['end'],
        )
        session.add(new)

    session.commit()


def create_timezone(name: str):
    """Create a new timezone timeline."""
    test = Loader.load(name)

    transitions = test[0]

    intervals = []
    current_interval = None
    for transition in transitions:
        if not current_interval:
            current_interval = {
                'name': name,
                'utc-offset': transition.time - transition.utc_time,
                'start': transition.utc_time,
            }
            continue

        current_interval['end'] = transition.utc_time
        intervals.append(current_interval)

        current_interval = {
            'name': name,
            'utc-offset': transition.time - transition.utc_time,
            'start': transition.utc_time,
        }

    current_interval['end'] = pendulum.utcnow()

    return intervals
