#!/bin/bash
#
# Runs the dialog flow tests of the skills in ./test/flow
# Relies on the following env vars:
#   WA_URL
#   WA_APIKEY
#

export PYTHONUNBUFFERED=TRUE

for skill in ./test/flow/*; do
    if [ -d "${skill}" ]; then
        skill=$(basename "$skill")
        SANDBOX_NAME=$(wa-cli sandbox name "${skill}")
        echo "Running test on skill '$SANDBOX_NAME'..."
        wa-cli sandbox test flow "$skill" || exit 1
    fi
done

