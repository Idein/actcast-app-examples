ARG PYTHON_VERSION=3.12.0

FROM --platform=linux/arm/v7 python:${PYTHON_VERSION}-slim-bullseye as builder

# Upgrade pip
RUN python -m pip install --upgrade pip

# numpy と pillow のインストール
# 典型的なアプリではこの2つが必要になります。
RUN apt update
RUN apt install -y build-essential cmake ninja-build
# Build numpy as a wheel
RUN python -m pip wheel --wheel-dir=/root/wheels numpy
# Build pillow as a wheel
RUN apt-get install -y libjpeg-dev libfreetype6-dev
# actfw requires pillow<9.0.0,>=8.0.0
RUN python -m pip wheel --wheel-dir=/root/wheels 'pillow<9.0.0,>=8.0.0'

RUN python -m pip install --no-index --find-links=/root/wheels numpy pillow

# 他のパッケージをインストールしたいときは以降に追記してください。
# インストールしたパッケージに実行時の依存がある場合は Stage 2 で依存パッケージをインストールしてください。
# 例: scipy の場合
# RUN apt install -y pkg-config gfortran libopenblas-dev
# RUN python -m pip wheel --wheel-dir=/root/wheels scipy
# RUN python -m pip install --no-index --find-links=/root/wheels scipy

# Stage 2: Final image
FROM idein/actcast-rpi-app-base:bullseye-1

# Set environment variable for Python
ENV PATH /usr/local/bin:$PATH

# python環境を引っこ抜いてくる
COPY --from=builder /usr/local/lib/ /usr/local/lib/
COPY --from=builder /usr/local/include/ /usr/local/include/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# RUNTIME dependency
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libexpat1 \
    # pillow
    libfreetype6 libjpeg62-turbo \
    # 例: scipy をインストールする場合は以下を追加
    # libopenblas-base \
    && apt-get clean \
    && apt-get autoclean \
    && apt-get autoremove -y \
    && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*
