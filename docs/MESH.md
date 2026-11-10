# Navi Mesh — your machines, one pool of inference

Navi Mesh lets your own machines share the work of answering. A modest laptop assembles a chat request the way it always does — persona, Vault, knowledge packs, conversation — and a stronger machine you own writes the reply on its own model. The routing is **whole-request**: one machine answers, start to finish. There is no split answer and no streaming between machines in Ring 1.

Mesh is off until you turn it on, and it works between machines **you** pair by hand. Nothing about it is tied to a specific person, machine name, or domain: every name and address comes from your own settings and the cards you exchange.

## Pairing — the card is the handshake

Each machine has a **Mesh card** — a PNG picture whose face a person can read and whose inside carries the card data: its name, its node id, its public key, the fingerprint of the certificate its Mesh door serves, the addresses it can be reached at, and a **capabilities block** — an honest self-report of the machine's hardware class, GPU or CPU, RAM, model, speed class, and the caps it lends under, so a borrower can see what it is borrowing from before it asks.

1. On the first machine, open the **Mesh page** (Mesh in the left menu), turn Mesh on, and give the machine a name.
2. Choose **Download PNG card** and carry the picture file to the second machine.
3. On the second machine, turn Mesh on, then drop the picture onto the **Paired machines** area — or use **Upload a PNG card** — and the peer is added.
4. Do the same in the other direction — each machine needs the other's card.

Pairing is the consent act: a paired machine is a trusted machine, and a paired machine's signed requests are accepted on that basis alone. Either side can unpair at any time by removing the card. The **can borrow** toggle on a peer is the borrowing machine's own choice about that peer: untick it there and that machine will not borrow from the peer, while staying paired — it does not gate what the peer accepts.

**The card is a picture — the only way it travels.** **Download PNG card** on the Mesh page saves the card as a .png. Its face is the card a person reads — the machine's name, its node identity, and the offer in words: its capabilities, the lending limits it is configured with, and whether it lends when idle or even while busy. The whole card rides inside the picture, in the same data-in-picture format the chips use (a PNG text chunk carrying the card), so Apex keeps one cartridge language across the product. On the other machine, drop the picture onto the Mesh page's **Paired machines** area, or use **Upload a PNG card** there, and the peer is added — a PNG exported by one machine imports into another with every field intact. Earlier builds also offered the card as copyable text; that path is gone — there is nothing to paste anymore, and a text card saved from an earlier build can no longer be used. Machines already paired are unaffected: pairing was the consent, and the record it made never depended on how the card travelled.

**Send the picture as a file.** The payload survives only if the file's bytes arrive untouched. Put the .png inside a **.zip** before sending it through a chat app: Discord and similar apps recompress the images people upload and strip out the extra data chunks, leaving a picture that looks like the card and pairs nothing. The same goes for any channel that re-encodes images — send it as a file attachment, a zip, a USB stick, anything byte-exact. When a payload-less picture is imported, the Mesh page says so in plain words — *this image has no readable Mesh card data; it may have been recompressed by a chat app; send the original file inside a .zip instead* — and a damaged or truncated picture is refused just as specifically, never silently ignored.

## Borrowing — automatic, with off switches

Once Mesh is on and a lender is paired and reachable, borrowing happens by itself: a chat request goes to the first reachable lender, and the reply arrives with a small pill under it — the Hexlink glyph and **via <machine name>** in Mesh cyan.

Three off switches, from widest to narrowest:

- The **Mesh master switch** turns the whole thing off.
- The **Borrowing switch** stops this machine from borrowing while leaving it able to lend.
- **This chat only: keep it on this machine**, beside the composer, holds one chat session home — no borrow is attempted for it at all.

If the lender is **busy**, your machine waits a short grace (2 seconds by default, changeable on the Mesh page) for it to free up, then answers locally; a lender that frees up during the grace can still take that request, but once your machine starts answering, the lender is never claimed mid-reply — it serves the next request. If a lender **drops mid-answer**, you see the notice — *"<machine> dropped mid-answer — this reply was generated locally instead"* — and your machine writes a fresh reply of its own. Two machines' prose is never spliced together.

CLI mode, chips, and every built-in route never borrow. Only model answers do.

## Lending — automatic when idle, off means off

Lending can only be turned **on** from the lending machine's own dashboard, in person, at that machine. It cannot be armed through the DHD door. Turning it off works from anywhere you are signed in — and **Stop lending now** ends lending and aborts a borrowed generation already running, mid-flight, at once.

Open the Mesh page through the DHD door and the **Lend this machine** switch shows the lock itself: while lending is off it renders locked — dimmed, not clickable — with the reason in plain words directly under the switch, because lending can only be turned on in person. While lending is on, the switch stays live on the remote view, since turning lending off works from anywhere; a note under it says turning it back on will require being at the machine. The lock is the bridge's, not the page's: the bridge refuses a lending turn-on that arrives through the DHD door regardless of what any client renders.

A lender serves only inside the limits you set:

- **Idle only** (on by default): the machine must have been quiet for 60 seconds, and no local generation may be running.
- **Share cap**: borrowed work may take at most a set share of any rolling hour — **25%** as shipped.
- **Generation caps**: at most a set number of borrowed generations an hour — **20** as shipped — and a set number for any one machine — **10** as shipped.

The three caps are yours to set, on the lending machine itself: they sit in the **Lending** section of its Mesh page, beside the Caps line that shows the current values, and they take effect as soon as you save — no restart. Set them for the machine it is; a strong server can take far more than the shipped defaults. Your card advertises the caps you set, so a paired machine sees the real offer before it asks.

**Idle only** has an override in the same section: the **Lend only when idle** switch, on as shipped. Turn it off and the machine lends without waiting for a quiet minute — borrowed generations run alongside your own work, and your own replies may slow down. The caps still apply, and lending still serves one borrowed generation at a time: a request that arrives mid-generation waits for the next slot, exactly as before. Your card states the posture either way — *lends when idle* or *lends even while busy*.

Your own work always wins: a local request takes the next slot ahead of any new borrowed work, though it never kills a borrowed answer already running. A request whose assembled context exceeds the lender's context setting is refused whole — never silently truncated.

## Privacy — what travels, what never does

**What travels** when you borrow: the assembled prompt for that one reply — your Soul and Memory text, any Vault or knowledge-pack material the question pulled in, and the recent conversation — sent encrypted to the lending machine, whose model reads it to write the reply. The lender keeps none of it: no prompt or reply text is written to disk on the lending machine, ever. But that machine's operator owns the machine it runs on. **Only borrow from machines you trust with the conversation.** The Mesh page shows this in plain words the first time borrowing is enabled.

**What never travels**: your files and data stores, your credentials and access codes, and command-line access. Mesh carries chat requests and replies, nothing else. Mesh keys and dashboard codes are separate credentials that share nothing in either direction: a guest signed in through DHD can never reach Mesh, and a paired Mesh peer gains no dashboard access. A peer's network addresses likewise stay in the plumbing — they are used to dial the machine and are never shown in the roster or any other surface.

Every Mesh request is signed with the borrowing machine's Ed25519 node key and checked against the key on its paired card; stale or unsigned requests are refused with no detail given. The connection itself is pinned to the certificate fingerprint on the card — if the machine answering presents a different certificate, the borrower refuses and says so in plain words.

## The ledger and balances

Each machine keeps a small ledger of Mesh work: who, which direction, how long, how it ended — metadata only, never content. The Mesh page's **roster** shows each paired machine's **balance** in seconds lent minus seconds borrowed, alongside its capability line and live status (reachable, lending, busy, idle, unreachable). That status is kept current by the bridge itself: while Mesh is on, every paired peer is checked in the background about every thirty seconds — and immediately when a peer is paired and when Mesh is turned on — so a pair reaches "checked" on its own, with no chat sent. A failed check stays on the roster with its reason and how long it has been since the peer last answered — *unreachable — unauthorized (last checked 42s ago)* — until a newer check replaces it; the age keeps growing while the peer stays down, because failed checks refresh the reason, not the clock. "not checked yet" appears only before a peer's first check has ever completed. The roster shows names, capabilities, status, and balances only — a machine's addresses are plumbing for the transport and never appear on any screen. Balances are a record, not a rule: Ring 1 has no give-to-get enforcement. The ledger stays out of GitHub backups unless you tick **Include the Mesh ledger in backups** (off by default); the node keypair never rides a backup either way. The pairing-card pictures are a separate matter: **Mesh pairing cards** (Settings → GitHub & Backup, its own essential, ticked like the rest) carries this machine's own card as a PNG — minted fresh from the live card as the backup runs — and a re-drawn PNG for every paired peer, so a restored machine lands the pictures in `config/mesh/cards/` and re-pairs the peers through the same card check a hand import passes. Your own picture is kept as a file; restoring it never overwrites the identity of the machine doing the restoring.

## Getting there — the dedicated door

Mesh always travels through its **own dedicated TLS listener** on the Mesh port (8765 by default), whether or not DHD is on. The certificate it serves is the Mesh certificate under `config/mesh/`, and that is the fingerprint the paired card pins — in every configuration, so a card stays valid when DHD comes and goes. Mesh never rides the DHD door: the DHD proxy refuses `/mesh/*` outright, and the dashboard itself serves only the dashboard-local Mesh controls (the card view, Stop lending, the settings API) behind the access-code gate — the node-facing status and borrow endpoints live only on the dedicated port. There is no plaintext Mesh listener. Ring 1 does no NAT traversal, no relay, and no lender racing: the first reachable lender serves, and a home pair on one network is the shape it is built and tested for; reaching a lender across the internet means forwarding the Mesh port yourself.

## Troubleshooting

- **"Certificate fingerprint does not match."** The machine that answered is not presenting the certificate on its card — the card is stale, or something else is answering at that address. Download a fresh PNG card from that machine's Mesh page and re-add the peer.
- **Replies keep saying "answered locally" with a busy / cap / idle note.** The lender is doing its job: it is mid-answer, over its caps for the hour, or not idle yet. The note names which. Wait, or raise the caps on the lender.
- **"<machine> dropped mid-answer."** The lender went away during a reply — its operator hit Stop lending now, or the machine or its bridge stopped. Your reply was written locally, whole. Check the lender.
- **A peer shows unreachable.** The roster says why, and when it was last checked. *unauthorized* means the other machine does not hold this machine's card — pairing is the consent, so re-exchange cards. *fingerprint* means the machine answering is not presenting the certificate on its card. Anything else means it could not be reached at all: its Mesh is off, its bridge is stopped, or the addresses on its card no longer reach it. Checks retry on their own about every thirty seconds, and the roster updates when one succeeds.
- **"This image has no readable Mesh card data."** The PNG card arrived without its payload — almost always because a chat app recompressed it on the way. Resend the original card file inside a .zip, or by any channel that moves files byte-for-byte, and import that.
- **The status row says a peer dropped, but chats keep being answered locally.** A peer that was recorded as dropped keeps that word on its roster row while it stays down — a check that finds it still down does not replace the word, because the drop is the freshest thing this machine knows about it. The warning never gates borrowing: the next chat re-checks the peer before giving up on it, and borrows normally the moment it answers. If the machine is back, give it one health-check cycle (about thirty seconds) and the warning clears on its own.
