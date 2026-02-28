FROM python:3.11-slim

# 시스템 최적화
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 의존성 먼저 복사 (캐시 최적화)
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# 소스 전체 복사
COPY . .

WORKDIR /app/cdiary-be

EXPOSE 5050

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5050"]
