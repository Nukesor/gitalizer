
select distinct(extract(TIMEZONE from commit_time))
    from commit
    join commit_repository
    on commit.sha = commit_repository.commit_sha
    join repository
    ON repository.clone_url = commit_repository.repository_clone_url
    join contributor_repository
    ON contributor_repository.repository_clone_url = repository.clone_url
    join contributor
    ON contributor.login = contributor_repository.contributor_login
    where contributor.login = 'nukesor';
