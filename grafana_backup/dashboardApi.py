import json
import re
import sys

import requests

from grafana_backup.commons import log_response
from grafana_backup.core.send_requests import GrafanaApiClient

# Module-level session for connection pooling (HTTP keep-alive)
_session = requests.Session()


# core_config = CoreSettings(
#     url="http://localhost:3000",
#     headers={"Authorization": "Bearer your_token"},
#     verify_ssl=False,
#     client_cert="",
#     debug=False,
# )


def uid_feature_check(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    print("\n[Pre-Check] grafana uid feature check: calling 'search_dashboard'")
    (status, content) = search_dashboard(
        1, 1, grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    if status == 200 and len(content):
        if "uid" in content[0]:
            dashboard_uid_support = True
        else:
            dashboard_uid_support = False
    else:
        if len(content):
            dashboard_uid_support = (
                "get dashboards failed, status: {0}, msg: {1}".format(status, content)
            )
        else:
            # No dashboards exist, disable uid feature
            dashboard_uid_support = False
    # Get first datasource
    print("\n[Pre-Check] grafana uid feature check: calling 'search_datasource'")
    (status, content) = search_datasource(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    if status == 200 and len(content):
        if "uid" in content[0]:
            datasource_uid_support = True
        else:
            datasource_uid_support = False
    else:
        if len(content):
            datasource_uid_support = (
                "get datasources failed, status: {0}, msg: {1}".format(status, content)
            )
        else:
            # No datasources exist, disable uid feature
            datasource_uid_support = False

    return dashboard_uid_support, datasource_uid_support


def paging_feature_check(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    print("\n[Pre-Check] grafana paging_feature_check: calling 'search_dashboard'")

    def get_first_dashboard_by_page(page):
        (status, content) = search_dashboard(
            page, 1, grafana_url, http_get_headers, verify_ssl, client_cert, debug
        )
        if status == 200 and len(content):
            if sys.version_info[0] > 2:
                content[0] = {k: v for k, v in content[0].items()}
                dashboard_values = sorted(content[0].items(), key=lambda kv: str(kv[1]))
            return True, dashboard_values
        else:
            if len(content):
                return False, "get dashboards failed, status: {0}, msg: {1}".format(
                    status, content
                )
            else:
                return False, False

    (status, content) = get_first_dashboard_by_page(1)
    if status is False and content is False:
        return False  # Paging feature not supported
    elif status is True:
        dashboard_one_values = content
    else:
        return content  # Fail Message

    (status, content) = get_first_dashboard_by_page(2)
    if status is False and content is False:
        return False  # Paging feature not supported
    elif status is True:
        dashboard_two_values = content
    else:
        return content  # Fail Message

    return dashboard_one_values != dashboard_two_values


def contact_point_check(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    print("\n[Pre-Check] grafana contact_point api check")
    (status, content) = search_contact_points(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    if status == 200:
        return True
    else:
        return False


def search_dashboard(
    page, limit, grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    url = f"{grafana_url}/api/search/?type=dash-db&limit={limit}&page={page}"
    print(f"search dashboard in grafana: {url}")
    return client.get(url)


def get_dashboard(
    board_uri, grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    url = f"{grafana_url}/api/dashboards/{board_uri}"
    print(f"query dashboard uri: {url}")
    (status_code, content) = client.get(url)
    return (status_code, content)


def search_library_elements(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    url = f"{grafana_url}/api/library-elements?perPage=5000"
    print(f"search library-elements in grafana: {url}")
    return client.get(url)


def create_library_element(
    library_element, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    url = f"{grafana_url}/api/library-elements"
    return send_grafana_post(
        url, library_element, http_post_headers, verify_ssl, client_cert, debug
    )


def delete_library_element(
    id_, grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    return client.delete(f"{grafana_url}/api/library-elements/{id_}")


def search_teams(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    url = f"{grafana_url}/api/teams/search?perPage=5000"
    print(f"search teams in grafana: {url}")
    return send_grafana_get(url, http_get_headers, verify_ssl, client_cert, debug)


def create_team(team, grafana_url, http_post_headers, verify_ssl, client_cert, debug):
    url = f"{grafana_url}/api/teams"
    return send_grafana_post(
        url, team, http_post_headers, verify_ssl, client_cert, debug
    )


def delete_team(id_, grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    return send_grafana_delete(
        f"{grafana_url}/api/teams/{id_}",
        http_get_headers,
        verify_ssl,
        client_cert,
    )


def search_team_members(
    team_id, grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    url = f"{grafana_url}/api/teams/{team_id}/members"
    print(f"search team members in grafana: {url}")
    return send_grafana_get(url, http_get_headers, verify_ssl, client_cert, debug)


def create_team_member(
    user, team_id, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    url = f"{grafana_url}/api/teams/{team_id}/members"
    return send_grafana_post(
        url, user, http_post_headers, verify_ssl, client_cert, debug
    )


def delete_team_member(
    user_id, team_id, grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    return send_grafana_delete(
        f"{grafana_url}/api/teams/{team_id}/members/{user_id}",
        http_get_headers,
        verify_ssl,
        client_cert,
    )


def search_annotations(
    grafana_url, ts_from, ts_to, http_get_headers, verify_ssl, client_cert, debug
):
    # there are two types of annotations
    # annotation: are user created, custom ones and can be managed via the api
    # alert: are created by Grafana itself, can NOT be managed by the api
    url = f"{grafana_url}/api/annotations?type=annotation&limit=5000&from={ts_from}&to={ts_to}"
    (status_code, content) = send_grafana_get(
        url, http_get_headers, verify_ssl, client_cert, debug
    )
    return (status_code, content)


def create_annotation(
    annotation, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    url = f"{grafana_url}/api/annotations"
    return send_grafana_post(
        url, annotation, http_post_headers, verify_ssl, client_cert, debug
    )


def delete_annotation(
    id_, grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    return send_grafana_delete(
        f"{grafana_url}/api/annotations/{id_}",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def search_alert_rules(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    url = f"{grafana_url}/api/v1/provisioning/alert-rules"
    print(f"search alert rules in grafana: {url}")
    return send_grafana_get(url, http_get_headers, verify_ssl, client_cert, debug)


def get_alert_rule(uid, grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    url = f"{grafana_url}/api/v1/provisioning/alert-rules/{uid}"
    return send_grafana_get(url, http_get_headers, verify_ssl, client_cert, debug)


def create_alert_rule(
    alert, grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    url = f"{grafana_url}/api/v1/provisioning/alert-rules"
    return send_grafana_post(
        url, alert, http_get_headers, verify_ssl, client_cert, debug
    )


def delete_alert_rule(
    uid, grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    url = f"{grafana_url}/api/v1/provisioning/alert-rules/{uid}"
    return send_grafana_delete(url, http_get_headers, verify_ssl, client_cert, debug)


def update_alert_rule(
    uid, alert, grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    url = f"{grafana_url}/api/v1/provisioning/alert-rules/{uid}"
    return send_grafana_put(
        url, alert, http_get_headers, verify_ssl, client_cert, debug
    )


def search_alert_channels(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    url = f"{grafana_url}/api/alert-notifications"
    print(f"search alert channels in grafana: {url}")
    return send_grafana_get(url, http_get_headers, verify_ssl, client_cert, debug)


def create_alert_channel(
    payload, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_post(
        f"{grafana_url}/api/alert-notifications",
        payload,
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def delete_alert_channel_by_uid(
    uid, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_delete(
        f"{grafana_url}/api/alert-notifications/uid/{uid}",
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def delete_alert_channel_by_id(
    id_, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_delete(
        f"{grafana_url}/api/alert-notifications/{id_}",
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def search_alerts(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    url = f"{grafana_url}/api/alerts"
    (status_code, content) = send_grafana_get(
        url, http_get_headers, verify_ssl, client_cert, debug
    )
    return (status_code, content)


def pause_alert(id_, grafana_url, http_post_headers, verify_ssl, client_cert, debug):
    url = f"{grafana_url}/api/alerts/{id_}/pause"
    payload = '{ "paused": true }'
    (status_code, content) = send_grafana_post(
        url, payload, http_post_headers, verify_ssl, client_cert, debug
    )
    return (status_code, content)


def unpause_alert(id_, grafana_url, http_post_headers, verify_ssl, client_cert, debug):
    url = f"{grafana_url}/api/alerts/{id_}/pause"
    payload = '{ "paused": false }'
    (status_code, content) = send_grafana_post(
        url, payload, http_post_headers, verify_ssl, client_cert, debug
    )
    return (status_code, content)


def delete_folder(uid, grafana_url, http_post_headers, verify_ssl, client_cert, debug):
    return send_grafana_delete(
        f"{grafana_url}/api/folders/{uid}",
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def delete_snapshot(
    key, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_delete(
        f"{grafana_url}/api/snapshots/{key}",
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def delete_dashboard_by_uid(
    uid, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_delete(
        f"{grafana_url}/api/dashboards/uid/{uid}",
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def delete_dashboard_by_slug(
    slug, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_delete(
        f"{grafana_url}/api/dashboards/db/{slug}",
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def create_dashboard(
    payload, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_post(
        f"{grafana_url}/api/dashboards/db",
        payload,
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def search_datasource(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    print("search datasources in grafana:")
    return send_grafana_get(
        f"{grafana_url}/api/datasources",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def search_snapshot(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    print("search snapshots in grafana:")
    return send_grafana_get(
        f"{grafana_url}/api/dashboard/snapshots",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def get_snapshot(key, grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    url = f"{grafana_url}/api/snapshots/{key}"
    (status_code, content) = send_grafana_get(
        url, http_get_headers, verify_ssl, client_cert, debug
    )
    return (status_code, content)


def create_snapshot(
    payload, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_post(
        f"{grafana_url}/api/snapshots",
        payload,
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def create_datasource(
    payload, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_post(
        f"{grafana_url}/api/datasources",
        payload,
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def delete_datasource_by_uid(
    uid, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_delete(
        f"{grafana_url}/api/datasources/uid/{uid}",
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def delete_datasource_by_id(
    id_, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_delete(
        f"{grafana_url}/api/datasources/{id_}",
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def search_folders(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    print("search folder in grafana:")
    return send_grafana_get(
        f"{grafana_url}/api/search/?type=dash-folder",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def get_folder(uid, grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    (status_code, content) = send_grafana_get(
        f"{grafana_url}/api/folders/{uid}",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )
    print(f"query folder:{uid}, status:{status_code}")
    return (status_code, content)


def get_folder_permissions(
    uid, grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    (status_code, content) = send_grafana_get(
        f"{grafana_url}/api/folders/{uid}/permissions",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )
    print(f"query folder permissions:{uid}, status:{status_code}")
    return (status_code, content)


def update_folder_permissions(
    payload, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    items = json.dumps({"items": payload})
    return send_grafana_post(
        f"{grafana_url}/api/folders/{payload[0]['uid']}/permissions",
        items,
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def get_folder_id(
    dashboard, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    folder_uid = ""
    try:
        folder_uid = dashboard["meta"]["folderUid"]
    except KeyError:
        matches = re.search("dashboards\/f\/(.*)\/.*", dashboard["meta"]["folderUrl"])
        if matches is not None:
            folder_uid = matches.group(1)
        else:
            folder_uid = "0"

    if folder_uid != "":
        response = get_folder(
            folder_uid, grafana_url, http_post_headers, verify_ssl, client_cert, debug
        )
        if isinstance(response[1], dict):
            folder_data = response[1]
        else:
            folder_data = json.loads(response[1])

        try:
            return folder_data["id"]
        except KeyError:
            return 0
    else:
        return 0


def create_folder(
    payload, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_post(
        f"{grafana_url}/api/folders",
        payload,
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def get_dashboard_versions(
    dashboard_id, grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    (status_code, content) = send_grafana_get(
        f"{grafana_url}/api/dashboards/id/{dashboard_id}/versions",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )
    print(f"query dashboard versions: {dashboard_id}, status: {status_code}")
    return (status_code, content)


def get_version(
    dashboard_id,
    version_number,
    grafana_url,
    http_get_headers,
    verify_ssl,
    client_cert,
    debug,
):
    (status_code, content) = send_grafana_get(
        f"{grafana_url}/api/dashboards/id/{dashboard_id}/versions/{version_number}",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )
    print(
        f"query dashboard {dashboard_id} version {version_number}, status: {status_code}"
    )
    return (status_code, content)


def search_orgs(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    return send_grafana_get(
        f"{grafana_url}/api/orgs",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def get_org(
    id, grafana_url, http_get_headers, verify_ssl=False, client_cert=None, debug=True
):
    return send_grafana_get(
        f"{grafana_url}/api/orgs/{id}",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def create_org(payload, grafana_url, http_post_headers, verify_ssl, client_cert, debug):
    return send_grafana_post(
        f"{grafana_url}/api/orgs",
        payload,
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def update_org(
    id, payload, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_put(
        f"{grafana_url}/api/orgs/{id}",
        payload,
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def search_users(
    page, limit, grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    return send_grafana_get(
        f"{grafana_url}/api/users?perpage={limit}&page={page}",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def get_users(grafana_url, http_get_headers, verify_ssl, client_cert, debug):
    return send_grafana_get(
        f"{grafana_url}/api/org/users",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def set_user_role(
    user_id, role, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    json_payload = json.dumps({"role": role})
    url = f"{grafana_url}/api/org/users/{user_id}"
    r = requests.patch(
        url,
        headers=http_post_headers,
        data=json_payload,
        verify=verify_ssl,
        cert=client_cert,
    )
    return (r.status_code, r.json())


def get_user(
    id, grafana_url, http_get_headers, verify_ssl=False, client_cert=None, debug=True
):
    return send_grafana_get(
        f"{grafana_url}/api/users/{id}",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def get_user_by_email_or_username(
    email, grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    return send_grafana_get(
        f"{grafana_url}/api/users/lookup?loginOrEmail={email}",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def get_user_org(
    id, grafana_url, http_get_headers, verify_ssl=False, client_cert=None, debug=True
):
    return send_grafana_get(
        f"{grafana_url}/api/users/{id}/orgs",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def create_user(
    payload, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_post(
        f"{grafana_url}/api/admin/users",
        payload,
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def add_user_to_org(
    org_id, payload, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_post(
        f"{grafana_url}/api/orgs/{org_id}/users",
        payload,
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def search_contact_points(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    client = GrafanaApiClient(
        grafana_url, http_get_headers, verify_ssl, client_cert, debug
    )
    return client.get(f"{grafana_url}/api/v1/provisioning/contact-points")


def create_contact_point(
    json_palyload, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_post(
        f"{grafana_url}/api/v1/provisioning/contact-points",
        json_palyload,
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def update_contact_point(
    uid, json_palyload, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_put(
        f"{grafana_url}/api/v1/provisioning/contact-points/{uid}",
        json_palyload,
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def search_notification_policies(
    grafana_url, http_get_headers, verify_ssl, client_cert, debug
):
    return send_grafana_get(
        f"{grafana_url}/api/v1/provisioning/policies",
        http_get_headers,
        verify_ssl,
        client_cert,
        debug,
    )


def update_notification_policy(
    json_palyload, grafana_url, http_post_headers, verify_ssl, client_cert, debug
):
    return send_grafana_put(
        f"{grafana_url}/api/v1/provisioning/policies",
        json_palyload,
        http_post_headers,
        verify_ssl,
        client_cert,
        debug,
    )


# TODO DONE in REQUESTS CLASS
def send_grafana_get(url, http_get_headers, verify_ssl, client_cert, debug):
    r = _session.get(url, headers=http_get_headers, verify=verify_ssl, cert=client_cert)

    if debug:
        log_response(r)

    if r.status_code == 404:
        print(f"Warning: Resource not found at {url}, skipping...")
        return (404, {})  # Return empty JSON insead of error

    try:
        return (r.status_code, r.json())
    except requests.exceptions.JSONDecodeError:
        print(f"⚠ Warning: Received empty response from {url}, skipping...")
        return (r.status_code, {})  # Return empty JSON


# TODO DONE in REQUESTS CLASS
def send_grafana_post(
    url, json_payload, http_post_headers, verify_ssl=False, client_cert=None, debug=True
):
    r = requests.post(
        url,
        headers=http_post_headers,
        data=json_payload,
        verify=verify_ssl,
        cert=client_cert,
    )
    if debug:
        log_response(r)
    try:
        return (r.status_code, r.json())
    except ValueError:
        return (r.status_code, r.text)


# TODO DONE in REQUESTS CLASS
def send_grafana_put(
    url, json_payload, http_post_headers, verify_ssl=False, client_cert=None, debug=True
):
    r = requests.put(
        url,
        headers=http_post_headers,
        data=json_payload,
        verify=verify_ssl,
        cert=client_cert,
    )
    if debug:
        log_response(r)
    return (r.status_code, r.json())


# TODO DONE in REQUESTS CLASS
def send_grafana_delete(
    url, http_get_headers, verify_ssl=False, client_cert=None, debug=True
):
    r = requests.delete(
        url, headers=http_get_headers, verify=verify_ssl, cert=client_cert
    )
    return int(r.status_code)
