import json

from grafana_backup.components.registry import MINIMUM_GRAFANA_VERSION
from grafana_backup.components.utils import get_grafana_version
from grafana_backup.dashboardApi import (
    create_alert_rule,
    create_folder,
    get_alert_rule,
    get_folder,
    update_alert_rule,
)


def ensure_folder_exists(
    folder_uid,
    grafana_url,
    http_get_headers,
    http_post_headers,
    verify_ssl,
    client_cert,
    debug,
):
    """Checks if a folder exists, and creates it if it doesn't

    Args:
        folder_uid (_type_): _description_
        grafana_url (_type_): _description_
        http_get_headers (_type_): _description_
        http_post_headers (_type_): _description_
        verify_ssl (_type_): _description_
        client_cert (_type_): _description_
        debug (_type_): _description_

    Returns:
        _type_: _description_
    """
    if not folder_uid:
        return True  # General always exists, no need to check

    status_code, response = get_folder(
        folder_uid, grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )

    if status_code == 200:
        return True  # Folder exists

    # Folder does not exist - create it
    if status_code == 404:
        print(f"Folder {folder_uid} not found, creating it...")
        print(f"JOPA folder_uid: {folder_uid}")
        folder_data = {
            "uid": folder_uid,
            "title": f"Restored Folder ({folder_uid[:8]})",
        }
        result = create_folder(
            json.dumps(folder_data),
            grafana_url,
            http_post_headers,
            verify_ssl,
            client_cert,
            debug,
        )
        if result[0] == 200:
            print(f"Folder {folder_uid} created successfully")
            return True
        else:
            print(f"Failed to create folder {folder_uid}: {result[1]}")
            return False

    return False


def main(args, settings, file_path):
    grafana_url = settings.get("GRAFANA_URL")
    http_post_headers = settings.get("HTTP_POST_HEADERS")
    http_get_headers = settings.get("HTTP_GET_HEADERS")
    verify_ssl = settings.get("VERIFY_SSL")
    client_cert = settings.get("CLIENT_CERT")
    debug = settings.get("DEBUG")

    with open(file_path, "r") as f:
        data = f.read()

    current_grafana_version = get_grafana_version(
        grafana_url, verify_ssl, http_get_headers, client_cert, debug
    )
    if MINIMUM_GRAFANA_VERSION <= current_grafana_version:
        alert_rule = json.loads(data)
        del alert_rule["id"]
        uid = alert_rule["uid"]

        # Ensure folder exists before creating alert rule
        folder_uid = alert_rule.get("folderUID")
        if folder_uid and not ensure_folder_exists(
            folder_uid,
            grafana_url,
            http_get_headers,
            http_post_headers,
            verify_ssl,
            client_cert,
            debug,
        ):
            print(
                f"Skipping alert rule '{alert_rule['title']}': could not ensure folder exists"
            )
            return

        get_response = get_alert_rule(
            uid, grafana_url, http_get_headers, verify_ssl, client_cert, debug
        )
        status_code = get_response[0]
        if debug:
            print(f"Got a code: {status_code}")
        http_post_headers["x-disable-provenance"] = "*"
        if status_code == 404:
            result = create_alert_rule(
                json.dumps(alert_rule),
                grafana_url,
                http_post_headers,
                verify_ssl,
                client_cert,
                debug,
            )
        else:
            result = update_alert_rule(
                alert_rule["uid"],
                json.dumps(alert_rule),
                grafana_url,
                http_post_headers,
                verify_ssl,
                client_cert,
                debug,
            )
        print(
            f"Created alert rule: {alert_rule['title']}, status: {result[0]}, msg: {result[1]}"
        )
    else:
        print(
            f"Unable to create alert rules, requires Grafana version {MINIMUM_GRAFANA_VERSION} or above. Current version is {current_grafana_version}"
        )
