#!/bin/bash

REPO="$(pwd)"

MESSAGE=$(zenity --entry \
    --title="RootRecord Commit" \
    --text="Commit description:" \
    --width=500)

if [ -z "$MESSAGE" ]; then
    exit 0
fi

git add .

git commit -m "$MESSAGE"

git push
