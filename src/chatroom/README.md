# blundr-chatroom

Backend service that provides real-time video capabilities and call room matching for Blundr. Built with Node.js, TypeScript, Express, and mediasoup; communicates with clients over WebSockets.

### Requirements

- Node.js 18+ (recommended for Next.js)
- A system capable of running mediasoup (Linux recommended)
- Docker (optional, for containerized usage)

### Setup

Install dependencies:

```bash
npm install
```

### Environment Variables

The project uses environment variables for configuration. An example file is provided; copy it and adjust values as needed:

```bash
cp example.env .env
```

> Environment variables are automatically loaded using dotenv-cli.

### Development

Start the development server with hot reloading:

```bash
npm run dev
```

This runs the server directly from TypeScript using `ts-node` and restarts on file changes.

### Build

Compile TypeScript to JavaScript:

```bash
npm run build
```

The compiled output will be generated in the `dist/` directory.

### Production

Start the production server:

```bash
npm run start
```

By default, this runs:

```bash
node dist/server.js
```

### Docker

Build the Docker image:

```bash
docker build -t chatroom .
```

Run the container:

```bash
docker run --env-file .env -p <PORT from .env file>:<HOST_PORT> chatroom
```

### Scripts

Available npm scripts:

- `dev` – Start the development server
- `build` – Compile TypeScript to JavaScript
- `start` – Start the compiled server
