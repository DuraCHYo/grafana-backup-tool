FROM python:3.14-slim

WORKDIR /opt/grafana-backup-tool

COPY requirements.txt setup.py ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install --no-cache-dir .
RUN mkdir -p _OUTPUT_

# Окружение
ENV RESTORE=false
ENV ARCHIVE_FILE=""
ENV GRAFANA_URL="http://localhost:3000"

ENTRYPOINT ["grafana-backup"]

CMD ["save"]