#!/usr/bin/bash

ssh nuke@jarvis 'pg_dump gitalizer > gitalizer.dump'
rsync nuke@jarvis:gitalizer.dump ./
dropdb gitalizer || true
createdb gitalizer
psql gitalizer < gitalizer.dump
rm gitalizer.dump
ssh nuke@jarvis 'rm gitalizer.dump'
