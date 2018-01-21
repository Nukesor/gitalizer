"""Data collection from Github."""
from collections import deque
from pygit2 import Repository, GitError
from sqlalchemy.orm import joinedload
from github import Repository as Github_Repository
from datetime import datetime, timedelta, timezone

from gitalizer.extensions import sentry
from gitalizer.models import (
    Email,
    Commit,
    Repository as RepositoryModel,
)


class CommitScanner():
    """Get features from all commits in a repository."""

    def __init__(self, git_repo: Repository,
                 session,
                 github_repo: Github_Repository=None):
        """Initialize a new CommitChecker."""
        self.session = session
        self.repository = session.query(RepositoryModel) \
            .options(joinedload(RepositoryModel.commits_by_hash)) \
            .get(github_repo.clone_url)
        self.git_repo = git_repo
        self.github_repo = github_repo
        self.queue = deque()
        self.scanned_commits = 0
        self.commit_stats = {}
        self.commit_hashes = set()
        self.checked_emails = set()

    def scan_repository(self):
        """Get all commits from this repository.

        It extracts the user as well as additions, deletions and the timestamp.
        This function gathers all commits in the git commit tree
        """
        # Walk through the repository and get all commits
        # that are reachable as parents from master commit
        try:
            master_commit = self.git_repo.head.get_object()
            self.queue.appendleft(master_commit)
        except GitError as e:
            sentry.sentry.captureException(
                extra={
                    'message': 'GitError during repo cloning. Probably empty',
                    'clone_url': self.repository.clone_url,
                },
            )
            return self.scanned_commits

        # List of commit hashes to check if we already were at this point in the tree.
        all_commits = []
        # This is a simple BFS through the git commit tree.
        # If we already know a node or already scanned a node, we don't add the parents.
        while len(self.queue) > 0:
            commit = self.queue.pop()
            # Break if we already visited this tree node
            if commit.hex in self.commit_hashes:
                continue

            self.commit_hashes.add(commit.hex)
            if len(commit.parents) == 1:
                diff = commit.tree.diff_to_tree(commit.parents[0].tree)
                self.commit_stats[commit.hex] = {
                    'additions': diff.stats.insertions,
                    'deletions': diff.stats.deletions,
                }

            commit_known = commit.hex in self.repository.commits_by_hash
            # Repo has been completely scanned and a this is a known commit.
            if commit_known and self.repository.completely_scanned:
                break

            # Repo has been partially scanned and a this is a known commit.
            elif commit_known and not self.repository.completely_scanned:
                [self.queue.appendleft(parent) for parent in commit.parents]

            # This is an unknown commit.
            elif not commit_known:
                self.scan_commit(commit)
                [self.queue.appendleft(parent) for parent in commit.parents]

            all_commits.append(commit)

        # Set the time of the first commit as repository creation time if it isn't set yet.
        self.repository.completely_scanned = True
        if not self.repository.created_at:
            timestamp = all_commits[-1].author.time
            utc_offset = timezone(timedelta(minutes=all_commits[-1].author.offset))
            self.repository.created_at = datetime.fromtimestamp(timestamp, utc_offset)

        self.repository.add(self.repository)
        self.session.commit()
        return self.scanned_commits

    def scan_commit(self, git_commit):
        """Get all features of a specific commit."""
        # Get or create new mail
        committer_email = Email.get_email(git_commit.committer.email, self.session)
        author_email = Email.get_email(git_commit.author.email, self.session)

        # Check every email only once to avoid github api calls
        if git_commit.author.email not in self.checked_emails:
            # Try to get the contributer if we have a github repository and
            # don't know the contributer for this email yet.
            author_email.get_github_relation(
                git_commit,
                'author',
                self.session,
                self.github_repo,
            )

            if author_email.contributer:
                author_email.contributer.repositories.append(self.repository)
            self.session.add(author_email)
            self.session.commit()

            self.checked_emails.add(git_commit.author.email)

        # Check every email only once to avoid github api calls
        if git_commit.committer.email not in self.checked_emails:
            # Try to get the contributer if we have a github repository and
            # don't know the contributer for this email yet.
            committer_email.get_github_relation(
                git_commit,
                'committer',
                self.session,
                self.github_repo,
            )

            if committer_email.contributer:
                committer_email.contributer.repositories.append(self.repository)
            self.session.add(committer_email)
            self.session.commit()

            self.checked_emails.add(git_commit.author.email)

        try:
            # Create a new commit and extract all valuable information
            commit = Commit(git_commit.hex, self.repository,
                            author_email, committer_email)
            if git_commit.hex in self.commit_stats:
                commit.additions = self.commit_stats[git_commit.hex]['additions']
                commit.deletions = self.commit_stats[git_commit.hex]['deletions']

            # Get timestamp with utc offset
            if git_commit.author:
                timestamp = git_commit.author.time
                utc_offset = timezone(timedelta(minutes=git_commit.author.offset))
                commit.creation_time = datetime.fromtimestamp(timestamp, utc_offset)

            if git_commit.committer:
                timestamp = git_commit.committer.time
                utc_offset = timezone(timedelta(minutes=git_commit.committer.offset))
                commit.commit_time = datetime.fromtimestamp(timestamp, utc_offset)

            self.session.add(commit)
        except BaseException as e:
            sentry.sentry.captureException(
                extra={
                    'message': 'Error during Commit creation',
                    'clone_url': self.repository.clone_url,
                    'hex': git_commit.hex,
                    'stats': self.commit_stats,
                },
            )

        # Commit session every 20 commits to avoid loss of all data on crash.
        self.scanned_commits += 1
        if self.scanned_commits % 20 == 0:
            self.session.commit()
