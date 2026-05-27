import requests

from grafana_backup.components.utils import status_code_validator  #  # noqa: F401
from grafana_backup.core.send_requests import GrafanaApiClient


def list_playlists(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    url = f"{grafana_url}/apis/playlist.grafana.app/v1/namespaces/default/playlists"

    try:
        status_code, json_response = client.get(url)
        if debug:
            print(json_response)
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


def get_playlist_by_uid(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug, uid
):
    url = (
        f"{grafana_url}/apis/playlist.grafana.app/v1/namespaces/default/playlists/{uid}"
    )
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    try:
        status_code, json_response = client.get(url)
        result = []
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


def create_a_playlist(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug, playlist_data
):
    url = f"{grafana_url}/apis/playlist.grafana.app/v1/namespaces/default/playlists"
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    try:
        status_code, json_response = client.post(url, json_payload=playlist_data)
        if debug:
            print(json_response)
        return status_code
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"Error: {e}")
        return None


def update_a_playlist(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug, uid, playlist_data
):
    url = (
        f"{grafana_url}/apis/playlist.grafana.app/v1/namespaces/default/playlists/{uid}"
    )
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    try:
        status_code, json_response = client.put(url, json_payload=playlist_data)
        if debug:
            print(json_response)
        return status_code
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"Error: {e}")
        return None


def delete_a_playlist(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug, uid
):
    url = (
        f"{grafana_url}/apis/playlist.grafana.app/v1/namespaces/default/playlists/{uid}"
    )
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    try:
        status_code, json_response = client.delete(url)
        if debug:
            print(json_response)
        return status_code
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"Error: {e}")
        return None
