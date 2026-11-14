# Apex — the container node (0.2.0e Build 7).
#
# One image, every architecture the runtime runs on: the bridge
# is Python (stdlib only) and navi.llamafile is a single
# polyglot binary that runs on x86_64 and ARM64 alike, so this
# file carries no architecture-specific anything. Build it with
# buildx for amd64 + arm64; the arm64 build is the same artifact
# family the Apex | Dropbox kit's image will descend from.
#
# NO IDENTITY IS BAKED INTO THIS IMAGE, EVER. The node's Mesh
# keypair, its door certificate, its pairing card, and its DHD
# access code are all minted at FIRST BOOT, inside the data
# volume, by the bridge's own machinery (docker/first_boot.py).
# A shipped keypair would make every copy the same node; a
# shipped access code would be a vulnerability, not a feature.
# The model binary is not baked in either: the entrypoint
# downloads navi.llamafile once, on first run, to the volume —
# the installer's own pattern — so the image stays small and
# the model persists across container replacements.
#
# The pristine tree rides at /opt/navi-apex-dist; the data
# volume mounts at /opt/navi-apex and is seeded from it on
# first boot. Everything that makes the node itself — identity,
# config, chats, chips, the model — lives in that one volume:
# the installer's preservation law, in container form.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      bash curl openssl openssh-client ca-certificates procps \
 && rm -rf /var/lib/apt/lists/*

COPY . /opt/navi-apex-dist/
RUN chmod +x /opt/navi-apex-dist/start.sh \
             /opt/navi-apex-dist/run-llamafile.sh \
             /opt/navi-apex-dist/install.sh \
             /opt/navi-apex-dist/docker/entrypoint.sh

# The container marker: the one flag the product reads to give
# a container node its container posture (DHD on at first boot,
# the gate page's first-boot hint). Bare metal never sets it,
# and its defaults are exactly as shipped.
ENV APEX_CONTAINER=1

VOLUME ["/opt/navi-apex"]

# The Mesh door (one door, one certificate, every number) and
# the DHD door (443, plus 80 for its certificate machinery).
EXPOSE 8765 8443 2475 443 80

ENTRYPOINT ["/opt/navi-apex-dist/docker/entrypoint.sh"]
