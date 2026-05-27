import json

from grafana_backup.components.registry import MINIMUM_GRAFANA_VERSION
from grafana_backup.components.utils import get_grafana_version
from grafana_backup.dashboardApi import update_notification_policy


def main(args, settings, file_path):
    grafana_url = settings.get("GRAFANA_URL")
    http_post_headers = settings.get("HTTP_POST_HEADERS")
    http_get_headers = settings.get("HTTP_GET_HEADERS")
    verify_ssl = settings.get("VERIFY_SSL")
    client_cert = settings.get("CLIENT_CERT")
    debug = settings.get("DEBUG")

    current_grafana_version = get_grafana_version(
        grafana_url, verify_ssl, http_get_headers, client_cert, debug
    )
    if MINIMUM_GRAFANA_VERSION <= current_grafana_version:
        with open(file_path, "r") as f:
            data = f.read()

        notification_policies = json.loads(data)
        result = update_notification_policy(
            json.dumps(notification_policies),
            grafana_url,
            http_post_headers,
            verify_ssl,
            client_cert,
            debug,
        )
        print(f"update notification_policy, status: {result[0]}, msg: {result[1]}")
    else:
        print(
            f"Unable to update notification policy, requires Grafana version {MINIMUM_GRAFANA_VERSION} or above. Current version is {current_grafana_version}"
        )
