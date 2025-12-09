FROM node:24-slim

RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/frontend
COPY . .

RUN npm install
RUN npm run build

CMD ["npm", "run", "start"]
