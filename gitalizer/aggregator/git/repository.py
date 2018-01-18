"""Clone repositories and get data from it."""
import os
import shutil
from flask import current_app
from pygit2 import Repository, clone_repository


def get_git_repository(url: str, owner: str, name: str):
    """Clone or update a repository."""
    base_dir = current_app.config['GIT_CLONE_PATH']
    clone_dir = os.path.join(base_dir, owner, name)

    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)

    os.makedirs(clone_dir)
    repo = clone_repository(url, clone_dir, bare=True)
    repo = Repository(clone_dir)

    return repo


def delete_git_repository(owner: str, name: str):
    """Delete a git repository."""
    base_dir = current_app.config['GIT_CLONE_PATH']
    clone_dir = os.path.join(base_dir, owner, name)
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)
