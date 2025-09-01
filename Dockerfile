FROM python:3.13-slim

# 필요한 런타임 라이브러리 + 유틸 + 폰트
RUN apt-get update && \
    apt-get install -y \
        unzip \
        ca-certificates \
        wget \
        curl \
        gnupg \
        xdg-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install -r requirements.txt

# 소스 코드 복사 (모든 모듈 포함)
COPY main.py .
COPY appraiser/ ./appraiser/
COPY db/ ./db/
COPY helper/ ./helper/
COPY tests/ ./tests/

# 컨테이너 실행 시 main.py 실행
CMD ["python", "main.py"]
