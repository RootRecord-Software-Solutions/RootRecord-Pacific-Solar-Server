#!/bin/bash

REPO="$(pwd)"

OUTPUT=$(git pull 2>&1)

if [ $? -eq 0 ]; then
    zenity --info \
        --title="RootRecord Pull Complete" \
        --text="Repository updated successfully.\n\n$OUTPUT" \
        --width=600
else
    zenity --error \
        --title="RootRecord Pull Failed" \
        --text="$OUTPUT" \
        --width=600
fi
