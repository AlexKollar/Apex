#!/usr/bin/env python3
# Apex container first boot (0.2.0e Build 7).
#
# Runs on EVERY container start, from the entrypoint, before
# anything serves. Almost everything it can do is gated on the
# volume's first boot (APEX_FIRST_BOOT, set by the entrypoint
# only when it just seeded the volume); on later boots it is a
# quiet no-op that re-prints nothing. What it does, in order,
# all of it through the bridge's OWN machinery — this file
# invents no second way of doing any of it:
#
#   1. The container posture (first boot): DHD enabled (the
#      no-domain first run — self-signed certificate, access
#      code), Mesh enabled, the node named from APEX_NODE_NAME
#      when given, the declared public endpoint seeded from
#      APEX_PUBLIC_ENDPOINT when given. Bare metal is untouched
#      by all of this: nothing here runs there, and the tree's
#      shipped defaults are exactly as shipped.
#   2. The node's identity (first boot): the Mesh keypair and
#      the door certificate, minted by mesh_ensure_identity /
#      mesh_ensure_cert into the volume. Born on the machine
#      that runs them; never baked in, never backed up.
#   3. The access code: on the first boot a FRESH code is
#      minted — the config's shipped placeholder is never
#      inherited by a container node, because a code everyone
#      can read is a vulnerability, not a feature. The mint is
#      announced in a boxed banner, printed ONCE, here, and the
#      same banner is kept in FIRST-BOOT.txt in the volume.
#      Later boots never re-print it; the deliberate doors are
#      the bridge's own: `python3 bridge.py --dhd-code`
#      (re-print) and `--dhd-code-reset` (a new code).
#   4. The federation invitation (0.2.0e Build 8, first boot):
#      an image built to join a fedinet carries the gateway's
#      card at docker/gateway-card.png. When it is present, it
#      is copied into the volume as the waiting invitation
#      (config/federation/invitation.png); the bridge imports
#      it at start — ADMISSION ONLY: the node is introduced to
#      the gateway, and nothing lends until the fedinet's
#      signed roster syncs. The card is public data (a pairing
#      card's facts + the gateway's signature); the gateway's
#      identity never leaves the gateway — the card is minted
#      THERE, never in the image build's audience. An image
#      carrying no card simply starts unfederated. (The tree's
#      docker/sample-gateway-card.png is a SAMPLE — its shape,
#      with sample facts — never wired as an invitation.)
import importlib.util
import os
import shutil
import socket
import sys

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(APP)
sys.path.insert(0, APP)


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "bridgeFirstBoot", os.path.join(APP, "bridge.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def banner(code, name, fingerprint, node_id):
    bar = "=" * 68
    lines = [
        bar,
        "  YOUR DHD ACCESS CODE — WRITE IT DOWN OR TAKE A PHOTO NOW",
        "",
        "      Code:  " + code,
        "      Node:  " + name + "  ·  node " + (node_id[:12] if node_id else "—"),
        "      Mesh fingerprint:  " + fingerprint,
        "",
        "  This code is the ONLY key to this node's DHD door on your",
        "  network, and the door is already on: browse to this",
        "  computer's address (https — the DHD door Docker publishes",
        "  on port 443), type the code once, name your device, and",
        "  you are in. Every device after the first waits for an",
        "  approval from one that is already trusted, and your Mesh",
        "  pairing card waits on the dashboard's Mesh page.",
        "",
        "  This is the only time the code is printed in these logs.",
        "  A copy of this banner is kept in FIRST-BOOT.txt in the",
        "  data volume. If you lose the code anyway, the Docker",
        "  page of the Apex docs has the one command that brings",
        "  it back — you will need access to this computer.",
        bar,
    ]
    return "\n".join(lines)


def main():
    first = os.environ.get("APEX_FIRST_BOOT") == "1"
    container = os.environ.get("APEX_CONTAINER") == "1"
    bridge = load_bridge()
    cfg = bridge.load_config()

    if container and first:
        # The posture (this node's first run only — an operator's
        # later changes to any of it are theirs and persist).
        bridge.dhd_save(cfg, {"enabled": True})
        cfg = bridge.load_config()
        block = cfg.get("mesh") if isinstance(cfg.get("mesh"), dict) else {}
        block = dict(block)
        block["enabled"] = True
        name_env = (os.environ.get("APEX_NODE_NAME") or "").strip()
        if name_env and not str(block.get("nodeName") or "").strip():
            block["nodeName"] = name_env[:80]
        ep_env = (os.environ.get("APEX_PUBLIC_ENDPOINT") or "").strip()
        if ep_env and not str(block.get("publicEndpoint") or "").strip():
            cleaned = bridge._mesh_endpoint_clean(ep_env)
            if cleaned:
                block["publicEndpoint"] = cleaned
        cfg["mesh"] = block
        bridge.save_config(cfg)
        cfg = bridge.load_config()

    if first:
        # The identity: minted here, by the bridge's own hands,
        # into the volume — the keypair and the door certificate
        # the pairing card will carry.
        bridge.mesh_ensure_identity(cfg)
        bridge.mesh_ensure_cert()
        cfg = bridge.load_config()

    if container and first:
        # The federation invitation (Build 8): the image's
        # bundled gateway card, when it carries one, becomes the
        # volume's waiting invitation. The bridge performs the
        # import itself at start (admission-only); here we only
        # place the file — first_boot invents no second import
        # path.
        bundled = os.path.join(APP, "docker", "gateway-card.png")
        waiting = os.path.join(APP, "config", "federation", "invitation.png")
        if os.path.isfile(bundled) and not os.path.exists(waiting):
            os.makedirs(os.path.dirname(waiting), exist_ok=True)
            shutil.copyfile(bundled, waiting)
            print("Apex container: a bundled gateway card rides this "
                  "image — it waits as this node's federation "
                  "invitation and is imported, admission-only, at "
                  "start.", flush=True)

    # The access code. First boot mints fresh, unconditionally:
    # whatever the shipped config carries as a placeholder is
    # not this node's code. Any later boot keeps the node's own
    # code exactly as it stands — minting again only if the code
    # is somehow absent (a volume repaired by hand), which is a
    # first-boot-class event and is announced the same way.
    minted = False
    if first:
        block = cfg.get("public_server") if isinstance(cfg.get("public_server"), dict) else {}
        block = dict(block)
        block["access_code"] = bridge.generate_access_code()
        if "enabled" not in block:
            block["enabled"] = False
        cfg["public_server"] = block
        bridge.save_config(cfg)
        code = block["access_code"]
        minted = True
    elif not bridge.public_settings(cfg)["access_code"]:
        code = bridge.ensure_access_code(cfg)
        minted = True
    else:
        code = bridge.public_settings(cfg)["access_code"]

    if minted:
        cfg = bridge.load_config()
        ms = bridge.mesh_settings(cfg)
        name = ms["nodeName"] or socket.gethostname()
        text = banner(code, name, bridge.mesh_cert_fingerprint() or "—",
                      bridge.mesh_node_id() or "")
        print(text, flush=True)
        keep = os.path.join(APP, "FIRST-BOOT.txt")
        if not os.path.exists(keep):
            with open(keep, "w", encoding="utf-8") as f:
                f.write(text + "\n")
    else:
        print("Apex container: existing node configuration found — "
              "starting with its saved identity and code "
              "(nothing re-printed).", flush=True)


if __name__ == "__main__":
    main()
