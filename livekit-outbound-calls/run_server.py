#!/usr/bin/env python
"""Run the API server."""
import uvicorn
from config import config

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
    )
