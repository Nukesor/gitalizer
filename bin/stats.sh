#!/bin/bash

result=$(psql -d gitalizer -t -c "SELECT pg_size_pretty(pg_database_size('gitalizer'));")
echo "DB size: $result"

result=$(psql -d gitalizer -t -c 'SELECT count(*) FROM commit;')
echo "commit count: $result"

result=$(psql -d gitalizer -t -c 'SELECT count(*) FROM repository;')
echo "repository count: $result"

result=$(psql -d gitalizer -t -c 'SELECT count(*) FROM contributer;')
echo "contributer count: $result"
