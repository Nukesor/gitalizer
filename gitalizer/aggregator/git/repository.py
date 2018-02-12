"""Clone repositories and get data from it."""
import os
import shutil
import pygit2
from flask import current_app
from pygit2 import Repository, clone_repository


def get_git_repository(url: str, owner: str, name: str):
    """Clone or update a repository."""
    base_dir = current_app.config['GIT_CLONE_PATH']
    clone_dir = os.path.join(base_dir, owner, name)

    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)

    callbacks = None
    if 'https://' not in url:
        keypair = pygit2.Keypair(current_app.config['GITHUB_USER'],
                                 "id_rsa.pub", "id_rsa",
                                 current_app.config['SSH_PASSWORD'])
        callbacks = pygit2.RemoteCallbacks(credentials=keypair)

    os.makedirs(clone_dir)
    repo = clone_repository(url, clone_dir, bare=True, callbacks=callbacks)
    repo = Repository(clone_dir)

    return repo


def delete_git_repository(owner: str, name: str):
    """Delete a git repository."""
    base_dir = current_app.config['GIT_CLONE_PATH']
    clone_dir = os.path.join(base_dir, owner, name)
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)
