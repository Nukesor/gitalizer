#!/usr/bin/bash

for user in 'athi' 'raffomania' 'nukesor' 'hatzel' 'tronje' 'c-gotoh' '3wille' 'svenstaro'; do
    flask get_friends $user

    if [ $? -ne 0 ]; then
        echo "Previous command failed"
        exit
    fi
done
