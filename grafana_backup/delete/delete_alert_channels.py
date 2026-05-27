from grafana_backup.commons import print_horizontal_line
from grafana_backup.components.registry import register_component
from grafana_backup.components.utils import status_code_validator
from grafana_backup.dashboardApi import (
    delete_alert_channel_by_id,
    delete_alert_channel_by_uid,
    search_alert_channels,
)


@register_component("delete", "alert-channels")
def main(args, settings):
    grafana_url = settings.get("GRAFANA_URL")
    http_get_headers = settings.get("HTTP_POST_HEADERS")
    verify_ssl = settings.get("VERIFY_SSL")
    client_cert = settings.get("CLIENT_CERT")
    debug = settings.get("DEBUG")

    alert_channels = get_all_alert_channels_in_grafana(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    get_individual_alert_channel_and_delete(
        alert_channels,
        grafana_url,
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )
    print_horizontal_line()


def get_all_alert_channels_in_grafana(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    (status, content) = search_alert_channels(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    if status_code_validator(status, 200):
        channels = content
        print(f"There are {len(channels)} channels:")
        for channel in channels:
            print(f"name: {channel['name']}")
        return channels
    else:
        print(f"query alert channels failed, status: {status}, msg: {content}")
        return []


def get_individual_alert_channel_and_delete(
    channels,
    grafana_url,
    http_get_headers,
    verify_ssl,
    client_cert,
    debug,
):
    if channels:
        for channel in channels:
            if "uid" in channel:
                status = delete_alert_channel_by_uid(
                    channel["uid"],
                    grafana_url,
                    http_get_headers,
                    verify_ssl,
                    client_cert,
                    debug,
                )
            else:
                status = delete_alert_channel_by_id(
                    channel["id"],
                    grafana_url,
                    http_get_headers,
                    verify_ssl,
                    client_cert,
                    debug,
                )

            if status_code_validator(status, 200):
                print(f"alert_channel:{channel['name']} is deleted")
            else:
                print(f"deleting alert_channel {channel['name']} failed with {status}")
