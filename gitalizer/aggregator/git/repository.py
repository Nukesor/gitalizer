"""Clone repositories and get data from it."""
import os
import shutil
from flask import current_app
from pygit2 import Repository, clone_repository, GIT_RESET_HARD, GitError


def get_git_repository(url: str, owner: str, name: str):
    """Clone or update a repository."""
    base_dir = current_app.config['GIT_CLONE_PATH']
    clone_dir = os.path.join(base_dir, owner, name)
    # Directory doesn't exist, clone it
    if not os.path.exists(clone_dir):
        os.makedirs(clone_dir)
        repo = clone_repository(url, clone_dir, bare=True)

    # Repository is already cloned, pull new changes
    else:
        # Manually fetch new head
        repo = Repository(clone_dir)
        repo.remotes['origin'].fetch()

        try:
            current_ref = repo.head
            # Hard reset repository to get clean repo
            repo.reset(current_ref.target, GIT_RESET_HARD)
        except GitError as e:
            current_app.logger.info(f'GitError at repo {url}')

    return repo


def delete_git_repository(owner: str, name: str):
    """Delete a git repository."""
    base_dir = current_app.config['GIT_CLONE_PATH']
    clone_dir = os.path.join(base_dir, owner, name)
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)
