"""Data collection from Github."""
from collections import deque
from pygit2 import Repository, GitError
from sqlalchemy.orm import joinedload
from github import Repository as Github_Repository
from github.GithubObject import NotSet
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    InvalidRequestError,
)

from gitalizer.extensions import sentry
from gitalizer.aggregator.github import call_github_function
from gitalizer.models import (
    Email,
    Commit,
    Contributor,
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
            .get(github_repo.ssh_url)
        self.git_repo = git_repo
        self.github_repo = github_repo
        self.queue = deque()
        self.scanned_commits = 0
        self.diffs = {}

        self.emails = {}

    def scan_repository(self):
        """Get all commits from this repository.

        It extracts the user as well as additions, deletions and the timestamp.
        This function gathers all commits in the git commit tree
        """
        commits_to_scan = self.get_commits_to_scan()
        if not commits_to_scan:
            self.repository.completely_scanned = True
            return 0

        existing_commits = self.preload_commits(commits_to_scan)

        # Get emails for all commits.
        emails_to_scan = self.unique_emails(commits_to_scan)
        self.preload_emails(emails_to_scan)
        self.collect_emails(emails_to_scan)
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

    def get_commits_to_scan(self):
        """Walk through the repository and get all commits reachable in master."""
        try:
            master_commit = self.git_repo.head.get_object()
            self.queue.appendleft(master_commit)
        except GitError as e:
            sentry.captureException(
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
                sentry.captureMessage(
                    'Repository too big',
                    extra={'url': self.repository.clone_url},
                    level='info',
                    tags={'type': 'too_big', 'entity': 'repository'},
                )
                self.repository.too_big = True
                self.session.add(self.repository)
                commits_to_scan = []
                break

        return commits_to_scan

    def preload_commits(self, commits_to_scan):
        """Fetch all commits from db with matching shas.

        We do this once to bunch-fetch all matching commits to avoid performance breaks.
        """
        hashes_to_scan = [c.hex for c in commits_to_scan]
        if len(hashes_to_scan) != 0:
            existing_commits = self.session.query(Commit) \
                .filter(Commit.sha.in_(hashes_to_scan)) \
                .all()
            existing_commits = {c.sha: c for c in existing_commits}
        else:
            existing_commits = {}
        return existing_commits

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
                    offset_delta = timedelta(minutes=git_commit.author.offset)
                    utc_offset = timezone(offset_delta)
                    commit.creation_time = datetime.fromtimestamp(timestamp, utc_offset)

                timestamp = git_commit.commit_time
                offset_delta = timedelta(minutes=git_commit.commit_time_offset)
                utc_offset = timezone(offset_delta)
                commit.commit_time = datetime.fromtimestamp(timestamp, utc_offset)
                commit.commit_time_offset = offset_delta

                self.session.add(commit)
            except BaseException as e:
                sentry.captureException(
                    extra={
                        'message': 'Error during Commit creation',
                        'clone_url': self.repository.clone_url,
                        'hex': git_commit.hex,
                    },
                )

    def unique_emails(self, commits):
        """Get all commits that should be collected."""
        checked_emails = set()
        emails_to_scan = []
        for commit in commits:
            if commit.author.email not in checked_emails:
                emails_to_scan.append((commit, 'author', commit.author.email))
                checked_emails.add(commit.author.email)

            if commit.committer.email not in checked_emails:
                emails_to_scan.append((commit, 'committer', commit.committer.email))
                checked_emails.add(commit.committer.email)

        return emails_to_scan

    def preload_emails(self, emails_to_scan):
        """Bulk preload all emails to avoid DB overhead."""
        addresses = [e[2] for e in emails_to_scan]
        emails = self.session.query(Email) \
            .filter(Email.email.in_(addresses)) \
            .all()
        if emails:
            self.emails = {e.email: e for e in emails}
        else:
            self.emails = {}

    def collect_emails(self, emails):
        """Get emails of all commits to scan."""
        collecting = True
        one_more_try = False
        while collecting:
            try:
                email_count = 0
                for (commit, address_type, address) in emails:
                    email = self.emails.get(address)

                    # Create a new mail if we don't know it yet
                    if not email:
                        email = Email.get_email(
                            address,
                            self.session,
                            do_commit=False,
                        )
                        self.emails[address] = email

                    # Get the email relation to github contributors
                    if address_type == 'author':
                        self.get_github_author(email, commit, do_commit=False)
                    if address_type == 'committer':
                        self.get_github_committer(email, commit, do_commit=False)

                    # Add the contributor to the repository if he isn't known yet.
                    if email.contributor:
                        if self.repository not in email.contributor.repositories:
                            email.contributor.repositories.append(self.repository)
                    else:
                        # Mark email as unknown to prevent further github queries for this email.
                        email.unknown = True
                    self.session.add(email)
                    email_count += 1

                    # Commit all 20 emails to prevent large reloads on transaction failures.
                    if email_count % 20:
                        self.session.commit()
                        one_more_try = False
                        collecting = True

                collecting = False
            except (IntegrityError, OperationalError, InvalidRequestError) as e:
                # This can happen in case two threads add the same email addresses
                # Rollback the transaction, try one more time and raise if it fails again.
                # If the next transaction is successful, we reset the retry behaviour.
                sentry.captureMessage(f'Email collection IntegrityError', level='info')
                self.session.rollback()
                self.preload_emails(emails)
                if one_more_try:
                    collecting = False
                    raise e

                one_more_try = True

    def get_github_author(self, email, git_commit, do_commit=True):
        """Get the related Github author."""
        # No Github repository or the contributor is already known
        if not self.github_repo or email.contributor is not None or email.unknown:
            return
        github_commit = call_github_function(self.github_repo, 'get_commit', [git_commit.hex])

        if github_commit.author and github_commit.author is not NotSet:
            # Workaround for issue https://github.com/PyGithub/PyGithub/issues/279
            if github_commit.author._url.value is None:
                sentry.captureMessage('Author has no _url', level='info')
                return

            contributor = Contributor.get_contributor(
                github_commit.author.login,
                self.session,
                do_commit=do_commit,
            )
            email.contributor = contributor

    def get_github_committer(self, email, git_commit, do_commit=True):
        """Get the related Github committer."""
        # No Github repository or the contributor is already known
        if not self.github_repo or email.contributor is not None or email.unknown:
            return
        github_commit = call_github_function(self.github_repo, 'get_commit', [git_commit.hex])

        if github_commit.committer and github_commit.committer is not NotSet:
            # Workaround for issue https://github.com/PyGithub/PyGithub/issues/279
            if github_commit.committer._url.value is None:
                sentry.captureMessage('committer has no _url', level='info')
                return

            contributor = Contributor.get_contributor(
                github_commit.committer.login,
                self.session,
                do_commit=do_commit,
            )
            email.contributor = contributor
        return
