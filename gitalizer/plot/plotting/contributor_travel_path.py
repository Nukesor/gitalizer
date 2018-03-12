"""Plot the changes as a box plot for a user."""
from gitalizer.models import Commit


def contributor_travel_path(commits: Commit, path, title):
    """Print the travel history of a contributor."""
    current_day = None
    current_timezone = None
    last_timezone = None

    ignore = False
    changed = False
    for commit in commits:
        commit_time = commit.commit_time
        commit_timezone = commit.commit_time_offset
        if commit_timezone is None:
            continue

        # Initial variable population for the first two days
        # This block is unimportant after the first few iterations
        if current_day is None:
            current_day = commit_time.date()
            current_timezone = commit_timezone
            continue
        elif last_timezone is None:
            if commit_time.date() != current_day:
                last_timezone = current_timezone
                current_day = commit_time.date()
                current_timezone = commit_timezone
            continue

        # Check if we got a new day and the timezone differs from the last day
        if commit_time.date() != current_day:
            # It is changed and the change should not be ignored
            # (Changes are ignored if multiple timezones are present at the same day)
            if changed and not ignore:
                print(f'Change at {current_day} detected:')
                print(f'    New timezone {current_timezone} detected.\n')
                last_timezone = current_timezone

            current_day = commit_time.date()
            current_timezone = commit_timezone
            ignore = False
            changed = False

        if not changed and commit_timezone != last_timezone:
            changed = True
        # We got a change and an original at the same day. Ignore it
        elif not ignore and commit_timezone == last_timezone:
            ignore = True

    return


def get_timezone(time):
    """Handle to get timezone utcoffset."""
    return time.tzinfo.utcoffset(time)
