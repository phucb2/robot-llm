from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
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

app = FastAPI()

# Load environment variables from .env file
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

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

@app.post("/token/")
async def login_for_access_token(credentials: HTTPBasicCredentials = Depends(security)):
    authenticate(credentials)
    data = {
        "sub": credentials.username,
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    token = jwt.encode(data, "secret")
    return {"access_token": token, "token_type": "bearer"}

from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, FastAPI, HTTPException, status
from jose import JWTError, jwt


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
from enum import Enum

class Direction(str, Enum):
    forward = "forward"
    backward = "backward"
    left = "left"
    right = "right"
    
broker = os.getenv('BROKER')
port = int(os.getenv('PORT'))
topic = os.getenv('TOPIC')
mqtt_username = os.getenv('MQTT_USERNAME')
mqtt_password = os.getenv('MQTT_PASSWORD')
print(f"Broker: {broker}, Port: {port}, Topic: {topic}, Username: {mqtt_username}, Password: {mqtt_password}")

import random
from paho.mqtt import client as mqtt_client
import paho.mqtt.client as mqtt

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

# Command DTO (Data Transfer Object)
class Command:
    def __init__(self, command: str, value: str):
        self.command = command
        self.value = value

import json

class RobotController:
    def __init__(self):
        self.client = connect_mqtt()
        # check if the client is connected otherwise exit
        self.client.loop_start()
    
    def send_command(self, direction: Direction):
        command = Command("move", direction.value)
        # convert command to json and publish to the topic
        data = json.dumps(command.__dict__)
        self.client.publish(topic, data)
    

@app.post("/cmd/move/")
async def move_robot(direction: str):
    # Check if the direction is valid
    if direction not in Direction.__members__:
        raise HTTPException(status_code=400, detail="Invalid direction")
    # Move the robot in the specified direction
    controller.send_command(Direction(direction)) 
    return {"direction": direction}

# Flashlight command, on/off
@app.post("/cmd/flashlight/")
async def flashlight(status: str):
    # Check if the status is valid
    if status not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    # Send the flashlight command
    controller.send_command(Command("flashlight", status))
    return {"status": status}

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

controller = RobotController()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
