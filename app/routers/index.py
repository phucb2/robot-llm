from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/")
async def read_index():
    return FileResponse("static/index.html")

@router.get("/aquarium")
async def read_aquarium():
    return FileResponse("static/aquarium.html")

# Check status of server
@router.get("/status/")
async def status():
    return {"status": "ok"}