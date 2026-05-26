import os

from grafana_backup.commons import print_horizontal_line, save_json
from grafana_backup.components.registry import MINIMUM_GRAFANA_VERSION
from grafana_backup.components.utils import get_grafana_version, status_code_validator
from grafana_backup.dashboardApi import (
    search_alert_rules,
)


def main(args, settings):
    backup_dir = settings.get("BACKUP_DIR")
    timestamp = settings.get("TIMESTAMP")
    grafana_url = settings.get("GRAFANA_URL")
    http_get_headers = settings.get("HTTP_GET_HEADERS")
    verify_ssl = settings.get("VERIFY_SSL")
    client_cert = settings.get("CLIENT_CERT")
    debug = settings.get("DEBUG")
    pretty_print = settings.get("PRETTY_PRINT")
    folder_path = "{0}/alert_rules/{1}".format(backup_dir, timestamp)
    log_file = "alert_rules_{0}.txt".format(timestamp)

    current_grafana_version = get_grafana_version(
        grafana_url, verify_ssl, http_get_headers, client_cert, debug
    )

    if MINIMUM_GRAFANA_VERSION <= current_grafana_version:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        save_alert_rules(
            folder_path,
            log_file,
            grafana_url,
            http_get_headers,
            verify_ssl,
            client_cert,
            debug,
            pretty_print,
        )
    else:
        print(
            f"Unable to save alert rules, requires Grafana version {MINIMUM_GRAFANA_VERSION} or above. Current version is {current_grafana_version}"
        )


def get_all_alert_rules_in_grafana(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    (status_code, json_response) = search_alert_rules(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    if status_code_validator(status_code):
        alert_rules = json_response
        print(f"There are {len(alert_rules)} alert rules:")
        for alert_rule in alert_rules:
            print(f"name: {alert_rule['title']}")
        return alert_rules
    else:
        raise Exception(
            f"Failed to get alert rules, status: {status_code}, msg: {json_response}"
        )


def save_alert_rules(
    folder_path,
    log_file,
    grafana_url,
    http_get_headers,
    verify_ssl,
    client_cert,
    debug,
    pretty_print,
):
    alert_rules = get_all_alert_rules_in_grafana(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    for alert_rule in alert_rules:
        print_horizontal_line()
        print(f"alert_rule: {alert_rule['title']}")
        file_path = save_json(
            alert_rule["uid"], alert_rule, folder_path, "alert_rule", pretty_print
        )
        print(f"alert_rule: {alert_rule['title']} -> saved to: {file_path}")
        print_horizontal_line()
