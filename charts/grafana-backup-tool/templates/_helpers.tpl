{{/*
Expand the name of the chart.
*/}}
{{- define "grafana-backup-tool.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "grafana-backup-tool.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "grafana-backup-tool.labels" -}}
helm.sh/chart: {{ include "grafana-backup-tool.chart" . }}
{{ include "grafana-backup-tool.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "grafana-backup-tool.selectorLabels" -}}
app.kubernetes.io/name: {{ include "grafana-backup-tool.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}