#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/env/local.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  cat >&2 <<EOW
[run_dev] Missing env file: ${ENV_FILE}
Create one by copying env/local.env.example and filling in your local Supabase values.
EOW
  exit 1
fi

DEVICE_ID=""
PASSTHRU=()
LAN_REQUESTED=false
LAN_IP=""
LAN_INTERFACE=""
DEVICE_LABEL=""
BUILD_MODE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--device)
      if [[ $# -lt 2 ]]; then
        echo "[run_dev] Missing value for $1" >&2
        exit 1
      fi
      DEVICE_ID="$2"
      shift 2
      ;;
    --device=*)
      DEVICE_ID="${1#*=}"
      shift
      ;;
    --list-devices)
      flutter devices
      exit 0
      ;;
    --lan)
      LAN_REQUESTED=true
      shift
      ;;
    --lan-ip)
      if [[ $# -lt 2 ]]; then
        echo "[run_dev] Missing value for $1" >&2
        exit 1
      fi
      LAN_IP="$2"
      shift 2
      ;;
    --lan-ip=*)
      LAN_IP="${1#*=}"
      shift
      ;;
    --lan-interface)
      if [[ $# -lt 2 ]]; then
        echo "[run_dev] Missing value for $1" >&2
        exit 1
      fi
      LAN_INTERFACE="$2"
      shift 2
      ;;
    --lan-interface=*)
      LAN_INTERFACE="${1#*=}"
      shift
      ;;
    --profile)
      BUILD_MODE="profile"
      shift
      ;;
    --release)
      BUILD_MODE="release"
      shift
      ;;
    --debug)
      BUILD_MODE="debug"
      shift
      ;;
    *)
      PASSTHRU+=("$1")
      shift
      ;;
  esac
done

choose_device() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "[run_dev] python3 is required for interactive device selection. Install it or pass -d <device_id>." >&2
    return 1
  fi
  local devices_json=""
  if ! devices_json=$(flutter devices --machine); then
    echo "[run_dev] Unable to list devices. Try 'flutter devices' manually." >&2
    return 1
  fi

  local entries=()
  local parsed_devices=""
  if ! parsed_devices=$(
    DEVICES_JSON="${devices_json}" python3 - <<'PY'
import json
import os
import sys

def describe(entry):
    platform = entry.get('platform') or entry.get('targetPlatform') or entry.get('platformType') or 'unknown'
    category = entry.get('category') or entry.get('platformType') or ''
    emulator = entry.get('emulator')
    ephemeral = entry.get('ephemeral')
    labels = []
    if category and category not in platform:
        labels.append(category)
    if emulator or (ephemeral is True):
        labels.append('emulator')
    elif ephemeral is False:
        labels.append('device')
    name = entry.get('name') or entry.get('emulatorId') or entry.get('deviceName') or entry.get('model')
    if not name:
        name = entry.get('id')
    suffix = f" ({', '.join(labels)})" if labels else ''
    return f"{name} • {platform}{suffix}"

def main():
    payload = os.environ.get('DEVICES_JSON') or '[]'
    try:
        devices = json.loads(payload)
    except json.JSONDecodeError:
        sys.exit(1)

    for device in devices:
        device_id = device.get('id')
        name = describe(device)
        if device_id and name:
            print(f"{device_id}::{name}")

if __name__ == '__main__':
    main()
PY
  ); then
    echo "[run_dev] Failed to parse Flutter device list." >&2
    return 1
  fi

  if [[ -n "${parsed_devices}" ]]; then
    while IFS= read -r line; do
      [[ -z "${line}" ]] && continue
      entries+=("${line}")
    done <<<"${parsed_devices}"
  fi

  local count="${#entries[@]}"
  if [[ "${count}" -eq 0 ]]; then
    echo "[run_dev] No Flutter devices detected. Connect one or use an emulator." >&2
    return 1
  fi

  if [[ "${count}" -eq 1 ]]; then
    DEVICE_ID="${entries[0]%%::*}"
    DEVICE_LABEL="${entries[0]#*::}"
    echo "[run_dev] Using ${DEVICE_LABEL} (${DEVICE_ID})." >&2
    return 0
  fi

  if [[ ! -t 0 || ! -t 1 ]]; then
    echo "[run_dev] Multiple devices detected. Re-run with -d <device_id> or --list-devices." >&2
    return 1
  fi

  echo "[run_dev] Select a target device:"
  local options=("${entries[@]}" "Cancel")
  local selection=""
  local index=0

  PS3="[run_dev] Choice: "
  select selection in "${options[@]}"; do
    index="${REPLY:-0}"
    if [[ "${selection}" == "Cancel" ]]; then
      echo "[run_dev] Cancelled by user." >&2
      return 1
    fi
    if [[ -n "${selection}" && "${index}" -ge 1 && "${index}" -le "${count}" ]]; then
      DEVICE_ID="${selection%%::*}"
      DEVICE_LABEL="${selection#*::}"
      echo "[run_dev] Using ${DEVICE_LABEL} (${DEVICE_ID})." >&2
      return 0
    fi
    echo "[run_dev] Invalid selection. Try again." >&2
  done

  return 1
}

if [[ -z "${DEVICE_ID}" ]]; then
  if ! choose_device; then
    exit 1
  fi
fi

CMD=(flutter run --dart-define-from-file="${ENV_FILE}")

if [[ -n "${BUILD_MODE}" ]]; then
  echo "[run_dev] Using build mode: ${BUILD_MODE}" >&2
  CMD+=(--${BUILD_MODE})
fi

if [[ "${LAN_REQUESTED}" == true && -z "${LAN_IP}" ]]; then
  detect_ip() {
    local ip=""
    if command -v ipconfig >/dev/null 2>&1; then
      local iface="${LAN_INTERFACE:-en0}"
      ip=$(ipconfig getifaddr "${iface}" 2>/dev/null || true)
      if [[ -z "${ip}" && -z "${LAN_INTERFACE}" ]]; then
        ip=$(ipconfig getifaddr en1 2>/dev/null || true)
      fi
    fi
    if [[ -z "${ip}" ]]; then
      if command -v hostname >/dev/null 2>&1; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
      fi
    fi
    if [[ -z "${ip}" ]]; then
      if command -v ip >/dev/null 2>&1; then
        ip=$(ip -4 addr show scope global | awk '/inet / {sub(/\/.*$/, "", $2); print $2; exit}')
      fi
    fi
    echo "${ip}"
  }

  LAN_IP=$(detect_ip)
  if [[ -z "${LAN_IP}" ]]; then
    echo "[run_dev] Unable to detect LAN IP. Use --lan-ip <address> or --lan-interface <iface>." >&2
    exit 1
  fi
fi

if [[ -n "${LAN_IP}" ]]; then
  echo "[run_dev] Using LAN IP ${LAN_IP} for Supabase/Postgres/Backend endpoints." >&2
  CMD+=(
    --dart-define="SUPABASE_URL=http://${LAN_IP}:54321"
    --dart-define="POSTGRES_HOST=${LAN_IP}"
    --dart-define="POSTGRES_PORT=54322"
    --dart-define="POSTGRES_DATABASE=postgres"
    --dart-define="BASE_URL=http://${LAN_IP}:8000/dashboard"
  )
fi

if [[ -n "${DEVICE_ID}" ]]; then
  CMD+=(-d "${DEVICE_ID}")
fi

if [[ ${#PASSTHRU[@]} -gt 0 ]]; then
  CMD+=("${PASSTHRU[@]}")
fi

"${CMD[@]}"
