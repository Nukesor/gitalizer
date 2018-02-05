"""Data collection from Github."""
from collections import deque
from pygit2 import Repository, GitError
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
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
        self.diffs = {}

        self.emails = {}
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
        commits_to_scan = []
        known_commit_hashes = set()
        # This is a simple BFS through the git commit tree.
        # If we already know a node or already scanned a node, we don't add the parents.
        while len(self.queue) > 0:
            commit = self.queue.pop()
            # Break if we already visited this tree node
            if commit.hex in known_commit_hashes:
                continue
            known_commit_hashes.add(commit.hex)

            commit_known = commit.hex in self.repository.commits_by_hash
            # Repo has been completely scanned and a this is a known commit.
            if commit_known and self.repository.completely_scanned:
                break

            # Repo has been partially scanned and a this is a known commit.
            elif commit_known and not self.repository.completely_scanned:
                [self.queue.appendleft(parent) for parent in commit.parents]
                continue
            # This is an unknown commit.
            elif not commit_known:
                [self.queue.appendleft(parent) for parent in commit.parents]

            if len(commit.parents) == 1:
                self.diffs[commit.hex] = commit.tree.diff_to_tree(commit.parents[0].tree)
            commits_to_scan.append(commit)

            if len(commits_to_scan) > 100000:
                self.repository.too_big = True
                self.session.add(self.repository)
                self.session.commit()

        # Fetch all commits from db with matching shas.
        # We do this once to bunch-fetch all matching commits
        # to avoid performance breaks.
        hashes_to_scan = [c.hex for c in commits_to_scan]
        if len(hashes_to_scan) != 0:
            existing_commits = self.session.query(Commit) \
                .filter(Commit.sha.in_(hashes_to_scan)) \
                .all()
            existing_commits = {c.sha: c for c in existing_commits}
        else:
            existing_commits = {}

        # Get emails for all commits.
        try:
            for commit in commits_to_scan:
                self.get_commit_emails(commit)
            self.session.commit()
        except IntegrityError as e:
            sentry.sentry.captureException()
            self.session.rollback()
            self.emails = {}
            self.checked_emails = set()
            for commit in commits_to_scan:
                self.get_commit_emails(commit)
            self.session.commit()

        # Actually scan the commits
        for commit in commits_to_scan:
            self.scan_commit(commit, existing_commits)
            # Commit session every 20 commits to avoid loss of all data on crash.
            self.scanned_commits += 1
            if self.scanned_commits % 1000 == 0:
                self.session.commit()

        self.session.commit()

        # Set the time of the first commit as repository creation time if it isn't set yet.
        self.repository.completely_scanned = True
        if not self.repository.created_at:
            timestamp = commits_to_scan[-1].author.time
            utc_offset = timezone(timedelta(minutes=commits_to_scan[-1].author.offset))
            self.repository.created_at = datetime.fromtimestamp(timestamp, utc_offset)

        self.session.add(self.repository)
        self.session.commit()
        return self.scanned_commits

    def scan_commit(self, git_commit, existing_commits):
        """Get all features of a specific commit."""
        # If we already know this commit just add the commit to this repository.
        if git_commit.hex in existing_commits:
            commit = existing_commits[git_commit.hex]
            commit.repositories.append(self.repository)
            self.session.add(commit)

        # Unknown commit, thereby we need to get all information
        else:
            try:
                author_email = self.emails[git_commit.author.email]
                committer_email = self.emails[git_commit.committer.email]
                commit = Commit(git_commit.hex, self.repository,
                                author_email, committer_email)

                diff = self.diffs.get(git_commit.hex)
                if diff:
                    commit.additions = diff.stats.insertions
                    commit.deletions = diff.stats.deletions

                if git_commit.author:
                    timestamp = git_commit.author.time
                    utc_offset = timezone(timedelta(minutes=git_commit.author.offset))
                    commit.creation_time = datetime.fromtimestamp(timestamp, utc_offset)

                timestamp = git_commit.commit_time
                utc_offset = timezone(timedelta(minutes=git_commit.commit_time_offset))
                commit.commit_time = datetime.fromtimestamp(timestamp, utc_offset)

                self.session.add(commit)
            except BaseException as e:
                sentry.sentry.captureException(
                    extra={
                        'message': 'Error during Commit creation',
                        'clone_url': self.repository.clone_url,
                        'hex': git_commit.hex,
                    },
                )

    def get_commit_emails(self, git_commit):
        """Get emails of all commits to scan."""
        if git_commit.author.email not in self.checked_emails:
            author_email = Email.get_email(
                git_commit.author.email,
                self.session,
            )
            self.emails[git_commit.author.email] = author_email
            # Try to get the contributer if we have a github repository and
            # don't know the contributer for this email yet.
            author_email.get_github_relation(
                git_commit,
                'author',
                self.session,
                self.github_repo,
            )

            if author_email.contributer:
                if self.repository not in author_email.contributer.repositories:
                    author_email.contributer.repositories.append(self.repository)
            self.session.add(author_email)

            self.checked_emails.add(git_commit.author.email)

        #  Get or create new mail. Check every email only once
        if git_commit.committer.email not in self.checked_emails:
            committer_email = Email.get_email(
                git_commit.committer.email,
                self.session,
            )
            self.emails[git_commit.committer.email] = committer_email
            # Try to get the contributer if we have a github repository and
            # don't know the contributer for this email yet.
            committer_email.get_github_relation(
                git_commit,
                'committer',
                self.session,
                self.github_repo,
            )

            if committer_email.contributer:
                if self.repository not in committer_email.contributer.repositories:
                    committer_email.contributer.repositories.append(self.repository)
            self.session.add(committer_email)

            self.checked_emails.add(git_commit.author.email)
