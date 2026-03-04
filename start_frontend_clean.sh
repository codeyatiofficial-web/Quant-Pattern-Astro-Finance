#!/bin/bash
cd /Users/anitarawat/nakshatranse/frontend || exit 1
pkill -9 -f "next dev" || true
pkill -9 "node" || true
rm -rf .next
rm -rf node_modules package-lock.json
npm install next@14 react@18 react-dom@18
npm install lucide-react next-themes
npm run build
