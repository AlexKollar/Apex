# Apex | Federation — fedinets, rosters, and deep trust

Build 8 of 0.2.0e takes the Mesh from a set of hand-made pairs to
what it was designed to be: a **distributed, federated network** —
form factors are separate products, but the Mesh is one federated
whole. The unit of federation is the **fedinet**: a named set of
nodes whose membership is kept by one node's **gateway** as a
**signed roster**.

## The roster is the gateway's signed word

A roster carries, for every member: its node id, its name, its
public key and door-certificate fingerprint, its addresses and
declared public endpoint, its capabilities, when it joined — and
its **Node number**, the join order the gateway assigned at
admission. Node numbers are *roster facts*: they exist only
inside the signed roster, nowhere else.

The gateway signs every roster revision with its node key.
Versions only move forward. A member accepts a roster only
whole: right fedinet, the gateway's signature verifying,
version strictly newer than the one it holds. A forged,
unsigned, or rolled-back roster is refused by name at the door
and the stored roster stands.

Rosters travel over the Mesh door (`POST /mesh/roster`), signed
like every Mesh request. Authentication at the roster door is
deliberately wider than pairing: a fedinet member is known by
the roster itself — its key is a roster fact — so a member this
node has not paired with yet can still sync, knock, and be
answered. Asks go **direct first**, then **via relay**: Build 8
admits the roster class to Build 7's sealed relay carriage, on
the same three consent ticks and the same one-hop rule, with
the destination checking its own relay consent at its roster
door. Rosters also gossip member-to-member (the `roster`
action), so a fedinet heals around a dark gateway; the gateway's
signature is the only credential an offered roster needs.

## Gateway cards — admission + introduction, never trust

A gateway hands out a **gateway card**: a pairing card's form
rendered **green**, the fedinet's name on its face, and a
`navi-gateway-card` payload inside the picture — the gateway's
own pairing card, the fedinet's identity, and the gateway's
signature over the claim.

The card's reachability is the gateway's **declared public
endpoint alone** (v0.4.4e, #238). A pairing card carries the
machine's LAN addresses because pairing is arranged between
machines whose operators can meet on a network; a gateway
card is imported by machines *outside* the gateway's network,
and a member's bridge dials the card's addresses in order —
a LAN address on it is a door that exists in only one house.
On the member's own LAN such an address is a connection
sitting in SYN-SENT until it times out, or a stranger's
machine holding the same private address, and the automatic
route can fall back to a local answer without the public
road ever being tried. So the local addresses come out of
the gateway's card entirely — the embedded pairing card
carries the endpoint as its only address, and the gateway's
own roster entry is shaped the same way. A gateway with **no
declared public endpoint** mints no gateway card at all: the
mint refuses, on the Federation page and at the download
alike, with a sentence naming the missing declaration.
Declare the endpoint on the Mesh page and the card can be
minted. (Pairing cards are unchanged: they keep their LAN
addresses by design.)

Importing a gateway card does exactly two things: **admission**
(this node now keeps the fedinet) and **introduction** (the
gateway becomes a peer, and its roster becomes fetchable). It
grants **no trust** — no lending posture moves at import.
Trust is a separate act, below.

A gateway that founded its fedinet is also its **Founding
Member** — two distinct facts, both visible: the roster lists
the gateway as Node 1 with the Founding Member mark, and the
Federation page says both.

## Joining: the knock, and the gateway's word

A node admitted by a gateway card **knocks**: it sends its own
pairing card, self-signed, to the gateway's roster door. The
knock proves the knocker holds the key its card names — and
nothing more; admission is the **gateway operator's act**, on
the Federation page's pending list (admit or deny). Admission
adds the member to the roster at the next Node number, pairs it
on the gateway, and republishes the signed roster.

**When the road is dark (v0.3.0e — Build 6, #226).** A knock or
a roster sync that cannot reach the gateway names the stage it
died at and the last road tried — nothing answered in time at
an address, no connection to be had, a TLS handshake that
failed, a door that answered without the pinned certificate, a
connection dropped mid-answer — instead of every failure
reading the same *did not answer*. A failed knock is written
to the node's federation audit log with its stage, one entry
per operator-initiated attempt, the same cadence a failed sync
already kept: silence in the log once again means no knock was
sent.

**Cards keep their kinds, and verified cards refresh
(v0.3.0e — Build 6, #227).** A gateway card can never become a
hand-made pairing record, and a pairing record can never serve
as a fedinet's gateway record: every import path — the pairing
picture import, the federation import, backup restore, and
sync-carried cards — refuses the other kind by name. Gateway
cards are imported on the Federation page, where the gateway's
signature is checked; pairing cards pair one machine from the
Mesh page. And when a *verified* gateway card's node already
has a peer record on the importing node, the import refreshes
that record's card-claimed reachability — addresses, port,
certificate fingerprint, name — from the card, because the
knock dials the record, never the card: a record made before
the federation existed (a hand pairing carrying only the
gateway's LAN address) otherwise keeps its stale roads
forever. Operator facts are never the card's to change: relay
ticks, the tunnel route, borrow posture, pair history, and
the auto-paired mark all stand. The Mesh health check names a
federation-marked record whose stored addresses are a proper
subset of its verified card's, and offers the same refresh as
an in-place heal on that peer's card.

**Expulsion** is a signed roster revision like any other: the
member leaves the roster, and at every member's next sync the
federation-made records for it go away. Pairings made by hand
outside the fedinet are never touched — one that was later
admitted is *unmarked*, not deleted.

## Deep trust — and its guardrails

Trust-by-default is **deep** (the founder's ruling, 2026-11-13,
taken with its threat model on the table): when an operator's
toggle for a fedinet is ON, that fedinet's signed roster
**auto-pairs and auto-lends** on their node. The federation
materializer reconciles the node's peer records with the
roster — it only ever touches records the federation itself
made. Lending is re-judged fresh on every borrow ask against
this node's own posture:

- **The roster's freshness.** A roster last verified more than
  **72 hours** ago degrades the fedinet to pairing-only, with
  the sentence on the Federation page saying so. Pairings hold;
  auto-lending waits for a sync.
- **The new-member tick.** Each operator's per-fedinet tick —
  "lend to new members automatically" — defaults ON. A member
  whose first-seen roster version is newer than the operator's
  trust baseline is *new*: unticked, new members are
  pairing-only *for that operator* until ticked individually.
- **Per-member untrust** always wins — over the toggle, the
  tick, everything.
- **A per-member lend tick** names an exception: that member
  lends even while the general toggle is off. It is not
  auto-lending; it is named lending, and untrust still beats it.
- **Borrow caps** are local policy: a per-fedinet hourly cap on
  generations lent to its members, counted from the ledger.
- **Owner preemption.** The owner's own work goes first: local
  generation starting aborts a federation borrow in flight,
  and the borrower is answered with the named outcome
  *preempted* — never dropped silently. A hand-made pairing's
  borrow is never preempted.

One flip of trust-by-default OFF ends all auto-lending for the
fedinet. Pairings already made stay pairings.

## Founding, and Rockport Mesh

Anyone can found a fedinet: name it, and your node becomes its
gateway, signs roster v1, and stands as its Founding Member.
A node keeps several fedinets at once; no trust bleeds across
them — every posture above is per-fedinet, per operator.

**Rockport Mesh** is the first fedinet. The product ships the
machinery and Rockport's *definition* — never a hardcoded
roster: its real roster lives on its gateway (Neo-Arcadia) and
is learned from the gateway's signature. First runs meet
Rockport through its gateway card.

## The Federation page, and the doors

Federation is administered on its **own page** (Apex |
Systems → Federation) — fedinets and rosters, gateway cards,
toggles and ticks, founding controls, caps, pending knocks, and
the **trust audit log**. The phone keeps a dedicated
arrangement of the same cards. Since DHD serves the same UI,
the page is also the remote admin surface — for the operator's
**own nodes only**: every act reads and writes the node it
lands on, so no door can flip another operator's switches.

The tiers (the crown-acts ruling, 2026-11-13):

- **Read + revoke** are open through DHD always.
- **Manage** acts — imports, ticks, caps, admissions — need a
  trusted-device session **plus the Operator Badge step-up**.
- **Crown acts** — enabling deep trust, founding a fedinet,
  authorizing a tunnel key — run through DHD under the full
  ceremony: trusted-device session + Badge presentation + a
  **named-action confirm** (the act spelled in words) + an
  audit entry. At the desk, the same acts need the same
  confirm + audit; the Badge is the door's addition.

The Badge factor is the operator's **Operator Badge** (the
operator card). The node stores only its **SHA-256
fingerprint**, enrolled **in person** on the Federation page —
enrollment itself never rides DHD. A presented Badge is hashed
and compared; the picture never stays on the node. With no
Badge enrolled, DHD manage and crown acts refuse **by name**:
the ceremony cannot run, and says so.

Every trust-class act, through any door, lands in the audit log
(`config/federation/audit.json`, the last 300 rows) — action,
fedinet, detail, and which door, in sentences. Metadata only.

## The Docker invitation

An image built to join a fedinet carries the gateway's card at
`docker/gateway-card.png`. The container's first boot copies it
into the volume as the waiting invitation
(`config/federation/invitation.png`), and the bridge imports it
at start — admission-only. Under the container's ruled Rockport
default, the imported fedinet's trust-by-default starts ON; it
engages only when a signed roster syncs, and the import itself
lends nothing. Node keypairs still mint at first boot and are
never baked into any image; the gateway's identity never leaves
the gateway — its card is minted in the field, on the gateway
itself. The tree's `docker/sample-gateway-card.png` is a
**sample** of the card's shape carrying sample facts, clearly
named as such, and is never wired as an invitation.

## "Mesh Online"

While a node keeps any fedinet, the Mesh status headline is
the state — **Mesh Online** — not a census of pairs. Warnings
still outrank it. A node keeping no fedinet speaks exactly as
it did before federation.
