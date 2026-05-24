from dataclasses import dataclass


@dataclass
class CoreSettings:
    url: str
    headers: dict
    verify_ssl: bool = False
    client_cert: str = ""
    debug: bool = False
    search_api_limit: int = 5000
    default_user_password: str = "00000000"
    version: int = 0
    admin_account: str = ""
    admin_password: str = ""


@dataclass
class GeneralSettings:
    debug: bool = True
    api_health_check: bool = True
    api_auth_check: bool = True
    backup_dir: str = "_OUTPUT_"
    backup_file_format: str = "%Y-%m-%d-%H-%M"
    uid_dashboard_slug_suffix: bool = False
    backup_workers: int = 3


@dataclass
class AwsSettings:
    s3_bucket_name: str = ""
    s3_bucket_key: str = ""
    default_region: str = ""
    access_key_id: str = ""
    secret_access_key: str = ""
    endpoint_url: str = ""


@dataclass
class AzureSettings:
    connection_string: str = ""
    container_name: str = ""


@dataclass
class GCPSettings:
    connection_string: str = ""
    bucket_name: str = ""
