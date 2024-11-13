from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, WebSocket
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from jose import jwt
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from pathlib import Path
import uuid
from dotenv import load_dotenv
import os
import random
from paho.mqtt import client as mqtt_client
from enum import Enum
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, FastAPI, HTTPException, status
from jose import JWTError, jwt
import json
import uvicorn

from app.logger_config import logger
from controller.robot import RobotController, Command

# warning; this is a temporary solution to suppress warnings
import warnings
warnings.filterwarnings("ignore")

import paho.mqtt.client as mqtt

app = FastAPI()

# Load environment variables from .env file
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

logger.info("This is a new message")

s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.get("/aquarium")
async def read_aquarium():
    return FileResponse("static/aquarium.html")

@app.post("/token/")
async def login_for_access_token(credentials: HTTPBasicCredentials = Depends(security)):
    authenticate(credentials)
    data = {
        "sub": credentials.username,
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    token = jwt.encode(data, "secret")
    return {"access_token": token, "token_type": "bearer"}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenData:
    def __init__(self, username: str):
        self.username = username

async def get_current_user(token: str = Depends(authenticate)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data

# Robot direction move
# Enum for robot directions
class Direction(str, Enum):
    forward = "forward"
    backward = "backward"
    left = "left"
    right = "right"

broker = os.getenv('BROKER')
port = int(os.getenv('PORT'))
topic = os.getenv('TOPIC')
feedback_topic = os.getenv('FEEDBACK_TOPIC', topic)
mqtt_username = os.getenv('MQTT_USERNAME')
mqtt_password = os.getenv('MQTT_PASSWORD')

client_id = f'python-mqtt-{random.randint(0, 1000)}'

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(mqtt.CallbackAPIVersion.VERSION1)
    # set username and password
    client.username_pw_set(mqtt_username, mqtt_password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

# Check status of server
@app.get("/status/")
async def status():
    return {"status": "ok"}

@app.post("/cmd/move/")
async def move_robot(direction: str):
    # Check if the direction is valid
    if direction not in Direction.__members__:
        raise HTTPException(status_code=400, detail="Invalid direction")
    simple_action = direction[0].upper(); # F, B, L, R
    # Move the robot in the specified direction
    controller.send_command(Command("move", simple_action))
    return {"direction": direction}

@app.websocket("/ws")
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

# Flashlight command, on/off
@app.post("/cmd/flashlight/")
async def flashlight(status: str):
    # Check if the status is valid
    if status not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    # Send the flashlight command
    controller.send_command(Command("flashlight", status))
    return {"status": status}

@app.post("/cmd/oxygen/")
async def oxygen(status: str):
    if status not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    controller.send_command(Command("oxygen", status))
    return {"status": status}

@app.post("/cmd/filter/")
async def filter(status: str):
    if status not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    controller.send_command(Command("filter", status))
    return {"status": status}

@app.post("/cmd/capture/jpg")
async def capture_jpg():
    # Send the capture command
    controller.send_command(Command("capture", "jpg"))
    return {"message": "Capturing image in JPG format"}

@app.post("/upload/")
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

# try:
#     controller = RobotController(connect_mqtt(), topic, feedback_topic)
# except Exception as e:
#     print(f"Error initializing the robot controller: {e}")
#     exit(-1)

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
