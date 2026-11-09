import os
import time
import boto3
from botocore.config import Config

ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "admin")
SECRET_KEY = os.getenv("S3_SECRET_KEY", "seminario123")
BUCKET = os.getenv("S3_BUCKET", "datalake")

def cliente_s3():
    ultimo_erro = None
    for _ in range(30):
        try:
            s3 = boto3.client(
                "s3",
                endpoint_url=ENDPOINT,
                aws_access_key_id=ACCESS_KEY,
                aws_secret_access_key=SECRET_KEY,
                region_name="us-east-1",
                config=Config(s3={"addressing_style": "path"})
            )
            s3.list_buckets()
            return s3
        except Exception as exc:
            ultimo_erro = exc
            time.sleep(2)
    raise RuntimeError(f"Não foi possível conectar ao armazenamento: {ultimo_erro}")

def garantir_bucket(s3):
    existentes = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    if BUCKET not in existentes:
        s3.create_bucket(Bucket=BUCKET)
        print(f"Bucket criado: {BUCKET}")
    else:
        print(f"Bucket já existe: {BUCKET}")
