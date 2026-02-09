import boto3
import json

def main():
    client = boto3.client(service_name="bedrock-runtime")

    messages = [
        {"role": "user", "content": [{"text": "Write a short poem"}]},
    ]

    try:
        model_response = client.converse(
            modelId="us.amazon.nova-lite-v1:0", 
            messages=messages
        )

        print("\n[Full Response]")
        print(json.dumps(model_response, indent=2, default=str))

        print("\n[Response Content Text]")
        print(model_response["output"]["message"]["content"][0]["text"])
        
    except Exception as e:
        print(f"Error invoking Bedrock model: {e}")

if __name__ == "__main__":
    main()