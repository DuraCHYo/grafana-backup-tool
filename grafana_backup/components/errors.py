class GrafanaUncompatibleVersionError(Exception):
    def __init__(self, minimum_version, current_version):
        self.minimum_version = minimum_version
        self.current_version = current_version
        super().__init__(
            f"Grafana version {current_version} is incompatible with the tool. Minimum required version is {minimum_version}."
        )


class GrafanaApiResourceNotFoundError(Exception):
    def __init__(self, endpoint):
        self.endpoint = endpoint
        super().__init__(f"API resource not found: {endpoint}")


class GrafanaApiError(Exception):
    def __init__(self, message):
        super().__init__(f"API error: {message}")
