from grafana_backup.components.registry import load_component_functions
from grafana_backup.archive import main as archive
from grafana_backup.providers import get_provider
from grafana_backup.api_checks import main as api_checks
import sys


def main(args, settings):
    all_backup_functions = load_component_functions(mode="save")

    status, json_resp, db_uid, ds_uid, paging, cp_support = api_checks(settings)
    if status != 200:
        print(f"Grafana server status is not ok: {json_resp}")
        sys.exit(1)

    settings.update(
        {
            "DASHBOARD_UID_SUPPORT": db_uid,
            "DATASOURCE_UID_SUPPORT": ds_uid,
            "PAGING_SUPPORT": paging,
            "CONTACT_POINT_SUPPORT": cp_support,
        }
    )

    arg_components = args.get("--components", False)
    if arg_components:
        target_keys = arg_components.replace("_", "-").split(",")
    else:
        target_keys = list(all_backup_functions.keys())

    for key in target_keys:
        if key in all_backup_functions:
            print(f"Saving {key}...")
            all_backup_functions[key](args, settings)
        else:
            print(f"Warning: Component {key} not found.")

    if not args.get("--no-archive", False):
        print("Creating archive...")
        archive(args, settings)

    provider = get_provider(settings)
    if provider:
        backup_dir = settings.get("BACKUP_DIR")
        timestamp = settings.get("TIMESTAMP")
        filename = f"{timestamp}.tar.gz"
        local_path = f"{backup_dir}/{filename}"

        provider.upload(local_path, filename)

    print("Backup process finished successfully.")
