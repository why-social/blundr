# blundr-frontend

Web frontend for Blundr, built with Next.js, React, and TypeScript. Provides the user interface and real-time media capabilities using mediasoup, styled with Tailwind CSS.

### Requirements

- Node.js 18+ (recommended for Next.js)
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

Start the development server:

```bash
npm run dev
```

The app will be available on port `8000` or the one mentioned in the `.env` file.

### Build

Create a production build:

```bash
npm run build
```

Run the production server locally:

```bash
npm run build
```

### Docker

Build the Docker image:

```bash
docker build -t frontend .
```

Run the container:

```bash
docker run --env-file .env -p <PORT from .env file>:<HOST_PORT> frontend
```

The application will be available at:

```
http://localhost:HOST_PORT
```

### Scripts

Available npm scripts:

- `dev` – Start the development server
- `build` – Build the production application
- `start` – Run the production server
- `lint` - Run ESLint
- `fix` - Automatically fix lint and formatting issues (ESLint + Prettier)
