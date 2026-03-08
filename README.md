# Cartoon Diary

AI-powered cartoon diary application based on AWS Nova and React.

## 🚀 시작하기 (Getting Started)

### 사전 요구사항 (Prerequisites)
- Node.js 18+
- Python 3.12+
- AWS 계정 (Nova Canvas 모델 사용 권한 필요)

---

### 1. 환경 변수 설정 (AWS Configuration)

백엔드에서 이미지 생성을 위해 AWS 자격 증명이 필요합니다.
터미널에서 다음 명령어로 설정하거나 `.env` 파일을 생성하세요.

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

---

### 2. Frontend (cdiary-fe) 실행

터미널을 열고 다음 명령어를 순서대로 입력하세요:

```bash
# 1. 프론트엔드 폴더로 이동
cd cdiary-fe

# 2. 의존성 설치 (최초 1회)
npm install

# 3. 개발 서버 실행
npm run dev
```

브라우저에서 `http://localhost:5173` 주소로 접속하면 화면을 볼 수 있습니다.

---

### 3. Backend (cdiary-be) 실행

새 터미널 탭을 열고(Command + T) 다음 명령어를 입력하세요:

```bash
# 1. 백엔드 폴더로 이동
cd cdiary-be

# 2. 가상환경 생성 (최초 1회, 권장)
python3 -m venv venv
source ../.venv/bin/activate

# 3. 의존성 설치 (최초 1회)
# (주의: boto3와 aiobotocore 충돌 방지를 위해 requirements.txt 사용 필수)
pip install -r requirements.txt

# 4. 서버 실행 (FastAPI)
python main.py
# 또는
# uvicorn main:app --host 0.0.0.0 --port 5050 --reload
```

백엔드 API는 `http://localhost:5050`에서 실행됩니다.
API 문서는 `http://localhost:5050/docs`에서 확인할 수 있습니다.

---

## ☁️ 배포 (Deployment)

### Frontend (AWS Amplify)
`cdiary-fe/amplify.yml` 파일이 설정되어 있습니다.
- Build: `npm run build`
- Output: `dist`

### Backend (AWS App Runner)
`cdiary-be/apprunner.yaml` 파일이 설정되어 있습니다.
- Runtime: Python 3
- Command: `python -m uvicorn main:app --host 0.0.0.0 --port 5050`
