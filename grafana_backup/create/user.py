import json

from grafana_backup.dashboardApi import add_user_to_org, create_user


def main(args, settings, file_path):
    """
    Cannot get user's password, use default password instead
    """
    grafana_url = settings.get("GRAFANA_URL")
    http_post_headers_basic_auth = settings.get("HTTP_POST_HEADERS_BASIC_AUTH")
    verify_ssl = settings.get("VERIFY_SSL")
    client_cert = settings.get("CLIENT_CERT")
    debug = settings.get("DEBUG")

    default_password = settings.get("DEFAULT_USER_PASSWORD")
    if http_post_headers_basic_auth:
        with open(file_path, "r") as f:
            data = f.read()

        user = json.loads(data)
        user.update({"password": default_password})

        result = create_user(
            json.dumps(user),
            grafana_url,
            http_post_headers_basic_auth,
            verify_ssl,
            client_cert,
            debug,
        )
        print(
            f'create user "{user.get("login", "")}" response status: {result[0]}, msg: {result[1]} \n'
        )

        if result[0] == 200:
            for org in user.get("orgs", []):
                org_payload = {
                    "loginOrEmail": user.get("login", "email"),
                    "role": org.get("role", "Viewer"),
                }
                result = add_user_to_org(
                    org.get("orgId"),
                    json.dumps(org_payload),
                    grafana_url,
                    http_post_headers_basic_auth,
                    verify_ssl,
                    client_cert,
                    debug,
                )
                print(
                    f'add user "{user.get("login", "")}" to org: {org.get("name", "")} response status: {result[0]}, msg: {result[1]}'
                )
    else:
        print(
            "[ERROR] Restoring users needs to set GRAFANA_ADMIN_ACCOUNT and GRAFANA_ADMIN_PASSWORD first. \n"
        )
