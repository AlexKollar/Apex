# Recovery: a seat that comes back dark

_For the operator, at the machine, when Apex does not answer after a
boot, an update, or a rollback. No step here needs sudo except the
linger note at the end, which says so._

## What "dark" usually means

On a boot (headless) install, Apex is started by two systemd **user**
units: `navi-llamafile.service` (the engine) and `navi-bridge.service`
(the bridge, on port 8675). If a unit's `ExecStart` points at a file
that no longer exists — the classic case is a tree that was replaced
or removed after the units were written — systemd fails the unit with
`203/EXEC` and nothing listens. The seat looks dead; the install is
usually intact.

Since v0.7.8e the updater's rollback re-aims and verifies the units
itself, and the apply confirmation refuses to call an update done
while a unit aims at a missing tree. This page is for when you are
already standing in front of the dark seat.

## 1. Find the live tree

The live tree is the folder that holds `bridge.py`, `start.sh` and
`VERSION` — by default `~/.local/share/navi-apex`. Parked and
temporary trees sit beside it with names like `.apex-prev`,
`.apex-stage`, `.apex-failed-*`: they are records, not the install.
Everything below works on the **live** tree only. Never run a parked
tree's bridge or helper to repair the seat — since v0.7.8e a bridge
running from a temporary tree refuses to arm the boot units, by name.

## 2. Read the units' aim

```sh
grep -H '^ExecStart' ~/.config/systemd/user/navi-*.service
systemctl --user status navi-llamafile.service navi-bridge.service
```

Each `ExecStart` path must be inside the live tree, and the file must
exist and be executable:

```sh
ls -l <the path each ExecStart names>
```

## 3. Repoint the units

Rewrite both units from the live tree's own templates, reload, clear
the failed state, and restart:

```sh
LIVE=~/.local/share/navi-apex        # your live tree, from step 1
sed "s|__INSTALL_DIR__|$LIVE|g" "$LIVE/systemd/navi-llamafile.service" > ~/.config/systemd/user/navi-llamafile.service
sed "s|__INSTALL_DIR__|$LIVE|g" "$LIVE/systemd/navi-bridge.service"    > ~/.config/systemd/user/navi-bridge.service
systemctl --user daemon-reload
systemctl --user reset-failed navi-llamafile.service navi-bridge.service
systemctl --user restart navi-llamafile.service navi-bridge.service
```

(The rollback helper does exactly this itself since v0.7.8e:
`python3 "$LIVE/apply-helper.py" --rollback` re-aims before it
relaunches, and fails by name if a unit still aims at nothing.)

## 4. Verify the seat answers

```sh
curl -s http://127.0.0.1:8675/api/status
```

You want `"app": "Navi: Apex"` in the answer, and both units `active`
in the status from step 2. If the bridge answers only after a login,
linger is off — that part does need sudo, once:

```sh
sudo loginctl enable-linger "$USER"
```

## If it is still dark

Work from the outside in: is the user manager running
(`systemctl --user status` answers at all), is linger on
(`loginctl show-user "$USER" -p Linger`), and what do the journals
say (`journalctl --user -u navi-bridge.service -n 50`). The install
record at `<live tree>/.apex-install-record` and the self-check
record at `<live tree>/config/install-self-check.json` name the
build and the last verdicts the product recorded about itself —
the self-check's `unitAim` entry, on v0.7.8e and later, says whether
the units aimed true the last time it ran.
