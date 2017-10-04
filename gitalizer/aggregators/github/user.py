import sys
from github import Github

from flask import current_app
from flask.extensions import db
from flask.models.contributer import Contributer
from flask.models.repository import Repository


def get_user(name):
    github = Github(current_app.config['GITHUB_USER'],
                    current_app.config['GITHUB_PASSWORD'])

    user = github.get_user(name)
    repos = user.get_repos()

    contributer = db.session.query(Contributer).get(user.login)
    if not contributer:
        contributer = Contributer(user.login)
        db.session.add(contributer)
        db.session.commit()

    for starred in user.get_starred():
        repo = db.session.query(Repository).get(starred.clone_url)
        if not repository:
            repository = Repository(starred.clone_url)
        db.session.add(repo)
        db.session.commit()

        try:
            """Check if user contributed to this repo."""
            contributed = list(filter(lambda x: x.login == user.login, starred.get_contributors()))
            if len(contributed) > 0:
                    print(starred.clone_url)
        except KeyboardInterrupt:
            sys.exit(1)
        except:
            print(f'Error for repo {starred.clone_url}')
            pass

    print(github.rate_limiting)

    import pprint
    pprint.pprint(github)
