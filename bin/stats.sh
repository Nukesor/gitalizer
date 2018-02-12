#!/bin/bash
db=gitalizer

db_size=$(psql -d $db -t -c "SELECT pg_size_pretty(pg_database_size('gitalizer'));")

echo "DB size: $db_size"


commit_count=$(psql -d $db -t -c 'SELECT count(*) FROM commit;')
commit_repository_count=$(psql -d $db -t -c 'SELECT count(*) FROM commit_repository;')
echo ""
echo "Commits:"
echo "    Total: $commit_count"
echo "    Repository references: $commit_repository_count"


repository_count=$(psql -d $db -t -c 'SELECT count(*) FROM repository;')
filtered_repository_count=$(psql -d $db -t -c 'SELECT count(*) FROM repository WHERE broken = TRUE OR fork = TRUE or too_big = TRUE;')
finished_repository_count=$(psql -d $db -t -c 'SELECT count(*) FROM repository WHERE completely_scanned = TRUE;')
echo ""
echo "Repositories:"
echo "    Total: $repository_count"
echo "    Filtered: $filtered_repository_count"
echo "    Finished: $finished_repository_count"


contributer_count=$(psql -d $db -t -c 'SELECT count(*) FROM contributer;')
too_big_contributer_count=$(psql -d $db -t -c 'SELECT count(*) FROM contributer WHERE too_big = TRUE;')
contributer_repository_count=$(psql -d $db -t -c 'SELECT count(*) FROM contributer_repository;')
echo ""
echo "Contributer:"
echo "    Total: $contributer_count"
echo "    Too big: $too_big_contributer_count"
echo "    Repository references: $contributer_repository_count"

email_count=$(psql -d $db -t -c 'SELECT count(*) FROM email;')
unknown_email_count=$(psql -d $db -t -c 'SELECT count(*) FROM email WHERE unknown = TRUE;')
echo ""
echo "Email:"
echo "    Total: $email_count"
echo "    Unknown: $unknown_email_count"
