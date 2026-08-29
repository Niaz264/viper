FROM python:3.10-slim-bookworm

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        wget \
        curl \
        ffmpeg \
        ca-certificates \
        tzdata \
        build-essential \
        libpq-dev \
        qbittorrent-nox \
        aria2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /usr/src/app/start.sh

CMD ["bash", "/usr/src/app/start.sh"]
