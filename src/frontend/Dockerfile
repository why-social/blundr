FROM node:24-slim

RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/frontend
COPY . .

ARG CHATROOM_URL
ARG CHATROOM_WS_URL

ENV CHATROOM_URL=$CHATROOM_URL
ENV NEXT_PUBLIC_CHATROOM_WS_URL=$CHATROOM_WS_URL

RUN npm install
RUN npm run build

CMD ["npm", "run", "start"]
