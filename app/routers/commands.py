from fastapi import APIRouter, HTTPException, Depends
from fastapi.websockets import WebSocket
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from fastapi import Depends, File, HTTPException, UploadFile
from fastapi.security import HTTPBasicCredentials
from ..configs import AWS_S3_BUCKET_NAME
from .auth import security
from pathlib import Path

from ..services.s3 import s3_client
from ..controller.robot import RobotController, Command, Direction
import uuid

router = APIRouter()

try:
    controller = RobotController.get_instance()
except Exception as e:
    print(f"Error initializing the robot controller: {e}")
    controller = None

@router.post("/move/")
async def move_robot(direction: str):
    # Check if the direction is valid
    if direction not in Direction.__members__:
        raise HTTPException(status_code=400, detail="Invalid direction")
    simple_action = direction[0].upper()  # F, B, L, R
    # Move the robot in the specified direction
    controller.send_command(Command("move", simple_action))
    return {"direction": direction}

# Flashlight command, on/off
@router.post("/flashlight/")
async def flashlight(status: str):
    # Check if the status is valid
    if status not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    # Send the flashlight command
    controller.send_command(Command("flashlight", status))
    return {"status": status}

@router.post("/oxygen/")
async def oxygen(status: str):
    if status not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    controller.send_command(Command("oxygen", status))
    return {"status": status}

@router.post("/filter/")
async def filter(status: str):
    if status not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    controller.send_command(Command("filter", status))
    return {"status": status}

@router.post("/capture/jpg")
async def capture_jpg():
    # Send the capture command
    controller.send_command(Command("capture", "jpg"))
    return {"message": "Capturing image in JPG format"}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        try:
            if data == "forward":
                controller.move_forward()
            elif data == "backward":
                controller.move_backward()
            elif data == "left":
                controller.turn_left()
            elif data == "right":
                controller.turn_right()
            elif data == "stop":
                controller.stop()
            # Add more commands as needed
            await websocket.send_text(f"Command executed: {data}")
        except Exception as e:
            print(f"Error executing command {data}: {e}")
            await websocket.close(code=1011)
            break

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...), credentials: HTTPBasicCredentials = Depends(security)):
    try:
        file_extension = Path(file.filename).suffix
        unique_filename = str(uuid.uuid4()) + file_extension
        file_location = f"temp/{unique_filename}"

        with open(file_location, "wb") as buffer:
            buffer.write(file.file.read())

        s3_client.upload_file(
            file_location, 
            AWS_S3_BUCKET_NAME, 
            unique_filename
        )
        Path(file_location).unlink()  # delete the temp file
        return {"filename": unique_filename}
    
    except (NoCredentialsError, PartialCredentialsError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An error occurred while uploading the file")