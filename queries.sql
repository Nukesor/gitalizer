
select distinct(extract(TIMEZONE from commit_time))
    from commit
    join commit_repository
    on commit.sha = commit_repository.commit_sha
    join repository
    ON repository.clone_url = commit_repository.repository_clone_url
    join contributer_repositor
    ON contributer_repository.repository_clone_url = repository.clone_url
    join contributer
    ON contributer.login = contributer_repository.contributer_login
    where contributer.login = 'lattner'
