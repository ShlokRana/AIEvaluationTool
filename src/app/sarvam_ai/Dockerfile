FROM python:3.11-slim
# FROM nvidia/cuda:12.6.3-cudnn-devel-ubuntu22.04

# ENV DEBIAN_FRONTEND=noninteractive

# RUN apt-get update && apt-get install -y \
#     python3.11 \
#     python3.11-dev \
#     python3-pip \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app
RUN mkdir -p /models
WORKDIR /app

COPY requirements.txt /app

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 16000

CMD ["python3", "/app/main.py"]

