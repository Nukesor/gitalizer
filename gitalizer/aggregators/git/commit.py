"""Data collection from Github."""

from collections import deque
from pygit2 import Repository, GitError
from github import Repository as Github_Repository
from datetime import datetime, timedelta, timezone

from gitalizer.extensions import db
from gitalizer.models.email import Email
from gitalizer.models.commit import Commit
from gitalizer.models.repository import Repository as RepositoryModel
from gitalizer.aggregators.github.contributer import get_contributer


class CommitScanner():
    """Get features from all commits in a repository."""

    def __init__(self, git_repo: Repository,
                 repository: RepositoryModel, github_repo: Github_Repository=None):
        """Initialize a new CommitChecker."""
        self.repository = repository
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
            print(f'\n\nGitError at repo {self.repository.clone_url}\nProbably an empty Repo\n\n')
            return
        except Exception as e:
            print(f'\n\nUnknown error at repo {self.repository.clone_url}\n\n')
            print(e)
            raise e

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
            already_scanned = self.scan_commit(commit)
            if not already_scanned:
                [self.queue.appendleft(parent) for parent in commit.parents]
            all_commits.append(commit)

        # Set the time of the first commit as repository creation time if it isn't set yet.
        if not self.repository.created_at:
            timestamp = all_commits[-1].author.time
            utc_offset = timezone(timedelta(minutes=all_commits[-1].author.offset))
            self.repository.created_at = datetime.fromtimestamp(timestamp, utc_offset)

        db.session.commit()
        return self.scanned_commits

    def scan_commit(self, git_commit):
        """Get all features of a specific commit."""
        commit = db.session.query(Commit) \
            .filter(Commit.sha == git_commit.hex) \
            .filter(Commit.repository == self.repository) \
            .one_or_none()

        if commit:
            return False
        else:
            # Check every email only once to avoid github api calls
            if git_commit.author.email not in self.checked_emails:
                # Save the email of this commit
                email = db.session.query(Email).get(git_commit.author.email)
                # If there is no such email we create a new email and a new contributer,
                # if the author is known and doesn't exist yet.
                if not email:
                    email = Email(git_commit.author.email)

                    # Try to get the contributer if we have a github repository
                    if self.github_repo:
                        if email.contributer:
                            email.contributer.repositories.append(self.repository)

                        # We don't know the contributer for this email yet.
                        # If we know the github author of this commit, we add it to this email address.
                    else:
                        github_commit = self.github_repo.get_commit(git_commit.hex)
                        if github_commit.author:
                            contributer = get_contributer(github_commit.author.login, self.repository)
                            email.contributer = contributer

                    db.session.add(email)
                    db.session.commit()
                    self.checked_emails.add(git_commit.author.email)

                # Create a new commit and extract all valuable information
                commit = Commit(git_commit.hex, self.repository, email)
                if git_commit.hex in self.commit_stats:
                    commit.additions = self.commit_stats[git_commit.hex]['additions']
                    commit.deletions = self.commit_stats[git_commit.hex]['deletions']
                # Get timestamp with utc offset
                timestamp = git_commit.author.time
                utc_offset = timezone(timedelta(minutes=git_commit.author.offset))
                commit.time = datetime.fromtimestamp(timestamp, utc_offset)

                db.session.add(commit)

            # Commit session every 20 commits to avoid loss of all data on crash.
            self.scanned_commits += 1
            if self.scanned_commits % 20 == 0:
                db.session.commit()
            # Print a status every 1000 commits to indicate progress.
            if self.scanned_commits % 1000 == 0:
                print(f"{self.scanned_commits} commits scanned.")
            return True
