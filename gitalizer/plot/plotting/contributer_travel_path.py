"""Plot the changes as a box plot for a user."""
from gitalizer.models import Commit


def contributer_travel_path(commits: Commit, path, title):
    """Print the travel history of a contributer."""
    last_timezone = None
    changed_day = None
    current_day = None

    ignore = False
    changed = False
    for commit in commits:
        commit_time = commit.commit_time
        if not commit_time.tzinfo:
            continue

        # Initial variable population for the first two days
        # This block is unimportant after the first few iterations
        if not current_day:
            current_day = commit_time
            continue
        elif not last_timezone:
            if commit_time.date() != current_day.date():
                last_timezone = current_day
                current_day = commit_time
            continue

        # Check if we got a new day and the timezone differs from the last day
        if commit_time.date() != current_day.date():
            # It is changed and the change should not be ignored
            # (Changes are ignored if multiple timezones are present at the same day)
            if changed and not ignore:
                print(f'Change at {changed_day.date()} detected:')
                print(f'    New timezone {get_timezone(changed_day)} detected.\n')
                last_timezone = commit_time

            current_day = commit_time
            ignore = False
            changed = False

            continue

        offset = get_timezone(commit_time)
        if not changed and offset != get_timezone(last_timezone):
            changed_day = commit_time
            changed = True

        # We got a change at the same day. Ignore it
        elif not ignore and offset == get_timezone(last_timezone):
            ignore = True

    return


def get_timezone(time):
    """Handle to get timezone utcoffset."""
    return time.tzinfo.utcoffset(time)
