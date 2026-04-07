# Makefile
.PHONY: build shell backup restore test update_version

IMAGE_NAME := grafana-backup-tool
IMAGE_TAG := v1.6.1
GRAFANA_URL := http://localhost:3000
GRAFANA_TOKEN := SA_TOKEN
NEW_VERSION := X.Y.Z

build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

shell:
	docker run -it --rm $(IMAGE_NAME):$(IMAGE_TAG) sh

backup:
	docker run --rm \
		-e GRAFANA_URL=$(GRAFANA_URL) \
		-e GRAFANA_TOKEN=$(GRAFANA_TOKEN) \
		-e VERIFY_SSL=False \
		-v $(PWD)/backups:/opt/grafana-backup-tool/_OUTPUT_ \
		$(IMAGE_NAME):$(IMAGE_TAG) save

restore:
	docker run --rm \
		-e GRAFANA_URL=$(GRAFANA_URL) \
		-e GRAFANA_TOKEN=$(GRAFANA_TOKEN) \
		-e VERIFY_SSL=False \
		-v $(PWD)/backups:/opt/grafana-backup-tool/_OUTPUT_ \
		$(IMAGE_NAME):$(IMAGE_TAG) restore $(FILE)

test:
	docker run --rm $(IMAGE_NAME):$(IMAGE_TAG) help

logs:
	docker run --rm -e LOG_LEVEL=DEBUG $(IMAGE_NAME):$(IMAGE_TAG) save

update_version:
	sed -i '' 's/$(IMAGE_TAG)/$(NEW_VERSION)/g' VERSION
	sed -i '' 's/$(IMAGE_TAG)/$(NEW_VERSION)/g' charts/grafana-backup-tool/Chart.yaml
	sed -i '' 's/$(IMAGE_TAG)/$(NEW_VERSION)/g' charts/grafana-backup-tool/templates/cronjob.yaml
	sed -i '' 's/$(IMAGE_TAG)/$(NEW_VERSION)/g' README.md
	sed -i '' 's/$(IMAGE_TAG)/$(NEW_VERSION)/g' grafana_backup/constants.py
	sed -i '' 's/$(IMAGE_TAG)/$(NEW_VERSION)/g' setup.py