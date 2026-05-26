from urllib.parse import urljoin

import requests

import grafana_backup.components.errors as errors


class GrafanaApiClient:
    def __init__(
        self, base_url="", headers=None, verify_ssl=False, client_cert=None, debug=False
    ):
        self.base_url = base_url
        self.headers = headers if headers is not None else {}
        self.verify_ssl = verify_ssl
        self.client_cert = client_cert
        self.debug = debug
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    r = requests

    def get(self, endpoint):
        url = urljoin(self.base_url, endpoint.lstrip("/"))

        if self.debug:
            print(f"GET request to {url}")

        r = self.session.get(url, verify=self.verify_ssl, cert=self.client_cert)

        # Handler for 404
        if r.status_code == 404:
            if self.debug:
                print(f"Resource not found at {url}, returning empty dict")
            return r.status_code, {}

        # Check for non 2xx responses
        if not r.ok:
            # Raise errors class exceptions
            raise errors.GrafanaApiError(f"HTTP {r.status_code}: {r.text}")

        # Try to get JSON
        try:
            if self.debug:
                print(f"Response status: {r.status_code}")
            return r.status_code, r.json()
        except requests.exceptions.JSONDecodeError:
            # Return {}, if JSON is empty or invalid
            return r.status_code, {}

    def post(self, endpoint, json_payload=None):
        url = urljoin(self.base_url, endpoint.lstrip("/"))

        if self.debug:
            print(f"POST request to {url}")

        r = self.session.post(
            url, data=json_payload, verify=self.verify_ssl, cert=self.client_cert
        )

        # Check for non 2xx responses
        if not r.ok:
            # Raise errors class exceptions
            raise errors.GrafanaApiError(f"HTTP {r.status_code}: {r.text}")

        # Try to get JSON
        try:
            if self.debug:
                print(f"Response status: {r.status_code}")
            return r.status_code, r.json()
        except requests.exceptions.JSONDecodeError:
            # Return {}, if JSON is empty or invalid
            return r.status_code, r.text

    def put(self, endpoint, json_payload=None):
        url = urljoin(self.base_url, endpoint.lstrip("/"))

        if self.debug:
            print(f"PUT request to {url}")

        r = self.session.put(
            url, data=json_payload, verify=self.verify_ssl, cert=self.client_cert
        )

        # Check for non 2xx responses
        if not r.ok:
            # Raise errors class exceptions
            raise errors.GrafanaApiError(f"HTTP {r.status_code}: {r.text}")

        # Try to get JSON
        try:
            if self.debug:
                print(f"Response status: {r.status_code}")
            return r.status_code, r.json()
        except requests.exceptions.JSONDecodeError:
            # Return {}, if JSON is empty or invalid
            return r.status_code, r.text

    def delete(self, endpoint):
        url = urljoin(self.base_url, endpoint.lstrip("/"))

        if self.debug:
            print(f"DELETE request to {url}")

        r = self.session.delete(url, verify=self.verify_ssl, cert=self.client_cert)

        # Check for non 2xx responses
        if not r.ok:
            # Raise errors class exceptions
            raise errors.GrafanaApiError(f"HTTP {r.status_code}: {r.text}")

        # Try to get JSON
        try:
            if self.debug:
                print(f"Response status: {r.status_code}")
            return r.status_code, r.json()
        except requests.exceptions.JSONDecodeError:
            # Возвращаем {}, если JSON пустой или невалидный
            return r.status_code, r.text
