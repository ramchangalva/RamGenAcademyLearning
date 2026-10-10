#!/usr/bin/env bash
set -euo pipefail
# Usage: docker login && ./scripts/docker-push.sh YOUR_DOCKERHUB_USERNAME [tag]
USER="${1:?Docker Hub username required}"
TAG="${2:-latest}"
SRC="wealthplanner:${TAG}"
DST="${USER}/wealthplanner:${TAG}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if ! docker image inspect "$SRC" &>/dev/null; then
  echo "Building image..."
  (cd "$ROOT" && docker compose build web)
fi
echo "Tagging $SRC -> $DST"
docker tag "$SRC" "$DST"
echo "Pushing $DST"
docker push "$DST"
echo "Done: $DST"
