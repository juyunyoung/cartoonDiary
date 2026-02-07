import boto3
import json
import base64
import os
from typing import Optional

class NovaService:
    def __init__(self):
        # Ensure credentials are in environment or ~/.aws/credentials
        self.region_name = os.getenv('AWS_REGION', 'us-east-1')
        self.client = boto3.client('bedrock-runtime', region_name=self.region_name)
        # Using Nova Canvas model ID
        self.model_id = 'amazon.nova-canvas-v1:0'

    def generate_image(self, prompt: str, negative_prompt: str = "") -> Optional[bytes]:
        """
        Generates an image using AWS Nova Canvas via Bedrock.
        Returns the image bytes or None if failed.
        """
        # Payload structure for Amazon Nova Canvas (approximate based on Titan/Standard)
        # Adjust if specific Nova documentation reveals differences.
        payload = {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": prompt,
                "negativeText": negative_prompt
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "height": 1024,
                "width": 1024,
                "cfgScale": 8.0,
                "seed": 0 # 0 for random seed usually
            }
        }

        try:
            print(f"Invoking {self.model_id} with prompt: {prompt}")
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(payload),
                accept="application/json",
                contentType="application/json"
            )
            
            response_body = json.loads(response.get("body").read())
            
            # Response handling
            if "images" in response_body:
                # Titan/Nova usually return base64 encoded strings in 'images' array
                base64_image = response_body["images"][0]
                return base64.b64decode(base64_image)
            elif "artifacts" in response_body:
                 # Stability AI models return 'artifacts'
                base64_image = response_body["artifacts"][0].get("base64")
                return base64.b64decode(base64_image)
            else:
                print(f"Unexpected response structure: {response_body.keys()}")
                return None

        except Exception as e:
            print(f"Error calling Nova Canvas: {str(e)}")
            return None

# Singleton instance
try:
    nova_service = NovaService()
except Exception as e:
    print(f"Failed to initialize NovaService: {e}")
    nova_service = None
