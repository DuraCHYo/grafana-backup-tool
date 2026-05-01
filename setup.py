from setuptools import setup, find_packages

setup(
    name="grafana-backup-tool",
    version="v1.6.2",
    packages=find_packages(),
    install_requires=[
        "boto3",
        "requests",
        "azure-storage-blob",
        "google-cloud-storage",
        'python-dotenv',
        'setuptools',
        'docopt',
        'influxdb',
        'botocore',
        'packaging',
        'azure-core',
        'azure-storage-blob',
        'google-api-core'
    ],
    entry_points={
        "console_scripts": [
            "grafana-backup=grafana_backup.cli:main",
        ],
    },
    python_requires=">=3.10",
)