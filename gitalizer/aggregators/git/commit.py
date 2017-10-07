"""Data collection from Github."""

import socket
from pygit2 import Repository
from github import Repository as Github_Repository
from datetime import datetime, timedelta, timezone

from gitalizer.extensions import db
from gitalizer.models.email import Email
from gitalizer.models.commit import Commit
from gitalizer.models.contributer import Contributer
from gitalizer.models.repository import Repository as RepositoryModel
from gitalizer.aggregators.github.contributer import get_contributer


def scan_repository(
        git_repo: Repository,
        repository: RepositoryModel,
        github_repo: Github_Repository=None):
    """Get all commits from this repository.

    It extracts the user as well as additions, deletions and the timestamp.
    """
    # Walk through the repository and get all commits
    # that are reachable as parents from master commit
    master_commit = git_repo.lookup_reference("refs/heads/master").get_object()
    queue = [master_commit]
    # List of commit hashes to check if we already were at this point in the tree.
    commit_hashes = set()
    all_commits = []
    commit_stats = {}
    while len(queue) > 0:
        commit = queue.pop()
        # Break if we already visited this tree node
        if commit.hex in commit_hashes:
            continue
        commit_hashes.add(commit.hex)
        if len(commit.parents) == 1:
            diff = commit.tree.diff_to_tree(commit.parents[0].tree)
            commit_stats[commit.hex] = {
                'additions': diff.stats.insertions,
                'deletions': diff.stats.deletions,
            }
        queue.extend(commit.parents)
        all_commits.append(commit)

    # Set the time of the first commit as repository creation time.
    timestamp = all_commits[-1].author.time
    utc_offset = timezone(timedelta(minutes=all_commits[-1].author.offset))
    repository.created_at = datetime.fromtimestamp(timestamp, utc_offset)

    commit_count = 0
    checked_emails = set()
    # Walk through all commits and save the details in our database
    for git_commit in all_commits:
        # Check if the commit already exists
        commit = db.session.query(Commit) \
            .filter(Commit.sha == git_commit.hex) \
            .filter(Commit.repository == repository) \
            .one_or_none()

        if not commit:
            # Check every email only once to avoid github api calls
            if git_commit.author.email not in checked_emails:
                # Save the email of this commit
                email = db.session.query(Email).get(git_commit.author.email)
                # If there is no such email we create a new email and a new contributer,
                # if the author is known and doesn't exist yet.
                if not email:
                    email = Email(git_commit.author.email)

                # Try to get the contributer if we have a github repository
                if github_repo:
                    if email.contributer:
                        email.contributer.repositories.append(repository)

                    # We don't know the contributer for this email yet.
                    # If we know the github author of this commit, we add it to this email address.
                    else:
                        github_commit = github_repo.get_commit(git_commit.hex)
                        if github_commit.author:
                            contributer = get_contributer(github_commit.author.login, repository)
                            email.contributer = contributer

                db.session.add(email)
                db.session.commit()
                checked_emails.add(git_commit.author.email)

            # Create a new commit and extract all valuable information
            commit = Commit(git_commit.hex, repository, email)
            if git_commit.hex in commit_stats:
                commit.additions = commit_stats[git_commit.hex]['additions']
                commit.deletions = commit_stats[git_commit.hex]['deletions']
            # Get timestamp with utc offset
            timestamp = git_commit.author.time
            utc_offset = timezone(timedelta(minutes=git_commit.author.offset))
            commit.time = datetime.fromtimestamp(timestamp, utc_offset)

            db.session.add(commit)

        # Commit session every 20 commits to avoid loss of all data on crash.
        commit_count += 1
        if commit_count % 20 == 0:
            db.session.commit()
        # Print a status every 1000 commits to indicate progress.
        if commit_count % 1000 == 0:
            print(f"{commit_count} commits scanned.")

    db.session.commit()
    return commit_count
