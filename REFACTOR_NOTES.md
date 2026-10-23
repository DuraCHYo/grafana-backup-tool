# Grafana Backup Tool v2.0.0 — Refactor Notes

This document describes what changed in the v2 rewrite, what no longer works, and what stays compatible.
It is intended both as release-notes source material and as a migration guide for existing users.

---

## 1. Summary

Version 2.0.0 is a full rewrite of the tool. The v1 implementation (a collection of per-resource
`save_*.py` / `delete_*.py` / `create_*.py` scripts around a shared request helper) has been removed.
Everything now runs through a single async, registry-driven engine:

```
CLI (typer)
  └── BackupCoordinator / RestoreCoordinator
        └── ComponentRegistry  (15 components, dependency-ordered)
              └── component.backup(client) / component.restore(client)
                    └── GrafanaClient (httpx, retries, auth)
```

Key properties of the new engine:

* **One registry** (`v2/components/registry.py`) is the single source of truth for component names,
  implementations and restore ordering.
* **Async I/O** (`httpx`, `asyncio`) with per-item error isolation: a broken item increments `failed`
  but never aborts the whole component run.
* **Uniform output layout** for every component: `<component>/<timestamp>/<files>`.
* **Backward-compatible restore** for archives produced by v1 and by early v2 builds.

---

## 2. What is backed up now

All 15 components are supported by both engines. `restore` resolves dependencies first
(organizations → users → teams → team-members → folders → library-elements → datasources →
dashboards → dashboard-versions → snapshots → annotations → alerting layer).

| Component | Directory | Backup | Restore | Notes |
| --- | --- | :---: | :---: | --- |
| Organizations | `organizations/` | ✅ | ✅ | Org records only; per-org memberships are not exported |
| Users | `users/` | ✅ | ✅ | Requires Admin auth; restored with temporary password `temp_password_123` |
| Teams | `teams/` | ✅ | ✅ | |
| Team Members | `team_members/` | ✅ | ✅ | Memberships with roles |
| Folders | `folders/` | ✅ | ✅ | Includes folder permissions |
| Library Elements | `library-elements/` | ✅ | ✅ | Panels (kind=1); Grafana API has no write support for library variables |
| Datasources | `datasources/` | ✅ | ✅ | `secureJsonData` preserved when Grafana returns it |
| Dashboards | `dashboards/` | ✅ | ✅ | Full JSON incl. folder assignment, variables, tags |
| Dashboard Versions | `dashboard_versions/` | ✅ | ✅ | Per-dashboard subdirectories; restore replays every backed-up version in order |
| Snapshots | `snapshots/` | ✅ | ✅ | Supports legacy and Grafana 13 list endpoints |
| Annotations | `annotations/` | ✅ | ✅ | Window limited to the last 13 months |
| Alert Rules | `alert_rules/` | ✅ | ✅ | Unified alerting + recording rules |
| Contact Points | `contact_points/` | ✅ | ✅ | Provisioning API |
| Notification Policies | `notification_policies/` | ✅ | ✅ | Policy tree, routes, mute timings |
| Alert Channels | `alert_channels/` | ✅ | ⚠️ | Legacy alerting; restore only works on Grafana ≤ 12 (API removed in 13) |

---

## 3. CLI changes

The CLI is still `grafana-backup` with `save` and `restore`, but the `--engine v1|v2` switch is gone
(v2 is the only engine):

```bash
grafana-backup save    [--config PATH] [--components LIST] [--no-archive]
grafana-backup restore ARCHIVE [--config PATH] [--components LIST]
grafana-backup --help
```

* `--components` accepts comma-separated names in either spelling:
  `dashboards,library-elements` or `dashboards,library_elements`.
* `--no-archive` now actually works (in the previous v2 implementation it deleted the freshly
  written files through an unconditional cleanup).
* Exit codes are meaningful now: `0` on success, `1` on configuration error, component failures
  or a failed S3 upload. This matters for Kubernetes CronJobs/CI.
* `LOG_LEVEL` environment variable is honoured (previously only the internal `--debug` flag was).

### What no longer exists

* `--engine v1` (the whole v1 engine was deleted).
* The `help` subcommand (`uv run grafana-backup help` from the old docs); use `--help`.
* `create`, `delete`, `pause-alerts`, `unpause-alerts`, `influx`, `make-users-viewers`,
  `restore-user-permissions`, `update-folder-permissions`, `update-notification-policy` commands
  and their modules — the v1 tree that contained them is gone.

---

## 4. Configuration changes

### 4.1 Environment variables now work (fixed)

Previously the v2 loader ignored the documented `GRAFANA_URL` / `GRAFANA_TOKEN` /
`VERIFY_SSL` / `BACKUP_DIR` variables (only the legacy JSON file was read), which broke every
Docker/Helm example. Priority is now identical to v1:

**environment > JSON config > defaults**

Supported variables:

| Variable | Maps to |
| --- | --- |
| `GRAFANA_URL` | `grafana.url` |
| `GRAFANA_TOKEN` | `grafana.token` |
| `GRAFANA_ADMIN_ACCOUNT` | `grafana.admin_user` |
| `GRAFANA_ADMIN_PASSWORD` | `grafana.admin_password` |
| `VERIFY_SSL` | `grafana.verify_ssl` |
| `BACKUP_DIR` | `storage.backup_dir` |
| `BACKUP_FILE_FORMAT` | `storage.timestamp_format` |
| `PRETTY_PRINT` | `storage.pretty_print` |
| `LOG_LEVEL` | log verbosity |
| `AWS_S3_BUCKET_NAME` / `AWS_S3_BUCKET_KEY` | S3 bucket / prefix |
| `AWS_DEFAULT_REGION` | S3 region |
| `AWS_ENDPOINT_URL` | S3-compatible endpoint |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | S3 credentials |

The JSON configuration format did not change (sections `general`, `grafana`, `aws`, `azure`, `gcp`).
Lookup order without `--config`: `~/.grafana-backup.json` → `./grafanaSettings.json` →
packaged `conf/grafanaSettings.json` → built-in defaults.

### 4.2 New config keys

* `aws.endpoint_url`, `aws.access_key_id`, `aws.secret_access_key` are now read by the v2 loader
  (they existed in the example config but were ignored before).
* S3 upload configuration is unchanged in shape: bucket, prefix, region, endpoint.

### 4.3 Config keys that are no longer used

These v1 keys are accepted (the loader ignores unknown fields) but have no effect:

* `general.api_health_check`, `general.api_auth_check`
* `general.uid_dashboard_slug_suffix`, `general.backup_workers`
* `general.client_cert` (no client-certificate support in v2)
* `grafana.search_api_limit` (v2 uses a fixed 5000 pagination limit)
* `grafana.default_user_password` — restored users always get `temp_password_123`
* `azure.*`, `gcp.*` — providers removed from v2 (see §6)

---

## 5. Backup format and compatibility

### 5.1 Archive layout

```
<timestamp>.tgz
├── dashboards/<timestamp>/<uid>.dashboard
├── dashboard_versions/<timestamp>/<uid>/<version>.dashboard_version
├── folders/<timestamp>/<uid>.folder
├── folders/<timestamp>/<uid>_permissions.folder
├── datasources/<timestamp>/<uid>.datasource
├── contact_points/<timestamp>/contact-points_<timestamp>.contact_point
└── ...
```

* The `<timestamp>` level is part of the v2 format.
* Files inside a component use the v1 extensions (`.dashboard`, `.folder`, `.datasource`, ...), so
  tools that understand v1 archives can still inspect the contents.

### 5.2 Restore compatibility

| Source archive | Supported |
| --- | --- |
| v2 archive (`<component>/<timestamp>/...`) | ✅ |
| v2.0.0-beta flat archive (`<component>/<file>`) | ✅ (auto-detected as "v1 format") |
| v1 archive (flat `<component>/<file>` and nested `dashboard_versions/<uid>/...`) | ✅ |

The extractor detects the layout using a strict `YYYY-MM-DD-HH-MM` timestamp pattern, so uid-based
subdirectories are never mistaken for a timestamp level.

### 5.3 Grafana version compatibility

* Tested against **Grafana 13.0.1**.
* Unified alerting components require **Grafana 9.x+**.
* Library elements require **Grafana 8.4+**.
* Legacy alert channels (`/api/alert-notifications`) were removed in **Grafana 13**; backup/restore
  of that component only works on older versions and reports zero items on 13.

---

## 6. What stopped working / was removed

1. **Azure Blob and GCS upload.**
   v1 uploaded archives to Azure/GCS through `providers/`. The v2 coordinator only implements S3.
   The SDKs remain available via the `cloud` extra, but `AZURE_*` and `GCS_*` settings are currently
   ignored, and `restore` cannot download from those backends.

2. **Alert channels on Grafana 13.**
   The legacy REST API was removed upstream. The component still exists (so old archives restore on
   old Grafana), but on 13 it finds nothing.

3. **`validate`/create/delete style maintenance commands.**
   The v1 helpers (`create/`, `delete/`, `tools.py`, `api_checks.py`, ...) are gone. Only `save` and
   `restore` remain.

4. **Per-user passwords.**
   Passwords are not exportable from Grafana. Restored users receive `temp_password_123` instead of
   the v1-configurable `default_user_password`.

5. **Client certificates / extra HTTP headers.**
   `general.client_cert` and `GRAFANA_HEADERS` are not supported by the v2 HTTP client.

6. **Single-file component statistics.**
   Components stored in one file (contact points, notification policy) report `Saved: 1` even when
   they contain many items. This is cosmetic — all items are written into the single JSON file.

7. **Cloud upload statistics in old logs.**
   v1 printed upload results with `print()`; v2 exports an `upload` block in the backup stats and
   prints `☁ Uploaded to s3://...` in the CLI.

---

## 7. Bugs fixed during the rewrite

* **Dashboard version history (Grafana 13).** The component called the removed
  `/api/dashboards/id/{id}/versions` endpoint, so every dashboard returned 404. It now uses
  `/api/dashboards/uid/{uid}/versions` first and falls back to the legacy id endpoint on older
  Grafana versions (supports both response shapes: bare list and `{versions, continueToken}`).
* **Snapshot listing (Grafana 13).** Now tries `/api/snapshots` (legacy) and
  `/api/dashboard/snapshots` (Grafana 13).
* **Nested files were missing from archives.** The archiver only added files directly under a
  component directory, silently dropping `dashboard_versions/<uid>/*`.
* **Archive cleanup deleted the wrong thing.** The cleanup condition compared directory names to the
  timestamp, which never matched, leaving stale artifact directories behind.
* **Restore extraction nested components inside themselves**
  (`datasources/datasources/...`) because `shutil.move` moved a directory into an existing target.
* **Format detection false positives.** Any uid-like subdirectory triggered the "v2 format" branch;
  detection now uses a strict timestamp regex.
* **`--no-archive` deleted the backup.** Cleanup ran even when no archive was created; it now runs
  only after a successful archive (and upload).
* **`GrafanaClient.post(..., json=...)` was unsupported**, breaking restore of dashboards, snapshots,
  library elements, organizations, annotations, notification policies and alert channels. The client
  now accepts both `data=` and `json=`.
* **Double restore table.** Restore results were printed by both the coordinator and the CLI.
* **Silent no-op when using `python -m grafana_backup.cli`.** The module lacked a `__main__` guard,
  so the command exited with code 0 without doing anything.
* **Lint.** 400+ Ruff findings in the v2 tree fixed; the remaining intentional ones
  (`BLE001` broad per-item exception handlers, `DTZ005` local timestamps for directory names) are
  documented and ignored in `pyproject.toml`.
* **Python packaging.** `[tool.setuptools] packages = ["grafana_backup"]` excluded all subpackages,
  so a built wheel/sdist contained no `v2/` code and no default config. The project now uses the
  native **`uv_build`** backend (`uv build`, `make package`); package discovery covers
  `grafana_backup*`, `conf/*.json` is bundled, and a clean-venv install was verified. The release
  workflow now builds and attaches the sdist/wheel to GitHub Releases.
* **Release binaries.** The PyInstaller build now bundles every `grafana_backup` submodule and the
  packaged config, and CI smoke-tests each executable with `--help` before publishing. Releases
  contain Linux (amd64/arm64), macOS (arm64) and Windows (amd64) binaries plus `SHA256SUMS`.

---

## 8. Code layout after the refactor

```
grafana_backup/
├── cli.py                      # thin typer CLI (save / restore)
├── conf/grafanaSettings.json   # default (legacy JSON) configuration
└── v2/
    ├── cli.py                  # command implementations + result tables
    ├── config/
    │   ├── loader.py           # JSON → Settings, env overrides
    │   └── settings.py         # pydantic models (grafana, storage, components)
    ├── core/
    │   ├── backup.py           # BackupCoordinator (archive + S3 upload)
    │   ├── restore.py          # RestoreCoordinator (download/extract + restore)
    │   └── client.py           # GrafanaClient (httpx, retries, auth)
    ├── components/
    │   ├── registry.py         # single source of truth (names, classes, order)
    │   ├── base.py             # BaseComponent (backup side)
    │   ├── restore_base.py     # BaseRestoreComponent (+ v1 extension mapping)
    │   ├── <component>.py      # 15 backup components
    │   └── restore_<component>.py
    ├── storage/
    │   ├── base.py             # StorageProvider interface
    │   └── s3.py               # boto3 S3 / S3-compatible provider
    └── utils/logging.py        # loguru setup
```

Removed in this release: `save/`, `create/`, `delete/`, `api_methods/`, `components/` (v1 registry and
helpers), `core/send_requests.py`, `providers/`, `archive.py`, `api_checks.py`, `commons.py`,
`constants.py`, `grafanaSettings.py`, `dashboardApi.py`, `grafana_api.py`, `tools.py`, `restore.py`,
`influx.py`, `make_users_viewers.py`, `pause_alerts.py`, `unpause_alerts.py`,
`restore_user_permissions.py`, `update_folder_permissions.py`, `update_notification_policy.py`.

---

## 9. Migration guide (v1 → v2)

1. **Update the image/version** to v2.0.0.
2. **Configuration:** the JSON file format is unchanged. Prefer environment variables — they now take
   precedence as documented.
3. **Scripts:**
   * `grafana-backup save ...` — unchanged.
   * `grafana-backup restore <archive>` — unchanged, but `--engine v1` must be removed.
   * Any script calling removed maintenance commands must be replaced.
4. **S3:** existing `AWS_*` settings keep working; upload now happens automatically after archiving.
5. **Existing archives:** v1 archives can be restored directly; no conversion is required.
6. **Users restored from backup:** they get `temp_password_123`; distribute/reset passwords
   accordingly.
7. **Azure/GCS users:** stay on v1 until the providers are re-implemented in v2 (or open an issue).

---

## 10. Known limitations

* Azure/GCS upload and download are not implemented in v2.
* Organization memberships, per-org teams and user permissions are not exported.
* Library variables cannot be restored (Grafana API limitation).
* Annotations are exported for the last 13 months only.
* Legacy alert channels cannot be restored on Grafana 13+.
* Snapshot restore creates new snapshot keys (as Grafana does for every import).
* `--no-archive` keeps raw files on disk; the archive is not created, so S3 upload is skipped.
