import importlib
import re

MINIMUM_GRAFANA_VERSION = 940
VERSION_PATTERN = re.compile(r"(\d+\.\d+\.\d+)")

# Registry for components
_COMPONENTS_REGISTRY = {"save": {}, "delete": {}}


def register_component(mode: str, name: str):

    def decorator(func):
        _COMPONENTS_REGISTRY[mode][name] = func
        return func

    return decorator


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
    """Loads all registered components for the selected mode

    Args:
        mode (str, optional): mode (str): Mode to import modules from (e.g., "save" or "delete"). Defaults to "save".

    Returns:
        _type_: _description_
    """
    # If the registry is empty, import all modules to initialize
    if not _COMPONENTS_REGISTRY[mode]:
        _import_all_modules(mode)

    return _COMPONENTS_REGISTRY[mode].copy()


def _import_all_modules(mode: str):
    """Imports all modules in the mode for initializing decorators.

    Args:
        mode (str): Mode to import modules from (e.g., "save" or "delete")
    """
    all_names = get_all_components()

    for name in all_names:
        file_suffix = name.replace("-", "_")
        module_path = f"grafana_backup.{mode}.{mode}_{file_suffix}"

        try:
            importlib.import_module(module_path)
        except ImportError:
            continue
