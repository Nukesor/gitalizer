"""Helper for unified return messages between worker and manager."""
import traceback


def user_too_big_message(user_login: str):
    """Create an user_too_big_message."""
    return {
        'message': f'User {user_login} has too many repositories',
        'error': 'Too big',
    }


def user_up_to_date_message(user_login: str):
    """Create an user_up_to_date_message."""
    return {
        'message': f'User {user_login} is already up to date',
        'tasks': [],
    }


def error_message(message: str):
    """Return a error message with stacktrace."""
    return {
        'message': message,
        'error': traceback.format_exc(),
    }
