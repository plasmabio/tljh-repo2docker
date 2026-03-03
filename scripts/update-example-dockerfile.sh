#!/usr/bin/env bash
set -eux

VERSION=$(node -p "require('./package.json').version")
echo "Updating example/Dockerfile to version $VERSION"
sed -i "s/tljh-repo2docker>=.*/tljh-repo2docker==$VERSION\"/" example/Dockerfile
