# 1. 베이스 이미지 버전을 확실히 명시
FROM python:3.11-slim-bookworm

WORKDIR /app

# 2. 기존 소스 리스트 완전히 삭제 후 다시 생성 (안전한 공식 주소 사용)
RUN rm -rf /etc/apt/sources.list.d/* && \
    echo "deb http://deb.debian.org/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list

# 3. DNS 문제일 수 있으므로 다시 업데이트 시도
RUN apt-get update --fix-missing && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8080

# 환경변수 설정 (기본값)
ENV PYTHONUNBUFFERED=1

# Uvicorn으로 FastAPI 애플리케이션 실행
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
