"""Data collection from Github."""

import pytz
from datetime import datetime, timedelta

from gitalizer.extensions import github, logger
from gitalizer.models import Contributor, Organization, Repository
from gitalizer.aggregator.github import call_github_function
from gitalizer.helpers.parallel import new_session
from gitalizer.helpers.parallel.manager import Manager
from gitalizer.aggregator.github.user import check_fork


def get_organization_memberships():
    """Refresh all user organizations."""
    session = new_session()

    tz = pytz.timezone('Europe/Berlin')
    now = datetime.now(tz)
    contributors = session.query(Contributor).all()
    for contributor in contributors:
        if contributor.last_full_scan and contributor.last_full_scan > now - timedelta(days=2):
            continue
        logger.info(f'Checking {contributor.login}. {github.github.rate_limiting[0]} remaining.')

        github_user = call_github_function(github.github, 'get_user',
                                           [contributor.login])

        github_orgs = call_github_function(github_user, 'get_orgs')
        for org in github_orgs:
            organization = Organization.get_organization(org.login, org.url, session)
            contributor.organizations.append(organization)
        contributor.last_full_scan = datetime.utcnow()
        session.add(contributor)
        session.commit()


def get_github_organization(name: str, members=False):
    """Get all collaborators of an organization."""
    session = new_session()
    orga = call_github_function(github.github, 'get_organization', [name])

    # Get orga repos
    orga_repos = call_github_function(orga, 'get_repos')
    while orga_repos ._couldGrow():
        call_github_function(orga_repos, '_grow')

    # Check orga repos
    repos_to_scan = set()
    for github_repo in orga_repos:
        repository = Repository.get_or_create(
            session,
            github_repo.ssh_url,
            name=github_repo.name,
            full_name=github_repo.full_name,
        )
        if github_repo.fork:
            check_fork(github_repo, session, repository, repos_to_scan)
        session.add(repository)

        if not repository.should_scan():
            continue

        session.commit()
        repos_to_scan.add(github_repo.full_name)

    member_list = set()
    if members:
        # Get members
        members = call_github_function(orga, 'get_members')
        while members._couldGrow():
            call_github_function(members, '_grow')
        member_list = set([m.login for m in members])

    # Create and start manager with orga repos and memeber_list
    sub_manager = Manager('github_repository', repos_to_scan)
    manager = Manager('github_contributor', member_list, sub_manager)
    manager.start()
    manager.run()
