from dotenv import load_dotenv
load_dotenv(".env.local") 

import json
from lambda_function import lambda_handler

# ALB or API Gateway로 Callback 받은 값을 시뮬레이션하는 테스트 코드
mock_event = {
    "queryStringParameters": {
        "code": "TESTCODE123",
        "state": "devsecret",
        "mall_id": "testmall"
    }
}

response = lambda_handler(mock_event, None)
print("Lambda response status:", response["statusCode"])
print("Lambda response body:", response["body"])
print("Full response:", json.dumps(response, indent=2, default=str))