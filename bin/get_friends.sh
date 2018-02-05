#!/usr/bin/bash

for user in 'nukesor' 'ahti' 'raffomania' 'hatzel' 'tronje' 'c-gotoh' '3wille' 'svenstaro'; do
    flask get_friends $user

    if [ $? -ne 0 ]; then
        echo "Previous command failed"
        exit
    fi
done
