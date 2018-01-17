#!/usr/bin/bash

for user in 'athi' 'raffomania' 'nukesor' 'hatzel' 'tronje' 'c-gotoh' '3wille'; do
    flask get_friends $user
done
