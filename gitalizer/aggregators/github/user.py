"""Data collection from Github."""

import socket
from github import NamedUser
from github import Repository as Github_Repository
from datetime import datetime, timedelta

from flask import current_app

from gitalizer.extensions import db, github
from gitalizer.models.contributer import Contributer
from gitalizer.models.repository import Repository
from gitalizer.models.commit import Commit
from gitalizer.aggregators.github.helper import get_commit_count


def get_friends(name: str):
    """Get all relevant Information about all friends of a specific user.."""
    user = github.github.get_user(name)
    followers = user.get_followers()
    following = user.get_following()

    # Add all following and followed people into list
    # Then deduplicate the list as we have to hold the API call count as low as possible.
    user_list = [user]
    for follower in followers:
        user_list.append(follower)
    for followed in following:
        exists = filter(lambda x: x.login == followed.login, user_list)
        if len(list(exists)) == 0:
            user_list.append(followed)

    for user in user_list:
        print(f'Start scanning user {user.login}:')
        get_user(user)


def get_user_by_name(user: str):
    """Get a user by his login name."""
    user = github.github.get_user(user)
    get_user(user)


def get_user(user: NamedUser):
    """Get all relevant Information for a single user."""
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
        register_repository(star)

    for repo in repos:
        register_repository(repo)


def register_repository(github_repo: Github_Repository):
    """Get all information from a single repository."""
    repository = db.session.query(Repository).get(github_repo.clone_url)
    if not repository:
        repository = Repository(github_repo.clone_url)
        db.session.add(repository)
        db.session.commit()

    # Skip repositories that are too big.
    contributors = github_repo.get_contributors()
    count = get_commit_count(contributors)

    current_time = datetime.now().strftime('%H:%M')
    limit = current_app.config['GITHUB_SKIP']
    if count >= limit:
        print(f'\n{current_time}: Skip {repository.clone_url}. It has more than {limit} commits.')
        return
    else:
        # Repository isn't too big, start to scan
        print(f'\n{current_time}: Started scan {repository.clone_url} with {count} commits.')

    # Register all contributors
    for user in contributors:
        contributer = db.session.query(Contributer).get(user.login)
        if not contributer:
            contributer = Contributer(user.login)
        contributer.repositories.append(repository)
        db.session.add(contributer)
    db.session.commit()

    commit_count = get_commits(github_repo, repository, contributer)

    time = datetime.fromtimestamp(github.github.rate_limiting_resettime)
    time = time.strftime("%H:%M")
    current_time = datetime.now().strftime('%H:%M')
    print(f'{current_time}: Scanned {repository.clone_url} with {commit_count} commits')
    print(f'{github.github.rate_limiting} of 5000 remaining. Reset at {time}')


def get_commits(github_repo: Github_Repository,
                repository: Repository,
                contributer: Contributer):
    """Get all commits from this repository.

    The user is extracted as well as additions, deletions and timestamp
    """
    # Try to get all commits at once.
    # If this fails, we need to chunk the data into multiple requests
    commit_count = 0
    try:
        commits = github_repo.get_commits()
        commit_count = save_commits(commits, repository, contributer)
    except socket.timeout:
        # We try to get the commits in 30 day intervals
        # If this fails again, we continuously subtract one day until it works.
        # The loop stops if the `until` parameter is before repository creation.
        interval = timedelta(days=30)
        print("Using 30 day Interval.")
        until = datetime.now()
        since = until - interval
        failed = False
        while until > github_repo.created_at and interval.days > 2:
            if failed:
                interval -= timedelta(days=1)
                print(f"Using {interval.days} day interval.")
                since = until - interval
                failed = False
            else:
                since -= interval
                until -= interval
            try:
                commits = github_repo.get_commits(since=since, until=until)
                commit_count += save_commits(commits, repository, contributer)
            except socket.timeout:
                failed = True
                pass
        pass
    return commit_count


def save_commits(commits,
                 repository: Repository,
                 contributer: Contributer):
    """Save the queried commits to the database."""
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

        # Commit session every 20 commits to avoid loss of all data on crash.
        commit_count += 1
        if commit_count % 20 == 0:
            db.session.commit()
    db.session.commit()
    return commit_count
