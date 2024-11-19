import os
import uuid

# warning; this is a temporary solution to suppress warnings
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import boto3
import uvicorn
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jose import JWTError

from .routers import auth_router, commands_router, index_router
from .routers.auth import security

warnings.filterwarnings("ignore")


app = FastAPI()


# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(commands_router, prefix="/cmd")
app.include_router(auth_router, prefix="/auth")
app.include_router(index_router)


def init():
    from .controller.robot import RobotController
    from .services.mqtt import connect_mqtt, feedback_topic, topic

    try:
        controller = RobotController(connect_mqtt(), topic, feedback_topic)
        print("Robot controller initialized")
    except Exception as e:
        print(f"Error initializing the robot controller: {e}")

init()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
