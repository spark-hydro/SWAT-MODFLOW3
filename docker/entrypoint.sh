#!/bin/sh
# Starts SWAT-MODFLOW3. Normal (fast) build by default; the debug build with -e DEBUG=1.
case "${DEBUG:-0}" in
  0|false|FALSE|False|no|NO|"")
    exec swatmf3-release "$@" ;;
  *)
    echo "[swatmf3 docker] DEBUG build: checks array bounds, about 3x slower." >&2
    exec swatmf3-debug "$@" ;;
esac
