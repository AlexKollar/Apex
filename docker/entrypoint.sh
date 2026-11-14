#!/usr/bin/env bash
# Apex container entrypoint (0.2.0e Build 7).
#
#   1. First boot only: seed the data volume from the image's
#      pristine tree, and say so — the volume's existence from
#      then on is how every later boot knows it is not the
#      first.
#   2. Run the first-boot step (docker/first_boot.py): on the
#      first boot it gives the node its container posture (DHD
#      on, Mesh on), mints its identity and its DHD access code
#      with the bridge's own machinery, and prints the code's
#      boxed banner ONCE. On later boots it prints none of it.
#   3. The model: downloaded once to the volume, on first run,
#      exactly as the installer does it; skipped when present.
#   4. Launch headless — llamafile + the supervised bridge —
#      in the foreground: start.sh --headless is the same mode
#      the systemd unit runs on bare metal.
set -euo pipefail

APP=/opt/navi-apex
DIST=/opt/navi-apex-dist
export APEX_CONTAINER=1

if [ ! -f "$APP/bridge.py" ]; then
  echo "Apex container: first boot — seeding the data volume from the image."
  mkdir -p "$APP"
  cp -a "$DIST/." "$APP/"
  export APEX_FIRST_BOOT=1
fi

cd "$APP"
python3 docker/first_boot.py

if [ ! -f ./navi.llamafile ]; then
  echo "Apex container: downloading the model (navi.llamafile) — first run only; it is kept in the data volume."
  curl -fL --retry 3 -o navi.llamafile.part \
    "https://huggingface.co/saintssec/navi.llamafile/resolve/main/navi.llamafile"
  chmod +x navi.llamafile.part
  mv navi.llamafile.part navi.llamafile
fi

exec ./start.sh --headless
