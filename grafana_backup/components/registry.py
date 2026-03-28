import importlib

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
        module_path = f"grafana_backup.{mode}_{file_suffix}"

        try:
            module = importlib.import_module(module_path)
            functions[name] = module.main
        except ImportError:
            continue
    print(f"TUT {functions}")
    return functions
