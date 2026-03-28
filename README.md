# 📊 Grafana Backup Tool (Modern Fork)

[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![Grafana Support](https://img.shields.io/badge/grafana-v12.x-orange.svg)](https://grafana.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful Python-based tool to backup and restore Grafana settings via API.  
This is a **maintained fork** of [ysde/grafana-backup-tool](https://github.com/ysde/grafana-backup-tool), updated for modern Grafana versions.

> [!IMPORTANT]
> **Why use this fork?** > Unlike the original tool, this version fully supports **Grafana 12.x** and fixes the critical bugs that has existed since Grafana 8.0.0.

---

## 📑 Table of Contents
- [📊 Grafana Backup Tool (Modern Fork)](#-grafana-backup-tool-modern-fork)
  - [📑 Table of Contents](#-table-of-contents)
  - [🚀 Quick Start](#-quick-start)
  - [✨ Key Improvements](#-key-improvements)
  - [📦 Supported Components](#-supported-components)
  - [⚙️ Configuration](#️-configuration)
    - [Core Variables](#core-variables)
  - [🛠 Installation](#-installation)
    - [Using Virtual Environment](#using-virtual-environment)
  - [🐳 Docker \& Kubernetes](#-docker--kubernetes)
    - [Docker](#docker)
    - [Kubernetes](#kubernetes)
  - [☁️ Cloud Storage](#️-cloud-storage)
    - [Amazon S3](#amazon-s3)
    - [Azure Blob Storage](#azure-blob-storage)
    - [Google Cloud Storage (GCS)](#google-cloud-storage-gcs)
    - [AIStor ex. MinIO](#aistor-ex-minio)
    - [Garage](#garage)
  - [🛠 Automation with Makefile](#-automation-with-makefile)
    - [Available Commands](#available-commands)
    - [Usage Examples](#usage-examples)
  - [💡 Future Ideas](#-future-ideas)
  - [🤝 Contribution](#-contribution)

---

## 🚀 Quick Start
If you just want to run a quick backup to a local folder:

```bash
export GRAFANA_URL=http://your-grafana:3000
export GRAFANA_TOKEN=your_admin_token
pip install .
grafana-backup save
```

---

## ✨ Key Improvements
* ✅ **Grafana 12.x Ready**: Fixed authentication and API schema changes.
* ✅ **Library Panels Fix**: Proper restoration of library elements (tested v8.4.3 to v11.x).
* ✅ **Unified Alerting**: Support for Alert Rules, Contact Points, and Policies (v9.4.0+).
* ✅ **Security Updates**: Modernized base Docker images and dependencies.

---

## 📦 Supported Components
| Component          | Backup | Restore | Notes                     |
| :----------------- | :----: | :-----: | :------------------------ |
| **Dashboards**     |   ✅    |    ✅    | Includes embedded alerts  |
| **Folders**        |   ✅    |    ✅    | Includes permissions      |
| **Library Panels** |   ✅    |    ✅    | **Fixed in this fork**    |
| **Datasources**    |   ✅    |    ✅    | -                         |
| **Alert Rules**    |   ✅    |    ✅    | v9.4.0+ required          |
| **Teams/Users**    |   ✅    |    ✅    | Requires Admin Basic Auth |
| **Snapshots**      |   ✅    |    ✅    | -                         |

---

## ⚙️ Configuration
You can configure the tool via `grafanaSettings.json` or **Environment Variables** (preferred).

### Core Variables
| Variable                 | Description                              | Required             |
| :----------------------- | :--------------------------------------- | :------------------- |
| `GRAFANA_URL`            | URL of your Grafana (no trailing slash)  | **Yes**              |
| `GRAFANA_TOKEN`          | Admin API Token or Service Account Token | **Yes**              |
| `GRAFANA_ADMIN_ACCOUNT`  | Admin username (for Teams/Users backup)  | No                   |
| `GRAFANA_ADMIN_PASSWORD` | Admin password                           | No                   |
| `VERIFY_SSL`             | Set to `False` for self-signed certs     | No (Default: `True`) |

> [!TIP]
> I highly recommend using a **Service Account Token** with Admin permissions.

---

## 🛠 Installation
### Using Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🐳 Docker & Kubernetes
### Docker
```bash
docker run --rm --name grafana-backup-tool \
  -e GRAFANA_TOKEN="your_token" \
  -e GRAFANA_URL="http://grafana:3000" \
  -v /tmp/backup:/opt/grafana-backup-tool/_OUTPUT_ \
  ghcr.io/durachyo/grafana-backup-tool:v1.6.0 grafana-backup save
```

### Kubernetes
- **Helm Chart**: Available in the `/charts` directory.
- **CronJob**: See [values.yaml](charts/grafana-backup-tool/values.yaml) for scheduled backups.

---

## ☁️ Cloud Storage
The tool supports versioned archives automatically uploaded to any S3-compatible storages such as:

### Amazon S3
```bash
-e AWS_S3_BUCKET_NAME="my-bucket" \
-e AWS_DEFAULT_REGION="us-east-1" \
-e AWS_ACCESS_KEY_ID="xxx" \
-e AWS_SECRET_ACCESS_KEY="yyy"
```

### Azure Blob Storage
```bash
-e AZURE_STORAGE_CONTAINER_NAME="my-container" \
-e AZURE_STORAGE_CONNECTION_STRING="my-connection-string"
```

### Google Cloud Storage (GCS)
```bash
-e GCS_BUCKET_NAME="my-bucket" \
-e GCLOUD_PROJECT="my-project" \
-e GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### [AIStor](https://www.min.io/pricing) ex. MinIO

```bash
-e AWS_S3_BUCKET_NAME="grafana-backups" \
-e AWS_ENDPOINT_URL="http://minio:9000" \
-e AWS_ACCESS_KEY_ID="minioadmin" \
-e AWS_SECRET_ACCESS_KEY="minioadmin" \
-e AWS_DEFAULT_REGION="us-east-1"
```

### [Garage](https://garagehq.deuxfleurs.fr/)
```bash
Works as such as AWS and AIStor. Fully compatible. Use AWS connector.
```

---

## 🛠 Automation with Makefile
A `Makefile` is included in the repository to simplify local development and automate routine tasks via Docker.

### Available Commands
| Command                    | Description                                                             |
| :------------------------- | :---------------------------------------------------------------------- |
| `make build`               | Builds the local Docker image with the tag defined in the Makefile.     |
| `make backup`              | Runs a backup and saves the archive to the `./backups` folder.          |
| `make restore FILE=<name>` | Restores Grafana state from a specific archive in `./backups`.          |
| `make shell`               | Starts an interactive shell session inside the container for debugging. |
| `make test`                | Checks functionality by running the help command.                       |
| `make logs`                | Runs a backup with `LOG_LEVEL=DEBUG` for troubleshooting.               |
| `make update_version`      | Updates all versions in required files to new                           |

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
    make restore FILE=2026-03-28_22-00.tar.gz
    ```

> [!TIP]
> You can edit the `GRAFANA_URL` and `GRAFANA_TOKEN` variables directly inside the `Makefile` to avoid typing them during every local test.

---

## 💡 Future Ideas
1. **GitOps Mode**: Save dashboards as raw JSON (no archive) for easy Git tracking.
2. **Multi-Org Support**: Iterate through all organizations automatically.
3. **Selective Restore**: Restore only specific folders or dashboard UID patterns.
4. **Modern CLI**: Migration to `Typer` for better command-line experience.

---

## 🤝 Contribution
1. Clone the repo.
2. Run test stack: `cd tests && docker-compose up -d`.
3. Run TUI debug: `PYTHONPATH=.. python3 tests/grafana_backup_tui.py`.

---
*Maintained with ❤️ by DuraCHYo. Original tool by ysde.*