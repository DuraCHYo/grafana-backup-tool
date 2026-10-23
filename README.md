# 📊 Grafana Backup Tool (Modern Fork)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Grafana Support](https://img.shields.io/badge/grafana-v9.4%2B%20--%20v13.x-orange.svg)](https://grafana.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful Python-based tool to back up and restore Grafana settings via API.  
This is a **maintained fork** of [ysde/grafana-backup-tool](https://github.com/ysde/grafana-backup-tool), rewritten for modern Grafana versions.

> [!IMPORTANT]
> **Why use this fork?**
> Unlike the original tool, this version fully supports **Grafana 13.x** (and 9.4+) and fixes the critical bugs that have existed since Grafana 8.0.0.
> Version **2.0.0** is a complete rewrite: the legacy v1 engine has been removed, and all components are now backed up and restored through a single async registry-driven engine.

---

## 📑 Table of Contents
- [📊 Grafana Backup Tool (Modern Fork)](#-grafana-backup-tool-modern-fork)
  - [📑 Table of Contents](#-table-of-contents)
  - [🚀 Quick Start](#-quick-start)
  - [✨ Key Improvements](#-key-improvements)
  - [📦 Supported Components](#-supported-components)
  - [⚙️ Configuration](#️-configuration)
    - [Environment Variables](#environment-variables)
    - [Configuration File](#configuration-file)
  - [🖥 CLI Reference](#-cli-reference)
  - [🗄 Backup Format & Compatibility](#-backup-format--compatibility)
  - [🛠 Installation](#-installation)
    - [Using uv](#using-uv)
    - [🐳 Docker examples](#-docker-examples)
      - [Save to hostdir](#save-to-hostdir)
      - [Save to S3](#save-to-s3)
      - [Restore from hostdir](#restore-from-hostdir)
      - [Restore from S3](#restore-from-s3)
  - [🌌 Kubernetes](#-kubernetes)
  - [☁️ Cloud Storage](#️-cloud-storage)
    - [Amazon S3](#amazon-s3)
    - [AIStor ex. MinIO](#aistor-ex-minio)
    - [Garage](#garage)
    - [Azure Blob Storage (not available in v2 yet)](#azure-blob-storage-not-available-in-v2-yet)
    - [Google Cloud Storage (not available in v2 yet)](#google-cloud-storage-not-available-in-v2-yet)
  - [🛠 Automation with Makefile](#-automation-with-makefile)
    - [Available Commands](#available-commands)
    - [Usage Examples](#usage-examples)
  - [🧪 Development & Testing](#-development--testing)
  - [💡 Future Ideas](#-future-ideas)
  - [🤝 Contribution](#-contribution)

---

## 🚀 Quick Start
If you just want to run a quick backup to a local folder:

```bash
export GRAFANA_URL=http://your-grafana:3000
export GRAFANA_TOKEN=your_service_account_token
uv sync
uv run grafana-backup save
```

The archive is written to `./_OUTPUT_/<timestamp>.tgz` (the directory is created automatically).
Basic-auth setups can use `GRAFANA_ADMIN_ACCOUNT` / `GRAFANA_ADMIN_PASSWORD` instead of a token.

---

## ✨ Key Improvements
* ✅ **Grafana 13.x Ready**: Tested against Grafana 13.0.1 (uid-based dashboard version API, new snapshot list endpoint, removed legacy APIs handled gracefully).
* ✅ **Single v2 Engine**: one async, registry-driven implementation for backup and restore — the old v1 code paths are gone.
* ✅ **15 Components**: dashboards, dashboard versions, datasources, folders (+permissions), library elements, alert rules, contact points, notification policies, users, teams, team members, organizations, annotations, snapshots, legacy alert channels.
* ✅ **Reliable Archives**: nested layouts (per-dashboard version history) are preserved; local archives are cleaned only after a successful archive/upload.
* ✅ **S3 Upload/Download**: automatic upload after backup and automatic download on restore when the archive is missing locally (AWS, MinIO, Garage, AIStor, R2).
* ✅ **Correct Exit Codes**: `0` on success, `1` on component/upload/configuration failure — safe for CronJobs and CI.

---

## 📦 Supported Components
| Component | Backup | Restore | Notes |
| :--- | :---: | :---: | :--- |
| **Organizations** | ✅ | ✅ | Organization records. Per-org members/teams are not exported. |
| **Users** | ✅ | ✅ | Requires Admin auth. Restored users get the temporary password `temp_password_123`. |
| **Teams** | ✅ | ✅ | Team records. |
| **Team Members** | ✅ | ✅ | Memberships with roles. |
| **Folders** | ✅ | ✅ | Includes folder permissions. |
| **Library Elements** | ✅ | ✅ | Panels only (Grafana API does not support library variables). |
| **Datasources** | ✅ | ✅ | `secureJsonData` is preserved when Grafana returns it. |
| **Dashboards** | ✅ | ✅ | Full dashboard JSON, folder assignment, template variables, tags. |
| **Dashboard Versions** | ✅ | ✅ | Full history under `dashboard_versions/<uid>/`; restore replays every backed-up version in order. |
| **Snapshots** | ✅ | ✅ | Works with both the legacy and the Grafana 13 list endpoints. |
| **Annotations** | ✅ | ✅ | Last 13 months (retention window is configurable in code). |
| **Alert Rules** | ✅ | ✅ | Unified alerting (Grafana 9.x+), including recording rules. |
| **Contact Points** | ✅ | ✅ | Provisioning API (Grafana 9.x+). |
| **Notification Policies** | ✅ | ✅ | Policy tree, routes and mute timings. |
| **Alert Channels** | ✅ | ⚠️ | Legacy alerting. The API was removed in Grafana 13; restore works only on Grafana ≤ 12. |

Component selection (`--components`) accepts both spellings, e.g. `library-elements` or `library_elements`.
Restore always resolves dependencies first (folders → library elements → datasources → dashboards, etc.).

---

## ⚙️ Configuration
Priority: **environment variables > configuration file > defaults** (same as v1).
The configuration file is the legacy JSON format still used by the fork; see [examples/grafanaSettings.example.json](examples/grafanaSettings.example.json).

### Environment Variables
| Variable | Description | Default |
| :--- | :--- | :--- |
| `GRAFANA_URL` | Grafana URL (no trailing slash) | `http://localhost:3000` |
| `GRAFANA_TOKEN` | Service account / API token | — |
| `GRAFANA_ADMIN_ACCOUNT` | Admin username (basic auth) | — |
| `GRAFANA_ADMIN_PASSWORD` | Admin password (basic auth) | — |
| `VERIFY_SSL` | Verify TLS certificates | `False` |
| `BACKUP_DIR` | Directory for archives | `_OUTPUT_` |
| `BACKUP_FILE_FORMAT` | Timestamp format for archive names | `%Y-%m-%d-%H-%M` |
| `PRETTY_PRINT` | Pretty-print JSON files | `False` |
| `LOG_LEVEL` | Log verbosity (`INFO`, `DEBUG`, ...) | `INFO` |
| `AWS_S3_BUCKET_NAME` | S3 bucket (enables upload) | — |
| `AWS_S3_BUCKET_KEY` | Key prefix inside the bucket | — |
| `AWS_DEFAULT_REGION` | AWS region | boto3 default |
| `AWS_ENDPOINT_URL` | Custom S3 endpoint (MinIO/Garage/AIStor) | AWS |
| `AWS_ACCESS_KEY_ID` | AWS access key (optional; instance roles work too) | — |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key (optional) | — |

> [!TIP]
> A **Service Account Token** with Admin permissions is recommended.

### Configuration File
If `--config` is not provided, the tool looks for (in order):
1. `~/.grafana-backup.json`
2. `./grafanaSettings.json`
3. the packaged `conf/grafanaSettings.json`

```json
{
  "general": {
    "backup_dir": "_OUTPUT_",
    "verify_ssl": false,
    "pretty_print": false,
    "backup_file_format": "%Y-%m-%d-%H-%M"
  },
  "grafana": {
    "url": "http://localhost:3000",
    "token": "glsa_...",
    "admin_account": "admin",
    "admin_password": "admin123"
  },
  "aws": {
    "s3_bucket_name": "grafana-backups",
    "s3_bucket_key": "grafana-backup",
    "region": "us-east-1",
    "access_key_id": "AKIA...",
    "secret_access_key": "...",
    "endpoint_url": "http://minio:9000"
  }
}
```

---

## 🖥 CLI Reference

```bash
# Create a backup (all components)
grafana-backup save

# Backup only selected components
grafana-backup save --components dashboards,folders,alert-rules

# Backup without creating the .tgz archive (keeps raw files in BACKUP_DIR)
grafana-backup save --no-archive

# Restore from a local archive
grafana-backup restore _OUTPUT_/2026-10-23-22-00.tgz

# Restore selected components (dependencies are added automatically)
grafana-backup restore 2026-10-23-22-00.tgz --components dashboards

# Restore an archive by name: downloaded from S3 if it is not present locally
grafana-backup restore 2026-10-23-22-00.tgz

# Use a specific configuration file
grafana-backup save --config ./grafanaSettings.json
```

**Exit codes:** `0` — success; `1` — configuration error, failed component, or failed S3 upload.

---

## 🗄 Backup Format & Compatibility
* Archives are `gzip` tarballs named `<timestamp>.tgz` (default `%Y-%m-%d-%H-%M`).
* Inside, every component is stored as `<component>/<timestamp>/<files>`:
  ```text
  dashboards/2026-10-23-22-00/dash-host-overview.dashboard
  dashboard_versions/2026-10-23-22-00/dash-host-overview/1.dashboard_version
  folders/2026-10-23-22-00/folder-infra.folder
  ```
* **Restore is backward compatible** with archives produced by v1 and by earlier v2 builds (flat layout without the timestamp level). The format is detected automatically.
* Restoring a v1 archive is supported; `dashboard_versions` nested directories are read recursively.
* When `--no-archive` is used, raw component directories are kept in `BACKUP_DIR` for GitOps-style workflows.

> [!NOTE]
> See [REFACTOR_NOTES.md](REFACTOR_NOTES.md) for the complete list of v2 changes, removed features and migration notes.

---

## 🛠 Installation
### Using uv
```bash
uv sync
# Optional: Azure/GCS SDKs (not wired into v2 backup yet)
uv sync --extra cloud
```

Python 3.10+ is required.

### Prebuilt binaries
Every GitHub Release ships standalone executables (built with PyInstaller, no Python required):

| Asset | Platform |
| :--- | :--- |
| `grafana-backup-tool-linux-amd64` | Linux x86_64 |
| `grafana-backup-tool-linux-arm64` | Linux ARM64 |
| `grafana-backup-tool-darwin-arm64` | macOS (Apple Silicon) |
| `grafana-backup-tool-windows-amd64.exe` | Windows x86_64 |

The same release includes the source distribution, a wheel, and a `SHA256SUMS` file.
The binaries bundle all v2 modules and the default configuration, so they run without the repository.

```bash
chmod +x grafana-backup-tool-linux-amd64
./grafana-backup-tool-linux-amd64 --help
```

---

### 🐳 Docker examples
#### Save to hostdir
```bash
docker run --network=host --rm --name grafana-backup-tool \
  -e GRAFANA_TOKEN="your_token" \
  -e GRAFANA_URL="http://grafana:3000" \
  -v /tmp/backup:/opt/grafana-backup-tool/_OUTPUT_ \
  ghcr.io/durachyo/grafana-backup-tool:v2.0.0 save
```
#### Save to S3
```bash
docker run --network=host --rm --name grafana-backup-tool \
  -e GRAFANA_TOKEN=glsa_B1pZjuj87lcnc7TSK6vBPSrhTFPLe70o_0d8785f9 \
  -e GRAFANA_URL="http://grafana:3000" \
  -e AWS_S3_BUCKET_NAME=backup-tool-bucket \
  -e AWS_S3_BUCKET_KEY=grafana-backup \
  -e AWS_ACCESS_KEY_ID=GK8fd0d61da5e7b1659a24a171 \
  -e AWS_SECRET_ACCESS_KEY=d084c2836e8e38bc0cf8ea9db915d15c0b8dad6ddd40219bdb733953f4b452da \
  -e AWS_ENDPOINT_URL=http://localhost:3900 \
  -v ./OUTPUT/:/opt/grafana-backup-tool/_OUTPUT_ \
  ghcr.io/durachyo/grafana-backup-tool:v2.0.0 save
```
#### Restore from hostdir
```bash
docker run --network=host --rm --name grafana-backup-tool \
  -e GRAFANA_TOKEN="your_token" \
  -e GRAFANA_URL="http://grafana:3000" \
  -v /tmp/backup:/opt/grafana-backup-tool/_OUTPUT_ \
  ghcr.io/durachyo/grafana-backup-tool:v2.0.0 restore _OUTPUT_/2026-03-29-00-18.tgz
```
#### Restore from S3
The archive is downloaded from the configured bucket automatically when it is missing locally.
```bash
docker run --network=host --rm --name grafana-backup-tool \
  -e GRAFANA_TOKEN="glsa_B1pZjuj87lcnc7TSK6vBPSrhTFPLe70o_0d8785f9" \
  -e GRAFANA_URL="http://localhost:3000" \
  -e AWS_S3_BUCKET_NAME=backup-tool-bucket \
  -e AWS_S3_BUCKET_KEY=grafana-backup \
  -e AWS_ACCESS_KEY_ID=GK8fd0d61da5e7b1659a24a171 \
  -e AWS_SECRET_ACCESS_KEY=d084c2836e8e38bc0cf8ea9db915d15c0b8dad6ddd40219bdb733953f4b452da \
  -e AWS_ENDPOINT_URL=http://localhost:3900 \
  ghcr.io/durachyo/grafana-backup-tool:v2.0.0 restore 2026-03-29-00-18.tgz
```

## 🌌 Kubernetes

- **Helm Chart**: Available in the `/charts` directory.
- **CronJob**: See [values.yaml](charts/grafana-backup-tool/values.yaml) for scheduled backups.
  The chart passes `GRAFANA_URL`, `GRAFANA_ADMIN_ACCOUNT` and `AWS_*` through a ConfigMap, and tokens/passwords through a Secret.

---

## ☁️ Cloud Storage
Archives are uploaded right after they are built. On `restore`, if the archive is not present locally, it is downloaded from the configured bucket automatically.

S3 is enabled when a bucket is configured (config file `aws.s3_bucket_name` or `AWS_S3_BUCKET_NAME`). Credentials, region and endpoint follow standard AWS variables, so IAM instance roles and S3-compatible endpoints work out of the box. Upload failures are reported and produce exit code `1`, while the local archive is kept.

### Amazon S3
```bash
-e AWS_S3_BUCKET_NAME="my-bucket" \
-e AWS_S3_BUCKET_KEY="grafana-backup" \
-e AWS_DEFAULT_REGION="us-east-1" \
-e AWS_ACCESS_KEY_ID="xxx" \
-e AWS_SECRET_ACCESS_KEY="yyy"
```

### [AIStor](https://www.min.io/pricing) ex. MinIO

```bash
-e AWS_S3_BUCKET_NAME="grafana-backups" \
-e AWS_S3_BUCKET_KEY="grafana-backup" \
-e AWS_ENDPOINT_URL="http://minio:9000" \
-e AWS_ACCESS_KEY_ID="minioadmin" \
-e AWS_SECRET_ACCESS_KEY="minioadmin" \
-e AWS_DEFAULT_REGION="us-east-1"
```

### [Garage](https://garagehq.deuxfleurs.fr/)
```bash
Works the same as AWS and AIStor. Fully compatible. Use the AWS connector.
```

### Azure Blob Storage (not available in v2 yet)
> [!WARNING]
> Azure upload was only implemented in the removed v1 engine. The `[cloud]` extra still installs the SDK, but v2 does not upload to Azure yet. `AZURE_STORAGE_*` variables are currently ignored.

### Google Cloud Storage (not available in v2 yet)
> [!WARNING]
> GCS upload was only implemented in the removed v1 engine. The `[cloud]` extra still installs the SDK, but v2 does not upload to GCS yet. `GCS_*` variables are currently ignored.

---

## 🛠 Automation with Makefile
A `Makefile` is included in the repository to simplify local development and automate routine tasks via Docker.

### Available Commands
| Command                    | Description                                                             |
| :------------------------- | :---------------------------------------------------------------------- |
| `make build`               | Builds the local Docker image with the tag defined in the Makefile.     |
| `make package`             | Builds the Python sdist and wheel with `uv build` (`dist/`).            |
| `make backup`              | Runs a backup and saves the archive to the `./backups` folder.          |
| `make restore FILE=<name>` | Restores Grafana state from a specific archive in `./backups`.          |
| `make shell`               | Starts an interactive shell session inside the container for debugging. |
| `make test`                | Checks the CLI by running `grafana-backup --help` in the container.     |
| `make logs`                | Runs a backup with `LOG_LEVEL=DEBUG` for troubleshooting.               |
| `make update_version`      | Updates the version in `VERSION`, the chart, the README and `pyproject.toml`. |

### Usage Examples

1.  **Build the image**:
    ```bash
    make build
    ```

2.  **Run a quick backup**:
    You can override variables directly in the command line:
    ```bash
    make backup GRAFANA_TOKEN="your_token" GRAFANA_URL=https://grafana.example.com
    ```

3.  **Restore from a file**:
    Ensure the file exists in your local `./backups` directory:
    ```bash
    make restore FILE=2026-03-28_22-00.tgz
    ```

> [!TIP]
> You can edit the `GRAFANA_URL` and `GRAFANA_TOKEN` variables directly inside the `Makefile` to avoid typing them during every local test.

---

## 🧪 Development & Testing

```bash
# Install dev dependencies (pytest, ruff, moto)
uv sync --extra dev

# Lint
uv run ruff check grafana_backup tests

# Unit tests (S3 provider is tested against an in-memory S3 via moto)
uv run pytest tests -q

# Build the sdist and wheel (uv_build backend)
uv build
```

An integration stack with Grafana 13 and Garage (S3) is available in `tests/docker-compose.yaml`:

```bash
docker compose -f tests/docker-compose.yaml up -d
```

---

## 💡 Future Ideas
1. **GitOps Mode**: Save dashboards as raw JSON (no archive) for easy Git tracking — partially available via `--no-archive`.
2. **Multi-Org Support**: Iterate through all organizations and their members automatically.
3. **Selective Restore**: Restore only specific folders or dashboard UID patterns.
4. **Azure/GCS Upload**: Bring back the cloud providers that existed in v1.

---

## 🤝 Contribution

1. **Clone this repo:**
   ```bash
   git clone https://github.com/DuraCHYo/grafana-backup-tool.git
   cd grafana-backup-tool
   ```
2. **Run test docker-compose stack:**
   ```bash
   docker compose -f ./tests/docker-compose.yaml up -d
   ```
3. **Set up the environment:**
   We use `uv` for dependency management. If you don't have it, [install it here](https://docs.astral.sh/uv/getting-started/installation/).

   Create a virtual environment and install dependencies:
   ```bash
   uv sync --extra dev
   ```
4. **Run the tool:**
   ```bash
   uv run grafana-backup --help
   ```

---

*Maintained with ❤️ by DuraCHYo. Original tool by ysde.*
