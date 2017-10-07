"""Data collection from Github."""

import socket
from github import Repository as Github_Repository
from datetime import datetime, timedelta


from gitalizer.extensions import db
from gitalizer.models.email import Email
from gitalizer.models.commit import Commit
from gitalizer.models.contributer import Contributer
from gitalizer.models.repository import Repository
from gitalizer.aggregators.github.contributer import get_contributer


def get_commits(github_repo: Github_Repository,
                repository: Repository,
                contributer: Contributer,
                inaccurate_commit_count=0):
    """Get all commits from this repository.

    The user is extracted as well as additions, deletions and timestamp
    """
    # Try to get all commits at once if there are less than 1000 commits
    # If this fails, we need to chunk the data into multiple requests
    if inaccurate_commit_count <= 1000:
        try:
            commits = github_repo.get_commits()
            return save_commits(commits, repository, contributer)
        except socket.timeout:
            pass

    commit_count = 0
    # We got too many commits or the request failed.
    # Thereby we try to get the commits in 90 day intervals
    # If this fails again, we continuously subtract one day until it works.
    # The loop stops if the `until` parameter is before repository creation.
    interval = timedelta(days=90)
    print(f'Using {interval.days} day Interval.')
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
            commit_count += save_commits(commits, repository, contributer, commit_count)
        except socket.timeout:
            failed = True
            pass
    return commit_count


def save_commits(commits,
                 repository: Repository,
                 contributer: Contributer,
                 commit_count=0):
    """Save the queried commits to the database."""
    for github_commit in commits:

        # Check if the commit already exists
        commit = db.session.query(Commit) \
            .filter(Commit.sha == github_commit.sha) \
            .filter(Commit.repository_url == repository.clone_url) \
            .one_or_none()

        if not commit:
            # Save the email of this commit
            author = github_commit.commit.author
            email = db.session.query(Email).get(author.email)
            # If there is no such email we create a new email and a new contributer,
            # if the author is known and doesn't exist yet.
            if not email:
                email = Email(author.email)
                if github_commit.author:
                    contributer = get_contributer(github_commit.author.login, repository)
                    email.contributer = contributer
            else:
                # If we know this email we just add the repository to
                # the contributers list in case the user isn't linked any longer.
                if email.contributer:
                    email.contributer.repositories.append(repository)
                # We don't know the contributer for this email yet.
                # If we know the author of this commit, we add it to this email address.
                elif github_commit.author:
                    contributer = get_contributer(github_commit.author.login, repository)
                    email.contributer = contributer

            db.session.add(email)
            db.session.commit()

            # Create a new commit and extract all valuable information
            commit = Commit(github_commit.sha, repository, contributer)
            commit.time = author.date
            commit.author_email = author.email
            stats = github_commit.stats
            if stats:
                commit.additions = stats.additions
                commit.deletions = stats.deletions
            db.session.add(commit)

        # Commit session every 20 commits to avoid loss of all data on crash.
        commit_count += 1
        if commit_count % 20 == 0:
            db.session.commit()
        # Print a status every 200 commits to indicate progress.
        if commit_count % 200 == 0:
            print(f"{commit_count} commits scanned.")

    db.session.commit()
    return commit_count
