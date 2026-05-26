import json

from grafana_backup.components.registry import MINIMUM_GRAFANA_VERSION
from grafana_backup.components.utils import get_grafana_version
from grafana_backup.dashboardApi import (
    create_alert_rule,
    get_alert_rule,
    update_alert_rule,
)


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
            f"create alert rule: {alert_rule['title']}, status: {result[0]}, msg: {result[1]}"
        )
    else:
        print(
            f"Unable to create alert rules, requires Grafana version {MINIMUM_GRAFANA_VERSION} or above. Current version is {current_grafana_version}"
        )
