import json
from lambda_function import lambda_handler

# API Gateway HTTP API가 Lambda로 넘겨주는 형태랑 비슷하게 구성
mock_event = {
    "queryStringParameters": {
        "code": "TESTCODE123",
        "state": "dev-secret-abc",
        "mall_id": "mallA"
    }
}

response = lambda_handler(mock_event, None)
print("Lambda response status:", response["statusCode"])
print("Lambda response body:", response["body"])
print("Full response:", json.dumps(response, indent=2, default=str))