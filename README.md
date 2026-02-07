# Cartoon Diary

## 🚀 시작하기 (Getting Started)

### 1. Frontend (cdiary-fe) 실행

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

### 2. Backend (cdiary-be) 실행

새 터미널 탭을 열고(Command + T) 다음 명령어를 입력하세요:

```bash
# 1. 백엔드 폴더로 이동
cd cdiary-be

# 2. 가상환경 생성 (최초 1회, 권장)
python3 -m venv venv
source venv/bin/activate

# 3. 의존성 설치 (최초 1회)
pip install -r requirements.txt

# 4. 서버 실행
uvicorn main:app --reload
```

백엔드 API는 `http://localhost:8000`에서 실행됩니다.
- API 문서 확인: `http://localhost:8000/docs`

---

## 📂 프로젝트 구조

- **cdiary-fe**: React + TypeScript + Vite 기반 웹 프론트엔드
- **cdiary-be**: FastAPI 기반 백엔드 API
