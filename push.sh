#!/bin/bash
# Quick push script — run this after making any changes
# Usage: ./push.sh "your commit message"

cd "$(dirname "$0")"

MSG="${1:-auto: update $(date '+%Y-%m-%d %H:%M')}"

echo "📦 Staging all changes..."
git add -A

echo "✍️  Committing: $MSG"
git commit -m "$MSG"

echo "🚀 Pushing to GitHub..."
git push origin main

echo "✅ Done! Check: https://github.com/codeyatiofficial-web/Quant-Pattern-Astro-Finance"
