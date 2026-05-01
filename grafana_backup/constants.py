import os

homedir = os.path.expanduser("~")

PKG_NAME = "grafana-backup"
PKG_VERSION = "v1.6.2"
JSON_CONFIG_PATH = "{0}/.grafana-backup.json".format(homedir)
