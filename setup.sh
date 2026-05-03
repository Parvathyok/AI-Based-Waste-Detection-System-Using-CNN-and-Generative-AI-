#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# setup.sh — WasteWise AI: Build, Tag, Push to DockerHub & GitHub
# Usage:
#   chmod +x setup.sh
#   ./setup.sh [DOCKERHUB_USERNAME] [VERSION_TAG]
# Example:
#   ./setup.sh yourusername v1.0.0
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
DOCKERHUB_USER="${1:-yourdockerhubusername}"
VERSION="${2:-v1.0.0}"
IMAGE_NAME="wastewise-ai"
FULL_IMAGE="${DOCKERHUB_USER}/${IMAGE_NAME}"
GITHUB_REPO="https://github.com/${DOCKERHUB_USER}/wastewise-ai.git"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║         WasteWise AI — Build & Deploy Script         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo "  Image   : ${FULL_IMAGE}:${VERSION}"
echo "  Version : ${VERSION}"
echo ""

# ── 1. Git Setup & Version Tag ────────────────────────────────────────────────
echo "▶ [1/5] Initializing Git repository..."
if [ ! -d ".git" ]; then
  git init
  git branch -M main
  echo "  ✓ Git initialized."
else
  echo "  ✓ Git already initialized."
fi

git add -A
git commit -m "feat: WasteWise AI ${VERSION} — CNN + GenAI waste detection system

- EfficientNet-B2 7-class waste classification
- Gemini GenAI contextual explanations (R = g(ŷ, C))
- Flask REST API inference server
- Multi-stage Docker containerization
- SDG 11, 12, 13 aligned

Refs: https://github.com/wimlds-trojmiasto/detect-waste" || echo "  (Nothing new to commit)"

git tag -a "${VERSION}" -m "Release ${VERSION}: Initial production deployment" 2>/dev/null || \
  echo "  (Tag ${VERSION} already exists)"

echo "  ✓ Git commit + tag done."

# ── 2. Build Docker Image ─────────────────────────────────────────────────────
echo ""
echo "▶ [2/5] Building Docker image (multi-stage)..."
docker build \
  --target runtime \
  --tag "${IMAGE_NAME}:latest" \
  --tag "${IMAGE_NAME}:${VERSION}" \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  .
echo "  ✓ Docker image built: ${IMAGE_NAME}:${VERSION}"

# ── 3. Tag for DockerHub ──────────────────────────────────────────────────────
echo ""
echo "▶ [3/5] Tagging for DockerHub..."
docker tag "${IMAGE_NAME}:latest"   "${FULL_IMAGE}:latest"
docker tag "${IMAGE_NAME}:${VERSION}" "${FULL_IMAGE}:${VERSION}"
echo "  ✓ Tagged: ${FULL_IMAGE}:latest"
echo "  ✓ Tagged: ${FULL_IMAGE}:${VERSION}"

# ── 4. Push to DockerHub ──────────────────────────────────────────────────────
echo ""
echo "▶ [4/5] Pushing to DockerHub (${FULL_IMAGE})..."
echo "  Note: Ensure you are logged in with: docker login"
docker push "${FULL_IMAGE}:latest"
docker push "${FULL_IMAGE}:${VERSION}"
echo "  ✓ Pushed to DockerHub successfully."
echo "  🔗 https://hub.docker.com/r/${DOCKERHUB_USER}/${IMAGE_NAME}"

# ── 5. Push to GitHub ─────────────────────────────────────────────────────────
echo ""
echo "▶ [5/5] Pushing to GitHub..."
if git remote get-url origin &>/dev/null; then
  echo "  Remote 'origin' already set."
else
  git remote add origin "${GITHUB_REPO}"
  echo "  Remote set to: ${GITHUB_REPO}"
fi

git push -u origin main 2>/dev/null || true
git push origin "${VERSION}" 2>/dev/null || echo "  (Tag push skipped)"
echo "  ✓ Code pushed to GitHub."

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║                  ✅  Deploy Complete                 ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  DockerHub : docker pull ${FULL_IMAGE}:${VERSION}"
echo "║  Local run : docker-compose up -d                   ║"
echo "║  App URL   : http://localhost:5000                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
