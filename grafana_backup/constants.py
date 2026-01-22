import os


homedir = os.path.expanduser("~")

PKG_NAME = "grafana-backup"
PKG_VERSION = "1.4.7"
JSON_CONFIG_PATH = "{0}/.grafana-backup.json".format(homedir)
