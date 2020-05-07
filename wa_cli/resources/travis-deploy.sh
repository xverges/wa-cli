#!/bin/bash
#
# Deploys and waits for readiness of the skills in ./test/flow
# Relies on the following env vars:
#   DEPLOY_MAIN_BRANCH
#   TRAINING_TIMEOUT_IN_SECONDS
#   WA_URL
#   WA_APIKEY
#

export PYTHONUNBUFFERED=TRUE

MAIN_BRANCH=$(cat ./.wa-cli/main_branch.txt)
wa-cli init --no-prompt --main-branch "${MAIN_BRANCH}"
echo TRAVIS_BRANCH="$TRAVIS_BRANCH"
echo TRAVIS_PULL_REQUEST_BRANCH="$TRAVIS_PULL_REQUEST_BRANCH"
echo TRAVIS_PULL_REQUEST="$TRAVIS_PULL_REQUEST"

for skill in ./test/flow/*; do
    if [ -d "${skill}" ]; then
        skill=$(basename "$skill")
        SANDBOX_NAME=$(wa-cli sandbox name "${skill}")
        if [[ $SANDBOX_NAME = "${skill}" && "$DEPLOY_MAIN_BRANCH" != TRUE ]]; then
            echo "Skipping deployment of '$skill' to main branch '${MAIN_BRANCH}'"
        else
            echo "Deploying to sandbox '${SANDBOX_NAME}'"
            wa-cli sandbox push "${skill}" || exit 1
        fi;
    fi
done
for skill in ./test/flow/*; do
    if [ -d "${skill}" ]; then
        skill=$(basename "$skill")
        wa-cli sandbox wait-for-ready --timeout "$TRAINING_TIMEOUT_IN_SECONDS" "${skill}" || exit 1
    fi
done
