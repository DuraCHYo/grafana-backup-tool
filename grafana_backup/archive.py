from glob import glob
import os
import tarfile
import shutil
from grafana_backup.components import registry as rg


def main(args, settings):
    backup_dir = settings.get("BACKUP_DIR")
    timestamp = settings.get("TIMESTAMP")

    archive_file = "{0}/{1}.tar.gz".format(backup_dir, timestamp)
    backup_files = list()
    folders_to_clean = set()

    print("Searching for backup components...")

    for component in rg.get_all_components():
        variants = [component, component.replace("-", "_")]

        for folder_name in set(variants):
            search_path = os.path.join(backup_dir, folder_name, timestamp)
            found_paths = glob(search_path)

            if found_paths:
                for file_path in found_paths:
                    print("Found {0} at: {1}".format(folder_name, file_path))
                    backup_files.append(file_path)
                    folders_to_clean.add(os.path.abspath(file_path))
                break

    if not backup_files:
        print("No backup files found to archive.")
        return

    if os.path.exists(archive_file):
        os.remove(archive_file)

    print("\nCreating archive...")
    with tarfile.open(archive_file, "w:gz") as tar:
        for file_path in backup_files:
            component_name = os.path.basename(os.path.dirname(file_path))
            tar.add(file_path, arcname=component_name)

    print("Archive created at: {0}".format(archive_file))

    print("\nCleaning up temporary files...")
    for folder in folders_to_clean:
        try:
            shutil.rmtree(folder)
            parent_dir = os.path.dirname(folder)
            if not os.listdir(parent_dir):
                os.rmdir(parent_dir)
        except Exception as e:
            print("Error cleaning up {0}: {1}".format(folder, e))

    print("Done!")
