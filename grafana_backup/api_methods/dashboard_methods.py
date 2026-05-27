import requests

from grafana_backup.components.utils import status_code_validator  #  # noqa: F401
from grafana_backup.core.send_requests import GrafanaApiClient


def create_dashboard(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug, dashboard_data
):
    url = f"{grafana_url}/apis/dashboard.grafana.app/v1/namespaces/default/dashboards"
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    try:
        status_code, json_response = client.post(url, json_payload=dashboard_data)
        return status_code_validator(status_code, 200)
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"Error: {e}")
        return False


def update_dashboard(
    grafana_url,
    http_get_headers,
    verify_ssl,
    client_cert,
    debug,
    dashboard_name,
    dashboard_data,
):
    url = f"{grafana_url}/apis/dashboard.grafana.app/v1/namespaces/default/dashboards/{dashboard_name}"
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    try:
        status_code, json_response = client.put(url, json_payload=dashboard_data)
        return status_code_validator(status_code, 200)
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"Error: {e}")
        return False


def get_dashboard_by_uid(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug, dashboard_name
):
    url = f"{grafana_url}/apis/dashboard.grafana.app/v1/namespaces/default/dashboards/{dashboard_name}"
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    try:
        status_code, json_response = client.get(url)
        if status_code_validator(status_code, 200):
            return json_response
        else:
            if debug:
                print(f"Failed to get dashboard: {json_response}")
            return None
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"Error: {e}")
        return None


def list_dashboards(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    url = f"{grafana_url}/apis/dashboard.grafana.app/v1/namespaces/default/dashboards"
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    try:
        status_code, json_response = client.get(url)
        if status_code_validator(status_code, 200):
            return json_response.get("items", [])
        else:
            if debug:
                print(f"Failed to list dashboards: {json_response}")
            return []
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"Error: {e}")
        return []


def delete_dashboard(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug, dashboard_name
):
    url = f"{grafana_url}/apis/dashboard.grafana.app/v1/namespaces/default/dashboards/{dashboard_name}"
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    try:
        status_code, json_response = client.delete(url)
        return status_code_validator(status_code, 200)
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"Error: {e}")
        return False
