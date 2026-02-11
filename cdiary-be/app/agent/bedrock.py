from __future__ import annotations

import base64
import json
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError


AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

NOVA_TEXT_MODEL_ID = os.getenv("NOVA_TEXT_MODEL_ID", "amazon.nova-lite-v1:0")
NOVA_IMAGE_MODEL_ID = os.getenv("NOVA_IMAGE_MODEL_ID", "amazon.nova-canvas-v1:0")

S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_PREFIX = os.getenv("S3_PREFIX", "cartoon-diary").strip("/")
S3_PUBLIC = os.getenv("S3_PUBLIC", "false").lower() == "true"
S3_PRESIGN_EXPIRE_SECONDS = int(os.getenv("S3_PRESIGN_EXPIRE_SECONDS", "3600"))


def _bedrock_runtime():
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)


def _s3():
    return boto3.client("s3", region_name=AWS_REGION)


def invoke_text_model(prompt: str, temperature: float = 0.3) -> str:
    """
    Nova Text Model Invocation
    """
    br = _bedrock_runtime()
    body = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {
            "temperature": temperature,
            "maxTokens": 2000,
        },
    }
    
    # Nova Lit/Pro uses Converse API or specific payload. 
    # Using Converse API structure (messages) in body for invoke_model if model supports it, 
    # OR better: use converse() method if boto3 supports it. 
    # User's test.py used client.converse(). Let's use that if possible, but here we use invoke_model with body.
    # Nova models usually require "messages" in body for invoke_model.
    
    try:
        resp = br.invoke_model(
            modelId=NOVA_TEXT_MODEL_ID,
            body=json.dumps(body),
            accept="application/json",
            contentType="application/json",
        )
        data = json.loads(resp["body"].read())
        
        # Standard Nova response parsing
        # Output is usually in data['output']['message']['content'][0]['text']
        return data["output"]["message"]["content"][0]["text"]
        
    except Exception:
        # Fallback for older/different models or if payload structure is different
        # Retry with older "inputText" format if needed, but Nova uses "messages"
        raise


@dataclass
class ImageInvokeResult:
    s3_key: str
    s3_uri: str
    url: str  # public url or presigned url
    raw: Dict[str, Any]


def invoke_image_model_to_s3(
    prompt: str,
    job_id: str,
    cut_index: int,
    width: int = 1024,
    height: int = 1024,
) -> ImageInvokeResult:
    """
    Bedrock Image Model -> S3
    """
    # If S3_BUCKET is not set, we cannot upload. For now, raise error or mock?
    # The sample code raises RuntimeError.

    
    br = _bedrock_runtime()
    print(prompt)
    body = {
        "taskType": "TEXT_IMAGE",
        "textToImageParams": {
            "text": prompt
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "width": width,
            "height": height,
            "cfgScale": 8.0
        }
    }
    
    resp = br.invoke_model(
        modelId=NOVA_IMAGE_MODEL_ID,
        body=json.dumps(body),
        accept="application/json",
        contentType="application/json",
    )
    raw = json.loads(resp["body"].read())

    b64_list = _extract_base64_candidates(raw)
    if not b64_list:
        raise ValueError(f"No base64 image found in response. Keys: {list(raw.keys())}")

    img_bytes = base64.b64decode(b64_list[0])
    ext = "png" # define default
    
    # User's local save logic
    print(f"Saving image locally to image_test/{job_id}_{cut_index}.png...")
    os.makedirs("image_test", exist_ok=True)
    local_path = f"image_test/{job_id}_{cut_index}.png"
    with open(local_path, "wb") as f:
        f.write(img_bytes)

    file_id = uuid.uuid4().hex
    s3_key = f"{S3_PREFIX}/jobs/{job_id}/cut-{cut_index:02d}-{file_id}.{ext}"
    
    if S3_BUCKET:
        _upload_bytes_to_s3(S3_BUCKET, s3_key, img_bytes, "image/png")
        s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
        url = _make_access_url(S3_BUCKET, s3_key)
    else:
        # Fallback if no S3
        s3_uri = f"file://{os.path.abspath(local_path)}"
        url = s3_uri  # Use file URI as URL

    return ImageInvokeResult(
        s3_key=s3_key,
        s3_uri=s3_uri,
        url=url,
        raw=raw,
    )


def _upload_bytes_to_s3(bucket, key, data, content_type):
    s3 = _s3()
    extra_args = {"ContentType": content_type}
    if S3_PUBLIC:
        extra_args["ACL"] = "public-read"
    
    s3.put_object(Bucket=bucket, Key=key, Body=data, **extra_args)


def _make_access_url(bucket, key):
    if S3_PUBLIC:
        return f"https://{bucket}.s3.amazonaws.com/{key}"
    
    s3 = _s3()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=S3_PRESIGN_EXPIRE_SECONDS
    )


def _extract_base64_candidates(raw: Any) -> List[str]:
    candidates = []
    
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k.lower() in ("base64", "images", "bytes"):
                    if isinstance(v, str):
                        candidates.append(v)
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, str):
                                candidates.append(item)
                walk(v)
        elif isinstance(x, list):
            for i in x:
                walk(i)
                
    walk(raw)
    return candidates
