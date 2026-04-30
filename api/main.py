"""
Vercel Serverless FastAPI Handler
This adapts the main game logic to run as serverless functions
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware
from mangum import Mangum
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app as game_app

# Add CORS for Vercel deployment
game_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mangum adapter for Vercel
handler = Mangum(game_app, lifespan="off")
