FROM node:24-slim

RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/frontend
COPY . .

# NEXT_PUBLIC_* variables are needed at build time
ARG NEXT_PUBLIC_CHATROOM_URL
ARG NEXT_PUBLIC_CHATROOM_WS_URL

ENV NEXT_PUBLIC_CHATROOM_URL=$NEXT_PUBLIC_CHATROOM_URL
ENV NEXT_PUBLIC_CHATROOM_WS_URL=$NEXT_PUBLIC_CHATROOM_WS_URL

RUN npm install
RUN npm run build

CMD ["npm", "run", "start"]
