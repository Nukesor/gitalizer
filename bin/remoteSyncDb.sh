#!/usr/bin/bash

host=nuke@jarvis

echo 'Dumping DB'
#pg_dump -F c gitalizer > gitalizer.dump

echo 'Sync DB to remote'
scp gitalizer.dump "${host}:"

echo 'Drop and recreate DB'
ssh $host 'dropdb gitalizer || true'
ssh $host 'createdb gitalizer'

echo 'Restoring DB'
ssh $host 'pg_restore -j 8 -F c -d gitalizer ~/gitalizer.dump'

echo 'Deleting dumps'
rm gitalizer.dump
ssh $host 'rm gitalizer.dump'
echo 'Done'
