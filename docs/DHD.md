# DHD — Apex from anywhere

DHD — Dial-Home Device, the way home — is Apex's public door. Apex | Node [local] lets a phone on your home network open Apex; DHD extends the **same dashboard** to a genuinely public address, so you can reach the Apex on your own machine from anywhere — work, the road, anywhere with a browser.

Everything is Apex's own work, assembled and managed by Apex itself. There is no Tailscale, no tunnel or proxy service, and no Certbot:

- A **reverse proxy Apex runs itself** listens on ports 80 and 443 and forwards to the bridge on `127.0.0.1:8675`. In DHD mode the bridge never binds publicly — the proxy is the only public face.
- **TLS from the first click.** With no domain, Apex generates a **self-signed certificate** and the door opens on it. With a domain, Apex's **built-in ACME client** obtains a real Let's Encrypt certificate and renews it on its own.
- The **same access code** as the home-network door guards DHD — one code, the same acceptance cookie. Nothing is served through the proxy before the code, and the public door throttles wrong codes: they slow down, and five in a row lock the door for five minutes.

DHD has its own page, reached from the menu's **Apex | Systems** group (its Node and DHD entries both open it), and the status column's **Servers** group shows it beside Llamafile and Apex | Node [local], each row with its own pulsing dot and its own dropdown of details. Directly under Navi's status, bracketed by separators, sits the update line: a green **Up to date**, or a yellow **Update available** when a check found one — that one line is the whole entry.

The DHD page is the one house for Apex's server controls: the **Apex | Node** [local] controls — the home-network door's on/off choice, its live state, and the access code — sit on the DHD page under the DHD options, so both ways of reaching Apex are managed in one place. Settings → System keeps only a pointer to them. The relocation is display-only: same config keys, same API paths, same code and cookie.

## Turning it on — one click

1. Open the **DHD** page from the menu's Apex | Systems group.
2. Flip the **master switch**. That is the click.
3. Apex does the rest in order: it generates the certificate, brings its proxy up on 80/443 in front of the bridge, and runs a local reachability check — the proxy must answer on 443 from this machine ("answered on this machine"; it proves the local half only). The page then reports the live state, the LAN address under its own label, and the public address when there is one.
4. Once the public path is set up (router forwards in place, and your domain live if you use one), open the public address from anywhere, type the **access code** (shown on the DHD page, on this machine only), and you are in — a full session, Updater included: a remote session can run the one-click update end to end, exactly like sitting at the machine.

If a step fails, the page names the step in plain words — the proxy could not take its ports, the certificate could not be prepared, the self-check did not answer — and the previous state is left completely untouched. Nothing ever half-opens.

One Linux note: ports below 1024 are reserved, so if the proxy step names them, grant the bridge the low-port capability once (`sudo setcap 'cap_net_bind_service=+ep'` on the python3 binary it runs with) and flip the switch again.

## Prerequisites, installs, and operation cards

**The prerequisites ship with Apex.** Everything the DHD stack needs — the OpenSSL binary, a writable certificate home under `config/dhd/`, the proxy component (which is part of the bridge itself) — is installed by the normal Apex installer, on every distro family, whether or not DHD is ever turned on. An update installs them too: the Updater runs the full installer (never a file-copy shortcut), and its step ladder and update log show **DHD prerequisites** as its own named step. The added weight is small and honest: OpenSSL is a roughly 1 MB package that is usually already present as a dependency of tools Apex already needs (when it is present, the step costs milliseconds and downloads nothing), the certificate home is one empty directory, and the low-port capability grant is file metadata, not data. The certificate home is also on the installer's keep-list: a `--fresh` reinstall preserves `config/dhd/` — DHD state and a real ACME certificate survive it, never wiped and forced to re-issue.

**The safety net.** If a prerequisite later goes missing — removed by hand, a partial system install — the DHD page lists it under **Prerequisites** and the enable offers an **Install** action right there: one click installs the missing piece through the same distro-aware machinery the installer uses (apt, dnf, or pacman; on immutable systems like Bazzite the page names the host-image route honestly instead of layering a package), shows its progress on the operation card, and then continues the enable on its own. A missing dependency is never a dead-end refusal; the only hard failure is the install itself failing.

**When a fix has to be yours, the commands are exact.** If an install fails, or any step in the enable ladder has a manual remedy, the failure state shows the literal command lines — complete and correct for your detected distro family — in one copyable block with a **Copy commands** button. Paste them into Apex chat (CLI mode runs them) or into a terminal.

**Operations live in chat as cards.** Ask in chat to turn DHD on and the thread shows a live operation card — prerequisites, certificate, proxy, reachability — each step marked pending, running, waiting, done, or failed, with its output expandable inline and, on failure, the exact manual commands inline with their copy button. The card is driven entirely by the bridge's own deterministic step state: **no model generation happens while an operation runs** — on home hardware the work itself is the load, and Navi stays silent until it finishes. The finished card stays in the thread as the record, the DHD page shows the same operation, and restarting the bridge mid-enable reconciles the card with the live state. Nothing on a card depends on opening an external file, link, or handler; everything it needs is inside the card.

## Addresses — domain, public IP, and LAN (build .76)

DHD works with **three different addresses**, and the page never mixes them up:

- **Your domain** — the public address once it is live: you set an **A record** for the name at your DNS host pointing at your home's public IP, your router forwards **443 and 80** to this machine, and Apex's ACME client issues the name's real certificate. Only then — name resolving to this machine, certificate live — does Apex say **outside reach verified**, and only then does the status dropdown say "from anywhere."
- **Your public IP (WAN)** — the address the internet sees for your home. Apex detects it with a small HTTPS echo lookup (cached, and it never blocks anything). With no domain, this is the public address the page shows — marked **outside reach unverified**, because Apex cannot prove your router forwards reach it until the path is actually proven. If the detected address is itself private or a carrier-NAT address (100.64.0.0/10), the page says plainly that this machine sits **behind another router/NAT** instead of presenting the address as directly reachable. If detection fails, the page says it **could not detect** the address — never a guess.
- **Your LAN address** — an address like `192.168.1.x`. It works **only on this network** and lives in its own labeled home on the DHD page and in the status dropdown: **On this network (LAN)**. It is never shown under a public label.

**What the state lines mean.** *On — listening, outside reach unverified* means the proxy is up and answering on this machine, but the outside path is not proven yet; the page names the next step in plain words (forward 443 + 80 on the router to this machine, or add your domain). The enable ladder's last step is a **local check** — "answered on this machine" — and it is labeled that way; it never claims anything about the internet. **Reachable anywhere** appears only for a verified domain setup.

**Ports 80/443 and Apex's own proxy.** When the listener on 80 or 443 is Apex's own DHD proxy, the availability rows read **"In use by Apex's DHD proxy — this door working"** — a healthy state, not an occupancy problem — and re-enabling with the proxy already running is a success, never "port is not free." That error is reserved for a *different* program holding the port.

## The parts you may still handle by hand

One click covers everything on the machine. Two things live outside it, in your router and your domain, and they are yours:

- **Router port forwarding.** Forward ports **80** and **443** (TCP) on your router to the machine Apex runs on. Without the forward, the internet cannot reach the proxy at all, and in domain mode port 80 is also how the certificate proof arrives — the DHD page will tell you plainly: "port 80 isn't reaching this machine — check the router forward."
- **Pointing your domain here.** At your domain's DNS host, set an **A record** for the name (for example `apex.example.com`) to your home's public IP address. **Dynamic IP caveat:** most home connections change address from time to time; when yours does, the name stops resolving here until the record follows. A dynamic-DNS hostname avoids the manual step — you can put a DDNS name in the domain field just as well.

The domain is **optional and addable at any time**: leave the field empty as long as you like. Adding one later changes nothing about the door except its certificate — the page holds the domain as "certificate pending" until the ACME step completes, and the self-signed door keeps answering meanwhile.

## Certificates — the warning, the real one, and renewal

**The self-signed warning is expected.** Until a domain is added, Apex serves a certificate it signed itself. Your browser cannot verify a self-signed certificate with any public authority, so it warns — on some browsers, loudly. That warning means "no authority vouches for this certificate," not "this connection is unencrypted": the traffic is still TLS-encrypted, and the access code is still the door's lock. It is the normal state of a no-domain DHD.

**With a domain, the warning goes away.** Apex's built-in ACME client talks to Let's Encrypt directly: it places an order, proves you control the domain by serving the HTTP-01 challenge through its own proxy on port 80, finalizes, downloads the certificate, installs it, and reloads the proxy. No Certbot, no external ACME tool.

**Renewal is automatic.** Let's Encrypt certificates live 90 days. Apex checks the expiry when the bridge starts and once a day after that, and renews on its own when 30 days or fewer remain — same ACME flow, no operator action. The DHD page always shows the current expiry.

## Turning it off

Flip the master switch on the DHD page back off. The proxy stops, ports 80/443 close, and Apex answers only on this machine and — if Apex | Node is on — your home network, exactly as before DHD. Your domain and certificate stay saved on the machine, so turning DHD back on later is the same one click.

Turning DHD off does not touch Apex | Node, the access code, or anything else. If you also forwarded ports on your router, you can leave the forwards in place (nothing is listening) or remove them — either is fine.
