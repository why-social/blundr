# Original Author: Razvan Albu
# Source: https://git.chalmers.se/courses/dit826/2025/team2
# License: MIT

FROM node:24-slim

RUN apt-get update && \
    apt-get install -y \
        ffmpeg \
        python3 \
        python3-pip \
        build-essential \
        pkg-config \
        libssl-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/chatroom
COPY . .

ARG FER_URL
ARG VER_URL
ARG MEDIASOUP_ANNOUNCED_IP

ENV FER_URL=${FER_URL}
ENV VER_URL=${VER_URL}
ENV MEDIASOUP_ANNOUNCED_IP=${MEDIASOUP_ANNOUNCED_IP}

# needed for the tls mounts in the vm
RUN mkdir -p /etc/tls
VOLUME ["/etc/tls"]
RUN mkdir -p /archive
VOLUME ["/archive"]

RUN npm install
RUN npm run build

CMD ["npm", "run", "start"]
