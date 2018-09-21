"""Clone repositories and get data from it."""
import os
import shutil
import pygit2
from pygit2 import Repository, clone_repository

from gitalizer.helpers.config import config


def get_git_repository(url: str, owner: str, name: str):
    """Clone or update a repository."""
    base_dir = config['cloning']['temporary_clone_path']
    clone_dir = os.path.join(base_dir, owner, name)

    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)

    callbacks = None
    if 'https://' not in url:
        keypair = pygit2.Keypair(username=config['cloning']['ssh_user'],
                                 pubkey=config['cloning']['public_key'],
                                 privkey=config['cloning']['private_key'],
                                 passphrase=config['cloning']['ssh_password'])
        callbacks = pygit2.RemoteCallbacks(credentials=keypair)

    os.makedirs(clone_dir)
    repo = clone_repository(url, clone_dir, bare=True, callbacks=callbacks)
    repo = Repository(clone_dir)

    return repo


def delete_git_repository(owner: str, name: str):
    """Delete a git repository."""
    base_dir = config['cloning']['temporary_clone_path']
    clone_dir = os.path.join(base_dir, owner, name)
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)
