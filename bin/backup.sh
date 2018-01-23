#!/usr/bin/bash
timestamp=`date +%Y%m%d`
dest="backup/gitalizer_${timestamp}.dump"

mkdir -p ~/backup
pg_dump -F c gitalizer > ~/$dest
