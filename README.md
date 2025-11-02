# 서버리스 환경에서 Cafe24 인증코드 저장
Cafe24 OAuth 인증 완료 후 리다이렉트되는 콜백 엔드포인트.
쿼리스트링의 code, state를 DB(cafe24.oauth_authorization_codes)에 저장한다.
이 함수만 외부에 공개(API Gateway)되고, 나머지 토큰 발급/재발급은 내부 실행이다.

## 목차
- [아키텍처](##아키텍처)
- [요구 스펙](#요구-스펙)
- [환경 변수](#환경-변수)
- [IAM 권한](#iam-권한)
- [VPC/네트워크](#vpc네트워크)
- [핸들러](#핸들러)
- [배포](#배포)
- [API 사양 (API Gateway)](#api-사양-apigateway)
- [로깅/모니터링](#로깅모니터링)
- [트러블슈팅](#트러블슈팅)

## 아키텍처
 • API Gateway (HTTP/REST) → Lambda(이 함수) → RDS(PostgreSQL)

 • 동일 VPC 내부에서 DB에 접근 (권장)

 • 퍼블릭 노출은 API Gateway만, Lambda는 VPC 내부 동작

## 요구 스펙
•	Python 3.13 (AWS Lambda Runtime)

•	의존성: psycopg[binary]

•	선택: 로컬 테스트용 python-dotenv

•   DB: PostgreSQL 17

•	DB 스키마(예시):

```sql
create schema if not exists cafe24;
create table if not exists cafe24.authorization_codes(
  id bigserial primary key,
  code text not null,
  state text not null,
  created_at timestamptz not null default now()
);
```

## 환경 변수
	•	PGHOST
	•	PGPORT
	•	PGUSER
	•	PGPASSWORD
	•	PGDATABASE
	•	EXPECTED_STATE_SECRET

## IAM 권한
	•	AWSLambdaVPCAccessExecutionRole
	•	secretsmanager:GetSecretValue (시크릿 사용 시)
	•	ec2:CreateNetworkInterface, ec2:DescribeNetworkInterfaces, ec2:DeleteNetworkInterface (VPC 사용 시)
	•	RDS는 DB 계정으로 권한 제어

## VPC/네트워크
	•	Lambda: 프라이빗 서브넷 (RDS와 동일 VPC)
	•	라우팅: 외부 인터넷 필요 없음 (Cafe24 호출 안 함)
	•	SG:
	•	Lambda SG → RDS SG(TCP 5432) 인바운드 허용
	•	Lambda SG 아웃바운드 all

## 핸들러
	•	파일: lambda_callback.py
	•	함수: callback_handler
	•	Lambda 설정: lambda_callback.callback_handler

## 배포
```bash
pip install --platform manylinux2014_aarch64 --only-binary=:all: \
  --implementation cp --python-version 3.13 \
  --target ./package psycopg[binary]

cp -r package/* .
zip -r deploy.zip *.py
aws lambda update-function-code --function-name <FUNC_NAME> --zip-file fileb://deploy.zip
```

[ARM64 환경 패키지 빌드](./arm64-package-build-guide.md)


## API 사양 (API Gateway)
	•	GET /oauth/callback?code=...&state=...
	•	응답:
```json
{ "ok": true, "message": "Saved", "id": 123 }
```

예시:
```bahs
curl "https://{apiId}.execute-api.ap-northeast-2.amazonaws.com/oauth/callback?code={code}&state={state}"
```

## 로깅/모니터링
	•	CloudWatch Logs: code/state 저장 성공/실패 로그
	•	메트릭: 호출 수, 에러 수, p50/p95

## 트러블슈팅
	•	500 + ECONNREFUSED: VPC/SG 확인
	•	400 Missing params: API 호출 파라미터 검증
	•	RDS 연결 끊김: DB 커넥션 재시도/타임아웃 설정

