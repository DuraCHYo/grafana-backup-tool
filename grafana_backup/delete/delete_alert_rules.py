from grafana_backup.core.send_requests import GrafanaApiClient
from grafana_backup.save.save_alert_rules import get_all_alert_rules_in_grafana


def main(args, settings):
    grafana_url = settings.get("GRAFANA_URL")
    http_post_headers = settings.get("HTTP_POST_HEADERS")
    verify_ssl = settings.get("VERIFY_SSL")
    client_cert = settings.get("CLIENT_CERT")
    debug = settings.get("DEBUG")

    client = GrafanaApiClient(
        grafana_url, http_post_headers, verify_ssl, client_cert, debug
    )
    alert_rules = get_all_alert_rules_in_grafana(
        grafana_url, http_post_headers, verify_ssl, client_cert, debug
    )
    for rule in alert_rules:
        result = client.delete(
            f"{grafana_url}/api/v1/provisioning/alert-rules/{rule['uid']}"
        )
        print(
            f"Deleted alert rule: {rule['title']}, status: {result[0]}, msg: {result[1]}"
        )
