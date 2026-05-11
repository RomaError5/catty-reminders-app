#!/bin/bash
set -e
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

COMMIT_HASH=$(git rev-parse HEAD)
echo "DEPLOY_REF=$COMMIT_HASH" > .env

sudo systemctl restart app.service
echo "Service restarted"