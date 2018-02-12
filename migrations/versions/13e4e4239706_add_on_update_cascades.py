"""Add on update cascades

Revision ID: 13e4e4239706
Revises: bbdaf7e96fbb
Create Date: 2018-02-12 16:16:15.830156

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '13e4e4239706'
down_revision = 'bbdaf7e96fbb'
branch_labels = None
depends_on = None


def upgrade():
    """Add `ON UPDATE CASCADE` foreign keys."""
    # Drop and recreate contributer_organizations keys
    op.drop_constraint('commit_repository_repository_clone_url_fkey',
                       'commit_repository', type_='foreignkey')
    op.create_foreign_key('commit_repository_repository_clone_url_fkey',
                          'commit_repository', 'repository',
                          ['repository_clone_url'], ['clone_url'],
                          onupdate='CASCADE', ondelete='CASCADE',
                          deferrable=True)

    op.drop_constraint('commit_repository_commit_sha_fkey',
                       'commit_repository', type_='foreignkey')
    op.create_foreign_key('commit_repository_commit_sha_fkey',
                          'commit_repository', 'commit',
                          ['commit_sha'], ['sha'],
                          onupdate='CASCADE', ondelete='CASCADE',
                          deferrable=True)

    # Drop and recreate contributer_organizations keys
    op.drop_constraint('contributer_organizations_contributer_login_fkey',
                       'contributer_organizations', type_='foreignkey')
    op.create_foreign_key('contributer_organizations_contributer_login_fkey',
                          'contributer_organizations', 'contributer',
                          ['contributer_login'], ['login'],
                          onupdate='CASCADE', ondelete='CASCADE',
                          deferrable=True)

    op.drop_constraint('contributer_organizations_organization_login_fkey',
                       'contributer_organizations', type_='foreignkey')
    op.create_foreign_key('contributer_organizations_organization_login_fkey',
                          'contributer_organizations', 'organization',
                          ['organization_login'], ['login'],
                          onupdate='CASCADE', ondelete='CASCADE',
                          deferrable=True)

    # Drop and recreate contributer_repository keys
    op.drop_constraint('contributer_repository_repository_clone_url_fkey',
                       'contributer_repository', type_='foreignkey')
    op.create_foreign_key('contributer_repository_repository_clone_url_fkey',
                          'contributer_repository', 'repository',
                          ['repository_clone_url'], ['clone_url'],
                          onupdate='CASCADE', ondelete='CASCADE',
                          deferrable=True)

    op.drop_constraint('contributer_repository_contributer_login_fkey',
                       'contributer_repository', type_='foreignkey')
    op.create_foreign_key('contributer_repository_contributer_login_fkey',
                          'contributer_repository', 'contributer',
                          ['contributer_login'], ['login'],
                          onupdate='CASCADE', ondelete='CASCADE',
                          deferrable=True)

    # Unique constraint on repository full_name
    op.create_unique_constraint('ix_repository_full_name', 'repository', ['full_name'])

    # Repository parent foreign key update
    op.drop_constraint('repository_parent_url_fkey', 'repository', type_='foreignkey')
    op.create_foreign_key('repository_parent_url_fkey',
                          'repository', 'repository',
                          ['parent_url'], ['clone_url'],
                          onupdate='CASCADE', ondelete='SET NULL',
                          deferrable=True)


def downgrade():
    """Reverse migration."""
    # Repository parent foreign key update
    op.drop_constraint('repository_parent_url_fkey', 'repository', type_='foreignkey')
    op.create_foreign_key('repository_parent_url_fkey',
                          'repository', 'repository',
                          ['parent_url'], ['clone_url'],
                          ondelete='SET NULL')

    op.drop_constraint('ix_repository_full_name', 'repository', type_='unique')

    op.drop_constraint('contributer_repository_repository_clone_url_fkey',
                       'contributer_repository', type_='foreignkey')
    op.create_foreign_key('contributer_repository_repository_clone_url_fkey',
                          'contributer_repository', 'repository',
                          ['repository_clone_url'], ['clone_url'],
                          ondelete='CASCADE', deferrable=True)

    op.drop_constraint('contributer_repository_contributer_login_fkey',
                       'contributer_repository', type_='foreignkey')
    op.create_foreign_key('contributer_repository_contributer_login_fkey',
                          'contributer_repository', 'contributer',
                          ['contributer_login'], ['login'],
                          ondelete='CASCADE', deferrable=True)

    op.drop_constraint('contributer_organizations_contributer_login_fkey',
                       'contributer_organizations', type_='foreignkey')
    op.create_foreign_key('contributer_organizations_contributer_login_fkey',
                          'contributer_organizations', 'contributer',
                          ['contributer_login'], ['login'],
                          ondelete='CASCADE', deferrable=True)

    op.drop_constraint('contributer_organizations_organization_login_fkey',
                       'contributer_organizations', type_='foreignkey')
    op.create_foreign_key('contributer_organizations_organization_login_fkey',
                          'contributer_organizations', 'organization',
                          ['organization_login'], ['login'],
                          ondelete='CASCADE', deferrable=True)

    op.drop_constraint('commit_repository_repository_clone_url_fkey',
                       'commit_repository', type_='foreignkey')
    op.create_foreign_key('commit_repository_repository_clone_url_fkey',
                          'commit_repository', 'repository',
                          ['repository_clone_url'], ['clone_url'],
                          ondelete='CASCADE', deferrable=True)

    op.drop_constraint('commit_repository_commit_sha_fkey',
                       'commit_repository', type_='foreignkey')
    op.create_foreign_key('commit_repository_commit_sha_fkey',
                          'commit_repository', 'commit',
                          ['commit_sha'], ['sha'])
