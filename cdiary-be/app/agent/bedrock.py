from __future__ import annotations

import base64
import json
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import random
import boto3
from botocore.exceptions import ClientError


AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

NOVA_TEXT_MODEL_ID = os.getenv("NOVA_TEXT_MODEL_ID", "amazon.nova-lite-v1:0")
NOVA_IMAGE_MODEL_ID = os.getenv("NOVA_IMAGE_MODEL_ID", "amazon.nova-canvas-v1:0")

S3_BUCKET = os.getenv("S3_BUCKET", "cartoon-diary")
S3_PREFIX = os.getenv("S3_PREFIX", "temp").strip("/")
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
    
    try:
        resp = br.invoke_model(
            modelId=NOVA_TEXT_MODEL_ID,
            body=json.dumps(body),
            accept="application/json",
            contentType="application/json",
        )
        data = json.loads(resp["body"].read())
        
        # Standard Nova response parsing
        return data["output"]["message"]["content"][0]["text"]
        
    except Exception:
        raise


@dataclass
class ImageInvokeResult:
    s3_key: str
    s3_uri: str
    url: str  # public url or presigned url
    raw: Dict[str, Any]
    img_bytes: Optional[bytes] = None


def generate_text_to_image(cut_prompt: str, seed: int = 42) -> tuple[Dict[str, Any], bytes]:
    """
    Generate image using Text-to-Image (Cut 1)
    """
    client = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")
    model_id = "amazon.nova-canvas-v1:0"
    
    # 4-Panel Strip Constraints
    text = (
            "Clean cartoon webtoon style. Gentle lighting. Soft shading. "
            "No text of any kind. No letters, numbers, logos, watermarks. No speech bubbles. "
            "Keep the main character consistent in all images (same face, same hairstyle, same outfit). "
            f"{cut_prompt}" 
        )
    negative = (
        "text, letters, words, typography, watermark, logo, signature, "
        "speech bubble, thought bubble, caption, subtitle, "
        "photorealistic, realistic, 3d, photo, render, "
        "blurry, low quality, noise, artifacts, "
        "harsh shadows, high contrast, neon, oversaturated, "
        "extra characters, crowd, multiple views, split screen, character sheet, reference sheet"
    )
    
    body = {
        "taskType": "TEXT_IMAGE",
        "textToImageParams": {
            "text": text,
            "negativeText": negative
        },
        "imageGenerationConfig": {
            "quality": "standard",
            "numberOfImages": 1,
            "height": 1024,
            "width": 1024,
            "cfgScale": 8.5,
            "seed": seed
        }
    }

    print(f"Invoking {model_id} (TEXT_IMAGE) with Body='{text}'...")

    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
        accept="application/json",
        contentType="application/json"
    )
    
    raw = json.loads(response["body"].read())
    b64_list = _extract_base64_candidates(raw)
    if not b64_list:
        raise ValueError(f"No base64 image found in response. Keys: {list(raw.keys())}")

    img_bytes = base64.b64decode(b64_list[0])
    return raw, img_bytes


def generate_image_variation(cut_prompt: str, ref_image: bytes, seed: int = 42) -> tuple[Dict[str, Any], bytes]:
    """
    Generate image using Image Variation (Cuts 2-4)
    """
    client = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")
    model_id = "amazon.nova-canvas-v1:0"
    
    # Text prompt is still used in variation to guide the content
    b64_img = base64.b64encode(ref_image).decode("utf-8")
    
    body = {
        "taskType": "IMAGE_VARIATION",
        "imageVariationParams": {
            "text": cut_prompt, 
            "images": [b64_img],
            "similarityStrength": 0.85 
        },            
        "imageGenerationConfig": {
            "quality": "standard",
            "numberOfImages": 1,
            "height": 1024,
            "width": 1024,
            "cfgScale": 8.5,
            "seed": seed
        }
    }
    
    print(f"Invoking {model_id} (IMAGE_VARIATION)...")

    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
        accept="application/json",
        contentType="application/json"
    )
        
    raw = json.loads(response["body"].read())
    b64_list = _extract_base64_candidates(raw)
    if not b64_list:
        raise ValueError(f"No base64 image found in response. Keys: {list(raw.keys())}")

    img_bytes = base64.b64decode(b64_list[0])
    return raw, img_bytes


def invoke_image_model_to_s3(
    cut_prompt: str,
    job_id: str,
    cut_index: int,
    ref_image: Optional[bytes] = None
) -> ImageInvokeResult:
    """
    Bedrock Image Model -> S3
    """
    
    if cut_index == 1 or ref_image is None:
        raw, img_bytes = generate_text_to_image("", cut_prompt)
    else:
        raw, img_bytes = generate_image_variation(cut_prompt, ref_image)
    
    # Save image (S3 or Local) using helper
    s3_key, url = save_cut_image(job_id, cut_index, img_bytes)

    return ImageInvokeResult(
        s3_key=s3_key,
        s3_uri=f"s3://{S3_BUCKET}/{s3_key}" if S3_BUCKET else url,
        url=url,
        raw=raw,
        img_bytes=img_bytes
    )


def save_cut_image(job_id: str, cut_index: int, img_bytes: bytes) -> tuple[str, str]:
    """
    Saves image bytes to S3 or local disk.
    Returns (s3_key, url)
    """
    ext = "png"
    file_id = uuid.uuid4().hex
    s3_key = f"{S3_PREFIX}/jobs/{job_id}/cut-{cut_index:02d}-{file_id}.{ext}"
    
    if S3_BUCKET:
        upload_bytes_to_s3(S3_BUCKET, s3_key, img_bytes, "image/png")
        s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
        url = make_access_url(S3_BUCKET, s3_key)
    else:
        # Fallback if no S3 (Local Save)
        os.makedirs("image_test", exist_ok=True)
        local_path = f"image_test/{job_id}_{cut_index}.png"
        print(f"Saving image locally to {local_path}...")
        with open(local_path, "wb") as f:
            f.write(img_bytes)
            
        s3_uri = f"file://{os.path.abspath(local_path)}"
        url = s3_uri
        
    return s3_key, url


def save_profile_image(user_id: str, img_bytes: bytes) -> tuple[str, str]:
    """
    Saves profile image to S3 or local disk.
    Path: profile/{user_id}/profile.png
    Returns (s3_key, url)
    """
    s3_key = f"profile/{user_id}/profile.png"
    
    if S3_BUCKET:
        upload_bytes_to_s3(S3_BUCKET, s3_key, img_bytes, "image/png")
        s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
        url = make_access_url(S3_BUCKET, s3_key)
    else:
        # Fallback if no S3 (Local Save)
        os.makedirs(f"image_test/profile/{user_id}", exist_ok=True)
        local_path = f"image_test/profile/{user_id}/profile.png"
        print(f"Saving profile image locally to {local_path}...")
        with open(local_path, "wb") as f:
            f.write(img_bytes)
            
        url = f"file://{os.path.abspath(local_path)}"
        
    return s3_key, url


def upload_bytes_to_s3(bucket, key, data, content_type):
    s3 = _s3()
    extra_args = {"ContentType": content_type}
    if S3_PUBLIC:
        extra_args["ACL"] = "public-read"
    
    s3.put_object(Bucket=bucket, Key=key, Body=data, **extra_args)


def make_access_url(bucket, key):
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
