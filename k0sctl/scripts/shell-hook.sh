#!/bin/sh

CONFIG_FILE="k0sctl.yaml"
STAMP_FILE=".k0sctl.yaml.sha256"
OUT_FILE="kubeconfig.yaml"

if [ ! -f "$OUT_FILE" ] || ! sha256sum --check --status "$STAMP_FILE" 2>/dev/null; then
    k0sctl kubeconfig --config "$CONFIG_FILE" > "$OUT_FILE"
    chmod 600 "$OUT_FILE"
    sha256sum "$CONFIG_FILE" > "$STAMP_FILE"
fi

export KUBECONFIG="$PWD/$OUT_FILE"
