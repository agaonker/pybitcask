"""FastAPI server for PyBitcask key-value store."""

import argparse
import logging
import signal
import sys
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from pybitcask.bitcask import Bitcask
from pybitcask.config import config as bitcask_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database instance
db: Optional[Bitcask] = None


# Pydantic models for request/response
class PutRequest(BaseModel):
    """Request model for PUT operations."""

    key: str
    value: Any


class BatchPutRequest(BaseModel):
    """Request model for batch PUT operations."""

    data: Dict[str, Any]


class GetResponse(BaseModel):
    """Response model for GET operations."""

    key: str
    value: Any
    found: bool


class DeleteResponse(BaseModel):
    """Response model for DELETE operations."""

    key: str
    deleted: bool


class ListResponse(BaseModel):
    """Response model for LIST operations."""

    keys: List[str]
    count: int


class StatusResponse(BaseModel):
    """Response model for server status."""

    status: str
    mode: str
    data_dir: str
    keys_count: int


# Create FastAPI app
app = FastAPI(
    title="PyBitcask Server",
    description="REST API for PyBitcask key-value store",
    version="1.0.0",
)


def initialize_database(data_dir: str, debug_mode: bool = False):
    """Initialize the database connection."""
    global db
    try:
        db = Bitcask(data_dir, debug_mode=debug_mode)
        logger.info(
            f"Database initialized: data_dir={data_dir}, debug_mode={debug_mode}"
        )
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def cleanup_database():
    """Clean up database connection."""
    global db
    if db:
        db.close()
        db = None
        logger.info("Database connection closed")


@app.on_event("startup")
async def startup_event():
    """Handle server startup."""
    logger.info("PyBitcask server starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Handle server shutdown."""
    logger.info("PyBitcask server shutting down...")
    cleanup_database()


@app.get("/", response_model=StatusResponse)
async def root():
    """Get server status."""
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")

    return StatusResponse(
        status="running",
        mode="debug" if db.debug_mode else "normal",
        data_dir=str(db.data_dir),
        keys_count=len(db.list_keys()),
    )


@app.post("/put")
async def put_value(request: PutRequest):
    """Store a key-value pair."""
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        db.put(request.key, request.value)
        return {"status": "success", "key": request.key}
    except Exception as e:
        logger.error(f"Error storing key {request.key}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/batch")
async def batch_put(request: BatchPutRequest):
    """Store multiple key-value pairs."""
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        db.batch_write(request.data)
        return {"status": "success", "count": len(request.data)}
    except Exception as e:
        logger.error(f"Error in batch write: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/get/{key}", response_model=GetResponse)
async def get_value(key: str):
    """Retrieve a value by key."""
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        value = db.get(key)
        return GetResponse(key=key, value=value, found=value is not None)
    except Exception as e:
        logger.error(f"Error retrieving key {key}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/delete/{key}", response_model=DeleteResponse)
async def delete_value(key: str):
    """Delete a key-value pair."""
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        deleted = db.delete(key)
        return DeleteResponse(key=key, deleted=deleted)
    except Exception as e:
        logger.error(f"Error deleting key {key}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/keys", response_model=ListResponse)
async def list_keys():
    """List all keys in the database."""
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        keys = db.list_keys()
        return ListResponse(keys=keys, count=len(keys))
    except Exception as e:
        logger.error(f"Error listing keys: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/clear")
async def clear_database():
    """Clear all data from the database."""
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        db.clear()
        return {"status": "success", "message": "Database cleared"}
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "pybitcask-server"}


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    cleanup_database()
    sys.exit(0)


def main():
    """Start the PyBitcask server."""
    parser = argparse.ArgumentParser(description="PyBitcask Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--data-dir", help="Data directory path")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--log-level", default="INFO", help="Log level")

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize database
    data_dir = args.data_dir or str(bitcask_config.get_data_dir())
    initialize_database(data_dir, args.debug)

    # Start server
    logger.info(f"Starting PyBitcask server on {args.host}:{args.port}")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Debug mode: {args.debug}")

    try:
        uvicorn.run(
            app, host=args.host, port=args.port, log_level=args.log_level.lower()
        )
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    finally:
        cleanup_database()


if __name__ == "__main__":
    main()
