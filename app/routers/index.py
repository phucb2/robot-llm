from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/")
async def read_index():
    return FileResponse("static/aquarium.html")


@router.get("/aquarium")
async def read_aquarium():
    return FileResponse("static/index.html")


# Check status of server
@router.get("/status/")
async def status():
    return {"status": "ok"}
