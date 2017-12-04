"""Result callbacks."""
from datetime import datetime

from gitalizer.aggregator.parallel import new_session
from gitalizer.models import Contributer


def user_scanned(result):
    """Check if a user is finished."""
    if 'user_login' in result:
        session = new_session()
        contributer = session.query(Contributer).get(result['user_login'])
        if contributer:
            contributer.full_scan = datetime.utcnow()
            session.add(contributer)
            session.commit()
        session.close()
