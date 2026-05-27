from grafana_backup.components.registry import VERSION_PATTERN
from grafana_backup.core.send_requests import GrafanaApiClient


def health_check(
    grafana_url: str,
    http_get_headers: dict,
    verify_ssl: bool,
    client_cert: None,
    debug: bool,
):
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    url = "/api/health"
    print(f"\n[Pre-Check] grafana health check: {url}")
    return client.get(url)


def auth_check(
    grafana_url: str,
    http_get_headers: dict,
    verify_ssl: bool,
    client_cert: None,
    debug: bool,
):
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    url = "/api/org"
    print(f"\n[Pre-Check] grafana auth check: {url}")
    return client.get(url)


def get_grafana_version(
    grafana_url: str,
    verify_ssl: bool,
    http_get_headers: dict,
    client_cert: None,
    debug: bool,
) -> int:
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    try:
        _, response = client.get(f"{grafana_url}/api/health")

        if not isinstance(response, dict) or "version" not in response:
            raise ValueError(f"Unexpected response format: {response}")

        version_str = response["version"]
        match = VERSION_PATTERN.search(version_str)

        if not match:
            raise ValueError(f"Could not parse version string: {version_str}")

        return int("".join(match.group(1).split(".")))

    except (ConnectionError, TimeoutError) as e:
        raise RuntimeError(f"Network error while fetching Grafana version: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve Grafana version: {e}") from e


def status_code_validator(status_code: int, expected_code: int = 200) -> bool:

    if status_code == expected_code:
        print(f"Status code {status_code} matches expected {expected_code}")
        return True
    else:
        print(f"Status code {status_code} does NOT match expected {expected_code}")
        return False
