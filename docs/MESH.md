# Navi Mesh — your machines, one pool of inference

Navi Mesh lets your own machines share the work of answering. A modest laptop assembles a chat request the way it always does — persona, Vault, knowledge packs, conversation — and a stronger machine you own writes the reply on its own model. The routing is **whole-request**: one machine answers, start to finish. There is no split answer and no streaming between machines in Ring 1.

Mesh is off until you turn it on, and it works between machines **you** pair by hand. Nothing about it is tied to a specific person, machine name, or domain: every name and address comes from your own settings and the cards you exchange.

## Pairing — the card is the handshake

Each machine has a **Mesh card**: one copyable block holding its name, its node id, its public key, the fingerprint of the certificate its Mesh door serves, the addresses it can be reached at, and a **capabilities block** — an honest self-report of the machine's hardware class, GPU or CPU, RAM, model, speed class, and the caps it lends under, so a borrower can see what it is borrowing from before it asks.

1. On the first machine, open the **Mesh page** (Mesh in the left menu), turn Mesh on, and give the machine a name.
2. Choose **Show my Mesh card** and copy the whole block.
3. On the second machine, turn Mesh on, paste the card into **Add a peer**, and add it.
4. Do the same in the other direction — each machine needs the other's card.

Pairing is the consent act: a paired machine is a trusted machine. Either side can unpair at any time by removing the card, and the lending side can untick a peer's **can borrow** to stop that one machine from borrowing without unpairing it.

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

A lender serves only inside the limits you set:

- **Idle only** (on by default): the machine must have been quiet for 60 seconds, and no local generation may be running.
- **Share cap**: borrowed work may take at most 25% of any rolling hour.
- **Generation caps**: at most 20 borrowed generations an hour, and at most 10 an hour for any one machine.

Your own work always wins: a local request takes the next slot ahead of any new borrowed work, though it never kills a borrowed answer already running. A request whose assembled context exceeds the lender's context setting is refused whole — never silently truncated.

## Privacy — what travels, what never does

**What travels** when you borrow: the assembled prompt for that one reply — your Soul and Memory text, any Vault or knowledge-pack material the question pulled in, and the recent conversation — sent encrypted to the lending machine, whose model reads it to write the reply. The lender keeps none of it: no prompt or reply text is written to disk on the lending machine, ever. But that machine's operator owns the machine it runs on. **Only borrow from machines you trust with the conversation.** The Mesh page shows this in plain words the first time borrowing is enabled.

**What never travels**: your files and data stores, your credentials and access codes, and command-line access. Mesh carries chat requests and replies, nothing else. Mesh keys and dashboard codes are separate credentials that share nothing in either direction: a guest signed in through DHD can never reach Mesh, and a paired Mesh peer gains no dashboard access. A peer's network addresses likewise stay in the plumbing — they are used to dial the machine and are never shown in the roster or any other surface.

Every Mesh request is signed with the borrowing machine's Ed25519 node key and checked against the key on its paired card; stale or unsigned requests are refused with no detail given. The connection itself is pinned to the certificate fingerprint on the card — if the machine answering presents a different certificate, the borrower refuses and says so in plain words.

## The ledger and balances

Each machine keeps a small ledger of Mesh work: who, which direction, how long, how it ended — metadata only, never content. The Mesh page's **roster** shows each paired machine's **balance** in seconds lent minus seconds borrowed, alongside its capability line and live status (reachable, lending, busy, idle, unreachable). The roster shows names, capabilities, status, and balances only — a machine's addresses are plumbing for the transport and never appear on any screen. Balances are a record, not a rule: Ring 1 has no give-to-get enforcement. The ledger stays out of GitHub backups unless you tick **Include the Mesh ledger in backups** (off by default); the node keypair never rides a backup either way.

## Getting there — the dedicated door

Mesh always travels through its **own dedicated TLS listener** on the Mesh port (8765 by default), whether or not DHD is on. The certificate it serves is the Mesh certificate under `config/mesh/`, and that is the fingerprint the paired card pins — in every configuration, so a card stays valid when DHD comes and goes. Mesh never rides the DHD door: the DHD proxy refuses `/mesh/*` outright, and the dashboard itself serves only the dashboard-local Mesh controls (the card view, Stop lending, the settings API) behind the access-code gate — the node-facing status and borrow endpoints live only on the dedicated port. There is no plaintext Mesh listener. Ring 1 does no NAT traversal, no relay, and no lender racing: the first reachable lender serves, and a home pair on one network is the shape it is built and tested for; reaching a lender across the internet means forwarding the Mesh port yourself.

## Troubleshooting

- **"Certificate fingerprint does not match."** The machine that answered is not presenting the certificate on its card — the card is stale, or something else is answering at that address. Re-copy the card from that machine's Mesh page and re-add the peer.
- **Replies keep saying "answered locally" with a busy / cap / idle note.** The lender is doing its job: it is mid-answer, over its caps for the hour, or not idle yet. The note names which. Wait, or raise the caps on the lender.
- **"<machine> dropped mid-answer."** The lender went away during a reply — its operator hit Stop lending now, or the machine or its bridge stopped. Your reply was written locally, whole. Check the lender.
- **A peer shows unreachable.** Its Mesh is off, its bridge is stopped, or the address on its card no longer reaches it. Re-check the card's addresses on the lender itself first.
