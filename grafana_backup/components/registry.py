import importlib
import re

MINIMUM_GRAFANA_VERSION = 940
VERSION_PATTERN = re.compile(r"(\d+\.\d+\.\d+)")

# TODO - refactor to use get_grafana_version from utils, and remove redundant code in utils
# def get_grafana_version(
#     grafana_url: str,
#     verify_ssl: bool,
#     http_get_headers: dict,
#     client_cert: None,
#     debug: bool,
# ) -> int:
#     client = GrafanaApiClient(
#         grafana_url, http_get_headers, verify_ssl, client_cert, debug
#     )
#     try:
#         status_code, response = client.get(f"{grafana_url}/api/health")

#         if not isinstance(response, dict) or "version" not in response:
#             raise ValueError(f"Unexpected response format: {response}")

#         version_str = response["version"]
#         match = VERSION_PATTERN.search(version_str)

#         if not match:
#             raise ValueError(f"Could not parse version string: {version_str}")

#         CURRENT_GRAFANA_VERSION = match.group(1).split(".")
#         return int("".join(CURRENT_GRAFANA_VERSION))
#     except (ConnectionError, TimeoutError) as e:
#         raise RuntimeError(f"Network error while fetching Grafana version: {e}") from e
#     except Exception as e:
#         raise RuntimeError(f"Failed to retrieve Grafana version: {e}") from e


COMPONENTS = {
    "core": [
        "dashboards",
        "datasources",
        "folders",
        "library-elements",
        "snapshots",
        "annotations",
        "dashboard-versions",
    ],
    "alerting": [
        "alert-rules",
        "contact-points",
        "notification-policy",
        "mute-timings",
        "alert-templates",
    ],
    "access": ["organizations", "users", "teams", "team-members", "service-accounts"],
}


def get_all_components():
    all_list = []
    for category in COMPONENTS.values():
        all_list.extend(category)
    return all_list


def load_component_functions(mode="save"):
    functions = {}
    all_names = get_all_components()

    for name in all_names:
        file_suffix = name.replace("-", "_")
        module_path = f"grafana_backup.{mode}.{mode}_{file_suffix}"

        try:
            module = importlib.import_module(module_path)
            functions[name] = module.main
        except ImportError:
            continue
    return functions
