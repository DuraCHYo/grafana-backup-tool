import requests

from grafana_backup.components.utils import status_code_validator  #  # noqa: F401
from grafana_backup.core.send_requests import GrafanaApiClient


def get_all_folders(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    url = f"{grafana_url}/apis/folder.grafana.app/v1/namespaces/default/folders"

    try:
        status_code, json_response = client.get(url)
        print(json_response)
        # data = json_response.json()
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"Error: {e}")
        return []

    result = []
    items = json_response.get("items", [])

    for item in items:
        metadata = item.get("metadata", {})
        spec = item.get("spec", {})

        name = metadata.get("name")
        uid = metadata.get("uid")
        title = spec.get("title")

        if name and uid:
            result.append((name, uid, title))

    return result


def get_folder_by_uid(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug, uid
):
    url = f"{grafana_url}/apis/folder.grafana.app/v1/namespaces/default/folders/{uid}"
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    try:
        status_code, json_response = client.get(url)
        result = []
        # data = json_response.json()
        result.append((
            json_response.get("metadata", {}).get("name"),
            json_response.get("metadata", {}).get("uid"),
            json_response.get("spec", {}).get("title"),
        ))
        return result
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"Error: {e}")
        return (None, str(e))


def create_folder(
    folder_json, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    client = GrafanaApiClient(
        grafana_url, http_post_headers, verify_ssl, client_cert, debug
    )
    url = f"{grafana_url}/apis/folder.grafana.app/v1/namespaces/default/folders"
    try:
        response = client.post(url, json_payload=folder_json)
        return (response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"Error: {e}")
        return (None, str(e))


def update_folder(
    folder_json, grafana_url, http_post_headers, verify_ssl, client_cert, debug, uid
):
    client = GrafanaApiClient(
        grafana_url, http_post_headers, verify_ssl, client_cert, debug
    )
    url = f"{grafana_url}/apis/folder.grafana.app/v1/namespaces/default/folders/{uid}"
    try:
        response = client.post(url, json_payload=folder_json)
        return (response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"Error: {e}")
        return (None, str(e))


def delete_folder(
    grafana_url, http_delete_headers, verify_ssl, client_cert, debug, uid
):
    client = GrafanaApiClient(
        grafana_url, http_delete_headers, verify_ssl, client_cert, debug
    )
    url = f"{grafana_url}/apis/folder.grafana.app/v1/namespaces/default/folders/{uid}"
    try:
        response = client.delete(url)
        return (response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"Error: {e}")
        return (None, str(e))


if __name__ == "__main__":
    print(
        get_all_folders(
            "http://localhost:3000",
            {
                "Authorization": "Bearer glsa_B1pZjuj87lcnc7TSK6vBPSrhTFPLe70o_0d8785f9",
                "Content-Type": "application/json",
            },
            False,
            None,
            False,
        )
    )
