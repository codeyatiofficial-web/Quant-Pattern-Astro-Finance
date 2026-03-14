#!/bin/bash
pkill -9 -f "uvicorn"
cd backend > /dev/null
uvicorn main:app --reload --port 8001 &
sleep 3
