ARG PYTHON_VERSION=3.12.1

FROM --platform=linux/arm/v7 python:${PYTHON_VERSION}-slim-bullseye as base

# Stage 2: Final image
FROM idein/actcast-rpi-app-base:bullseye-1

# Set environment variable for Python
ENV PATH /usr/local/bin:$PATH

# python環境を引っこ抜いてくる (仮)
COPY --from=base /usr/local/lib/ /usr/local/lib/
COPY --from=base /usr/local/include/ /usr/local/include/
COPY --from=base /usr/local/bin/ /usr/local/bin/

RUN apt update && apt install -y \
    # pip install に必要なパッケージ
    libexpat1-dev \
    # numpy のビルドに必要で、実行時には不要なパッケージ
    build-essential cmake ninja-build \
    # 実行時にも必要なパッケージ
    libjpeg-dev libfreetype6-dev && \
    # Upgrade pip
    python -m pip install --upgrade pip && \
    # numpy と pillow のインストール
    # 典型的なアプリではこの2つが必要になります。
    python -m pip install numpy 'pillow<9.0.0,>=8.0.0' && \
    # 実行時に不要なファイルを削除
    apt purge -y --auto-remove build-essential cmake ninja-build && \
    # キャッシュを削除
    apt clean && \
    rm -rf /var/lib/apt/lists/*
