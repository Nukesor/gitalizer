"""Data collection from Github."""

from github import Github
from github import Repository as Github_Repository
from datetime import datetime

from flask import current_app

from gitalizer.extensions import db
from gitalizer.models.contributer import Contributer
from gitalizer.models.repository import Repository
from gitalizer.models.commit import Commit
from gitalizer.aggregators.github.helper import get_commit_count


def get_friends(name: str):
    """Get all relevant Information about all friends of a specific user.."""
    github = Github(current_app.config['GITHUB_USER'],
                    current_app.config['GITHUB_PASSWORD'])

    user = github.get_user(name)
    followers = user.get_followers()
    following = user.get_following()


def get_user(name: str):
    """Get all relevant Information for a single user."""
    github = Github(current_app.config['GITHUB_USER'],
                    current_app.config['GITHUB_PASSWORD'])

    user = github.get_user(name)
    repos = user.get_repos()
    starred = user.get_starred()

    contributer = db.session.query(Contributer).get(user.login)
    if not contributer:
        contributer = Contributer(user.login)
        db.session.add(contributer)
        db.session.commit()

    for star in starred:
        # Check if user contributed to this repo.
        contributed = list(filter(lambda x: x.login == user.login, star.get_contributors()))
        if len(contributed) == 0:
            break
        register_repository(star, github)

    for repo in repos:
        register_repository(repo, github)


def register_repository(github_repo: Github_Repository, github: Github):
    """Get all information from a single repository."""
    repository = db.session.query(Repository).get(github_repo.clone_url)
    if not repository:
        repository = Repository(github_repo.clone_url)
        db.session.add(repository)
        db.session.commit()

    # Skip repositories that are too big.
    contributors = github_repo.get_contributors()
    limit = current_app.config['GITHUB_SKIP']
    if get_commit_count(contributors) >= limit:
        current_time = datetime.now().strftime('%H:%M')
        print(f'\n{current_time}: Skip {repository.clone_url}. It has more than {limit} commits.')
        return

    # Repository isn't too big, start to scan
    current_time = datetime.now().strftime('%H:%M')
    print(f'\n{current_time}: Started to scan {repository.clone_url}')

    # Register all contributors
    for user in contributors:
        contributer = db.session.query(Contributer).get(user.login)
        if not contributer:
            contributer = Contributer(user.login)
        contributer.repositories.append(repository)
        db.session.add(contributer)
    db.session.commit()

    # Get all commits from this repository
    # The user is extracted as well as additions, deletions and timestamp
    commits = github_repo.get_commits()
    commit_count = 0
    for github_commit in commits:
        commit = db.session.query(Commit) \
            .filter(Commit.sha == github_commit.sha) \
            .filter(Commit.repository_url == repository.clone_url) \
            .one_or_none()
        if not commit:
            # Create a new commit and extract all valuable information
            commit = Commit(github_commit.sha, repository, contributer)
            commit.time = github_commit.commit.author.date
            commit.author_email = github_commit.commit.author.email
            commit.additions = github_commit.stats.additions
            commit.deletions = github_commit.stats.deletions
            db.session.add(commit)

        commit_count += 1
        if commit_count % 50 == 0:
            db.session.commit()
    db.session.commit()

    time = datetime.fromtimestamp(github.rate_limiting_resettime)
    time = time.strftime("%H:%M")
    current_time = datetime.now().strftime('%H:%M')
    print(f'{current_time}: Scanned {repository.clone_url} with {commit_count} commits')
    print(f'{github.rate_limiting} of 5000 remaining. Reset at {time}')
