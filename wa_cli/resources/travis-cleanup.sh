#!/bin/bash
#
# Cleans up the sanboxes that have been created to run PRs
# Relies on the following env vars:
#   WA_URL
#   WA_APIKEY
#   TRAVIS_*
#

export PYTHONUNBUFFERED=TRUE

if [[ -n "${TRAVIS_PULL_REQUEST_BRANCH}" ]]; then
    echo "Deleting the PR sandboxes..."
    for skill in ./test/flow/*; do
        if [ -d "${skill}" ]; then
            skill=$(basename "$skill")
            SANDBOX_NAME=$(wa-cli sandbox name "${skill}")
            echo "Deleting sandbox '$SANDBOX_NAME'..."
            wa-cli sandbox delete "$skill"
        fi
    done
else
    echo "No ad-hoc PR skills were created for this build"
fi

