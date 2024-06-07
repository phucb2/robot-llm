from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from jose import JWTError, jwt
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
