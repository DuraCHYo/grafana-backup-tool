from grafana_backup.constants import PKG_NAME, PKG_VERSION, JSON_CONFIG_PATH
from grafana_backup.save import main as save
from grafana_backup.restore import main as restore
from grafana_backup.delete import main as delete
from grafana_backup.tools import main as tools
from grafana_backup.grafanaSettings import main as conf
from docopt import docopt
import os
import sys

docstring = """
{0} {1}

Usage:
    grafana-backup save [--config=<filename>] [--components=<>] [--no-archive]
    grafana-backup restore [--config=<filename>] [--components=<>] [<archive_file>]
    grafana-backup delete [--config=<filename>] [--components=<>]
    grafana-backup tools [-h | --help] [--config=<filename>] [<optional-command>] [<optional-argument>]
    grafana-backup [--config=<filename>]
    grafana-backup [-h | --help]
    grafana-backup --version

Options:
    -h --help                Show this help message and exit
    --version               Get version information and exit
    --config=<filename>      Override default configuration path
    --components=<>          Comma separated list of components
    --no-archive            Skip archive creation
""".format(PKG_NAME, PKG_VERSION)

def main():
    args = docopt(docstring, help=False, version="{0} {1}".format(PKG_NAME, PKG_VERSION))

    arg_config = args.get("--config", False)
    default_config = os.path.join(os.path.dirname(__file__), "conf", "grafanaSettings.json")

    if arg_config:
        settings = conf(arg_config)
    elif os.path.isfile(JSON_CONFIG_PATH):
        settings = conf(JSON_CONFIG_PATH)
    elif os.path.isfile(default_config):
        settings = conf(default_config)
    else:
        settings = conf() 

    is_save = args.get("save")
    is_restore = args.get("restore")
    is_delete = args.get("delete")
    is_tools = args.get("tools")

    if not any([is_save, is_restore, is_delete, is_tools]):
        env_mode = os.getenv("RESTORE", "false").lower()
        if env_mode == "true":
            is_restore = True
        else:
            is_save = True

    if is_save:
        save(args, settings)
    
    elif is_restore:
        archive = args.get("<archive_file>") or os.getenv("ARCHIVE_FILE")
        
        if not archive:
            print("Error: Restore mode active but no archive file provided.")
            print("Use: grafana-backup restore <file> OR set ENV ARCHIVE_FILE")
            sys.exit(1)

        backup_dir = settings.get("BACKUP_DIR", "_OUTPUT_")
        if not os.path.exists(archive) and os.path.exists(os.path.join(backup_dir, archive)):
            archive = os.path.join(backup_dir, archive)

        args["<archive_file>"] = archive
        restore(args, settings)

    elif is_delete:
        delete(args, settings)
    elif is_tools:
        tools(args, settings)
    else:
        print(docstring)

    sys.exit(0)

if __name__ == "__main__":
    main()