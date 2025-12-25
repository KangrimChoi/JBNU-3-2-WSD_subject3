FROM python:3.11-slim-bookworm

WORKDIR /app

# 1. 기존 소스 리스트를 카카오 미러로 강제 교체 (HTTP 사용)
RUN rm -rf /etc/apt/sources.list.d/* && \
    echo "deb http://mirror.kakao.com/debian bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://mirror.kakao.com/debian bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://mirror.kakao.com/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list

# 2. 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
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
