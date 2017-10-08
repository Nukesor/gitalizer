# Git analyzer




## Handy postgresql stuff

pglocks:
```
SELECT * FROM pg_locks pl LEFT JOIN pg_stat_activity psa ON pl.pid = psa.pid;
```

size:
```
    -- Database Size
    SELECT pg_size_pretty(pg_database_size('gitalizer'));
    -- Table Size
    SELECT pg_size_pretty(pg_relation_size('commit'));
```
