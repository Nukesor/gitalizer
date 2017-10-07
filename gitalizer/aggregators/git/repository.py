"""Clone repositories and get data from it."""
import os
from flask import current_app
from pygit2 import Repository, clone_repository, GIT_RESET_HARD


def get_git_repository(url, owner, name):
    """Clone or update a repository."""
    base_dir = current_app.config['GIT_CLONE_PATH']
    clone_dir = os.path.join(base_dir, owner, name)
    # Directory doesn't exist, clone it
    if not os.path.exists(clone_dir):
        os.makedirs(clone_dir)
        repo = clone_repository(url, clone_dir)

    # Repository is already cloned, pull new changes
    else:
        # Manually fetch new head
        repo = Repository(clone_dir)
        repo.remotes['origin'].fetch()

        # Set the reference of current HEAD to remote master
        master_ref = repo.lookup_reference('refs/heads/master')
        remote_master_id = repo.lookup_reference('refs/remotes/origin/master').target
        master_ref.set_target(remote_master_id)

        # Hard reset repository to get clean repo
        repo.reset(master_ref.target, GIT_RESET_HARD)

    return repo
