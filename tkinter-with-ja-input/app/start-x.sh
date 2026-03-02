#!/usr/bin/env bash
set -x
exec 1>&2

DISPLAY="${DISPLAY:-:0}"
VT="${VT:-7}"

mkdir -p /var/log

/etc/init.d/dbus start

# Xorg起動（VTを掴んでKMSへ出す）
# -keeptty: VT保持、-nolisten tcp: TCP無効、-noreset: クライアント終了で落ちない
Xorg "${DISPLAY}" "vt${VT}" -keeptty -nolisten tcp -noreset \
  -logfile /var/log/Xorg.0.log &
XORG_PID=$!

cleanup() {
  # debug
  echo "Xorg: log in cleanup"
  cat /var/log/Xorg.0.log
  echo "Xorg: log- in cleanup"

  kill "${XORG_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# 起動待ち
for _ in $(seq 1 10); do
  xdpyinfo -display "${DISPLAY}" >/dev/null 2>&1 && break
  sleep 0.5
done
xdpyinfo -display "${DISPLAY}" >/dev/null 2>&1 || { echo "ERROR: Xorg did not start"; exit 1; }

echo "Xorg: log"
cat /var/log/Xorg.0.log
echo "Xorg: log-"

uid=$(id -u "idein")
gid=$(id -g "idein")

chown -R idein:idein /home/idein
export HOME=/home/idein

exec setpriv --reuid="$uid" --regid="$gid" --init-groups \
  dbus-run-session -- bash -lc '
    set -e

    XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/xdg-${UID}}"
    export XDG_RUNTIME_DIR
    mkdir -p "${XDG_RUNTIME_DIR}"
    chmod 700 "${XDG_RUNTIME_DIR}"

    fcitx5 -d --replace

    setxkbmap -layout ${KEYLAYOUT}

    openbox &
    xterm &
    exec "$@"
  ' -- "$@"
