FROM node:24-slim

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/chatroom
COPY . .

RUN npm install
RUN npm run build

ENV PORT=3000
EXPOSE $PORT

CMD ["npm", "run", "start"]
