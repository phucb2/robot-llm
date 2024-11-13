import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import boto3
import uvicorn
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv
from fastapi import Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt

from ..configs import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET_NAME, AWS_REGION, USERNAME, PASSWORD
from fastapi import APIRouter, HTTPException, Depends, status
router = APIRouter()

security = HTTPBasic()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def authenticate(credentials: HTTPBasicCredentials):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
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

class TokenData:
    def __init__(self, username: str):
        self.username = username

@router.post("/token/")
async def login_for_access_token(credentials: HTTPBasicCredentials = Depends(security)):
    authenticate(credentials)
    data = {
        "sub": credentials.username,
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    token = jwt.encode(data, "secret")
    return {"access_token": token, "token_type": "bearer"}