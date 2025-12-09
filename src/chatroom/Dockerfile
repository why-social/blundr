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

ARG MEDIASOUP_ANNOUNCED_IP
ENV MEDIASOUP_ANNOUNCED_IP=${MEDIASOUP_ANNOUNCED_IP}

RUN npm install
RUN npm run build

CMD ["npm", "run", "start"]
