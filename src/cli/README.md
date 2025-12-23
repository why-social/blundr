# blundr-cli

Command-line tool for managing the Facial Emotion Recognition Service: uploading data, training models, and selecting the active model.

### Requirements

- Go 1.21+ (for building)
- Google Cloud SDK (gcloud) installed and authenticated

### Build

Build locally:

```bash
go build -o blundr-cli main.go
```

Build for all platforms:

```bash
chmod +x build.sh
./build.sh
```

### Usage

Authenticate with Google Cloud:

```bash
gcloud auth login
gcloud config set project blundr
```

> For this service to work, you need a Google account that has access to the Google Cloud platform.

Pass `--help` as argument to get usage examples and available commands.

```bash
./blundr-cli --help
```
