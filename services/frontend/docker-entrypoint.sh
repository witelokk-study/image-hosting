#!/bin/sh
set -e

# Allows overriding the API base URL at container runtime.
: "${API_BASE_URL:=http://localhost:8080}"

cat >/usr/share/nginx/html/config.js <<EOF
window.APP_CONFIG = { apiBaseUrl: "${API_BASE_URL%/}" };
EOF
