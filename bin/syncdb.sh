#!/usr/bin/bash

echo 'Dumping DB on remote'
ssh nuke@jarvis 'pg_dump -F c gitalizer > gitalizer.dump'
echo 'Sync DB'
scp nuke@jarvis:gitalizer.dump ./

echo 'Drop and recreate DB'
dropdb gitalizer || true
createdb gitalizer

echo 'Restoring DB'
pg_restore -j 4 -F c -d gitalizer gitalizer.dump

echo 'Deleting dumps'
rm gitalizer.dump
ssh nuke@jarvis 'rm gitalizer.dump'
echo 'Done'
