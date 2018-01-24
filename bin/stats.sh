#!/bin/bash
db=gitalizer

result=$(psql -d $db -t -c "SELECT pg_size_pretty(pg_database_size('gitalizer'));")
echo "DB size: $result"

result=$(psql -d $db -t -c 'SELECT count(*) FROM commit;')
echo "commit count: $result"

result=$(psql -d $db -t -c 'SELECT count(*) FROM repository;')
echo "repository count: $result"

result=$(psql -d $db -t -c 'SELECT count(*) FROM repository WHERE completely_scanned = TRUE OR broken = TRUE OR fork = TRUE;')
echo "Finished or filtered repository count: $result"

result=$(psql -d $db -t -c 'SELECT count(*) FROM contributer;')
echo "contributer count: $result"
