"""Data collection from Github."""

from github import Github
from github import Repository as Github_Repository
from datetime import datetime

from flask import current_app

from gitalizer.extensions import db
from gitalizer.models.contributer import Contributer, contributer_repositories
from gitalizer.models.repository import Repository
from gitalizer.models.commit import Commit


def get_user(name):
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

    # Register all contributers
    contributers = github_repo.get_contributors()
    for user in contributers:
        contributer = db.session.query(Contributer).get(user.login)
        if not contributer:
            contributer = Contributer(user.login)
            db.session.add(contributer)
        match = db.session.query(contributer_repositories) \
            .filter(contributer_repositories.c.contributer_login == contributer.login) \
            .filter(contributer_repositories.c.repository_url == repository.clone_url) \
            .one_or_none()
        if not match:
            contributer.repositories.append(repository)
            db.session.add(contributer)
    db.session.commit()

    commits = github_repo.get_commits()
    commit_count = 0
    for github_commit in commits:
        commit = db.session.query(Commit) \
            .filter(Commit.sha == github_commit.sha) \
            .filter(Commit.repository_url == repository.clone_url) \
            .one_or_none()
        if not commit:
            commit = Commit(github_commit.sha, repository, contributer)
            commit.additions = github_commit.stats.additions
            commit.deletions = github_commit.stats.deletions
            db.session.add(commit)
        commit_count += 1
    db.session.commit()

    time = datetime.fromtimestamp(github.rate_limiting_resettime)
    time = time.strftime("%H:%M")
    print(f'Scanned {repository.clone_url} with {commit_count} commits')
    print(f'{github.rate_limiting} of 5000 remaining. Reset at {time}')
