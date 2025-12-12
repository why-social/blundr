# local-ollama
Runs an ollama server locally and exposes it to a domain through a cloudflare tunnel.

## Prerequisites
- Have a cloudflare tunnel set up
- Save the tunnel token to the `.env` file as `TUNNEL_TOKEN`

## Run
_From local-ollama/_:

```docker compose up```
