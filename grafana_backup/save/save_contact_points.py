import os

from grafana_backup.commons import print_horizontal_line, save_json
from grafana_backup.components.registry import MINIMUM_GRAFANA_VERSION
from grafana_backup.components.utils import get_grafana_version, status_code_validator
from grafana_backup.dashboardApi import search_contact_points


def main(args, settings):
    backup_dir = settings.get("BACKUP_DIR")
    timestamp = settings.get("TIMESTAMP")
    grafana_url = settings.get("GRAFANA_URL")
    http_get_headers = settings.get("HTTP_GET_HEADERS")
    verify_ssl = settings.get("VERIFY_SSL")
    client_cert = settings.get("CLIENT_CERT")
    debug = settings.get("DEBUG")
    pretty_print = settings.get("PRETTY_PRINT")
    folder_path = "{0}/contact_points/{1}".format(backup_dir, timestamp)

    current_grafana_version = get_grafana_version(
        grafana_url, verify_ssl, http_get_headers, client_cert, debug
    )

    if MINIMUM_GRAFANA_VERSION <= current_grafana_version:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        contact_points = get_all_contact_points_in_grafana(
            grafana_url, http_get_headers, verify_ssl, client_cert, debug
        )
        save_contact_points("contact_points", contact_points, folder_path, pretty_print)
    else:
        print(
            f"Unable to save contact points, requires Grafana version {MINIMUM_GRAFANA_VERSION} or above. Current version is {current_grafana_version}"
        )

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def get_all_contact_points_in_grafana(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    (status, content) = search_contact_points(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    if status_code_validator(status, 200):
        contact_points = content
        print(f"There are {len(contact_points)} contact points: ")
        for contact_point in contact_points:
            print(f"name: {contact_point['name']}, type: {contact_point['type']}")
        return contact_points
    else:
        print(f"query contact points failed, status: {status}, msg: {content}")
        return []


def save_contact_points(file_name, contact_points, folder_path, pretty_print):
    file_path = save_json(
        file_name, contact_points, folder_path, "contact_point", pretty_print
    )
    print_horizontal_line()
    print(f"contact points are saved to {file_path}")
    print_horizontal_line()
