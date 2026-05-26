import json

from grafana_backup.components.registry import MINIMUM_GRAFANA_VERSION
from grafana_backup.components.utils import get_grafana_version, status_code_validator
from grafana_backup.dashboardApi import (
    create_contact_point,
    search_contact_points,
    update_contact_point,
)


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

        result = search_contact_points(
            grafana_url, http_post_headers, verify_ssl, client_cert, debug
        )
        status_code = result[0]
        existing_contact_points = []
        if status_code_validator(status_code, 200):
            for ecp in result[1]:
                existing_contact_points.append(ecp["uid"])

        contact_points = json.loads(data)
        for cp in contact_points:
            if cp["uid"] in existing_contact_points:
                print("Contact point {0} already exists, updating".format(cp["uid"]))
                result = update_contact_point(
                    cp["uid"],
                    json.dumps(cp),
                    grafana_url,
                    http_post_headers,
                    verify_ssl,
                    client_cert,
                    debug,
                )
                if not status_code_validator(result[0], 202):
                    print(
                        f"[ERROR] Contact point {cp['uid']} failed to update. Return code:{result[0]} - {result[1]}"
                    )
            else:
                print(f"Contact point {cp['uid']} does not exist, creating")
                result = create_contact_point(
                    json.dumps(cp),
                    grafana_url,
                    http_post_headers,
                    verify_ssl,
                    client_cert,
                    debug,
                )
                if not status_code_validator(result[0], 202):
                    print(
                        f"[ERROR] Contact point {cp['uid']} failed to create. Return code:{result[0]} - {result[1]}"
                    )

    else:
        print(
            f"Unable to create contact points, requires Grafana version {MINIMUM_GRAFANA_VERSION} or above. Current version is {current_grafana_version}"
        )
