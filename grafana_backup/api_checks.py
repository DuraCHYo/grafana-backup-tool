from grafana_backup.commons import print_horizontal_line
from grafana_backup.components.utils import (
    auth_check,
    health_check,
    status_code_validator,
)
from grafana_backup.dashboardApi import (
    contact_point_check,
    paging_feature_check,
    uid_feature_check,
)


def main(settings):
    grafana_url = settings.get("GRAFANA_URL")
    http_get_headers = settings.get("HTTP_GET_HEADERS")
    verify_ssl = settings.get("VERIFY_SSL")
    client_cert = settings.get("CLIENT_CERT")
    debug = settings.get("DEBUG")
    api_health_check = settings.get("API_HEALTH_CHECK")
    api_auth_check = settings.get("API_AUTH_CHECK")

    # TODO - refactor to use get_grafana_version from utils, and remove redundant code in utils
    # get_grafana_version(grafana_url, verify_ssl, http_get_headers, client_cert, debug)

    if api_health_check:
        (status_code, json_response) = health_check(
            grafana_url, http_get_headers, verify_ssl, client_cert, debug
        )
        if not status_code_validator(status_code, 200):
            return (status_code, json_response, None, None, None, None)

    if api_auth_check:
        (status_code, json_response) = auth_check(
            grafana_url, http_get_headers, verify_ssl, client_cert, debug
        )
        if not status_code_validator(status_code, 200):
            return (status_code, json_response, None, None, None, None)

    dashboard_uid_support, datasource_uid_support = uid_feature_check(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    if isinstance(dashboard_uid_support, str):
        raise Exception(dashboard_uid_support)
    if isinstance(datasource_uid_support, str):
        raise Exception(datasource_uid_support)

    paging_support = paging_feature_check(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    if isinstance(paging_support, str):
        raise Exception(paging_support)

    is_contact_point_available = contact_point_check(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )

    print_horizontal_line()
    if status_code_validator(status_code, 200):
        print("[Pre-Check] Server status is 'OK' !!")
    else:
        print(f"[Pre-Check] Server status is NOT OK !!: {json_response}")
    print_horizontal_line()

    return (
        status_code,
        json_response,
        dashboard_uid_support,
        datasource_uid_support,
        paging_support,
    )
