{{/*
Expand the name of the chart.
*/}}
{{- define "aura360.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "aura360.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "aura360.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "aura360.labels" -}}
helm.sh/chart: {{ include "aura360.chart" . }}
{{ include "aura360.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
environment: {{ .Values.global.environment }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "aura360.selectorLabels" -}}
app.kubernetes.io/name: {{ include "aura360.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Component-specific labels
*/}}
{{- define "aura360.componentLabels" -}}
{{ include "aura360.labels" . }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/*
Image name helper
*/}}
{{- define "aura360.image" -}}
{{- $values := .Values -}}
{{- $registry := $values.imageRegistry -}}
{{- $repository := .repository -}}
{{- $tag := .tag | default $values.imageTag | default "latest" -}}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "aura360.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "aura360.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
