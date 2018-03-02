#!/usr/bin/bash

host=nuke@jarvis

echo 'Dumping DB on remote'
ssh $host 'pg_dump -F c gitalizer > gitalizer.dump'
echo 'Sync DB'
scp $host:gitalizer.dump ./

echo 'Drop and recreate DB'
dropdb gitalizer || true
createdb gitalizer

echo 'Restoring DB'
pg_restore -j 4 -F c -d gitalizer gitalizer.dump

echo 'Deleting dumps'
rm gitalizer.dump
ssh $host 'rm gitalizer.dump'
echo 'Done'
