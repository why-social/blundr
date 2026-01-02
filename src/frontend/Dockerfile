# Original Author: Razvan Albu
# Source: https://git.chalmers.se/courses/dit826/2025/team2
# License: MIT

FROM node:24-slim

RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/frontend
COPY . .

ARG CHATROOM_URL
ARG CHATROOM_WS_URL
ARG ANALYSIS_IP_ADDRESS

ENV CHATROOM_URL=$CHATROOM_URL
ENV NEXT_PUBLIC_CHATROOM_WS_URL=$CHATROOM_WS_URL
ENV ANALYSIS_IP_ADDRESS=$ANALYSIS_IP_ADDRESS

RUN npm install
RUN npm run build

CMD ["npm", "run", "start"]
