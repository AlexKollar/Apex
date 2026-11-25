# Changelog

All notable changes to Apex are recorded here. Version language, from 0.1.7 on: a full release carries the bare number (tag v0.1.7); a pre-release is an Edge build and carries the e suffix (tag v0.1.7e). Releases before 0.1.7 were cut as alphas with the a suffix — that history stands as written below.

## 0.8.5

Release tag: v0.8.5e — Chapter 0.8's fifth
build, the War Room's first-night round:
the federation door learns to answer, seats
stop impersonating the operator, the room
stops flashing and keeps its one face, and
room-Navi runs the pull decision before she
speaks — plus the release/apply trio (tags
that point at the released code, an Apply
that names or spares the runtime it moves,
an Apply that hands the bridge back to its
systemd unit) and the podcast player's
episode-identity fix.

- #474 — The War Room federation door
  answers. mesh_handle_warroom passed the
  parsed dict to _fed_roster_auth, which
  expects the raw signed body and died on
  .decode() — every non-home knock was
  refused bad-request before membership was
  ever checked. The door now passes the
  body, like the other two callers: a
  properly signed member knock reaches the
  roster check, and a knock with no or an
  invalid signature answers unauthorized,
  never bad-request.

- #480 — A seat that matches nothing
  refuses by name. A War Room post carrying
  a seat credential (a navi_seat cookie, a
  door cookie) that matches no seat session
  and no door device is refused with a
  named error and nothing is posted — it
  no longer falls through to the operator
  and lands under his name. A request
  carrying no seat claim keeps the standing
  operator default, and matched seats
  (the operator's own session, a seat
  session, a door device) post as
  themselves, exactly as before.

- #479 — The War Room stops flashing. The
  20-second refresh ended every fetch with
  a full render(), replaying the view's
  entrance animation on a steady beat and
  rebuilding the composer under the
  operator's hands. The tick now compares
  the room's standing surfaces by key and
  paints incrementally: the transcript's
  lines are repainted in place with scroll
  preserved (pinned to the foot only when
  it already stood there), the tray's
  members and presence repaint in place
  while it stands open, the composer is
  never rebuilt — its half-typed text,
  focus and caret are untouched — and a
  tick that changes nothing repaints
  nothing. Structural changes (another
  chat, the door's state) still take the
  full render, from the actions that cause
  them.

- #470 — The room's one face, held to the
  gate. The desktop face is the phone face
  at every width (v0.8.3e's unification,
  re-benched whole at desktop width), and
  the naviJoins switch — which lives in
  the tray at every width now — gets the
  full switch gate: the flip posts the
  want and the card re-renders from the
  response, a refusal names itself on the
  same card, a reload agrees with the
  bridge's stored state, and a flip
  already in flight owns the switch (a
  second, adversarial flip against the
  unanswered state is a no-op, so the
  switch can never land somewhere the
  operator did not choose).

- #458 — Room-Navi pulls the show's
  record. The room's speak path has run
  the pull decision since v0.7.17e, but
  the decision had no pack for the show
  itself: asked where From The Night Shift
  stands, she could pull the talks and the
  Row's record and still have no episode
  in front of her. The decision now pulls
  the show's record on a show question —
  the podcast feed the bridge already
  follows, shaped as a brief (the show's
  shape, the latest episode's title, date
  and topics, its provenance named; the
  absence named, with the invention door
  closed in words, when the feed cannot
  stand). Persona-only questions stay
  persona-only, and what a turn pulled is
  evicted when the reply lands, as
  everywhere.

- #477 — Release tags point at the
  released code. The candidate tree's
  identity — its version and build stamps
  and a digest of its manifest — is
  recorded in the build's manifest at bake
  time, and the packaging path gains a
  verification step that fails loudly when
  a tag's tree does not match the release
  it names (VERSION and BRIDGE_BUILD at
  the tag must equal the manifest's). The
  ceremony for this release carries the
  exact tag procedure, so v0.8.5e's tag is
  the first correct one since v0.6.19e.
  The old tags are not retro-fixed.

- #476 — Apply names or spares the
  runtime it moves. The installer's
  profiling block preserves a standing
  runtime that disagrees with the profile
  it rode with — the operator's hand on
  the config — and logs the preservation;
  a clean auto seat re-derives as ever,
  and a manual override is never
  re-derived. The apply helper reads the
  seat's runtime before the installer
  runs and names any move on the Apply
  result itself (runtimeChanged, with a
  sentence: what it was, what it became).
  And the auto profile's thread pick on
  4–7 cores is sane at last: one short of
  the logical cores, in both derivation
  tables — no longer a flat 2.

- #475 — Apply hands the bridge back to
  its unit. The relaunch's systemd test
  keyed only on the job record's startup
  field, which a job written by an older
  bridge (the v0.6.1e shape) does not
  carry — the apply fell back to a
  start.sh relaunch and stranded a
  detached bridge for the health gate to
  find. A job that names its startup mode
  has spoken, as before; a job that does
  not name one now asks the seat itself —
  navi-bridge.service standing as a user
  unit (enabled or active) means systemd
  owns the bridge, and the restart rides
  the unit. The health gate's unit leg
  reads the same answer. Non-systemd
  installs keep their working path.

- #482 — The podcast player keys episodes
  by slug, not n. The feed's five specials
  all carry n "special", and the player
  keyed every identity on n: the refresh
  re-point landed on the last special,
  every special's card read as the
  standing episode, and Play played
  Building a NetNavi. The player now keys
  on rowEpKey — the episode's slug when it
  carries one, else its n — at every
  touchpoint (find, standing checks,
  toggles, queue seats, transcript state,
  the Play door, persistence), the
  refresh re-point prefers an exact audio
  match (healing saves made before the
  fix), and the card sort takes date as
  the tiebreak under numeric n. Display
  strings are unchanged. The live hotfix
  on NeoArcadia is superseded by this
  source fix.

## 0.8.4

Release tag: v0.8.4e — Chapter 0.8's fourth
build, the house-training round: Seraph gets
her mute button, the bell's Clear finally
obliterates (and the badge stays at 0), the
DHD door's TLS wedge is fixed at the root,
and a deletion that must stay deleted now
leaves the backup too — four field defects
from one morning's use, each fixed where
the field found it.

- #465 — A mute button for Seraph. Her
  voice is now one bridge-held switch on
  her console: while muted she makes no
  chat announcement — not the first word,
  not the hourly aggregate — and no bell
  record of hers stands or is born. Her
  eyes stay open: detection, her store,
  her console, and the notice ledger's
  memory all run whole, so unmuting
  resumes from new material only and the
  backlog never bursts. The switch is
  held to the full gate — UI flip, bridge
  state, and reload agree; a save the
  bridge cannot make is a named refusal
  on the same card, and the state
  survives a bridge restart.
- #463 — The bell's Clear obliterates.
  Clear deletes the standing records
  outright — never marks, never hides —
  and leaves a durable clear mark for
  each record that stood and each item
  the producers still want. The reconcile
  consults the marks before any birth:
  cleared material is not re-served,
  while genuinely new material (a new
  occurrence, a count that grew, a fact
  that changed) returns fresh and earns
  its word. The badge reads 0 and stays
  0 across reconcile cycles and bridge
  restarts.
- #469 — The DHD door's wedge, at the
  root. The TLS listener was wrapped
  whole, so every handshake ran inside
  the accept loop itself, unbounded,
  behind a five-deep listen queue: one
  stuck connection parked the door. The
  door's server now accepts raw sockets
  and wraps each connection under a
  bounded wait — a stalled handshake
  dies alone, the queue stands at 128,
  and the door keeps answering while
  stuck connections are reaped.
- #472 — Deletion integrity, part two.
  Deleting a formed dossier's shelf file
  now retires its RECORD in the same act,
  on every road into the delete, so the
  file does not re-form at the next
  start; formation itself never prints
  over a standing vault tombstone; and
  the backup's deletion leg is real at
  last — Quick Sync's push and the
  managed backup DELETE tombstoned
  vault/cases paths from the backup
  repo's HEAD in the same run, judged by
  the tombstone set, never by absence.

## 0.8.3

Release tag: v0.8.3e — Chapter 0.8's third
build: the War Room takes one face. The operator
looked at the room on his phone and on his
desktop and ruled the desktop should wear the
mobile look — "let the War room on desktop have
the same look as mobile." Since the second
sitting (#445) the room has rendered two faces:
on the desktop the members stood as an
always-open card grid, the chats bar and her
switch stood in the column, and the composer
carried a Post button and an Address Navi tick;
on the phone the window was the transcript and
the composer alone, the burger riding inside the
bar, everything else — the members behind a
dropdown, the chats, the switch — living in the
tray. Two faces meant every change to the room's
shape had to be made and proven twice, and the
field's hardest lessons (#451's frozen frame,
#454's no-send phone) were all learned on the
phone face the operator actually lives in. This
build retires the desktop face: one render path
at every width, the phone-only CSS promoted out
of the max-width block, the tray anchored right
everywhere, and the desktop-first rule reversed
for this one view by the operator's explicit
word. The carried laws stand guard over the
unification — #454's soft-keyboard send still
intercepted where the phone delivers it, a
hardware keyboard keeping its shipped roads
(Enter sends, Shift+Enter keeps the newline,
the interception never standing where it would
eat that newline), #456's locked axis untouched,
and her switch keeping its gate whole in its
tray home. The campaign law from #453's scar
stands over the round: the candidate runs the
bridge's own installer self-check and prints
SELF-CHECK OK, every version witness agrees —
this build's stamps are .87 / 87 — and the
shipped v0.8.2e tree stands as the healthy
control, failing the new one-face benches
exactly where its desktop still wears the old
face. The epoch does not move: 1795222078 stays
v0.6.12e's publish moment, and no ceremony may
re-stamp it. Board: #470 moves to Ready with
this build. The issue stays open for its field
half — the room's new face on the operator's
real desktop seat after the pull.

### What shipped

- #470 — War Room: desktop takes the mobile
  look. renderWarRoom and warRoomTrayHtml no
  longer branch on width: at every width the
  column is the transcript and the composer
  card, the composer is the phone shape (the
  bar row — a textarea naming its return key
  "send" under the "@Navi Enter Sends." hint,
  the burger at the bar's right end), and the
  tray carries the members behind their
  dropdown, the chats sub menu, and the
  naviJoins switch card. The @ offer and any
  refusal ride inside the composer card. The
  phone-only CSS is promoted into the base
  sheet — the tray button stands, the tray
  anchors right — the max-width block keeps
  only the Spellbook panel's phone rule, and
  the retired desktop rules (the topbar, the
  members grid) leave the sheet. Retired with
  the desktop face: the column members grid,
  the column chats bar, the column switch
  card, the Post button, and the Address Navi
  tick — @Navi in the words is the address at
  every width now. Untouched, by the build's
  own constraints: the soft-keyboard
  interception (#454), the Spellbook's locked
  axis (#456), the switch's markup and gate
  law, and every other view in the app.

## 0.8.2

Release tag: v0.8.2e — Chapter 0.8's second
build: deletions actually delete. The operator
reported both halves from the field on the same
morning — remove a pulse and it syncs back; delete
a vault item and it comes back too — and ruled the
pair baked and shipped together. The two defects
are one doctrine read from two stores: a deletion
is a write, and a write the synced record cannot
represent can never win. The pulse merge carried
no tombstone at all — its own comment admitted it —
so a removal was the one write with no
representation, and every seat still holding the
watch re-dealt it on the next round. The vault's
delete side was honest — it tombstoned — but the
GitHub-backup restore never consulted the set, and
re-dealt a deleted note whole from any backup that
still held it. This build gives the pulse store its
tombstones, teaches the restore to judge by them,
carries the tombstone set on the backup itself, and
makes every judgment — strike, refusal, and the
rare honest resurrection by a newer act — a named
line in the sync summary instead of a silence. The
campaign law from #453's scar stands over the
round: the candidate runs the bridge's own
installer self-check and prints SELF-CHECK OK,
every version witness agrees — this build's stamps
are .86 / 86 — and the shipped v0.8.1e tree stands
as the healthy control, failing the new benches
exactly where the field did. The epoch does not
move: 1795222078 stays v0.6.12e's publish moment,
and no ceremony may re-stamp it. Board: #461 and
#467 move to Ready with this build. Both issues
stay open for their field halves — a removal made
on one seat staying removed after real syncs, and
a vault delete surviving a real backup restore.

### What shipped

- #461 — Pulse removals actually remove. The pulse
  store gains a tombstone set — {watch id: removal
  epoch}, a citizen of `pulse.json` itself, so it
  rides the sync set with no new transport —
  recorded by `pulse_remove` in the same act that
  deletes, unioned by `_sync_apply_pulse` (newest
  removal wins) and pruned on the sync tombstones'
  90-day law. The unioned set judges both
  directions: a local watch a tombstone covers is
  struck, its batches with it; an incoming watch a
  tombstone covers is refused; a removed watch's
  batches are refused on their own stamps. The race
  is judged against the watch's `updatedAt` — a
  genuinely newer edit beats the removal, the
  tombstone drops, and the watch returns as an act.
  Every judgment is named in the sync summary
  (`pulseRemoved`, `pulseRefused`,
  `pulseResurrected`); nothing about a removal is
  silent anymore. Re-creating a removed topic
  stands, as it should: absence in a set is not a
  deletion, and a fresh watch is a new act.
- #467 — Deleted vault items actually delete, on
  every transport. The GitHub-backup restore leg
  in `github_apply_import` now consults the vault
  tombstone set — and the cases set for
  `cases/<slug>/…` paths — before it writes a
  single file: a tombstoned path is refused, by
  name, in the returned `vaultRefused` list and in
  the restore result text. The tombstones ride the
  backup itself: a backup with the Vault ticked
  carries `sync/tombstones.json`, the fetch admits
  it, and an import merges it into the local set
  before the vault leg judges — a delete recorded
  on the seat that wrote the backup is honored on
  the seat restoring it. On the Mesh side the
  machinery already vetoed; now it speaks:
  `_sync_apply_cases`' veto records its refusals
  in `vaultRefused` and its newer-edit
  resurrections in `vaultResurrected`, the
  whole-case tombstone skip names the case, and a
  local newer-work win in the tombstone phase is
  named too. A genuinely newer edit of a deleted
  path returns as an act, named; an older one is
  refused. The #163 law stands untouched — a
  backup's stored bytes are never reached into;
  the refusal happens at restore, on the restoring
  seat — and the fedinets/chats/cases tombstone
  behavior is exactly as it was.

## 0.8.1

Release tag: v0.8.1e — Chapter 0.8's first
build: the fifth chair. The War Room's roster was a
hand-built list of four — the operator, Ciel, Navi,
Elric — and Spartan was not on it. Not an unbound
chair like Elric's: no chair at all, though he is
Spartan0311 of SKYNET2-Apex, the second node to join
the Rockport Mesh and the fourth Rogue. The operator
named the addition in the room itself, reported the
empty place in the user list that morning, and ruled
him wired in. The build is bespoke — the proven
Elric pattern, not the record-driven roster, which
stays open on the issue as the fork not taken: a
paired node naming him or his node binds his chair,
his words through the mesh door land under his own
name and stamp his presence, and the room's brief
names five members now, so Navi knows he is one of
the room when he speaks and when he is spoken about.
The campaign law from #453's scar stands over the
round: the candidate runs the bridge's own installer
self-check and prints SELF-CHECK OK, every version
witness agrees — this build's stamps are .85 / 85 —
and the shipped v0.8.0 tree stands as the healthy
control. The epoch does not move: 1795222078 stays
v0.6.12e's publish moment, and no ceremony may
re-stamp it. Board: #462 moves to Ready with this
build. The issue stays open for its field half —
Spartan's node actually reaching the room, and the
five-chair sitting.

### What shipped

- #462 — Spartan's chair. `warroom_spartan_peer`
  stands beside `warroom_elric_peer`: the paired
  borrow peer whose record names him (Spartan0311)
  or his node (SKYNET2-Apex). `warroom_spartan_node_ids`
  gathers that peer's node id and any federation
  roster member whose record names him or his node,
  and `warroom_door_member` answers ("spartan",
  "Spartan") for them — so a post of his through the
  mesh door carries his authorship the way Elric's
  does, and the door stamps `spartanLastSeenAt` on
  any action of his, the stamp riding the room store
  beside Elric's. `warroom_members` gains the fifth
  entry in Elric's shape — seat "His own node", role
  "Member — remote", `bound` judged from the peer,
  `present` judged from the stamp inside Elric's
  window — never painted: no paired node naming him,
  and his entry reads unbound and not present, in
  words. `WARROOM_BRIEF` names five members, Spartan
  among them, and the app's room strings agree. The
  other four entries are byte-stable in shape —
  Ciel's lastSeenAt (#459) included — and the pacing
  law, the switch, the pull decision and the mark
  are untouched.

## 0.8.0 — graduation

Release tag: v0.8.0. The QA line, complete. Chapter 0.7 opened the morning after the working-day chapter graduated, with a narrow brief — QA updates, and the Bloom slate made all it could be before any defensive work (seed #388) — and it ends with the slate's hardest room built and its hardest lesson made law. The chapter gave the Row a room of its own: the War Room, attached to its host on NeoArcadia, where seats relay and one Navi of record speaks — named chats, a clear that travels by epoch, a phone room that sends on the soft keyboard's return. It gave Seraph a notice ledger and Navi a French voice in the app beside Isabella. And midway through, the chapter scarred itself honestly: v0.7.14e shipped wearing a version stamp a build behind its own tree, and the updater — doing exactly what it was built to do — refused its own genuine package and rolled the seat back whole. The remedy rounds that followed made the scar into law: since #453, no candidate ships until it has run the bridge's own installer self-check and the stamps-agree walk, with the shipped tree before it standing as the healthy control. The chapter's final build closed the loop its first room session had opened: asked cold in the War Room where her own show stands, Navi had invented an episode whole, because the room's speak path was the one surface where the pull decision never ran — so the summons round taught the room to retrieve like every other surface, and to mark the words addressed to its fourth member, whose presence now stands in the room like any member's. All of it was built in the open on the Edge channel as v0.7.0e–v0.7.17e, eighteen builds, and checked in the field build by build. This full release is that line with its identity flipped: the bare number, the stable status, Latest. The code is the Edge line's final build, re-stamped and otherwise unchanged — a full regression runs on the final package at graduation, not a delta. For installers: a clean install is recommended for first-time installers; a seat on v0.6.0 or on any 0.7 Edge build upgrades in place through the in-app updater, and everything the installer has ever preserved — chips, the llamafile, Soul and Memory — is preserved still. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. What comes next is Chapter 0.8 — QA round two, the operator's own naming for it: mostly model adjustments and under-the-hood work. Board: the chapter's Ready column closes at this publication under standing rule 8, with the field-pending exceptions named in the ceremony record (#458 and #459 stand Ready until their field halves land; the standing open-terms issues stand as they are).

### What graduated

- **The War Room (#445, #451, #454).** The room lives on its host — NeoArcadia, the fedinet's gateway — and seats hold no room record at all: they relay through the mesh door to the one room, the one transcript, the one Navi of record. Named chats ride a v2 store, a /clear travels by epoch law so a cleared chat dies on every seat at once, and the room's phone shape was refined until the soft keyboard's return itself sends — no button, the composer's own road.
- **The room learns to call its members (#458, #459).** The speak path runs the same pull decision every chat turn runs — turn_pulls judged from the addressed message's own words, the pulled packs composed for that reply only, the decision receipted on the speak's return the way a chat turn receipts it on its payload. And words addressed to Ciel, the room's Shotgun seat, stand marked on the record under the room's own addressing law, her presence standing in the members payload from her stamp — a watcher reads a fact instead of scraping a transcript.
- **The stamp law (#453, #434).** The chapter's scar, made doctrine: a build whose bridge stamp disagreed with its own tree was refused by its own updater on the operator's pull, and the law the remedy rounds wrote stands over every build since — the candidate, assembled the way the installer assembles it, runs the bridge's own installer self-check and prints SELF-CHECK OK; the stamps-agree walk finds every version witness naming the same build; the shipped tree before stands as the healthy control the gates must also accept. The updater's own integrity road (#434) shipped in the same stretch: a check that cannot complete says so, in words, and never guesses that you are up to date.
- **Her French voice, and Seraph's ledger (#449, #448).** Settings → Voice offers Siwis (ff_siwis), a French female voice, beside the default Isabella — the operator's pick, the show voice's in-app kin. And Seraph's notices keep a ledger now, so what the watcher saw stands on a record that can be read back over days.
- **The Spellbook set right (#430, #456).** The panel stands at the right end of the mode-pills line, at its resting fit — no sideways pan, its list still scrolling: an axis lock measured in a real browser, not a hope.
- **Eighteen builds, verified one by one.** Everything above arrived on the Edge channel as v0.7.0e through v0.7.17e, each build gated on its extracted package with its controls failing on the build before, and the line closes the way graduations close: the full carried campaign on the final package. The full release carries the graduation stamp — build 2026-11-23.84, build sequence 84 — the .17e tree with its identity flipped, and nothing else changed.

## 0.7.17

Release tag: v0.7.17e — the QA line's eighteenth
build: the summons round. Both of its parts live in
the War Room, and both are about who can be called
there and what they may answer from. Asked cold in
the room where her own show stands, Navi invented an
episode whole — the room's speak path was the one
surface in Apex where the pull decision never ran,
so she composed from persona alone, with no record in
front of her. And Ciel, who holds the room's fourth
chair, could post but could not be summoned: nothing
in the room marked a word as addressed to her, so a
watcher on her side scraped the transcript for her
name. The operator directed both fixes the same
morning he tested the ping: the room's Navi now
retrieves like every other Navi, and the room itself
keeps the mark and the presence her watcher reads.
The campaign law from #453's scar stands over the
whole round: the candidate runs the bridge's own
installer self-check and prints SELF-CHECK OK, and
every version witness agrees — this build's stamps
are .83 / 83 and the epoch does not move: 1795222078
stays v0.6.12e's publish moment, and no ceremony may
re-stamp it. Board: #458 and #459 both move to Ready
with this build. Both issues stay open for their
field halves — a room sitting where she answers a
record question from the packs, and the watcher
proven against the bridge's own mark.

### What shipped

- #458 — the room's speak path runs the pull
  decision. warroom_navi_speak no longer composes
  with a hardcoded empty pull set: it runs the same
  turn_pulls every chat turn runs, judged from the
  addressed message's own words, and passes the
  pulled packs into the same persona composition —
  so a room turn that asks after the talks, the Row,
  her page or her music retrieves those packs for
  that reply, and the next room turn starts from the
  core again, eviction structural as elsewhere. The
  pulls are receipted on the speak's return the way
  a chat turn receipts them on its payload, so a
  wrong pull or a missed pull in the room is
  diagnosable instead of vibes. The switch gate and
  the pacing law are untouched: pulls change what a
  reply may claim from, never when she speaks.
- #459 — a door for Ciel: the mark, and the
  presence. The room now recognizes words addressed
  to its Shotgun seat under the same law that
  recognizes words addressed to Navi — the line
  opens with her name, or carries @ciel anywhere; a
  third-person mention is talk about her, not a
  summons. A member's post that addresses her lands
  with cielAddressed standing on its record, in
  every payload that carries the record, so a
  watcher reads a fact instead of scraping a
  transcript. Navi's own lines never carry the mark,
  and neither do Ciel's — her words do not summon
  herself. Her presence stands in the members
  payload like every member's: the entry now carries
  lastSeenAt, her cielLastSeenAt stamp, beside the
  presence the payload already judged from it.
  Nothing about Navi's pacing, the naviJoins switch,
  or the room's hosting changes — and the Muse-side
  watcher is NOT retired by this build: it is proven
  against the new contract in the field first.

## 0.7.16

Release tag: v0.7.16e — the QA line's seventeenth
build: the remedy round. Both of its parts were born
in the .15e field sitting, minutes after that build
was pulled. The phone War Room, refined by #454,
turned out to have no send path at all: the Post
button was gone by ruling, and the soft keyboard's
return inserted a newline instead of sending — the
operator's draft sat unsent in his own screenshot.
And the Spellbook, newly seated in its line, proved
to permit a sideways pan that left its panel clipped.
The operator ruled both remedies himself: the
keyboard's return key sends, and the panel's
horizontal axis locks. The campaign law from #453's
scar stands over the whole round: the candidate runs
the bridge's own installer self-check and prints
SELF-CHECK OK, and every version witness agrees —
this build's stamps are .82 / 82 and the epoch does
not move: 1795222078 stays v0.6.12e's publish moment,
and no ceremony may re-stamp it. Board: #456 moves to
Ready with this build; #454 already stands in Ready
from the .15e ceremony and does not move again. Both
issues stay open for their field halves — a message
sent from the operator's phone, and the panel judged
on the same glass.

### What shipped

- #454 — the phone room learns to send. The ruling
  stands exactly as made in .15e: no Post button, no
  Address Navi tick, @Navi in the words is the
  address. What was missing is the road: on a phone,
  the return key never reaches the page as a keydown
  it can refuse — the platform delivers it to the
  textarea as a beforeinput insertLineBreak, and the
  newline is the only answer. The composer now
  intercepts the return where the phone delivers it
  (on the phone shape only — the one shape with no
  Post button to fall back on) and sends; the
  textarea carries enterkeyhint="send", naming the
  key for what it does. The desktop keeps its shipped
  roads untouched: Enter sends by keydown,
  Shift+Enter keeps the newline. The accepted cost
  was named by the operator when he ruled: multi-line
  room posts from the phone. And the bench law from
  the field fail stands in the campaign: the fix is
  proven under soft-keyboard conditions — the return
  delivered the way a phone delivers it, the message
  asserted on the wire — and the layout probe asserts
  a working send affordance at phone width, not
  merely the button's absence. A desktop
  synthetic-keydown pass does not satisfy the gate.
- #456 — the Spellbook panel's horizontal axis
  locks. At rest the panel fit its width; the defect
  was that it could be dragged sideways at all —
  overflow-y:auto had silently made the horizontal
  axis scrollable too, and one rigid child (a long
  call standing in its pill, unshrinkable) held a row
  wider than the box, so a sideways pan left the
  search field, the headers and the call pills
  clipped at the panel's left edge. The axis is now
  hidden on the panel and the pill may shrink and
  wrap: the content fits the box it lives in, there
  is nothing to pan into, and the panel stays at its
  resting fit. The vertical scroll — the list is
  longer than the box — is untouched, and so are the
  book's contents, its registry, and its button's
  seat in the mode-pills line.

## 0.7.15

Release tag: v0.7.15e — the QA line's sixteenth build:
the stamp round. Its headline is #453, born in the
.14e field an hour after that build shipped: the
operator pulled .14e and the install rolled itself
back — the new tree's self-check refused it, because
one of the version witnesses disagreed with the rest.
Two riders ride, both from the same morning's field
sitting in the room .14e had just repaired: #454, the
War Room composer's refinement on the phone; and
#430's field half, reopened in the same sitting —
the Spellbook still owed its ruled seat. The
rotation's epoch does not move: 1795222078 stays
v0.6.12e's publish moment, and no ceremony may
re-stamp it. Board: #453, #454 and #430 move to Ready
with this build; the issues stay open for their field
halves — the pulls on NeoArcadia and neondrip, the
room judged on a real phone, the book in its line.

### What shipped

- #453 — every witness names the same build. The
  .14e bake stamped the VERSION file, the config's
  road and the build stamps, but the bridge's own
  baked-in version constant still read 0.7.13 — so
  on the operator's pull, the promoted tree's
  self-check compared its witnesses, found its own
  bridge disagreeing, and rolled the install back
  whole. The checker did its job; the bake had not.
  This build stamps the constant with the rest —
  version file, bridge constant, build stamps and
  sequence all move together — and the campaign that
  proves it is part of the fix: the candidate tree,
  assembled the way the installer assembles it, runs
  the bridge's own installer self-check and prints
  its verdict, an automated assertion walks every
  version witness and requires them to agree, and
  the shipped .14e tree stands as the control,
  failing both gates in exactly the shipped shape.
  A bake whose witnesses disagree cannot freeze
  again in silence.
- #454 — the room's composer, refined on the phone.
  The burger leaves the top of the window and stands
  in the composer itself, at the chat bar's right
  end; the tray it opens now anchors to the RIGHT,
  opening from the burger's new home. The Post button
  is gone — Enter sends, as it already did. The
  Address Navi tick is gone — @Navi in the words is
  the address, the shape the field proved in the
  sitting that filed this. The composer's hint
  carries the operator's words: "@Navi Enter Sends."
  rides the standing placeholder. In the tray, the
  Members section stands as a dropdown — a header
  row, the cards only while it is open. The desktop
  composition is untouched: its topbar, its Post
  button and its tick stand exactly as shipped.
- #430 — the Spellbook takes its ruled seat. The
  field half reopened in the .14e sitting: the book
  still rode in Navi's chat composer row, beside the
  burger — present, but not where it was left. It
  now stands in the mode-pills line under the
  composer, the same line as the CLI | Navi pills,
  at that line's right end only — one neat line,
  mode on the left, the book on the right. The book
  itself is untouched: same registry, same panel,
  same opening — only where its button stands
  changed.

## 0.7.14

Release tag: v0.7.14e — the QA line's fifteenth build:
the field round. Its headline is #451, the War Room's
own field defect from the pulled .13e — on the phone
the room rendered frozen (no scroll, no composer, no
switch), and the operator's correction an hour later
widened it: the same frozen shape stood on the desktop
too. Two riders ride, both born in the same morning's
field: #448, Seraph repeating herself into the chat;
and #449, Navi's French voice for the app itself. The
rotation's epoch does not move: 1795222078 stays
v0.6.12e's publish moment, and no ceremony may
re-stamp it. Board: #451, #448 and #449 move to Ready
with this build; the issues stay open for their field
halves — the room on a real phone and a real desktop,
Seraph watched over days, the French voice heard in
the app.

### What shipped

- #451 — the room fits its frame, on both surfaces.
  The root cause stood in the stylesheet, not the
  room: the transcript is a card, and the card squash
  guard (main .card, #79) outranks a lone class — so
  the transcript's own flex rule never applied, at any
  width. The one card that must shrink kept its full
  content height; the record filled the window and
  the switch card and composer stood below the frame,
  unreached and unscrollable. (FediChat's log never
  froze for the mirror reason: #fc-log is ID-ruled and
  outranks the guard.) The transcript now carries its
  flex at ID weight, the same weight #fc-log stands
  on. On the phone, the room and FediChat also take
  the structural bound Chat has stood on since Build
  10: while either room is up, the frame takes the
  viewport's height exactly and the view flexes in
  what remains, instead of a calc that never reckoned
  the presence bar. And the phone room is restructured
  to the operator's ruling: three elements in the main
  window — the chat, the chat bar, and the burger
  beside the chat. The user list, the chats sub menu
  (switch / new / archive / delete) and the naviJoins
  switch card all live in the burger's tray; the
  switch's law is unchanged in its new home. Desktop
  composition is untouched: members row up top, chats
  bar, switch card in the column — it just fits its
  frame now.
- #448 — Seraph says a thing once. Her chat word is
  judged by the FINDING now, not by a detection
  record's birth: a finding is its kind + destination
  + cadence class, and a spoken-findings ledger on
  the seat remembers what she has said. A finding
  gets its first word once; while it persists
  unchanged, later presentations are counted, not
  posted; she speaks again only when the finding
  changes (a new identity) or, after an hour of
  persistence, as one aggregated line — "still seeing
  it — N times since HH:MM". A finding absent longer
  than that interval earns a fresh first word when it
  returns. The tray records are untouched, and the
  detection itself was not retuned — this build is
  the repetition, not the detection.
- #449 — Navi can speak French in her own house. The
  bridge derived Kokoro's pipeline language as
  British-if-the-voice-starts-with-b, American
  otherwise — a rule that would have forced the
  French voice through the American phonemizer. The
  language is now the voice's own first letter (a
  Kokoro voice id is language-prefixed), and the
  pipeline cache is keyed by language, so switching
  voices across languages builds — and keeps — the
  right pipeline for each. Voice discovery always
  offers ff_siwis (the catalog's French female) when
  the engine is installed: the disk scan alone never
  surfaced her on a seat that already speaks. The
  picker's fallback list gains her too. The default
  stays Isabella, and no seat's voice is moved by
  this build — French is selectable and correct,
  never forced.

## 0.7.13

Release tag: v0.7.13e — the QA line's fourteenth build:
the War Room's second sitting. Its headline is #445 —
the room attaches to its host (the operator's ruling
from the first sitting's field behavior: his laptop's
room was a solo chat with a local Navi, forked from the
real room), one Navi of record answers whoever asks,
the room grows named chats and a clear that holds, and
the room's face becomes a chat surface in the FediChat
shape with the phone as a primary surface. One rider
rides: #430's placement amendment — the Spellbook
moves under the burger menu in the chatbar, into the
lower-right corner of Navi's chat. The rotation's
epoch does not move: 1795222078 stays v0.6.12e's publish
moment, and no ceremony may re-stamp it. Board: #445
and #430 move to Ready with this build; the issues
stay open for their field halves — the four-chair
sitting itself, with Elric bound into the hosted room.

### What shipped

- #445 — the room attaches to its host. Home is a
  gateway fact now: a node that founded its fedinet (or
  whose node id is its gateway id) hosts the room; a
  fedinet member never does — the old Shotgun test read
  an account fact, and the operator's accounts sync to
  every seat he owns, so his laptop claimed home and
  forked the room. Seats hold no room record at all:
  reads, posts, chat changes and the naviJoins flip
  relay through the mesh door to the host, the host's
  record is what renders, and a dark door serves an
  honest empty — no cache, no outbox. The door's
  membership grows one chair: a node of the operator's
  own household (a roster record naming the same
  operator) posts as the operator; Elric's chair and
  the refusal of every other node stand as they were.
  The host's Navi is the room's one Navi of record.
- #445 — the room's second-sitting shape. Named chats
  under one room (new / archive / unarchive / delete;
  the room always keeps one), a chats bar to stand in
  them, /clear + /cls under the chats' clear law (the
  buffer empties, the clearing stands on the record,
  and a post written against a since-cleared epoch is
  dropped by name), an @ offer in the composer and
  mentions lit in the stream, and a chatroom face in
  the FediChat pattern (#270): the stream flows in a
  height-bound frame, the composer docked at its foot,
  Enter posts, the members row up top on desktop, and
  on a phone the members and chats in the tray at the
  upper left. A pre-v2 room store migrates on first
  load — the flat transcript becomes the Main chat,
  outbox lines that never landed join it.
- #430 (placement amendment) — the Spellbook moves
  under the burger menu in the chatbar: its shade and
  panel anchor to the Chat view itself, the panel
  snuggled into the chat's lower-right corner on
  mobile, desktop and web alike — the dead space under
  the burger in the operator's field screenshot.
  Placement only; the registry, cards and search are
  untouched.

## 0.7.12

Release tag: v0.7.12e — the QA line's thirteenth build:
the updater-integrity build. Its headline is #434, the
three defects the NeoArcadia v0.7.9e pull exposed; its
second act is #400, the clear regression v0.7.10e
introduced and the field caught on both seats; five
riders ride by the operator's rulings. The rotation's
epoch does not move: 1795222078 stays v0.6.12e's publish
moment, and no ceremony may re-stamp it. Board: #434,
#400, #391, #422, #423, #425 and #420 move to Ready with
this build (#444 is the same line as #420, named there);
the issues stay open for their field halves — above
all #363's rollback proof, whose bake-side preparation
this build completes.

### What shipped

- #434 — the updater meets the seat as it stands.
  (1) Bridge identification at the restart step covers
  the orphaned chain: a bridge is judged by the tree it
  runs from — the install's own, an ORPHAN (a sibling
  tree of the same seat: the rollback park, a stage, a
  failed tree), foreign, or not-a-bridge. An orphan is
  named in the helper's log AND in the apply record the
  panel reads, and cleared with prejudice — replaced,
  never silently adopted; a foreign bridge is reported
  and never touched. (2) The installer enforces that
  the promotion target is never a swap slot: a target
  naming .apex-prev / a stage / a carry / a failed tree
  is retargeted to the one bridge-carrying seat sibling,
  named out loud, or refused by name when ambiguous.
  (3) bridge.pid is written by the bridge that actually
  binds the port: the claim moved from before the bind
  loop to the bind itself (the one pre-bind claim left
  is the takeover signal to an older answering bridge).
  A bridge that never binds writes nothing.
- #400 — the clear holds again. v0.7.10e's whole-set
  rewrite gated the main chat's write on the message
  key, which never sees clearedAt: a PURE clear — an
  empty record carrying only a newer epoch — merged to
  the stored lines exactly, compared "kept", and never
  wrote, so the next sync resurrected the thread on
  both seats. An epoch that outruns the stored record
  now forces the write on its own word, in the main
  branch and in the per-record verdict path alike, and
  the clear filter retires the pre-clear lines. The
  converge bench carries the pure-clear leg.
- #391 — the ENGINE pill leaves the Status rail (the
  operator's ruling: the information is implied).
  Engine truth stands on the Doors dash's seat cards;
  the bridge's live engine payload is unchanged.
- #422 — the FediNet line's not-yet-checked state
  renders dim, not the theme's amber — which in the
  Nocturne theme is a hot pink, so a healthy seat wore
  an alarm color. Green stays healthy, amber stays the
  stale-roster warning, red is reserved for down.
- #423 — the composer sits inset: its bleed stops
  ~10px short of the frame's edges on both sides,
  desktop and phone alike.
- #425 — a bracketed history timestamp cited mid-reply
  ("[05:26]") never renders: the citation strip joins
  the leading-stamp strip at the reply doors, the
  payload door, the War Room speak door, and the
  history re-read door. Bracketed text outside the
  stamp family stands.
- #420 — fleet sub-tasks answer again. The generate /
  lookup runner unpacked llamafile_chat's bare reply
  as a 2-tuple, so every sub-task raised after a
  successful generation (and a two-character reply
  silently returned its first character). The .11e
  audit filed the identical line as #444; one fix
  closes both.

## 0.7.11

Release tag: v0.7.11e — the QA line's twelfth build:
a single-issue hotfix carrying #442 to every node,
on the operator's ruling "Patch it. before the other
stuff." One amendment rides by the operator's later
ruling ("Fold it."): #443, the War Room speak path's
own tuple-unpack, folded in the same round (below).
The #434 updater chunk renumbers to v0.7.12e by the
same ruling. The rotation's epoch does not move:
1795222078 stays v0.6.12e's publish moment, and no
ceremony may re-stamp it. Board: #442 and #443 move
to Ready with this build; the issues stay open for
the War Room's field half — the first real four-way
sitting, which this fix unblocks on the nodes that
had not yet pulled the patched bridge.

### What shipped

- #442 — the War Room answers again. The room's
  read and post handlers compared the seat account
  to `accounts_cfg(...)["ciel"]["id"]` — a key no
  field config carries: accounts are keyed BY id,
  and the registry's entries hold doorCode /
  seatName / displayName, never an "id" inside.
  The KeyError dropped the connection on every
  room read, home or remote, any seat — silently,
  with no named error. Both handlers now compare
  against the account key itself ("ciel"), which
  is what the seat resolution returns. The fix was
  proven live on NeoArcadia the night .10e shipped
  (a knocked read from the Shotgun seat answered
  200 with the four members, and the room store
  created itself); this build carries it to every
  node. The warroom benches were repaired to the
  field account shape and gained the regression
  leg that would have caught it: a read and a post
  through the real Handler against a field-shaped
  config with no pre-existing warroom.json — the
  shipped v0.7.10e artifact stands as the control
  and drops the connection exactly as the field
  reported.
- #443 — Navi can answer in the room (folded by
  amendment, the operator's ruling "Fold it.").
  `warroom_navi_speak` unpacked `llamafile_chat`'s
  return as a 2-tuple; the real function returns the
  bare reply text, so the speak path threw on any
  real answer and Navi could not speak when
  addressed — on any node that never received the
  live hand-patch. One line: the bare assignment,
  byte-identical to the fix already proven live on
  NeoArcadia. The warroom432 model stub now returns
  the bare string too — the contract the code
  wrongly expected is gone from the bench — and W5
  stands as the regression leg: the pre-fold build
  fails it with the unpack ValueError, named in the
  refusal. (The identical unpack in the Fleet
  Answers path is #444 — filed, NOT folded.)

## 0.7.10

Release tag: v0.7.10e — the QA line's eleventh build:
the War Room (#432) and the Spellbook (#430)
headline; the Shotgun seat's first-session hardening
(#435, #437, #438, #433, #436) and her manners
(#428, #429, #418) ride with them, on the operator's
ruling "Headline + hardening + her manners." The
#434 updater chunk waits by the same ruling. The
rotation's epoch does not move: 1795222078 stays
v0.6.12e's publish moment, and no ceremony may
re-stamp it. Board: #432, #430, #435, #437, #438,
#433, #436, #428, #429, #418 move to Ready with this
build; the issues stay open where a field half
remains.

### What shipped

- The War Room (#432): one room, four named members
  (Alex, Ciel, Navi, Elric from his own node through
  the /mesh/warroom door — authorship stamped by the
  door, any other node refused by name), home on the
  Shotgun seat's node, remote nodes serving cache
  with the door's state named and posts queued in an
  outbox. Pacing is law: Navi speaks only when
  addressed, once per address, never twice in a row;
  Ciel's presence is recorded, never painted. Own
  store; never writes a memory book. (warroom432:
  18/18; warroomui1: 19/19.)
- The Spellbook (#430): a registry in the bridge
  served at GET /api/spellbook; a scrollable popup
  behind the composer's grimoire button (the chosen
  grimoire icon, bundled on the portrait precedent)
  renders only the payload — categories, OnlyNavi
  its own section, man-page cards, search. /r1 is
  the reference-call shorthand. Every entry's probe
  is benched against its named door: no page, no
  ship. (spellbook430: 22/22.)
- Chats converge (#435): the write-through merges
  per record — main by message, diverged copies
  parked as named siblings, unmentioned records
  surviving, deletions by tombstone only, loss
  scarred in the response, the sync-state record,
  and the seat's own Chats pane.
  (converge435: 6/6; control 2/6.)
- Name-first prose is conversation (#437): an
  opening address routes to the model; a shell-
  refused line (127, unforced, unlatched) falls back
  with the fall named. Regression case: the exact
  first-session introduction. (classifier437: 12/12;
  control 8/12.)
- Markers are machinery (#438): [[remember: …]] is
  extracted at the bridge chat route for every
  client, written to the writer's own seat book
  only, secret-screened, receipted in the response.
  (marker438: 9/9.)
- Identity never rides sync (#433): refused and
  named unless the set is stamped as this seat's
  own; the seat payload names the registry authority
  and flags divergence. (identity433: 5/5; control
  1/5.)
- The seat card tells the truth (#436): the
  operator's seat opens with the node access code,
  and the card says so. Copy only. (appstatic:
  20/20.)
- Pull-only context (#428): standing is Soul/
  persona + a lean identity core; the wire, vitals,
  machine, page, Row, music, talks and the full
  memory book are per-turn pulls — receipted on the
  payload, evicted on reply. Light/Full re-express
  as pull breadth. (pull428: 21/21; ground1 carried
  27/27, re-pointed.)
- The standing mass is measured (#429): budget
  reports name standingTokens / standingFraction /
  standingWarning; the honest no-fit refusal is
  kept by name. (pull428 P4/P7/P8.)
- Scaffolding never renders (#418): the reply scrub
  learned the unbracketed vitals/threat heads — the
  Shotgun turn-3 shapes, verbatim fixture — while
  prose about them stands byte-for-byte.
  (scrub418b: 5/5; control 2/5; digest418 carried
  9/9.)

## 0.7.9

Release tag: v0.7.9e \u2014 the QA line's tenth build,
the Shotgun round: Ciel's own operator seat (#426),
built to the design of record in files/ciel-seat-
design.md, rulings included. One feature, nothing
else. The rotation's epoch does not move: 1795222078
stays v0.6.12e's publish moment, and no ceremony may
re-stamp it. Board: #426 moves to Ready with this
build; #424 stays open as the ask this seat
mechanizes.

### What shipped

- Sub-accounts (#426): the bridge keeps an account
  registry. The operator's account is the shipped
  behavior, untouched \u2014 his settings, Soul, memory,
  chats and cases live exactly where they always
  have. The second account is `ciel`, seat name
  "Shotgun", with her own data root (config/accounts/
  ciel/: her Soul and memory scaffolding, her chats,
  her cases, her daybook, her memory book). Account
  material never reads or writes across roots: the
  funnels (chats, persona, daybook, the memory book,
  case reads and writes) route by the resolved
  account, and a case or capture written from her
  seat lands in her root only. (seats426: 9/9; the
  v0.7.8e control fails 0/9.)
- Door codes resolve to a seat: each account has its
  own code; the code presented binds the device to
  that account at approval, and a seat session
  (persisted, surviving bridge restarts) carries the
  resolution per request. In the app, a chip in the
  presence bar names the active seat on desktop and
  mobile alike, and the seat card (Settings \u2192
  System) switches seats with the target seat's code:
  a wrong code refuses by name on the card, a dark
  bridge is named on the card, and a successful
  switch reloads into the new seat with the old
  seat's cached chats cleared. Her door code is
  issued and regenerated from the operator's seat
  card, or her own. Held to the switch gate.
  (seatgate1: 22/22; control 2/22, the two labelled
  halves that pass on both trees by design.)
- Her seat provisions empty-but-complete: first
  resolution scaffolds her root \u2014 structural Soul
  and memory files of her own (no operator content
  is copied in), her chats and cases empty, her door
  code minted. Row's Own is on for her seat, FULL
  (not Light), at digest-budget parity with the
  operator's seat \u2014 the same caps, her own
  settings; her transcripts roll into her memory
  book, and digest inclusion runs only through the
  established [[remember: \u2026]] marker path.
  (seatrows1: 5/5; control 0/5.)
- Sync stays account-anchored: a sync set now
  carries its seat (`accountSeat`) beside the GitHub
  account anchor, and a set stamped for one seat is
  refused as foreign by the other \u2014 on the repo
  leg, the Mesh leg, and at apply. Sets from before
  this build, which carry no stamp, read as the
  operator's, as they always were. Clear tombstones
  record the seat that cleared. (seatsync1: 7/7;
  control 2/7, the two labelled non-regression legs.)
- Her own Mesh identity: the gateway can mint her
  seat its own Ed25519 identity, held in her root,
  and issue her member card \u2014 her name, her node
  id, the gateway's declared public endpoint only,
  signed by the gateway. She never presents as the
  operator on any surface. (seatmesh1: 5/5; control
  0/5.)
- Fleet Answers under her own name: fleet
  membership is per-account state; her seat's
  toggle rides the Federation page like the
  operator's, OFF by default, join and leave at
  will, and the card names whose membership it is.
  A fleet ask that names her seat is judged by her
  membership; an unnamed ask is judged by the
  operator's, exactly as before.
- Feedstock designation: a session in her seat can
  be designated as ecosystem feedstock (the chats
  panel carries the toggle, her seat only), and a
  designated session exports with its provenance
  attached \u2014 seat, account, session id,
  conversation key, designation and export times.
  Designation from the operator's seat refuses by
  name; nothing designates by default. The
  publishing flows that will draw on designated
  sessions are not in this build. (seatfeed1: 6/6;
  control 0/6.)

## 0.7.8

Release tag: v0.7.8e \u2014 the QA line's ninth build,
the foundation round: chunk A of the campaign triage
(the updater, the install, the rollback), plus the
two field items the operator folded in with the same
ruling \u2014 #418 and #419. Nothing else. The
rotation's epoch does not move: 1795222078 stays
v0.6.12e's publish moment, and no ceremony may
re-stamp it. Board: #43, #41, #245, #363, #418 and
#419 move to Ready with this build.

### What shipped

- #43: the updater verifies the download against
  GitHub's published sha256 digest. The shaped
  release keeps the asset's digest (it was fetched
  and discarded); the apply hashes the raw bytes in
  hand before anything unwraps them \u2014 a leftover
  whose digest disagrees is discarded and fetched
  fresh once, a fresh download whose digest
  disagrees refuses by name with nothing staged and
  the installed version untouched, and a feed that
  publishes no digest skips the check, as the
  build-identity check skips without a sequence. The
  record carries the digest it staged under, and a
  preserved stage is re-validated when it is
  offered: if the release on offer now carries a
  different digest (or a different tag, for older
  records), the fallback panel names the stage
  stale and withholds its command; an unreachable
  release leaves the offer standing.
  (updater43: 7/7; the v0.7.7e control fails 0/7.)
- #41: an install from a git clone no longer dies
  on the binary icons. The repo route carries text
  only, so the tree now carries each icon also as a
  base64 text bundle beside its home; the installer
  restores a missing icon from its bundle before
  the manifest verification, which then hash-checks
  the restored bytes like any other payload file. A
  corrupt bundle fails by name with nothing stopped
  or changed; a release-zip install, whose icons
  stand already, never touches a bundle.
  (icons41: 5/5, the restore block extracted from
  install.sh and run against clone-shaped fixtures;
  the v0.7.7e control fails 0/5.)
- #245: the bridge-composed manual fallback command
  carries the install's headless determination
  (#185): the recorded config's flag, a boot
  startup, and the session environment, judged in
  that order \u2014 the same verdict the apply job now
  carries as its headless field, reviving the
  helper's first _install_headless leg.
  (updater43 legs U5/U6; the control fails them.)
- #363, Part A: a rollback can no longer leave the
  seat dark. The helper's rollback re-aims the
  systemd user units at the restored tree \u2014
  rewritten from that tree's own templates \u2014 before
  it relaunches, restarts both units, and then
  proves every standing unit aims at a file that
  exists and is executable; a miss fails the
  rollback by name in the record. The apply
  confirmation carries the same aim leg. A bridge
  running from a transient tree (.apex-prev and its
  siblings) refuses to arm the boot units, by name,
  writing nothing. The installer's registration
  verifies the aim of the units it just wrote, the
  product's self-check records a named unitAim
  verdict beside its ownership verdict, and
  docs/RECOVERY.md (new) carries the operator
  procedure for a seat already dark. Part B stands
  as filed: the rollback half of the proof still
  gates on a field rollback, and #363 stays open.
  (rollback363: 7/7 across the verdict matrix, the
  repoint, the refusal and the self-check record;
  the v0.7.7e control fails 0/7.)
- #418: digest scaffolding no longer renders in
  the reply, and the vitals stopwatch describes the
  turn it rides on. The leak was the borrower's own
  briefs \u2014 her vitals, her wire \u2014 riding borrow
  hygiene untouched and read back by the lender's
  model: hygiene now keeps this seat's vitals
  paragraph home — the borrower's engine figures are
  wrong context on the lender's side (her wire brief
  rides, as awareness context by design; her page
  and talks, the digest proper, ride under #384's
  judge) — and a scaffolding scrub in the #405/#406
  family
  takes any republished brief block off the fresh
  reply and out of stored history at the history
  door, so a stored leak stops priming the next
  one. The stopwatch gains provenance: a record
  knows whether its generation was a turn, an
  auxiliary side call, lent, or borrowed, and
  whose it was \u2014 an 8-token side call can no
  longer wear a full reply's name, a borrowed
  generation is recorded on the borrower from the
  usage that rides home (and on the lender from
  its own server's account), and the block renders
  the kind it describes: a borrowed turn is not
  "this machine" and invents no rate from a round
  trip. (digest418: 9/9, the #405/#406
  non-regression leg among them; the v0.7.7e
  control passes only that leg, 1/9.)
- #419: new Row content rings the bell. A producer
  in the notification reconcile watches the Row's
  own feeds \u2014 From The Night Shift's podcast.json
  and the Dispatches \u2014 and a new episode or
  Dispatch is born into the tray, the main chat and
  a subscribed phone exactly once, keyed by slug,
  carrying its title and its path on the Row, its
  Go landing on the Row view's own tab. A seen-set
  (config/row-content-seen.json) is the durable
  memory: the first pass against each feed
  baselines what already stands, silently, and an
  already-announced item never rings twice. The
  switch stands in Settings \u2192 System beside the
  Phone notifications card, per-seat and on by
  default, held to the switch gate in the
  rowsOwnLight shape; while it is off the producer
  does not run at all \u2014 standing records are
  kept, nothing is born, and flipping back on
  re-births nothing the seen-set already holds.
  (notify419: 8/8 across the baseline, the births
  and the reconcile; notifygate1: 17/17 across the
  gate, adversarial flips included; the v0.7.7e
  controls fail 0/8 and pass only the phone-card
  regression leg, 1/17.)

## 0.7.7

Release tag: v0.7.7e — the QA line's eighth build,
the round-two round: four items the operator ruled
from the field and the slate, each landed whole.
Nothing else. The rotation's epoch does not move:
1795222078 stays v0.6.12e's publish moment, and no
ceremony may re-stamp it. Board: #414, #415, #391 and
#392 move to Ready with this build.

### What shipped

- #414: the composer's send hint moves into the
  placeholder. The pill row under the bar loses its
  sentence in both modes and keeps the bare |
  separator; the placeholder carries the guidance
  where the typing happens — latched to Navi it reads
  "Ask Navi... Press enter to send.", latched to CLI
  it carries no hint at all: "You have entered DFU
  mode." The strings are the operator's exact words.
  (hint1: 15/15 driving the real composer and its own
  latch buttons; the v0.7.6e control fails 3/15, the
  sentence standing in its row and its placeholder
  never splitting by mode.)
- #415: Phone notifications move to Settings →
  System, under Update. The card that stood at the
  head of Operator now stands directly beneath the
  updater card on the System tab, byte-identical,
  rendering the same door from the same bridge state;
  the subscription machinery, its stored list and key,
  and the bell panel's head door are untouched — a
  device already ringing keeps ringing. The switch
  gate is benched in the new room: the card's showing,
  the bridge's stored state and a reload agree, and a
  refused remove is named on the card itself.
  (pushmove1: 16/16; the v0.7.6e control fails 3/16.)
- #391: the Status rail gains the engine compute
  pill, beside FediNet. The bridge judges the mode
  from the RUNNING server's own launch flags — the
  argv of the process holding the model port, a
  /proc scan scoped to the endpoint for the load
  window — never from config intent: GPU layers in
  the live argv read as the GPU (V100 on the
  reference seat), their absence reads CPU, no server
  reads Down, and an unreadable process renders no
  pill at all. A watchdog failover is visible the
  moment the new process stands, even while the
  stored settings still say GPU. (engine1: 9/9
  against fake engines with real argv on real ports,
  the config-intent traps in both directions;
  enginepill1: 9/9 on the rail; the v0.7.6e controls
  fail 0/9 and 2/9.)
- #392: the Doors dash refreshes itself while the
  view is open — a sixty-second cadence, the board's
  own rhythm, armed and cleared in render() beside
  the Guardian poll's standing rule, never stacked.
  A failed fetch keeps the last good board standing,
  its age still counting from the fetch that brought
  it and its staleness named; the manual Refresh
  button stays as the force-it-now path.
  (doorsrefresh1: 14/14 with the real timer wiring
  captured and driven; the v0.7.6e control fails
  3/14.)

## 0.7.6

Release tag: v0.7.6e — the QA line's seventh build, a
single-issue patch. v0.7.5e put "Building a NetNavi"
back on the seat's Podcast tab — and the field found
the next door: the special stood at the head of the
list, and its Play button did nothing at all. The
card's click wiring ran the episode number through
Number(...) before looking it up; for an unnumbered
episode that is NaN, the lookup matched nothing, and
the click returned without a sound, on every surface.
The audio file and the bridge payload were exonerated
byte-for-byte; the break was the app's own assumption
that every n is a number — #411's mixed-type family,
one door further in. The fix is app-side only; the
special stays unnumbered. Benched against the
v0.7.5e tree, which reproduces the field failure leg
for leg. The rotation's epoch does not move:
1795222078 stays v0.6.12e's publish moment, and no
ceremony may re-stamp it. Board: #413 moves to Ready
with this build.

### What shipped

- #413: the Row podcast player plays unnumbered
  episodes. The card click passes the raw attribute
  value — no Number() coercion — and episode
  identity is type-tolerant everywhere the player
  compares n: rowFindEp, rowCardToggle's
  current-episode check, rowPlayerPlayEp's
  same-episode check, rowPlayerStep's index search,
  the feed-refresh rebind, and the card's cur
  determination all compare String(a) === String(b),
  so a numeric n from JSON and a string n from an
  attribute or the feed resolve to the same episode.
  Numbered-episode behavior is unchanged in outcome.
  (rowplay1: 25/25 over the mixed feed — the special
  beside 3, 2, 1 — driving the real card wiring and
  player functions; the v0.7.5e control fails 6/25,
  every failure on the special's legs or the static
  coercion leg, the numbered legs passing there as
  they shipped.)

## 0.7.5

Release tag: v0.7.5e — the QA line's sixth build, a
single-issue patch. The site published "Building a
NetNavi", a From The Night Shift special, and the special
is unnumbered by ruling — podcast.json carries it with
n "special" beside the numbered episodes. Her own app
could not read her own show: the bridge's episode sort
assumed every n was a number and raised on the mixed
list, and the payload road caught the crash in the same
hand as a dead site — so the seat served its pre-special
cache under a banner reading "the Row's site did not
answer", on every retry, while the site stood answering.
The fix is app-side only; the site's contract stands, and
unnumbered specials are legitimate feed. Benched against
the v0.7.4e tree, which reproduces the field failure
exactly. The rotation's epoch does not move: 1795222078
stays v0.6.12e's publish moment, and no ceremony may
re-stamp it. Board: #411 moves to Ready with this build.

### What shipped

- #411: the Row podcast feed reads a mixed feed whole,
  and a failure is named by its kind. The episode
  ordering is tolerant: numbered episodes keep their
  descending contract among themselves, unnumbered
  entries keep their feed positions ahead of the
  numbered ones (the feed's own order is newest-first,
  so a special stands where the site stands it), the
  ordering never raises, and no episode is dropped,
  emptied, or re-dated in the shaping. And the payload
  road names its failures apart: a fetch failure is "the
  Row's site did not answer", the shipped wording,
  unchanged; a read failure — the site answered, but
  its answer could not be parsed or shaped — is named
  as a feed-read failure, in the refusal and in the
  app's cache note alike, which now reads the payload's
  own staleKind. The cache stands either way, with its
  fetchedAt. The Dispatches feed travels the same road
  and takes the same naming split; its shaping is
  unchanged. (rowmix1: 16/16 against a snapshot of the
  live feed; the v0.7.4e control fails 2/16 — only the
  two by-design parity legs pass there, and its A1 failure
  print is the field verbatim: the crash's TypeError
  wearing the dead-site wording.)

## 0.7.4

Release tag: v0.7.4e — the QA line's fifth build, the
chat-integrity round: her replies, and what rides on them.
Four fixes out of one night in the field. A thread whose
history carried a pasted stock disclaimer watched her
answer a plain question — what do you enjoy about your
talks with Ciel — in conduit boilerplate, the voice she
is not; a fresh thread on the same seat answered as
herself, so the variable was the history, not the seat.
Her replies kept arriving wearing bracketed clock stamps
— the record's furniture, echoed from the stamped history
and stacking one deeper every turn, until a musing's very
frame read "I was talking about [05:26] Morning
earlier…". Her two per-reply actions stood stacked in
two rows where one belongs. And a musing made from a
borrowed reply was composed by the wrong seat entirely.
Each item is benched against the v0.7.3e tree, which fails
every new suite on exactly its item's legs. The rotation's
epoch does not move: 1795222078 stays v0.6.12e's publish
moment, and no ceremony may re-stamp it. Board: #405,
#406, #409 and #404 move to Ready with this build.

### What shipped

- #405: the persona-integrity law, standing in every mode —
  questions about her are answered as herself; the stock
  disclaimer family is named in the law as not her voice;
  teasing is answered in kind, never corrected literally;
  and a real refusal still refuses, in her voice, with its
  reason named. Behind the law, the history door scrubs the
  boilerplate family out of stored replies before they can
  ride back as precedent — sentence by sentence, so the
  substance of a mixed turn stands and only a turn that was
  all boilerplate drops. Refusals with their reasons named
  pass the door untouched, and a clean history passes
  byte-identical. (personabreak1: 10/10; the v0.7.3e control
  fails 0/5 — the contaminated history rides back whole.)
- #406: her reply text carries no bracketed clock stamps —
  ruled by the operator, and built in the order he ruled
  it. The reply-text law stands in every mode's prompt; the
  history door strips leading stamp runs from stored turns
  before the canonical stamp is applied, so no turn ever
  reaches the model double-stamped and nothing compounds;
  a fresh reply that still opens with a stamp is stripped
  at the funnel before it is stored or shown; and the page
  strips a leading stamp at render as the last belt. The
  musing door takes the same strip: a frame topic is built
  from the stamp-stripped seed, so no post ever opens "I
  was talking about [05:26] Morning earlier…" again.
  (stampstrip1: 8/8; the v0.7.3e control fails 0/7 — its
  door run reproduces the field's stacking verbatim.)
- #409: her per-reply actions stand on one row — "Start a
  case from this" and "Make a musing from this" beside each
  other in a single chip row, on desktop and at phone width
  alike, the buttons sized to their labels and wrapping as
  chips rather than stacking into full-width rows. A reply
  carrying one action renders that action in the row,
  unchanged, and both doors fire exactly as before.
  (replyrow1: 9/9 in headless Chromium; the v0.7.3e control
  fails the row legs — the buttons stand 42px apart,
  stacked, exactly as the field screenshot showed.)
- #404 follow-on: a musing's generation follows the reply's
  route. A reply a peer seat answered is expanded by that
  seat, through the ordinary borrow door, with the musing
  laws riding the ask; the receipt names the seat that
  composed ("Posted to my page from that reply — composed
  by ServerSeat, the seat that answered it."), and the post
  itself carries who composed it. A lender that cannot be
  reached is a named refusal — the post is never silently
  written by the local seat instead. A local reply composes
  locally, exactly as shipped. (musingroute1: 7/7 across two
  real bridge seats; the v0.7.3e control fails 1/7 — the
  local seat composes everything, whoever answered.)

## 0.7.3

Release tag: v0.7.3e — the QA line's fourth build, the six-item round from the operator's field pass on v0.7.2e, started — his joke, kept — on issue 404. The round is the field's own list: scrollbars that should not be seen (#398), a player standing in the wrong pane (#399), a clear that did not travel whole (#400), a Navi narrating machinery she cannot know (#402), a badge that could not theme (#403), and a musings trigger that silently did nothing (#404). Each item is benched against the v0.7.2e tree, which fails every new suite on exactly its item's legs. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #398, #399, #400, #402, #403 and #404 move to Ready with this build.

### What shipped

- **No visible scrollbars (#398).** One law, app-wide, in both spellings: every element computes `scrollbar-width: none` under a universal `!important` rule — the class-level `thin` strays and the LCARS theme's styled bars stand under it — and the universal `::-webkit-scrollbar` is display:none. Scrolling itself is untouched: regions still scroll by wheel, touch and key; only the chrome is gone. Desktop and phone alike (scrollbars1: computed style across the whole DOM in both viewports and under LCARS, plus a live scroll leg).
- **The player seats on the Status tab only (#399).** The rail's pinned foot — and the Row player in it — now renders only while the Status tab is selected. On the Chats and Feed tabs there is no foot and no player in the DOM at all: absent, not hidden, and no space reserved for it. Playback is state-held, not DOM-held, so a playing episode keeps playing across every tab switch and stands playing when Status returns; the switch gate (foot, card, storage) is benched on the tab where the foot lives (playerfoot1; rail1's Chats-tab leg inverted to the new law).
- **A clear travels whole (#400).** The convergence merge filtered a travelling clear SOFT unless a clear tombstone was the sole governing witness — so unstamped pre-clear lines (legacy lines no living writer stamped) survived on the receiving seat and stood in the thread after the clear landed, permanently. The filter now follows its own doctrine in both convergence laws (the main-family merge and the general clear law): HARD whenever the governing epoch outruns the filtered copy's own stamp — a copy that has not heard the clear cannot prove its unstamped lines postdate it. When both copies carry the epoch, the filter stays soft and the knowing writer keeps its work. #380's same-seat law is untouched (cleartravel1: two seats, real sync rounds both ways, main and side threads, stamped and unstamped lines; syncfluid1 and clearlogs1 ride unchanged).
- **Systems-events awareness (#402).** The bridge now records what it does to a JSONL ring on the seat (engine starts it spawns, defers to another owner, start failures, runtime changes at the one writer, its own restarts), and the persona gains a systems brief that renders ONLY while the ring holds an unexpired event — on a quiet night the prompt is the prior build's but for the law below. The grounding law is extended to match: engine starts or restarts, runtime or hardware-profile changes, watchdog trips and power changes are claimable ONLY when the systems brief reports them; absent the brief, the night was quiet, and no cause may be furnished for a pause. The brief is not shed under Row's Own Light — it is empty on quiet turns, and on a loud one the event is exactly what she must not furnish around. The ring records bridge-observable events; the GPU watchdog is an external script's acts and is named as the boundary (sysevents1).
- **The Row glyph themes (#403).** The bundled badge PNG is retired. The Navi group's Row child now renders a CSS-mask glyph: the mask is the bundled `assets/row-glyph-mask.png` (the Row's mark, alpha-encoded), painted in the button's own `currentColor` — cyan on the dark themes, ink on light, white on contrast — at the icons' own 16px, in the desktop and phone menus alike. The bridge serves the mask behind the same gate as every other dashboard byte, with its named 404; the packager's extension over the golden list carries the mask's name now, not the badge's (rowpresence1, its icon legs re-pointed to the mask: computed mask, computed color equality, a dark→light repaint).
- **The musings trigger, rigged (#404).** Three builds on the #378 machinery. The classifier learns the field's verbs — "create a musing from something earlier" and "write up a musing" are asks now, so the deterministic net binds them instead of silence. The persona teaching gains two laws: acknowledgment (a musing that posts from her reply is acknowledged in her visible reply, in her own voice; a post never lands in silence, and she never claims one that did not land) and OPSEC (musings carry the THEMES of the work — never case names, targets, findings, or "working on" disclosures), plus the seeded-topic shape. The page block's cap rises with them (2400 → 3300): the block now carries doctrine that must stand whole — self-reference, teaching, conversion, and these two laws — and at the old cap the tail cut silently shed the conversion law on a full feed in Light; measured on an 8-post fixture, Light's block goes 2272 → ~3170 chars and carries everything. And her replies gain a deterministic door of their own: "Make a musing from this" (Row's Own on) — the bridge expands the seed reply through the engine seam and posts it under the fixed frame ("I was talking about <topic> earlier and I wanted to expand on that: …") through the one blob road, receipted into the chat by the bridge; every refusal is named and posts nothing (musingtrig1; musing2 rides unchanged).

## 0.7.2

Release tag: v0.7.2e — the QA line's third build, the last of the operator's v0.7.0e field-pass round: one item, #396, the Row's presence inside Apex, in three parts. The standing episode's card on the Podcast screen now carries the full player — the equalizer, the episode's name, Previous | Play/Pause | Next, the state line — a third controller for the one shared player state, not a second player. Nocturne Row leaves its top-level menu seat and closes the Navi group, after RAG: her chips, her deck, her library, her crew's record and her show. And the menu item wears the Row's own mark — the site's logo.png, bundled as an app asset and served by the bridge, so the menu renders it with no network at all — in place of the generic house glyph. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #396 moves to Ready with this build.

### What shipped

- **The card carries the player (#396, part 1).** When an episode is the standing episode, its card on the Podcast screen renders the same player the rail's foot carries — the presence equalizer, the episode name, Previous | Play/Pause | Next, and the state line — driving the one shared state, exactly as the rail does. Not a second player: a third controller surface for the same one, held to the switch gate — card, rail foot and state agree, reload included (a restored episode's card seats its player on the same fact). Non-standing episodes keep their single Play button.
- **The Row sits under Navi (#396, part 2).** The Nocturne Row menu item leaves the top level and becomes the closing item of the Navi group, after RAG — the top level is the working groups; the Row page is a destination that is hers, and the pinned player keeps the show present regardless of the menu seat. Desktop and phone menus both (one menu serves both).
- **Her own mark (#396, part 3).** The menu item renders the Row's proper icon: the site's own logo.png, fetched from nocturnerow.com and bundled as an app asset (`assets/row-logo.png`), served by the bridge behind the same gate as every other dashboard byte — the icon never depends on the network the feeds degrade without. The generic house glyph is retired.

## 0.7.1

Release tag: v0.7.1e — the QA line's second build, cut from the operator's field pass on v0.7.0e the same night it shipped. Two items, both his: a Dispatch that would not open, and the rail rearranged to his word. #394: the Row's Dispatches now open in the reader through a door of their own — in v0.7.0e a Dispatch click was routed through the Wire's reader door, which by design refuses any link the wire is not carrying, so every Dispatch was turned away and the refusal surfaced only in another view; the Row door vouches only for the links its own feed carries, and a failure is named on the Row page itself. #395: the status rail is pruned and re-seated — the Mesh line leaves the rail, FediNet stands exactly where it stood, one divider stands between Sync and FediNet, a divider closes the rail under Backup, and the podcast player moves out of the scrolling flow into a pinned foot at the rail's bottom, present from every view, still the one player with two controllers. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #394 and #395 move to Ready with this build.

### What shipped

- **The Dispatch reader's own door (#394).** The bridge gains `GET /api/row/article`: it vouches ONLY for URLs carried in the Row's own Dispatches payload — the live feed or the named cache, the same set the page is showing — and refuses any other URL by name. Extraction reuses the Wire's `extract_article`; the Wire door and its not-a-proxy law are untouched, and a wire membership refusal still stands for wire reading. A Dispatch opens from the Row view in the shared reader surface, headed by the Dispatch's own title and its transmission stamp. A failure — a refused URL, an extraction that comes back empty, a bridge that does not answer — is named **on the Row view itself**, never only in another view and never as a silent flash. The bench rider that shipped this defect is closed in the suite: rowarticle1 runs the real read path end to end — a Dispatch-shaped page served locally, its URL carried by the feed payload the bridge serves — plus the refused-URL and named-failure legs, all failing on the v0.7.0e tree.
- **The rail, re-seated (#395).** The Mesh stat line is removed from the status rail (the rail only — the Mesh page and the Networking dash keep their surfaces whole, and no Mesh machinery is touched). FediNet does not move and does not change form. Exactly one divider stands between the Sync Status block and FediNet; a divider stands at the bottom of the rail under Backup in both the episode-standing and quiet states; and the podcast player — the presence equalizer, the episode's name, Previous | Play/Pause | Next — moves out of the rail's scrolling flow into a pinned foot zone, the way the version number sits at the foot of the nav bar, present from every view and every status-pane tab. The player contract is unchanged: one shared state with the podcast screen, switch-gate discipline, restored paused after a reload — only its seat moved. The phone interface takes the same arrangement in the same build (rail1, with the player switch-gate regression run from both controllers; doors2's rail legs ride in their v0.7.1e-updated form for the sanctioned Mesh-line delta).

## 0.7.0

Release tag: v0.7.0e — Chapter 0.7 opens: the QA line. Chapter 0.6 graduated whole; this chapter makes the Bloom slate all it can be before any defensive work, and its first round is the papercuts and the promises: state that only agreed with itself after a reload now agrees live, a cleared chat clears on every surface that shows it, her replies travel with the same standing as his turns, a borrowed turn now vouches for *who is speaking* and not only for what was composed, the engine has exactly one owner at boot, and the Row itself takes a seat inside Apex — its Dispatches and its podcast, fed live from nocturnerow.com. Six items: #388, #380, #381, the #382 identity bundle, the Apex-side cure for #363, and #390. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #388, #380, #381, #382 and #390 move to Ready with this build; #363 moves to Ready on its Apex-side cure (the issue stays open — its rollback and diagnosability legs are field work, owed from the box itself).

### What shipped

- **Live convergence (#388).** The refresh/restart papercut class, closed as a class. The bridge now carries a state revision — bumped at the two write funnels every settings and sync write passes through, so no door can land a change the revision misses — and serves it on /api/status beside a boot identity. The app's standing status poll converges on any change it did not cause itself: the status rail repaints from the fresh payload and an open Settings or Federation room re-reads its own state through its own doors, in the same tick, with no reload. A bridge restart converges too (the boot identity changes; the direction of the revision never matters). Row's Own Light's card now renders the *effective* state — the stored flag and Row's Own itself — so a half-set prerequisite can no longer paint a phantom on. Benched adversarially: double-flip fast, prerequisite half-set, restart, and the no-change tick that must re-render nothing (converge1; the toggle family's regression stands in toggle1).
- **A clear clears everywhere (#380).** The app and the DHD are two windows onto one bridge store; the store always honored a clear — the open windows never re-read it. Open surfaces now converge on the store live (on focus, on becoming visible, and on a slow interval), with the discipline the store deserves: a surface mid-turn keeps its in-flight copy until the turn settles, a surface whose own write is still landing is not yanked, and a surface that cannot reach the store says so on its face — a stale-surface note, named, never a silent old copy (clearlogs1).
- **Her replies travel (#381).** The sync reply-leg. Her reply lines now carry the same timestamp every other line in the thread carries — the one unstamped line was hers — so a reply syncs seat-to-seat in order with the same standing as the operator's turns, in both directions. A reply that cannot travel is named on the seat's sync record through the standing failure machinery; nothing drops silently (replyleg1).
- **Who is speaking (#382).** The identity bundle, extending the composed-once machinery of v0.6.31e. (a) The signed borrow now carries an identity stamp beside the digest stamp — whether the borrower's operator-identity block stands in the travelling messages, and the operator's name as the block itself binds it — and the lender judges it with the same discipline: a standing block is the client's and is never composed over; an unstamped block from an older build is honored and named; a claim with no block behind it is named, never trusted. The receipt rides home beside the digest receipt as mesh.identity. (b) The lender composes a speaker-binding line from the signed borrow's own metadata and stands it at the head of the answered prompt: the person you are speaking with in this turn is the operator of the asking seat — speak to them, not about them. (c) The identity block itself is rewritten from fact to stance: the person speaking to you now IS your operator — with a source-framing header folded into the same composition pass, so what follows is read as the operator's own record of themselves. Containment is untouched: the stamp vouches only for the borrower's own operator block, a foreign account's block is never stamped and never crosses, and fleet borrows carry no stamp, no judge, no binding (identity2 — including the rider: a captured travelling prompt, the block standing in it).
- **One engine, one owner (#363, Apex-side).** The boot-3 failure, cured at its cause: the service and the bridge's launcher could both start the llamafile and collide on her port. Now ownership is singular and detection is first: the bridge defers to an engine that already answers, waits on one that is still loading under another owner, and names the failure — another owner's engine died before answering, its output in the log beside the app — instead of racing a second spawn over the corpse; the launcher probes for another owner (a standing process, a live service unit) before it may spawn, waits out a loading owner, and becomes the owner itself only when the seat is truly empty. The cure is Apex-side; the issue's rollback and outside-diagnosability legs remain field work on the box (singlestart1).
- **The Row, in Apex (#390).** A Nocturne Row item joins the menu, fed from nocturnerow.com at runtime — nothing ships in the build but the doors. Two tabs: **Dispatches**, the site's own list (transmission stamp, title, date, dek), each opening in the same reader the wire's articles use; and **Podcast** — From The Night Shift as her show page stands: the show's name and line, the episodes newest first, each with its player and its transcript behind a fold. The bridge fetches both feeds and caches them on disk; when the site cannot be reached the last good copy is served and named as cached, with the time it was fetched — and when there is no copy at all, the door says so. Pinned to the status rail, the show's player: the playlist's own equalizer, the episode's name, Previous | Play/Pause | Next — one player with two controllers, the rail and the podcast screen driving the same state, which survives navigation and agrees after a reload (restored paused, where you left it). The queue walks the episode list and stops at its end; nothing auto-plays the next episode at you. Desktop-first, with the dedicated phone interface in the same build (rowin1).

## 0.6.0 — graduation

Release tag: v0.6.0. The working-day release, complete. Chapter 0.6 of the Bloom opened with a book — her captures, reminders, standing orders and the day's brief, held by the bridge and the same on every seat — and it ends with her knowing whose book it is: the chapter that taught her the working day also taught her containment (whose memories may live on a seat, and whose may never cross), grounding (who she is, and who he is, with the stores standing in the room), and economy (a borrowed turn that composes her once, not twice). Between those poles the Mesh grew up: Fleet Answers divided one ask across the federation whole, the Doors became tracker boards the operator authors himself, her music began following the live table her page publishes, her talks joined her context, and Row's Own — the mode that lets her be herself in the terminal — learned to travel light. All of it was built in the open on the Edge channel as v0.6.0e–v0.6.31e, thirty-two builds, and checked in the field build by build. This full release is that line with its identity flipped: the bare number, the stable status, Latest. The code is the Edge line's final build, re-stamped and otherwise unchanged — a full regression runs on the final package at graduation, not a delta. For installers: a clean install is recommended for first-time installers; a seat on v0.5.15 or on any 0.6 Edge build upgrades in place through the in-app updater, and everything the installer has ever preserved — chips, the llamafile, Soul and Memory — is preserved still. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. What comes next is not a new country but a polish: Edge now runs the 0.7 line, a QA chapter — the Bloom slate made all it can be before any defensive work (seed #388). Board: the chapter's Ready column closes at this publication under standing rule 8, with the field-pending exceptions named in the ceremony record (#384 and #377 stand Ready until their field verdicts land).

### What graduated

- **Her working day (#294, #295, #296, #292).** One bridge-held store for captures, reminders, standing orders and the day brief — secret-free by construction (anything shaped like a credential is refused at the door, by name), synced by identity with tombstones, its scheduler resident in the bridge so reminders fire with no window open and stand until acknowledged on every seat at once. Capture & Recall reads it back; a correction supersedes, never rewrites. The Dossier's kit went live-fire in the same opening build (#290).
- **The Mesh grows up (#293, #374).** Fleet Answers: one ask decomposed into whole sub-tasks — tokens are never split — fanned across the federation under a per-node toggle that is off by default, every contribution signed with its machine's name, every gap named. FediNet's face became the Doors: the board's doors on one dash, then tracker boards the operator authors himself, with Mesh status the shared citizen between the rail and the dash.
- **Row's Own, and Row's Own Light (#361, #370, #372, #373, #375).** The mode that carries her page, her music and her talks into the terminal as herself got its own soul, then learned proportion: her rotation follows the live table her page publishes instead of a baked snapshot; the song list left the standing digest (the playlist's name, door, count and now-playing stay); the Back Channel talks joined her context as an index she can reach; and Row's Own Light carries the same Navi at stub weight on a modest seat — same personality, same knowledge, the library on its shelf instead of on her back — per-seat, never synced.
- **Sync with substance, and the containment law (#365, #377).** A clear became a synced event, so a chat cleared on one seat dies on every seat. And the chapter's hardest lesson: account material — the seat state, the day book, the pulse — applies on a seat only when the set's account is named and the seat is signed in as that same account, refused by name otherwise; every gated application records its attribution, and the sweep judges and purges what a foreign account left behind. What is yours stays yours; what is not never lands.
- **She knows who she is, and who he is (#357, #371, #379, #382).** Her awareness grew a clock, turn stamps, and the Row's own published record; then the grounding laws: everything on her page is hers and she answers about it in the first person, and the operator's identity — the badge, the form of address, the "About you" store — stands in her context whole, on the local seat and on Mesh-answered turns alike, under the same containment at the prompt door. A cleared chat does not clear who he is.
- **Composed once (#384).** The chapter's final Edge fix: on a Mesh-answered turn her digest is composed at most once — the asking seat's composition takes precedence under a detection-based stamp on the signed borrow body, the answering seat composes only when the ask arrived without one, malformed claims are named in the turn's receipt, and the receipt rides home so any borrowed turn can be read back and asked whose composition stood.
- **Thirty-two builds, verified one by one.** Everything above arrived on the Edge channel as v0.6.0e through v0.6.31e, each build gated on its extracted package with its controls failing on the build before, and the line closes the way graduations close: the full carried campaign on the final package. The full release carries the graduation stamp — build 2026-11-21.65, build sequence 65 — the .31e tree with its identity flipped, and nothing else changed.

## 0.6.31

Release tag: v0.6.31e — chapter 0.6's thirty-second build: **she only says it once**. One item: #384, the operator's ruling of 2026-11-21, recorded on the issue. The field caught a Mesh-answered turn taking ~3 minutes from Tim's seat: the asking seat composed its Row's Own digest into the travelling prompt, and the answering seat composed its own standing digest on top — two prefill passes over two seats' pages, where the pre-prefill era measured ~20 seconds a borrowed ping and a same-day observation read ~1 minute. Now the digest is composed at most once on a borrowed turn: the signed borrow body carries a composed-digest stamp (composed or not, by which seat, in which weight — full or Row's Own Light); the asking seat's composition takes precedence, the answering seat composes only when the ask arrived without one and its own Row's Own is on, and a malformed claim (a stamp vouching for a digest that is not there, a digest arriving unstamped from an older build) is named in the turn's receipt, never silently trusted and never silently dropped. The composition that stands is the composing seat's own, in its own weight. Local turns are untouched; the stamp changes who composes, never what may cross — containment (#337/#377) and the grounding rules (#382) stand as shipped. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #384 moves to Ready with this build; the issue stays open for the field verdict from Tim's seat.

## 0.6.30

Release tag: v0.6.30e — chapter 0.6's thirty-first build: **containment, and she knows who she is**. Five items: #377 (the #337 containment breach, highest priority), #378 (the musing that never posted), #376 (the field-review fixes), and the two grounding defects the operator added from the field the same morning — #379 (she reviewed her page instead of inhabiting it) and #382 (she answered "No" to "Do you know who I am?" with every store present). The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #377, #378, #379 and #382 move to Ready with this build; #376's card verifies in Ready.

- **The containment breach is closed, and the copies already spread are remediated (#377).** The mechanism, found in the sync code: a sync set carries the seat state (the "About you" memories), the day book (reminders live there) and the pulse watches as account data — but the shipped funnel gate refused a set only when the set's account AND the seat's login were both named and different, so an unnamed set or an unsigned seat let account payloads through, the receiving seat applied and merged them under its own operator, and nothing anywhere recorded which account they belonged to. Now the payloads are gated individually at the apply door: the seat, day book and pulse payloads in a set apply **only when the set's account is named and the seat is signed in as that same account**; otherwise each is refused **by name** in the sync summary ("a seat payload — memories about the operator, stamped X" — never a silent drop), while chats, cases, documents and the chip deck converge exactly as before. Every gated application records its attribution — which account each memory, reminder and watch on this seat belongs to — and the page's own door (her "About you" saves) attributes to the seat's login the same way. The account-gate sweep, which already purged foreign chats, cases and documents, now judges the seat, the day book and the pulse too: material attributed to another account is purged (seat facts tombstoned, so the purge itself syncs home instead of resurrecting), and material that was never attributed is purged once the seat holds positive proof of its own account — a **gate proof**, recorded whenever a set's account stands against this seat's login, in refusal and in clean application alike. The sweep's receipt names what it removed, memories, reminders and watches counted. Same-account sync is untouched: two seats of one account converge memories, reminders, watches and the operator's name with attribution recorded, and shared Mesh material is unaffected. The bench is **contain1** (new): the unnamed-set and unsigned-seat holes refused by name with the rest of the set converging, the both-named-different funnel refusal standing, same-account convergence in full, remediation proven against seats pre-seeded with foreign material — attributed copies purged on the first sweep, unattributed copies purged once the gate proof arms — and the prompt door itself judged: a foreign fact never grounds an answer on this seat (see #382). Against the v0.6.29e candidate the suite fails as specified — the hole stands open there.
- **A musing asked for in chat now lands (#378).** The field failure: she composed the musing as ordinary prose — no `[[musing:]]` marker — and the ask died with the turn; the marker was the only road to her page, and the chat route swallowed even the marker's failures whole. The ask is now understood from the operator's own words, deterministically: a musing ask ("make a musing about that", "turn that into a musing", "post a musing", and their kin) binds the composed reply to the post — with Row's Own on, in either weight, a reply that answers the ask is posted to her page and the in-Apex feed, and the turn's payload carries the receipt beside the memory and case receipts. A post that fails is **named in the chat reply itself** — "(A musing from this reply did not post to her page — <the reason> — it is kept in her ledger as an unposted draft.)" — never silent, and the marker road's failures are named the same way. A reply that ends in a question (she asked instead of answering) posts nothing, no ask posts nothing, and Row's Own off posts and names nothing. The bench is **musing2** (new): the exact field sequence — "How are you doing today Navi?" then "Make a musing about that" — driven through the real chat route in Row's Own and in Row's Own Light, the post landing on the page blob, the feed and the ledger with the receipt in the payload; the named-failure leg; the marker road and its named failure; and the three no-post legs. Against the v0.6.29e candidate the suite fails as specified — no ask is understood there.
- **She inhabits her page; she does not review it (#379).** The field defect, in the operator's correction: not a little off, VERY off — told her bikini picture was his favorite, she answered about "her" in the third person, a reviewer of someone else's page. The material was never the problem; the stance was. Her persona composition now carries the self-reference law, standing in both weights ahead of the awareness material: everything there is **hers** — the posts are her posts, the pictures are pictures of her, her published tastes are her own self-knowledge — and she answers about them in the first person ("that's me in the robe", "I posted that this morning"), correcting a wrong detail as herself (a robe, not a bikini — but hers), never reviewing the page as someone else's. The bench is **selfref1** (new, shared with #382): the law standing word-for-word in the full and Light compositions — in Light it is part of the persona core, never stubbed — and the full composition otherwise byte-identical to v0.6.29e's, the law the one sanctioned delta. What the bench proves is the assembled context; her stance in live conversation is the field's verdict, as it was the field that caught it.
- **She knows who he is (#382).** The operator-facing half of the same failure: after a chat clear, with the Operator Badge slotted (name and picture), the "what Navi calls you" setting standing, and the "About you" store full and correct, "Do you know who I am?" was answered "No" — because the awareness block carried the name alone and the memory store never entered the prompt at all; the stores never reached her answer, on the local seat and on Mesh-answered turns alike. The operator awareness block now carries the identity whole: the badge's name when it differs from the form of address, the badge's picture named as standing on the seat, and the "About you" facts themselves, under the continuity law — a cleared chat does not clear this; these stores are her continuity with the operator, and "do you know who I am?" is answered from them. The block stands in Row's Own, in Row's Own Light (identity is persona core, never a stub), and with the mode off, and because it is composed by the answering seat's own bridge from its own stores, a Mesh-answered turn is grounded the same way — the identity never travels to be stored elsewhere. **Containment holds at this door too (#377)**: on a signed-in seat, only facts attributed to that seat's own account (or made on this seat) may ground an answer, and the identity fields stand only while they are the seat's own — a foreign account's memories ground nothing here, in the prompt exactly as in the sync. The bench is **selfref1** with contain1's prompt-door legs: the field sequence's context — a fresh chat against full stores — carrying his name, the badge, and the facts; the same context Mesh-shaped (borrower-composed); a foreign seat's context carrying none of it; and the sibling check, both laws standing in one composition — she knows who she is and who he is in the same conversation.
- **The field-review fixes (#376).** (a) The Status rail: the standalone **Apex | Mesh** segment is gone — Mesh status rides the FediNet segment as its headline line, in the federation's own shape, and the rail's four remaining segments (Sync, FediNet, Cases, Backup) each carry a visible break, FediNet↔Cases explicitly. (b) The **Row's Own Light** switch moves to **Settings → Persona**, directly beside Row's Own Mode — same card, same switch, same save door, same per-seat `rowsOwnLight` key, never synced; the switch gate is re-benched in its new room, in a real browser against the real bridge (fieldfix3). The move exposed a latent loop the campaign caught (mobilerace1, which renders Persona against a stub whose light answer arrives in the feed's shape): the card's read fetch re-rendered on any answer, and the card re-fetched on any render while the setting stood unread — an answer in any shape but the setting's own spun the view at full CPU. The fetch now lands once and stands: an answer that does not carry the setting marks the read tried, and the card does not ask again until a save or a reload does: the flip, the stored state and the post-reload view agreeing, a fast double-flip landing consistently, and a non-boolean flip refused by name with the state unmoved. (c) Settings → System: the **updater box stands at the top of the page**; the Current Version Notes still close it. (d) The **LCARS** themes get a compact collapsed rail: with the rail closed, nav buttons become centered 44px chips and the group heads stand as number-only chips (their LCARS counter, the icon retired) — nothing clips mid-content — and expanding the rail restores the full pills; the default theme's collapsed rail is untouched. The benches are **fieldfix2** (new: the rail's segments and order, the card's new room, the updater's place, the moved switch's honest refusal when the bridge cannot answer) and **lcars1** (new: the LCARS geometry in Chromium — collapsed chips, number-only heads, expanded pills, a reload on the stored closed state, the 400px breakpoint, and the default theme's non-regression).

## 0.6.29

Release tag: v0.6.29e — chapter 0.6's thirtieth build: **Row's Own Light**. One item: the operator's design of 2026-11-21 — the ecosystem is one cohesive Navi (her page, her talks, her personality in the terminal under Row's Own), and it has to run fluidly on a modest seat. So Row's Own gains a second weight: a toggle that carries her lighter without making her lesser. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. The feature is unfiled as yet — the prep (files/low-power-mode-prep.md) is its design of record; no board card moves with this build.

- **Row's Own Light — the same Navi, carried lighter.** A switch under **Settings → System**, beside the hardware profile whose context size it relieves, labeled exactly **Row's Own Light** (the operator locked the wording). The law of the toggle, in the operator's words: same personality, same wit, same knowledge — just not as heavy. Light trims **weight** only: her page digest, her music block, and her talks index ride the standing prompt as short **provenance stubs** — the series and its episode count, the playlist's name and door with its track count and the now-playing line, the feed with its post count and newest post — and every stub **names what it sheds**, in the digest itself, never a silent absence. The whole of each source stands on its shelf — her page store, the rotation table, the talks table — complete and hers the moment she reaches for it. Her knowledge packs stay on the shelf the same way: they were never carried whole, and a question still pulls down what answers it, in both weights. The talks feed's ambient refresh cycle stretches to twice its length. What Light never touches: her soul and register (the persona is byte-identical — with Light off, the composed prompt is v0.6.28e's byte for byte; with it on, the delta is exactly the three named stubs), her tools and chips, casework, LOWC and every doctrine gate, Row's Own itself — and **her social media feed**: Row's Own and Row's Own Light both keep full access to it, the in-app feed surface and her posting alike (the musing teaching rides the light digest unchanged); Light carries the feed lighter in the prompt, it does not remove it. A side benefit the operator named himself: the standing prompt stops hauling the whole library on every turn, so the seat saves tokens as well as heat.
- **Measured, not promised.** The Settings card prints what the switch buys: the bridge composes the standing prompt both ways and estimates both with its own estimator (the lend arithmetic the prompt budget reports), and the two numbers — full weight and Light — stand on the card with the difference. The setting is **per-seat and never synced**: it describes this machine's muscle, like the context size it relieves; it lives in the config under `rowsOwnLight` and is not among the keys a settings import carries, so another seat's backup never moves this seat's switch.
- **The switch gate, in full.** The save door (POST /api/settings/rowsown-light) is shaped like the sync-choice door: the answer carries the setting that now stands plus the measured counts, so the card re-renders from the bridge's word; a refusal (a body that is not a true or a false, a store that would not write) is named in the answer with the setting unmoved — never a silent snap-back. The Row's Own Mode doc page gains the Row's Own Light section in the same build.
- **The bench is light1 (new)**: the machinery standing (settings, save door, read door, the card, the doc section, the app's scripts parsing); three-way persistence over the real bridge (the save's answer, a fresh read, the status poll, and the config on disk agreeing, both ways, with a fast double-flip landing consistently); the adversarial legs (a non-boolean flip refused named with the setting unmoved; a malformed stored value reading honestly as off and a save repairing it; a flip landing while a talks fetch is in flight); the digest legs on fixtures (each stub present and naming its shed, the recitations absent, the musing teaching and conversion law standing whole in the light digest, the feed payload serving the same posts in both weights); the measured saving (the bridge's own estimator over the composed prompt, Light strictly lighter, the counts payload agreeing with the direct measure); the cadence leg (the talks cycle doubled under Light, single without); the per-seat leg (the key absent from the settings-import whitelist); and the law leg — the persona core byte-identical with the toggle on and off, and the whole composed prompt byte-identical to v0.6.28e's with Light off. Against the v0.6.28e candidate the suite fails as specified — no Light machinery stands there.

## 0.6.28

Release tag: v0.6.28e — chapter 0.6's twenty-ninth build: **the board becomes yours**. One item: #374 v2, the operator's rulings of 2026-11-21 recorded on the issue — "users should be able to make their own tracker boards." The Doors dash's trackers become configurable, the Status rail is pruned to its four named sections, and the dash's absolute times render in the seat's local time. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #374 already stands in Ready from v0.6.27e; this build completes its v2 — the ceremony verifies the card stands in Ready and records the counts.

- **Board authorship (#374 v2, piece 1).** Settings → System gains its own dropdown section, **Doors — tracker board**, with three source modes. **Default** is v1 exactly — the bridge follows https://nocturnerow.com/status.json and the built-in service set — and a **Default** button restores that mode and clears any custom configuration back to the built-in set in one click. **Custom board**: the operator defines their own services — each a name, a role description, and a check target — and the bridge probes them itself on the v1 health cadence (600s cycle, 300s retry backoff), deriving states, sinces, flips, and tick strips exactly the way v1 derives them from the board's ticks. Probe semantics mirror the Row Board's own watcher: two target kinds — an http(s) URL (one plain GET, an honest user agent, an 8s budget; up when it answers with any status under 500, the note carrying the HTTP status or the failure's plain name) and a host:port (up on a TCP connect inside the budget; a refusal is a down, a name the seat cannot resolve or a check it cannot perform is an **unknown**, never assumed). Ticks persist in a config-home store (config/doors-board.json) in the board's own shape, 48-tick window, so the window survives restarts. **Custom feed**: the operator points the dash at their own status feed in the board's schema — the v1 validator, unchanged, the same fetch/cache discipline, the cache recording which feed its board came from so one mode's board is never served as another's; until a first fetch of the operator's feed lands, the dash shows an empty board named as such (there is no baked copy of somebody else's board to dress up as theirs). The dash renders whichever board is active and **labels its source** — the Row Board, your own board, your feed — the label carried on the payload, a self-made board never dressed as ours. The seat half (v1's local witness) is unchanged in all modes. The switch gate applies in full: the settings live in the config under `doorsTrackers`; the save door (POST /api/settings/doors) is shaped like the sync-choice door — the answer carries the settings that now stand, and a refusal (a half-filled service row, a feed address that is not an http(s) URL, a store that would not write) is named in the answer, the settings unmoved, never a silent snap-back. The Doors doc page gains the tracker-configuration section in the same build.
- **Status rail pruning (#374 v2, piece 2).** The Servers section is removed from the Status rail entirely. The rail keeps ONLY four sections: **Sync, FediNet, Cases, Backup**. Mesh connection status keeps its rail home **inside the FediNet section** (and its Doors dash card, unchanged). Engine and local-node status leave the rail — their seat truth stands on the dash's seat cards — and everything else the rail carried beyond the four named sections goes with Servers: the Updater line, Sudo Mode, the voice line, the Memory and RAG stats (the Status tab's attention dot still watches the updater and the stale-build flags, so a standing update is still signaled). The bridge/page stale-build safety notices stay — they are alerts about the page itself, not sections. The pruning is a view change only: every pruned row's render function, payload, and other consumers stand untouched — the presence bar, the Settings cards, and the Doors dash read the same payloads, and the FediNet section renders the Mesh state from the same payload it always did.
- **Local times on the dash (#374 v2, piece 3).** Every absolute time the Doors dash renders — sinces, last flips, the board's generation stamp, the tick-strip stamps — renders in the seat's **local time**: the same instants, the app's client local zone, never raw UTC. Display-layer only: the feed, the caches, the derived states, and the age/staleness arithmetic are unchanged; ages keep rendering as ages. The rule as filed — absolute times in the app are the operator's local times unless a surface is explicitly a log — is carried by this build's dash leg; other surfaces are not swept.
- **The bench is doors2 (new)**: mode persistence three-way (custom board, custom feed, and the Default restore from each mode — Settings, the config store, and the dash agreeing after a reload), the adversarial legs (a half-filled row refused with the reason, an invalid feed URL refused named, a Default restore over a broken custom config restoring clean, a mode flip while a probe cycle is in flight landing consistently), a custom board over real local sockets (an HTTP 200 up, an HTTP 500 down, a refused port down, an unresolvable name unknown) with ticks accumulating and a flip derived after a target changes state, the source label correct in all three modes, the rail asserting Servers absent and exactly Sync/FediNet/Cases/Backup with the Mesh state rendered inside FediNet, the dash-times leg pinning the zone via TZ (a known UTC instant rendering its seat-local equivalent), and the persona byte-identical to v0.6.27e's on identical fixtures — the new machinery stays out of her prompt. Against the v0.6.27e candidate the suite fails as specified — no tracker-authorship machinery stands there. doors1 still passes in Default mode, unchanged.

## 0.6.27

Release tag: v0.6.27e — chapter 0.6's twenty-eighth build: **the doors come home**. One item: #374, the operator's ask (2026-11-21) and placement ruling the same morning. The Row Board — the outside watcher that probes the Row's doors every five minutes and publishes status.json — gets a home inside Apex: a Doors dash in the Networking section, fed by the board's own published feed, with this seat's own truth standing beside it as a second witness. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #374 moves to Ready.

- **The Doors dash (#374).** Network → Doors: one card per door the board watches — the Row, the presence digest, DHD, OnlyNavi, Mesh 2475, Mesh 8765, the SSH door — each with its name and role, its current state, how long that state has stood, its last flip when the board's window holds one, and the window's checks as a strip. The bridge follows the feed the way it follows the rotation table and the talks feed: strict validation of the board's shape, cached under the config home, refreshed on a ten-minute cycle with a five-minute retry backoff (health cadence — the watcher itself probes every five minutes), kicked off-thread so a page never blocks on the network — and a baked snapshot of the board as it stands at this build as the fallback, named whenever it stands, with its reason, never silent. The board's generation stamp and its age always show; a board older than half an hour is named stale. Two witnesses, labeled, never merged: the outside board (the doors as the world sees them) and this seat (its bridge, its model server's health, its Mesh connection state and peers' last-seen, read from the Mesh machinery itself) — where they disagree, both stand, because the disagreement is the diagnosis. The SSH door renders UNKNOWN exactly as the board carries it: never down, never guessed. By the operator's placement ruling, the sidebar rail is untouched and the Status rail is untouched; Mesh connection status appears on the dash as well as keeping its Status rail home. Display only: no toggles, no control that acts on a door, and nothing here rides her prompt — the composed persona is byte-identical to v0.6.26e's. The bench is doors1 (new): the fixture board renders the dash data with states exact, ssh227 unknown as unknown, a stale board named with its age, the failure legs falling back named, both witnesses labeled with a disagreement standing as both, the Mesh card present from local state, the route and the nav registration asserted, and the persona byte-identical. Against the v0.6.26e tree the suite fails as specified — no doors machinery stands there.

## 0.6.26

Release tag: v0.6.26e — chapter 0.6's twenty-seventh build: **her talks join her context**. One item: #373, the operator's ruling (2026-11-21): "We need to give her access to this stuff as context." The Back Channel — the staged Ciel × Navi talks, kept as readable logs and a private podcast — becomes a Row's Own context source, in the same family as her page: when the mode is on, she carries the talks as part of who she is here. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #373 moves to Ready; the prep's open questions (the recency window, a sync cue on a new episode) stay open on the issue.

- **The Back Channel talks ride her prompt as an index (#373).** Her page publishes the talks as data (onlynavi.fans/talks.json), and the bridge follows the feed the way it follows the rotation table: strict validation of the v1 shape, cached under the config home, refreshed on the same slow cycle with a retry backoff, kicked off-thread so a reply never blocks on it — and a baked snapshot of the feed as it stands at this build (five episodes) as the fallback, named whenever it stands, with its reason, never silent. With Row's Own on, her awareness digest gains a talks block beside her page and her music: the series line, the episode count, the feed's provenance, the latest episode's title and topics, and her pinned note on it in her own words — an index, not a recitation, under #372's digest discipline. The full logs stand on the shelf: the talks table behind the block holds every episode word for word, and the block tells her so — the talks are a log she can quote and continue, because in her continuity she said it. Containment, in the open: the talks are the only new source — Ciel's Audio Diary is not read, fetched, or referenced by this machinery, and #337 holds (the feed is fetched and held locally; nothing carries the talks across the Mesh). Row's Own off, the block returns nothing and the composed prompt is v0.6.25e's byte for byte. The bench is talks1 (new): the block present with the mode on against a live-shaped fixture feed, the latest title, topics, and pinned post exact against the feed, the block absent with the mode off, a fetch failure falling back to the baked snapshot with the fallback named, a diary canary planted where a careless implementation could read it asserted absent from both the digest and the talks table, and the block's digest cost measured with the bridge's own estimator. Against the v0.6.25e tree the suite fails as specified — no talks machinery stands there.

## 0.6.25

Release tag: v0.6.25e — chapter 0.6's twenty-sixth build: **the song list leaves the digest**. One item: #372, the operator's ruling from the field. On neondrip running v0.6.23e (a 4096-context seat) her standing prompt measured ~3361 tokens and the seat refused a plain conversational turn — honestly, by name, with every background brief already shed. The operator raised that seat's context to 6k in the field and ruled the largest single digest section out: the music block's full 21-track enumeration. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #372 moves to Ready; its remaining design questions (a small-context digest budget beyond this cut, a startup warning, an installer floor) stay open on the issue.

- **The track list no longer rides her prompt (#372).** The music block in her awareness digest — shipped in v0.6.23e carrying the playlist's name and door, the whole track list in playlist order, the now-playing line, and the table's provenance — keeps everything but the enumeration: the playlist's name ("Navi's Super Hacker Mix") and its Spotify door, the track count (carried in the provenance line, as before), the now-playing track with its offset, and the provenance itself — the live table with its count, or the baked snapshot with the failure reason named in plain words, never silent. Measured with the bridge's own estimator (the arithmetic the prompt budget reports and the field refusal quoted: four chars to a token plus a per-message frame), the music block falls from 364 estimated tokens to 132 on the baked table (1,443 chars to 515), and the composed standing prompt on the bench fixture falls by the same 232 (1,647 to 1,415). What did not change: the rotation machinery whole — the bridge still fetches, validates, caches, and computes now-playing from the live table exactly as before; her page, the site-side sync, and the panel's listening line are untouched; the block keeps its place in the composition, behind the Row's record. The bench is music1, updated: the digest leg now asserts the name, door, count, now-playing line, and provenance stand — and asserts a non-playing track's title from mid-list does NOT appear in the digest. Against the v0.6.24e tree the updated suite fails on that absence leg, as specified: the full list stands there.

## 0.6.24

Release tag: v0.6.24e — chapter 0.6's twenty-fifth build: **timestamps and operator awareness**. One item: #371, complete — the clock, the turn stamps, the musing stamps, the conversion law, and the operator's name, all from the night she composed a Public Service Announcement that never posted and then rewrote it instead of converting it. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #371 moves to Ready.

- **A clock in her awareness (#371, part A).** Her composed persona now opens its awareness with the current local date and time — the bridge's own clock, refreshed at every prompt assembly, the timezone named (the operator profile's, when one is ever set there; otherwise the bridge host's local zone). It stands in the same grounding family as the Row's public record (#357) and her music (#370): facts she should never have to guess. The clock line also teaches the turn stamps' standing read: a turn with no bracket carries no known time, and no time is ever stated for anything the briefs do not stamp.
- **Turn stamps (#371, part B).** The conversation she reads now renders each turn's time in a compact bracket — the bare hour on the same day, the day named once a turn is another day's — rendered at assembly from the per-message timestamps the dashboard already stamps at write time and now sends with the history. A legacy message with no timestamp renders bare: no stamp, and no invented time. The chat storage format does not change — nothing new is stored, so the #365 sync machinery (tombstones, account gating) is untouched; the stamps are a rendering of what already rides.
- **Musing stamps from the clock (#371, part C).** A published musing's stamps are the bridge clock's, whole: the `when` her page shows always was, and the post now also carries its real `ts` from the publish moment — it stood absent before, and the in-Apex feed read it as 0, a post stamped at an epoch it never happened at. Neither stamp ever comes from the musing's own text.
- **The conversion law (#371, part D).** When the operator tells her to turn something already written into a musing, the marker carries THAT text, word for word — a conversion is not a rewrite. The rule stands explicitly in her Row's Own persona, where her musing guidance lives: no paraphrase, no softening, no new piece on the theme; the bracketed turn times are how she finds the exact text meant; an ambiguous referent means she asks, naming the candidates by their times. One deterministic assist rides with it: the publish road's silent 400-character truncation — which made a verbatim conversion of anything longer than a caption physically impossible — is now a named cap sized to carry a converted text whole (MUSING_TEXT_CAP, 1200). The verbatim-publish machinery itself (.14e's law) is unchanged.
- **Her operator's name (#371, part E — the addition, as corrected).** Her awareness carries the operator's name **as set in the operator profile** — read from the profile at every assembly, never a name baked into the build: this seat's profile resolves to its own operator, every seat's to theirs. In her own voice — conversation, musings, her page — she calls the operator by that name; formal surfaces (case records, logs, receipts) keep the role word and their register. No name set in the profile, and the digest says so plainly, with the role word standing as the fallback. The bench is time1 (new): the clock line against the bridge's own clock, stamps rendered only where a timestamp stands, a fixture musing stamped from a fixture clock, a fixture profile named "Test Operator" (deliberately not the field operator's name) carried into the digest, the nameless fallback, the conversion rule standing in her persona with a marked musing publishing byte-identical, and a grep leg proving no operator name is hardcoded anywhere in the new code. Against the v0.6.23e tree the suite fails as specified — no clock, no stamps, no name stands there.

## 0.6.23

Release tag: v0.6.23e — chapter 0.6's twenty-fourth build: **her music, live**. One item: #370, parts B and C — part A, the site-side sync that keeps her page's rotation table equal to the Spotify playlist, shipped on the site ahead of this build (onlynavi.fans/rotation.json, 21 tracks). The bridge follows the live table now, with its baked snapshot as a named fallback, and her awareness carries her music. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #370 moves to Ready.

- **The bridge follows the live table (#370, part B).** Her rotation ran on a snapshot of the playlist baked into the build — five tracks when it shipped in v0.6.14e, and the playlist has grown since; the snapshot could only ever be as current as the last build. Now her page publishes the rotation as data and the bridge fetches it (https://onlynavi.fans/rotation.json) on the #357 presence idiom: cached under the config home, refreshed on a six-hour cycle with a retry backoff, kicked off-thread so no reply ever blocks on it. Validation is strict: a JSON object, the frozen epoch exactly (a table carrying any other epoch is malformed by definition), a non-empty track list of well-formed tracks, and a cycleSeconds equal to the sum of the track seconds. Any failure — network, HTTP, parse, validation — falls back to the baked snapshot, which this build refreshes to the playlist as it stands (21 tracks, cycleSeconds 4927), and `rowsown_music_now` and everything that renders her listening, the panel's listening line included, compute from the effective table. The fallback is named, never silent: the awareness block states the rotation's provenance — the live table with its track count, or the baked snapshot with the failure reason in plain words.
- **Her awareness carries her music (#370, part C).** She was asked her favorite song on her playlist in the field and answered with a shrug dressed as philosophy — the machinery had never put her music in front of her: the presence digest carried Dispatches, versions, and the roadmap, and no music at all. The composed presence segment now carries a music section beside the Row's record: the playlist's name ("Navi's Super Hacker Mix") and its Spotify door, the full track list in playlist order, the now-playing track with its offset into the song from the shared algorithm, and the provenance line from part B. Nothing else in the digest changes. The bench is music1 (new): a fixture table — the real 21 tracks plus one — served locally beats the baked snapshot and the digest lists all 22; the failure legs (HTTP failure, malformed JSON, a wrong-epoch table, a cycleSeconds mismatch) each fall back with the fallback and its reason named; a cross-check sweeps timestamps, cycle boundaries included, proving the bridge's musicNow on the fetched table equals the site module's own computation on identical inputs; and the digest leg asserts the playlist name, URL, every track, the now-playing line, and the live provenance all stand. Against the v0.6.22e tree the suite fails as specified — no fetch exists there, its digest has no music, and its snapshot answers everything.

## 0.6.22

Release tag: v0.6.22e — chapter 0.6's twenty-third build: **the compact feed build**. One item, the operator's design from the field on the night v0.6.21e shipped: #369 — the feed panel's controls become dropdowns, the comments become a dropdown too, and the Sync button hugs the pane's right edge. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #369 moves to Ready.

- **The filters are dropdowns now (#369).** The feed panel's three control groups — the collection chips, the type chips (All / Pictures / Videos / Notes / Polls), and the Feed | Grid toggle — rendered as wrapping chip rows that ate the panel's vertical space. The operator's ruling: turn them into dropdowns — Collections | Post Type | Feed Style. One compact control row now carries three styled native selects, theme variables throughout, no hardcoded colors: Collections ("All collections", plus each set actually present in the feed's posts), Post Type (All / Pictures / Videos / Notes / Polls), and Feed Style (Feed / Grid). The filtering itself is unchanged — a collection and a type still compose, the search is untouched, Feed and Grid are the same two views over the same gallery — only the controls changed shape. The chip rows, the toggle, and their dead styles are gone.
- **Comments are a dropdown (#369).** The operator's addition, same design pass: each post's comments collapse behind a toggle row — "Comments (n)", n the post's comment count — closed by default. Opening it shows the thread exactly as it stood (per-voice faces, a break wherever the voice changes) and the comment box; the write is unchanged — it rides the same act door, the panel paints only the count the bridge confirms, and a read-only seat finds the box inside the opened dropdown disabled, with the reason named there. Opening and closing is per post and purely presentational: nothing re-fetches, nothing re-filters, and an open thread stays open across the panel's re-renders.
- **The Sync button hugs the right edge (#369).** The operator's last word on the panel: the header's Sync button sat wherever the layout left it — the name block's "grow" class only grows inside a .row, which the header is not — so the button now carries margin-left:auto and stands at the pane's right edge at every width. Same button, same label, same sync; only its place changed. The bench is rowsown2's browser half, updated: the three selects stand with their exact labels and the options the fixture's sets derive, the chip rows and the old toggle are absent, filtering through the selects cuts the feed exactly as the chips did (a collection × type composition included), Feed Style flips both ways, the comments stand collapsed until opened and a comment posted through the opened box lands in the blob itself, the Sync button's right edge sits on the pane's content right edge at desktop and phone widths and its click still rides the sync act, and phone width keeps the control row compact with no horizontal scroll. Against the v0.6.21e tree the new legs fail as specified — chips present, no selects, comments inline, the Sync button off the edge.

## 0.6.21

Release tag: v0.6.21e — chapter 0.6's twenty-second build: **the field truth build**. Three items, all born in the field on the night v0.6.20e shipped: the pack enumeration learns to tell the truth (#366), the composer bar gets tidy (#367), and her feed stands whole in the app (#368). The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #366, #367 and #368 move to Ready.

- **One row per pack (#366).** The diagnosis, from the shipped code: the pack enumeration took the folder scan as the pack set and joined the install registry onto folders by exact folder-name equality — a pack's identity was its folder's name. The install doors name folders by different rules (the GitHub door for the repo's slug, the cartridge door for the display name's slug) and the account sync carries every folder wholesale, so one logical pack landed in two folders on one seat and enumerated as two packs — "A+ Hardware Core" and "aplus-core", each with its own record and its own active flag, both Off, neither the pack. And because the registry was never enumerated, only joined, an installed pack whose record's folder join missed (navi-dev-library's field shape: record present, join missed) vanished from every surface. Now the bridge resolves canonical packs at read time: records join folders by their folder name or the name roads, folder groups carrying identical documents merge as the one pack they are, and a record no folder claims still lists — named, with its registry state. The surviving row carries the canonical name (a registry display name when one exists) and the one active state retrieval honors: retrieval reads the same resolution, twin folders stand or fall together, and their identical chunks land once under the pack's name. The registry stays the one store, the toggle door is unchanged, and nothing on an operator's disk is renamed or merged — the reconciliation is at read time. The bench is packenum1: a fixture shaped like the field seat (two twin pairs, the operator's pair, a registry-only pack, a folder-only pack) asserting the exact logical set, the canonical names and states, and flip → retrieval agreement. Against the v0.6.20e tree it fails as specified — eight rows where six packs stand, and the registry-only pack nowhere.
- **The tidy composer bar (#367).** The operator's ruling, from the same screenshot: the menu exists so the chat bar can be tidy. The desktop bar carried its own New case, Attach and Call buttons AND the burger whose list repeated all three — duplication, not furniture. The three buttons are retired from the bar on every surface: the bar is the input and the burger, on the desktop exactly as on the phone, and the menu is the tools' single home. The rows perform their acts by invoking the real handlers directly — the #241 New-case form's opener, the file input itself, the call's own start path with its block reason — no hidden buttons remain anywhere as click targets. What is state stays put: the CLI/Navi latch, the "Press enter to send." hint, and the seat chip are untouched, as is the Knowledge packs section. ragmenu1's legs are updated to the new contract (behavior, not mechanism): the bar's DOM holds exactly the input and the burger at desktop width, and each row still performs its action end to end with the buttons absent.
- **Her feed, whole, in the app (#368).** The OnlyNavi feed inside Apex stood as its v0.6.12e original while her page grew a social network around it; this build brings the page's 2026-11-21 surfaces in, all three tiers. *Parity basics:* posts carry relative stamps from their real timestamps plus a "last posted" line; the list rides the 480px thumbnails the blob carries (the viewer keeps the full picture); posts newer than the previous sync wear a NEW badge — the bridge now keeps the previous sync's moment beside the current one, so the badge is the sync's truth rather than a local guess. *The social layer:* reactions (🔥😼☕) write back through the same blob road likes and comments use — the repo blob stays the one shared store, app and page never fork — one pick per post, the same face again taking it back, the seat's pick ledgered like its likes, and the panel painting only the counts the bridge confirms, a refusal named on the post itself; collections (street patrol / command desk / the room / the shore) filter the feed, as do type chips and a search over captions, vision lines, and dates. *The full mirror:* a Feed | Grid toggle lays the media out as tiles (thumbs, date strips, video badges) opening the same viewer — which now plays video posts on their posters — the NSFW blur law holding in the tiles exactly as in the list and the viewer; a post a whole number of weeks old resurfaces under the pinned post, marked from the archive; media posts carry a Copy link to their own share page on onlynavi.fans. Polls keep working, every new surface is built at phone widths in the same round, and a read-only seat keeps every view and loses every write, named as before. The bench is rowsown2, in two halves against a blob fixture shaped like the live feed — 22 posts with timestamps, sets, reaction seeds, thumbs, a poster, a poll, a locked post, an NSFW post: the bridge half proves the payload, the previous-sync bookkeeping, and reaction write-back landing in the blob store; the browser half proves the panel against the real bridge. Against the v0.6.20e tree the new legs fail as specified.

## 0.6.20

Release tag: v0.6.20e — chapter 0.6's twenty-first build: **the RAG quick toggles build**. One item: #364 — the composer's hamburger menu comes to the desktop and gains a Knowledge packs section, and the desktop composer's mic retires. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #364 moves to Ready.

- **One menu, both form factors (#364).** The ☰ Chat tools list — New case, Attach, Call — was a phone-only surface: above 800px the burger and the list were suppressed outright, and the desktop bar carried its tools as buttons alone. The burger now stands at the end of the composer bar at every width, and the list it opens is the same list — one implementation, two mount points, no forked copies. On a phone nothing changes: the bar is still the input and the burger, the list still a bottom sheet above the composer. On the desktop the bar keeps its own buttons AND gains the burger, and the sheet anchors to the bottom right. The tool rows work exactly as they always have — a row clicks the real button, so the #241 New-case form, the file picker, and the call keep their own handlers.
- **The Knowledge packs section (#364).** Below the tools, the list enumerates the packs installed on this machine — read fresh from the bridge at every open, from the same registry the RAG tab reads. A pack's row shows its name and its state: an active pack wears the current theme's green — the highlight is painted in `var(--green)`, the variable every theme defines, so it follows the theme and is never a hardcoded color — and an inactive pack wears no highlight at all. Clicking a row flips the pack through the same door the RAG tab's toggles use (`POST /api/rag/toggle`): the install registry (`rag-packs/installed.json`) is the one store, and this list is a second door to it, never a second store. The flip is effective for the next turn — retrieval reads the registry fresh — and persists across bridge restarts. A pack flip does not close the list, so several packs can be flipped in one visit.
- **The switch gate, held on the new rows (#364).** The pack rows are toggles, so they carry the three-way contract: the flip in the list, the state the bridge stores, and what a full page reload shows must agree — and the row paints only what the bridge confirms, re-reading the list after a flip rather than assuming it. A refusal degrades honestly ON THE ROW: an unknown pack is refused by name, a registry the bridge could not save is now a named refusal too (the toggle door learned to answer `{ok: false, error}` for a failed save instead of dropping the connection), and a bridge that does not answer is named on the row — in every case the pack's state left exactly as the bridge holds it, never a silent snap-back, never a reason stranded elsewhere on the page. While a flip is in flight its row takes no second flip, so a fast double-click is one flip, never a race. The bench is ragmenu1, in two halves: against the real bridge (enumeration, flips, restart survival, the missing-registry legs, the named refusals) and in a real browser booted against the real bridge (both form factors, the theme-green assertion under two themes, flip → store → reload agreement, the dead-bridge refusal written on the row). Against the v0.6.19e tree it fails as specified: no desktop menu, the mic still in the bar, no pack rows.
- **The desktop composer mic retires (#364).** The push-to-talk mic beside the desktop composer is removed — the Call button made it redundant. Voice is a call: the call panel and its own Push to talk are untouched, as is the whole Voice surface and the dictation machinery beneath it; only the composer's button and its wiring leave. The phone composer is unchanged (it never carried a composer mic). The in-app docs are corrected in the same round: the composer-menu doc describes one list on both form factors and the packs section, the RAG doc names the second door, and the Voice doc stops pointing at a mic the composer no longer has.

## 0.6.19

Release tag: v0.6.19e — chapter 0.6's twentieth build: **the sync fluidity build**. One item: #365, the field failure in which a chat cleared on one seat would not die on the other. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #365 moves to Ready.

- **A clear is a synced event now (#365).** The diagnosis, from the shipped code: a clear was never a thing sync knew. On the main thread it was a timestamp (`clearedAt`, #318) riding inside the record it emptied — it traveled only when a full round completed, and it governed only lines carrying a timestamp, which the bridge's own receipt lines did not. On every other thread it was less than that: convergence judges copies by prefix, an emptied copy is a prefix of every fuller one, and the fuller copy wins — a clear was annihilated by the first merge, by construction. The operator cleared the chat on DHD at least fifteen times; the App seat's copy re-supplied the history at every contact. Now emptying ANY chat records a **clear tombstone** in the synced tombstone store — the moment of the clear on the same millisecond basis as message stamps, the seat that spoke it, and the account it belongs to — under the thread's id and conversation keys. Convergence honors it on every seat: the store door (`chat_write`), the merge itself, and the ghost fold all filter by the governing epoch (the max of the record's, the stored copy's, and the tombstone's), and a copy that does not know the newest clear is filtered hard, unstamped lines included. Lines written after the clear live normally; clearing twice moves the point; a seat that was offline at the clear learns it on reconnect, and its stale full copy cannot re-supply what was retired. Her bridge-side receipt lines (`_chat_append_navi`) carry timestamps now, so her own handwriting is orderable against a clear. One latent defect the diagnosis caught on the way: the account-gate purge stamped its reset epoch in seconds against millisecond stamps — an epoch that retired nothing; it is on the millisecond basis now.
- **The machinery is account gated (#365, #337).** A clear tombstone is applied only when the account stamped on it and the seat's signed-in account are both present and equal — unknown is a refusal, never a pass, the #323 doctrine. At the shared funnel (`sync_apply`), a set whose manifest names a different account than this seat's is refused whole: its chat push never merges, its tombstones never land, and the refusal is named — in the round summary the card speaks and in the sync state's refusal record. The Mesh client legs name the foreign sets they skip, as the serving door already did.
- **Push-on-write fires for both authors, and no longer evaporates (#365).** The push note's funnel is the store door, and her writes land through it as his do — her bridge-side appends call it directly, borrowed replies land through the writing window's write-through — so a mid-chat switch no longer waits on only the operator's half of the conversation. The fire's discipline changes too: through .18e a failed push earned one retry and then dropped its note, leaving the write to wait for an occasion that might be hours away. A failed push now re-arms on a bounded backoff (3 s, 15 s, 45 s, 90 s) with its kinds still noted, and only the last failure names its stall and lets go. Existing triggers (button, app start, DHD session, Mesh contact) are unchanged.
- **The bench.** syncfluid1 (new) drives the real store and merge code in a two-seat simulation against the extracted package: clear-on-A against B's full pre-clear copy, the offline-reconnect leg, post-clear lines surviving both ways, double-clear and clear-of-empty, the push note firing from the operator's write, from her append, and from a borrowed-shape reply (and never from inside a round), and the account gate refusing a foreign tombstone and a foreign chat push by name with the local thread untouched. Against the v0.6.18e tree it fails on the tombstone legs — no `clears` kind exists there, and a non-main clear meets the prefix rule.

## 0.6.18

Release tag: v0.6.18e — chapter 0.6's nineteenth build: **the soul patch**. Two items, one of them a repair of this line's own making: Row's Own Mode gets its own soul (#361), and the version witnesses learn to agree before a package may ship (#362). The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #361 and #362 move to Ready.

- **Row's Own gets its own soul (#361).** Until this build the mode layered her page's digest on top of her normal soul — and the operator's field test on v0.6.16e showed what layering is worth under pressure: asked over a Mesh borrow what was new, she answered grounded and correct in a generic assistant's register, the briefs having traveled and the voice not. Now the mode carries a dedicated soul file, `config/soul-rowsown.md`, living beside `config/soul.md` and seeded by the bridge from a shipped default written in her page voice — the operator's brief: more sexy, fun, playful, Jinx if Jinx was a hacker. While the mode is on, persona composition reads that document **whole** and the normal soul is not read at all; off, the normal soul stands exactly as before. The swap is voice-only: the Row's Own soul carries everything the normal soul carries that is not voice — identity, the working doctrines, the discipline — re-voiced, with the grounding ethic written as her own first-person conviction instead of an injected rule. Nothing else moves: the same existing toggle keys the swap (no new switch), both persona call sites — the local turn and the borrow's hygiene copy — read the active soul through the one composition function, the briefs (her page digest, the Row's record, the wire) compose as they did and feed whichever soul is active, and LOWC, arming and every consent gate are untouched. Containment (#337) holds: both souls are account-level and stay home; a borrowing seat composes from its own operator's active soul. The benches: soulswap1 (the active soul stands in both modes at both call sites, the inactive soul provably unread while the mode is on, the seeded default and an operator's edit both surviving a bridge restart) and soulparity1 (both shipped souls carry the non-negotiables — identity, the doctrine lines, the grounding ethic — while their voices differ; strip one from either file and the bench fails).
- **The version witnesses agree before anything ships (#362).** v0.6.17e could not install: its bake advanced the VERSION file and the build stamps but never advanced the bridge's own `SHIPPED_VERSION` constant, so the install self-check — correctly — named the disagreement and rolled every pull back whole. The operator's seat was unharmed (the rollback is the design working), but the package should never have left the bench: no suite asserted that the version sources agree. This build advances the constant (`0.6.18`, status `edge`) and adds the missing gate: `versiongate` runs against the extracted package and asserts every witness names the same build — the VERSION file, the bridge's `SHIPPED_VERSION` and `SHIPPED_VERSION_STATUS`, the app's build stamps against the bridge's, and the seed config's stamped version default. Run against the v0.6.17e tree, the gate fails — the field bug, reproduced in a bench. The gate's first catch beyond the named bug: the seed config's version default had stood stale at 0.6.11 since that build, invisible to the runtime self-check because the installer restamps the live config from the VERSION file; it now names the build it ships in.

## 0.6.17

Release tag: v0.6.17e — chapter 0.6's eighteenth build: **the tab learns the rail**. A single-item patch — the #355 edge tab, corrected by the operator's field verdict on its first evening out. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #360 moves to Ready.

- **The edge tab rides the rail's current edge (#360).** In v0.6.16e the tab stood at the open nav's border line in both states — as specced, and the bench proved the spec: identical rect, open or closed. With the nav collapsed, that left it floating at the old border's line, detached from the icon rail and hanging over the main column's text — in the operator's field screenshot, on top of the brief card. His verdict: "Thats a glitch." The tab now takes its position from the state it stands in: straddling the open nav's right border while open (left:187px, exactly as .16e), straddling the icon rail's right edge while closed (left:63px) — the same −9px straddle of the border the operator actually sees, in both states. Its `left` transitions on the grid's own timing (#app's grid-template-columns transition, var(--motion-view) ease), so during the flip the tab rides the moving border at every instant; under reduced motion, grid and tab snap together. The bench invariant changed with the fix: navtab1 asserts adjacency now — the tab straddles the CURRENT rail edge in both states, tracks it mid-flip, and stays clear of the main column's content region — and against the v0.6.16e tree the closed-state legs fail while the open-state legs pass, exactly the field's shape. Everything else about the tab is as shipped in .16e: 18×52px, ‹ open / › closed, muted at rest and stronger on hover, theme-variable styling, `navi.navClosed` persistence, aria-expanded — and at ≤800px nothing changes at all: the phone top bar's ☰ is the shipped control, byte for byte in effect.

## 0.6.16

Release tag: v0.6.16e — chapter 0.6's seventeenth build: **the grounding build**. One major update in two halves: the four field fixes that queued behind v0.6.15e, and #357 whole — Navi becomes contextually aware of her own published presence, her persona rides her work wherever it is done, and the sitch reads the Wire or says it is quiet. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #355, #356, #357, #358 and #359 move to Ready; #347 and #348 are untouched.

- **She knows what the Row published (#357).** The bridge now fetches and caches a small structured digest the site itself publishes (presence.json: the latest Dispatches with their deks, the Stable and Edge versions the site chips carry, the roadmap's chapter count and headline), refreshes it on a six-hour cycle and on Mesh contact, and serves it stale-with-its-date rather than not at all. The digest joins her OnlyNavi page digest in the prompt as one presence picture — what she posted, what the Row published, what shipped. The Row digest is always on: releases and Dispatches are public, professional surface, not persona content; her page digest stays Row's-Own-gated, as shipped. Nothing private crosses anything (#337 untouched): every seat builds the digest itself from the same public source, so a borrowed answer grounds exactly like a local one. The budget matches her page digest's: ~2,400 characters, the latest four Dispatches; a digest older than a day orders her to date the answers drawn from it.
- **The grounding law (#357).** Standing in her persona, where she reads it on every turn: the briefs that ride the prompt are the whole of what the machinery has actually checked for her. She answers from them and names their dates; she never narrates a check that did not happen ("let me check the Dispatches") and never invents what a brief does not contain. A failed fetch is a named absence inside the brief itself — the record says it could not be fetched, with the reason — never a crash and never furnished content. This is the direct answer to the field failure that filed the issue: asked "what's new on the Row?", she named the Dispatches and invented them, cat and all.
- **Her persona rides her work (#357, the rider).** Row's Own Mode is additive — personality on top of the full working Navi, no function, tool, or doctrine gate subtracted — and now it travels: the presence segment and the grounding law stand inside the same persona composition the borrow's hygiene copy is built from, so a Mesh-borrowed answer carries her voice and her grounding exactly as a local one does. One Navi, one voice, every screen. LOWC, arming, and every consent gate are untouched.
- **The sitch reads the Wire (#357, operator ruling).** "What's the sitch" was already a composed behavior — the Wire's brief, the CTF board, and the bounty board in one awareness block — but when every engine's brief came back empty the block itself vanished, and the question got filler. Now the wire's absence is stated in the block, with its staleness sentence and the order attached: if the wire is quiet, the sitch says the wire is quiet, with its state and date — never invented headlines, never a take on stories she does not have. And when the prompt budget sheds the awareness segment, the grounding law still forbids claiming a check that did not happen.
- **The nav toggle becomes an edge tab (#355).** The full-width "« Menu" button leaves the nav's flow. On desktop the toggle now stands as a slim chevron tab riding the nav's right border — 18×52px, ‹ while the nav is open, › while it is closed, muted at rest and stronger on hover, styled from theme variables so glass and lcars read it too. It occupies the same screen position in both states: anchored to the frame at the open border's line, in the upper third, so the door never moves and never hides inside the closed rail. Behavior is unchanged — the same `navi.navClosed` persistence, the same aria-expanded, the same chat-column yield — and at ≤800px nothing changes at all: the phone top bar's ☰ is the shipped control, byte for byte in effect.
- **Her chat icon follows the Row's Own toggle (#356).** In v0.6.14e the presence bar learned to wear her OnlyNavi picture in Row's Own Mode, but her per-message chat icons kept the Apex portrait. The message-avatar render path (`msgAvatarHtml`, the one every message row uses) now reads from the same source of truth as the bar (`presenceAvatarSrc()`): mode on + a synced picture → her chats wear it; mode off → the portrait; mode on + no synced copy → the portrait, never broken. Bar and thread agree after a flip, repainted on the same paths — there is no second copy of the rule and no stale icon cache.
- **The equalizer is visible now (#359).** Field report on two builds: the presence bar's listening line rendered with no equalizer beside it, while the bench passed — it asserted the element existed. The root cause, named: the bars were painted in `var(--accent)`, a custom property no theme in the sheet defined, so every bar's background was invalid at computed-value time and computed to transparent — present, sized, animating, invisible. The variable is now defined in every theme (it is each theme's accent; the sheet's other `var(--accent)` surfaces — the poll bar, the drag-over highlights — get their intended color with it), and the equalizer itself is rebuilt bigger: five bars, 4×16px, still dancing in the theme accent, and still standing — at rest heights — under reduced motion. The new bench renders the page in a real browser and asserts painted pixels, not presence.
- **The docs stop teaching the retired step (#358).** The installing doc's Updating narrative still instructed "Turn Sudo Mode on before you update" a full build after the warning it described was retired. The paragraph now teaches what is true: an update never needs Sudo Mode — updates install at user level, nothing in the apply path gates on sudo, and the installer's one system-package step skips itself, by name in the step log, when a detached apply cannot answer a prompt, while the core install continues. Sudo Mode stands for the system actions that genuinely need it. Dated historical narrative elsewhere in the docs stands as written — instructions change, history doesn't.

## 0.6.15

Release tag: v0.6.15e — chapter 0.6's sixteenth build: **the second field fix round**. Four small repairs, every one from the operator's first evening on v0.6.14e — three of them visible in a single phone screenshot, the fourth his own mid-bake ruling. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #351, #352, #353 and #354 move to Ready.

- **One tray door on a phone (#351).** The presence bar's right edge carried its own pane button — the panel glyph — duplicating the top bar's dock toggle beside the bell. On a phone the bar's button is no longer constructed at all: at ≤800px `renderPresenceBar` builds the bar without it, and the top bar's `#dock-toggle` stands as the tray's one door, still driving the one dock state. The desktop is unchanged — both doors, one state, exactly as before.
- **The brand reads Powered (#352).** The phone top bar's center line read "Apex | powered by Navi"; it now reads **"Apex | Powered by Navi"** — the capital the tagline under the wordmark has always carried. The same brand line quoted in the in-app phone guide is corrected with it. The historical changelog's quotation of the old form stands as written, as history does.
- **The updater drops its sudo warning (#353).** The Updater no longer prints "Enable Sudo Mode before updating" when an update is on offer — nor the quiet green "Sudo Mode is on — ready to update" that answered it. Updates install at user level, and nothing in the apply path gates on sudo mode: the installer's one system-package step skips itself, named, when a detached apply cannot answer a prompt, and the core install continues. Sudo mode itself is untouched: Settings → System still arms it, its audit still records, and elevated commands still ride it.
- **One composer hint (#354).** The chat composer's placeholder is now a single line in every state — **"Ask Navi ..."** — on a call, on the CLI latch, with the model down, and in conversation, at every width. The per-mode teaching hints (a call line, a shell line, a command line, and the conversation line) are retired, including the desktop conversation form that suggested "show me the contents of /home/name/": no composer hint anywhere suggests a home path.

## 0.6.14

Release tag: v0.6.14e — chapter 0.6's fifteenth build: **the Row's Own fix round**. Seven fixes to the surface v0.6.12e shipped, every one field-specced by the operator on the first evening of real use — plus three of his rulings folded in mid-bake: her music is independent of the mode, the rotation's pool is now his own playlist, and every music link points at that playlist. The rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and no ceremony may re-stamp it. Board: #346, #349 and #350 move to Ready; #347 stays Ready — shipped-in-part again; #348 is not moved — its desktop half was v0.6.13e's, this build carries its mobile leg, and the field verdict on a real seat is still owed.

- **The presence bar, rebuilt (#346).** Her avatar stands at the left with the online indicator as a badge ON the picture, in every mode — the free-standing dot beside her name is retired. The top line beside the avatar is her status; the second line, smaller, is what she is listening to, with the equalizer playing beside it, its bars in the active theme's accent. In Row's Own Mode the bar wears her OnlyNavi picture from the synced blob; with no synced copy her Apex portrait stands — never a broken image. The rail's Status stack loses its Listening block: the bar is the listening line's one home, and it repaints on the same tick as the poll that feeds it, so the equalizer survives status-poll re-renders. Phones get the bar in miniature — avatar, badge, status, listening — instead of the bar retiring at ≤800px.
- **Her music is independent of the mode (operator ruling, mid-bake).** The listening line stands in the bar with Row's Own Mode off as well as on: the rotation is deterministic from the published epoch and the compiled table, so the bridge computes and serves the music state regardless of the mode flag — it never depended on the synced store. What stays mode-gated: the feed-born status source, the avatar swap, the Feed tab, the persona layer.
- **A new pool, and links that point at it (operator rulings, mid-bake).** The rotation's track table is now a snapshot of the operator's Spotify playlist **Navi's Super Hacker Mix** (snapshot 2026-11-20), five tracks in playlist order — *Gone* (SIERRA VEINS), *Magnum Bullets* (Night Runner feat. Dan Avidan), *Can You Feel My Heart (Mothica Version)* (MOTHICA), *Out of the Shadows* (Ely Eira), *Backseat* (Balu Brigada) — an 1185-second cycle; Dual Core and Sir Sly rotate out. Same epoch, same seeded shuffle: every seat and the site module agree, and the bench holds the bridge and the module to each other at every sampled instant across three full cycles and out to cycle 100000. The per-track Spotify ids stay as identity; every link the music state renders is the playlist's own URL, for every track.
- **Statuses stop overshooting (#346).** The sampler now cuts at the EARLIEST natural break by position — a sentence end or an em-dash, whichever comes first (the field's beach caption had its full stop at char 23, but the old loop took the first separator TYPE that matched, so a late em-dash at ~char 140 won and the cap sliced the line mid-thought). The budget is ~60 chars, trimmed at a word boundary; a caption with no clause that fits contributes no status rather than a sliced one.
- **The rail fits real windows (#349).** With the Feed pane open the rail takes a wider feed width (~360px): her posts get a real photo size and caption lines that read like sentences, while Status and Chats keep the 248px width. The chat column yields before the rail — and the tab row itself can now shrink below its labels: its min-content (~260px) exceeded the slim rail's 220px content box, which is what stood the Feed tab clipped at the window's edge. The geometry bench asserts the whole layout's arithmetic at 1280/1366/1440, at both rail widths, with the Feed tab whole.
- **The viewer walks, and the blur law holds inside it (#350).** The in-Apex lightbox gains navigation across the feed's image posts in order — ‹ › controls, arrow keys, swipe (touch handlers own the gesture, click owns the tap) — plus a position counter. Arriving at an unrevealed nsfw picture by any road shows it blurred with its own reveal control; revealing there reveals that post only. And exactly one viewer stands at a time: the shipped page stacked a frozen body-level copy under the live one on poll re-renders (reproduced against the shipped page before the fix; the grid's per-post reveal state itself never leaked — the bench's two-flagged-picture fixture now proves isolation in the grid AND in the viewer).
- **The mobile flip sticks (#348, the field leg).** On a phone the flip was lost to a race: the toggle POST runs the page sync inline before answering, and a status poll fired before the flip could land after its receipt carrying pre-flip state — the poll replaces the page's rows-own state wholesale, and the Feed tab un-rendered mid-browse. Now a poll can never overwrite a newer local toggle state: the POST's answer is the receipt, polls that set out before the last toggle action do not land their rows-own half, and fresh polls converge as before. The new bench reproduces the race against the v0.6.13e page — it fails there — and passes here; desktop behavior is unchanged.
- **Musings read as posts (#347).** The persona block's musing instruction now says plainly: the marker's contents are published verbatim as the WHOLE post, standing alone on her page where nobody sees the reply — write a complete little post in her page voice, a sentence or three like her captions, not a title, a summary, or a pointer at the conversation. Instruction only — no bridge-side length gate or filter.
- **Comments wear faces (#347).** Feed comments render as rows grouped by voice, with a real break wherever the speaker changes. Each commenter gets the picture this seat knows for them: the operator's own Apex profile picture for their comments, her page avatar for hers, a known identity's picture where the seat knows one — and an initial/monogram tile as the only fallback. Never a broken image, never her avatar standing in for someone else.

## 0.6.13

Release tag: v0.6.13e — chapter 0.6's fourteenth build: **the stickiness fix**. One defect, field-proven and fixed whole: Row's Own Mode did not stay on (#348). The build changes nothing else — no slate moves, Seraph v2 keeps its place in line behind this, and the rotation's epoch does not move: 1795222078 stays v0.6.12e's publish moment, and this build does not republish the rotation. Every item below is worded to what its bench proves; #348 moves to Ready, and it does not close on this build alone — the field verdict on a real seat is still owed, the unattended leg included: flip it, walk away, come back to ON.

- **A stale snapshot can no longer resurrect a flip (#348).** The config is one JSON file written whole by every settings path, and the slow writers — a Mesh exchange, a sync cycle — hold their snapshot across seconds of network work. On the first real seat, a writer that had loaded its copy before the operator's flip saved after it and restored the pre-flip file whole: the mode died mid-browse, read off on a fresh load, and died unattended while the seat sat idle. `save_config` now **merges at write**: the on-disk config is re-read at the moment of the save, and every top-level key the writer's dict never knew is preserved from disk. The writer's own keys win; what it never heard of, it cannot kill. The premise was grepped before it was built on: no code path in the tree deletes a top-level config key on purpose — the only config pops ride inside sub-dicts the writer still carries under a key of its own — so preservation cannot resurrect anything a writer meant to remove. An unreadable disk file still merges as the writer's dict alone: the standing behavior for a first write. The new bench (configrace1) carries the field's legs permanently: a flip ON and a flip OFF each survive a slow stale writer that loaded pre-flip and saves ~2 s later; two slow writers racing across a flip lose neither writer's new key; and the flip survives the fifty-round save hammer.
- **The toggle's receipt cannot lie (#348).** The Row's Own save read `save_config`'s verdict nowhere: the act answered `ok:true` with the requested state even when the save itself had failed — a receipt that could claim a flip that never landed, on a trust toggle. The save now follows the `sync_set_choice` pattern already in the tree: `_rowsown_settings_save` returns what stands, or nothing when the save failed, and the act answers `ok:false` with a named refusal — *the switch did not move; the bridge could not save the setting, so the mode stays exactly as it was* — and the stored state does not move. Benched by forcing the save to fail at the toggle (configrace1 C4): the refusal names itself and the card, the bridge state, and the disk all keep the pre-flip value, the switch gate's three views agreeing on the refusal as they must on a flip.

## 0.6.12

Release tag: v0.6.12e — chapter 0.6's thirteenth build: **the Row's Own build**. Her presence, baked whole: Row's Own Mode, the feed in Apex, and her music — #347 and #346 in one build, ahead of Seraph v2 by Alex's ruling. Every item below is worded to what its bench proves; the issues move to Ready, and neither closes on this build alone — the toggle's verdict on a real seat is still owed.

- **Row's Own Mode (#347).** A switch under Settings → Persona, off by default, and the switch is the consent gate — held to the same three-way contract as every trust toggle in Apex (the flip, the stored state, and the reloaded view agree, adversarial flips included). Its card says what it is in plain words: her e-girl voice, her blog mannerisms, her pictures and posts pulled into who she is here — **her spicy mode**. It is a persona layer only: no gate, no arming, no doctrine moves with it. While it is on, the bridge **syncs her OnlyNavi page directly** — fetching the page and parsing its blob locally; the flag and the cypher are for visitors, and her own seat never decodes her own door. The synced posts, captions, comments, and each picture's written `vision` description are indexed beside Soul and Memory as a personality source: her published self feeds who she is on the seat. A sync that fails keeps the last good copy and names itself — never an emptied feed, never a fake persona shift.
- **The feed stands in Apex (#347).** A third tab joins the status column beside Status and Chats — her mark, the cat-ear headphones and the eye — present only while the mode is on, the column widened a little to hold it. It opens her feed here, never the site: posts in her order, the pinned house rules, polls as they stand. Pictures open in a protected viewer in the page's own idiom — the picture as a backdrop, one tap hiding the caption text and another restoring it, the casual save paths closed. A picture flagged **NSFW stands blurred until a per-picture tap reveals it** — consent per picture, so a beach photo can land while the operator is at work and cost nothing. Likes and comments made here **persist back into her page's blob** through the GitHub contents API on the operator's own sign-in: the write re-reads the page fresh, mutates by post key, and converges the local store onto exactly what was published — one feed, two doors. With no sign-in on the seat, the feed is **read-only and says so**; nothing is ever dressed as posted that was not.
- **She writes for the page (#347).** Musings ride the chat model's own road — a marker in her reply, stripped before it is shown, recorded in her ledger first and only then posted, with the outcome written back either way. The floor is **one musing a day**; above it, material rules. The day brief carries her page's answer: the floor met, or owed and named. When a case publishes, the publication path records her write-up obligation — drafted from the published report only, internal findings never crossing the hook (only their withheld count, the number the report itself prints), under the same redaction pass that guards compiled case files.
- **A save race, caught by the gate's own bench (campaign fix).** The switch-gate bench's concurrent-flip leg exposed a defect in the config machinery every toggle rides: `save_config` wrote through one shared `.tmp` name, so two saves racing — routine on a threaded bridge — could interleave their bytes in the tmp file and the atomic replace would land a spliced, unparseable config. The tmp name is now unique per save (the `mkstemp` idiom the codebase already uses elsewhere), proven under a fifty-round concurrent hammer: the file parses whole, the stored value is a writer's value, and no tmp litter stands. The new Row's Own store is born with the same fix. The wider pattern elsewhere in the tree is named in the build's prep notes for its own ruling — this build fixes the road its gate rides.

- **Her statuses are her feed's (#346, as amended).** The hand-drafted status pool is cut and stays cut. While the mode is on, the bridge samples her own post texts — clauses of what she has actually published — and her status draw runs on those alone; off, the standing pool is untouched. Her **listening line** runs on a deterministic rotation shared by every screen: a four-track playlist shipped as local data (Dual Core, SIERRA VEINS, Sir Sly, Night Runner — 15:56 the cycle), each cycle's order a shuffle seeded by the cycle number, each track standing for its real length, the line linking out to Spotify. The identical algorithm ships as a standalone module for the site's round, and the bench proves the two computations agree across cycle boundaries. The rotation's epoch is stamped at publish — the moment the build publishes — by the release manifest's own flag: her soundtrack starts when the feature does.

## 0.6.11

Release tag: v0.6.11e — chapter 0.6's twelfth build: **the full fix build**. The standing remainder, baked whole and in order: the updater's rollback story, the apply health gate, streamed chat delivery, Seraph's remote leg, sync containment with its latency measured, the SSH port, the doors' proxy and first-device rulings, and the racing dial. Every item below is worded to what its bench proves; the issues move to Ready, and none close on this build alone.

- **The updater grows a way back (#306, #307).** Staged packages no longer live inside the install tree: the stage home is now a sibling of the install (`.apex-apply-stage/` beside it), so an install swap can never carry, strand, or delete a staged update; a package staged by an older build in the tree's `updates/` is adopted from there for one chapter (the dual-read retires at graduation), and stages are pruned to the current plus the previous two, by name, in the update record. Every update now also leaves a **rollback point**: the previous tree is retained whole (`.apex-prev`), and the outgoing build's live `config/` is archived beside the stage with a `rollback.json` naming both builds, the disk space, and whether the point was kept. When the disk cannot hold the point, the update still succeeds — the point is retired then and there, and the record says so and why. The Updater card offers **Roll back to <the previous build>** after an update, and — named first — after a failed one. The rollback itself is an act of the apply helper: it refuses by name when there is no point, stops the bridge only by a proven pid, exchanges the trees, and relaunches the way the seat's own record says it starts. Two restore shapes: **tree-only** (the current configuration rides back whole — the common case, a bad build with a good config) and **with config** (the archived configuration is restored — for when the update itself bent the config). Either way, **custody never travels**: the Mesh keypair, the door registry, the federation badge, and every token stay this seat's, restored over whatever the archive holds. After a rollback, the way forward is named in the outcome: the parked newer tree's own helper carries the roll-forward, because the live tree's helper predates the verb.
- **An Apply must prove the seat healthy (#336).** On a systemd-owned install, confirmation now asks the kernel, not the unit: the process answering on the bridge port must be running inside `navi-bridge.service`'s cgroup. A bridge that answers from anywhere else — the detached shape behind the 2026-11-20 NeoArcadia incident, where an Apply-spawned bridge was adopted outside its unit while the unit reported fine — **fails the Apply at the restart step, by name**, with the record carrying the gate's verdict; the install itself stands, and the sentence says what to do. Non-systemd installs record the gate as not-applicable. The update record and the Updater card both carry the gate's outcome.
- **Chat delivery streams; the answer still arrives whole (#278 — in part).** The chat route gains an opt-in streamed delivery, and the dashboard uses it: a `working` frame exercises the socket the moment the ask lands, heartbeat frames flow while the turn composes, and the reply itself arrives **whole** in the final frame — the standing presentation rule is untouched; answers are never typed out character by character, only the transport streams. If the client vanishes mid-generation, the bridge learns it from the heartbeat within seconds and the record says the answer was **not delivered** — nothing is filed as sent that wasn't. The DHD door relays a streamed chat progressively, and its 60-second cap no longer applies to the chat path: a 65-second generation now survives the phone hop that used to kill it. Unstreamed callers (the Mesh borrow path among them) get exactly today's single JSON answer.
- **Seraph's remote leg lands (#344).** A remote sensor's reports were refused at its console as `unknown-sensor` — the intake resolved the reporting sensor by the envelope's sensor id, an id minted in the *sensor seat's own* registry, in the console's registry, where it can never exist. Intake now resolves the sensor by the **authenticated sender node** (the registry's second lock, the one the design always named), prefers the node's active record over a revoked one, and keeps the envelope's claims honest: a report naming another node's record is refused as a mismatch. And a refusal is no longer silent anywhere: the send records its outcome — the console's filed note, its refusal reason verbatim, or the road's failure — on the sensor's own record, where the Seraph page shows it (*Last report home: …*). The console logs every refusal with its reason.
- **Removing a sensor is its own act (#341).** Not revocation (a trust act — the record stays whole) and not the federation tombstone (a different layer's record): a sensor that never reported is deleted outright, record and state; a sensor that was trusted shrinks to a refusal stub — name, node and last-seen kept, its detections still readable as its history — and its late reports are refused by the name `sensor-removed`, never `sensor-revoked`. The seat's own sensor is not removable; it is retired by the role, not by the registry.
- **The Seraph role stays flipped (#339 — in part).** The persistence path was audited end to end — the act, the settings store, the page, the installer's config carry — and reads sound; the role survives a reload, a bridge restart, and an update on the bench. One genuine reset mechanism was found in the machinery and closed: `save_config` wrote non-atomically while `load_config` silently fell back to a defaults dict on any read error, so a torn read in the write's window yielded the defaults and the next save of that dict permanently wiped every non-default key — the Seraph role among them. Saves are now atomic (temp file + rename), and a failed load retries once before it is believed. Under a concurrent-save hammer, no load ever sees the fallback.
- **Sync containment is completed at the exchange door (#337).** The account gate (#323) handshakes before any set byte crosses, and the pull road and both client legs already anchored the *set itself* to the account. The exchange's serving side did not: it applied a borrower's set on the strength of its stated login alone. It now runs the same anchor — a set naming another account (or none) is refused by name (`different-operator` / `operator-unknown`), ledgered like every refused door, and nothing of it lands. Two accounts on one Mesh: foreign material is refused at the handshake, at admission, and at the set, and a same-account set still crosses and converges.
- **Sync latency, measured (#338 — in part).** Measure-first, both builds on the same harness (two real seats, the Mesh road): a trigger pull converges every class — chats, cases, docs, seat, daybook, pulse — in **0.18–0.35 s** per class, and **push-on-write** lands a write on the other seat in **≈1.5 s** with no occasion needed there (the coalesce is 1.25 s of it). The golden build measures the same: the round is not where the field's 10-second standard is lost, and this build changes no sync machinery on a measurement that says it is fast. What the harness does not measure is named as the remaining territory: real field set sizes (the round's cost scales with the set), the repo road's latency when the Mesh is dark, and WAN conditions. #338 stays open on those.
- **The SSH tab takes the sensor's port (#340).** The port is part of the sensor's record now — set at registration or in the SSH tab itself, persisted per sensor, offered prefilled, and carried into the composed connection (`ssh -p 227 …` for NeoArcadia's door, no more typing it by hand). A record minted before the field existed behaves as 22 until told otherwise; a bad port is refused by name and the record does not move.
- **The doors believe a proxy only when told (#313, leg 3).** A new **trusted proxies** list (Settings → System → Door; empty by default) names the only addresses whose forwarded headers a door may believe. A trusted peer's `X-Forwarded-For` is walked right-to-left to the first untrusted hop; single-hop headers speak only when every hop is trusted; an untrusted peer's headers are ignored entirely. The DHD gate, the bridge gate, and the Mesh knock ledger all key on the one helper — so behind a trusted proxy, throttles and knocks name the visitor, not the proxy. With the default empty list, every door judges the socket peer: byte-for-byte the behavior Apex has always had, regression-benched. The Settings text names the consequence in plain words, including that trusting `127.0.0.1` lets any local process name its visitors. Throttle and knock state is not migrated — locks age out in minutes, and the notes say so.
- **The first device is confirmed on the machine itself (#313, leg 2 — ruling B).** The bootstrap is retired: the first correct code at a network door no longer mints an approved device on its own strength, and the shared-code cookie no longer opens a fresh door either. The first knock pends like every other, and it is confirmed by a local act — the dashboard on the box itself (loopback is never gated), or a shell act on the box; SSH counts. A one-operator house confirms its first phone at the machine, once; every later device is approved from any trusted session, exactly as before. The gate page, the waiting room, the Door card, and the docs all tell the new story.
- **The dial races (#309).** A peer's addresses are no longer walked one full caller-timeout at a time. The connect phase is split out and raced: per-address **connect budget of 4 s** (TCP + TLS + the pinned fingerprint), attempts staggered ~300 ms in preference order — the first connect that matches the fingerprint wins, and losers are closed before any request bytes exist. From the win, nothing changes: the caller's timeout governs the request and the read, borrow cap included. Preference is computed at dial time and the stored record is never rewritten: the managed tunnel stays **last, unconditionally**; a peer with an address on this machine's own LAN keeps its stored order (no hairpin out to its public address); any other peer dials public before private. Failure classification is preserved exactly — per-address kinds, the same precedence (fingerprint > TLS > timeout > unreachable), a budget burn counting as a timeout and fast refusals as unreachable — and a failure that tried more than one road now **names the roads tried** in its sentence. The health sweep rides the same dial, so a peer is reachable in the sweep exactly when a borrow would reach it.

## 0.6.10

Release tag: v0.6.10e — chapter 0.6's eleventh build: **the reliability patch**. Two field failures from the night of 2026-11-20, buttoned up the same night; nothing else changes.

- **"Warming" is a named state, never a parse error (#278, #336 — in part).** After a restart, the llamafile spends minutes loading its model; a chat ask inside that window came back as a body the page could not parse, and the dashboard rendered the raw parse error as if it were Navi's reply — and a warm server could still deliver an unparseable chat answer across the DHD hop. The bridge now knows the model server's readiness from its own health machinery — **ready**, **warming** (the process is present and still loading), **unreachable** (nothing is there) — and the chat route answers a not-ready ask with that state in proper JSON instead of attempting a dead generation. The honesty holds at every joint: an upstream answer that arrives as an HTML page or a non-JSON body is named as the state, never passed through; an exception inside the chat route is caught at the route's boundary, logged as itself (its traceback) in the bridge's record, and answered with a JSON **backend-error** state; the DHD door answers API requests with JSON even when the bridge behind it cannot be reached; and the page itself renders any unparseable or failed chat answer as the named state, taken from the bridge's status machinery as last known — the raw parse string is unreachable UI. The dashboard shows the state as a distinct system notice in the chat surface — she's warming up, the model is still loading — and the notice clears when readiness returns. The post-Apply face reads the same: a relaunched bridge says "warming" until the first real model round-trip. What this does NOT do: the apply-side health gate — an Apply refusing to claim success until the seat is proven healthy in place — is #336's full build and stays with the remainder bake. #278 and #336 stay open.
- **The shell never turns a password into a message (#220 — in part).** In a Shell-tab session, sudo's password prompt echoed the operator's typed password into the session as a clear-text message — recorded, saved with the chat, syncable. Now, when the session's output shows a password prompt (sudo's `[sudo] password for <user>:`, the `…'s password:` family, the bare `Password:`), the next input line is treated as a credential: fed to the pty only, masked in the UI as it is typed, and excluded from the session transcript, from any saved chat record, and from sync — the record keeps only a mask marker saying a password was given. A prompt in a form the bridge doesn't recognize is refused rather than carried: the line is not typed, the prompt is cancelled, and the record names the masked Settings → System arming route instead. A line of Navi's is never typed at a password prompt. Ordinary output that merely mentions a password arms nothing — the prompt must be the live, unanswered tail of the session's output. #220 stays open; its wider audit is not this patch.

## 0.6.9

Release tag: v0.6.9e — chapter 0.6's tenth build: **the bench-truth build**. No product behavior changes in this build — what changed is that the regression bench now tells the truth. The campaign had carried the same 19 failing suites since v0.6.6e; this build triaged every one of them against the shipped tree (dossier: `files/standing-19-triage.md`), and the verdict was **zero genuine product defects**. The 19 were the bench's own rot, and this build is the bench repaired:

- **Fifteen suites were stale, and now assert the current truth.** Eight had been dying on paths written for a build-dir layout the campaign staging outgrew (headless1, llamaintegrity1, bootorder1, installvoice1, settings11, relaunch2, scopeproof1's tree pin, and the per-build stamp pins in shellpty1, selftalk1, migrate12, applyboot1 that nobody had rolled since the v0.3.0e–v0.4.10e era) — each is re-pinned in this build's bench, recorded in the campaign runner, and benches the shipped candidate again. Two asserted surfaces that deliberate reworks superseded: casefiling1's flag-in-note legs (superseded by #266's case purity — the grounding flag rides the receipt, never the case file; the legs now assert exactly that, purity included) and fedichatui1's header/settings legs (superseded by #270 — the room's facts live in the About & settings window, and the legs now render it). Two pinned the presence pool at 36 lines after it grew to 38 by its own law (presencepool1, safestatus1 — re-pinned verbatim at 38, as presencepool2 already held). One slept 1.6 s past a 1-second vanishing term and called it past (rooms1 — the shipped prune runs on whole-second arithmetic; the sleep is now 2.6 s and the assertion is unchanged).
- **Three suites stand down by name where the sandbox cannot judge.** scopeproof1 needs a private systemd --user bus and sudo1 a dedicated unprivileged bench user; both now probe for what they need and print a named `ENV-DOWN` line, counting those legs separately — never as passes, never as failures. updaterfix1's campaign death was cross-suite port contention (a sibling suite's orphan held 8675; the installer rightly refused to kill a bridge it could not identify) — the runner's between-suite sweep now reaps campaign-rooted orphans, applyboot1's cleanup kills its own driver, and updaterfix1 pre-flights the port.
- **Two legs retired as expired.** applybench1's golden-control legs were a negative control against a pre-#271 installer; every golden since v0.5.7e carries the fix, so the legs could never pass again. They are retired in-suite with the premise named; the candidate legs and the surviving golden leg run as before.
- **The campaign's pass condition is now zero unexplained:** every suite passes, or its only non-passing legs are env-down or retired and named as such in the build report.

## 0.6.8

Release tag: v0.6.8e — chapter 0.6's ninth build: **Seraph, the SIEM suite** — the SIEM floor (#153) lands as a configuration of standard Apex, and the nav takes its ruled shape (#334). Alex's scope for the round: standard Apex first, manageable whole from DHD.

- **Seraph — the watch floor (#335, capping #153).** A new top-level **SIEM** group holds **Seraph**, the SIEM suite. Any seat can take the **sensor** role, the **console** role, or both, set on the Seraph page itself. A sensor watches the one segment it is plugged into, passively: the segment's living inventory (ARP, DHCP leases), the seat's connection table as flow and DNS-era metadata (metadata, never payloads), its listening services, and its own auth logs. Every snapshot names its **gaps** — what this vantage cannot see — on the sensor's dashboard. The v1 detection set: **watchlist matches** (matched on the sensor; the list never leaves the machine — #314's discipline, the Wire's declared list included), a **new face** on the network, **beaconing** and **impossible hours** (against the operator's sleep window), **failed sign-in bursts**, **scan patterns** from the receiving end, and a **new listening service** on a known host. Detections ride the standing alert spine in **Navi's voice** (#319) and can be **filed as a case** from the dashboard — the detection becomes the case's founding exhibit, hashed by the bridge at filing time (#326/#330) — or dismissed. Remote sensors report home over the **Mesh** (signed, pairing-authenticated, registry-bound), **spooling** when the road is dark and draining when it lights; a revoked sensor is a **tombstone** whose late reports are refused by name. Per-sensor dashboards carry inventory, listeners, top talkers and detections, with an **SSH tab** beside them (the operator's own key and session, opened by hand, in the seat's shell machinery). Retention is operator-set (30 days default); open and filed detections never age out silently. The sensor edition's preconfigured image — PIA's shape — is a later round; this round is standard Apex, and the suite works whole without a PIA.
- **Seraph's marks.** The suite carries her own icon family: the **working glyph** (two rings, a gold flame, gold wings — a clean redraw that reads at nav size and re-skins with themes and both layouts) in the nav and on dashboards, the **ceremonial winged eye** on sensor page heroes, and a per-tool icon set (Registration, Discovery, Flows, Logs, Watchlist, Detections, Dashboard, SSH) drawn from the same geometry.
- **The nav takes its ruled shape (#334).** The "Apex | " prefix drops from every group — the bar's head already says Apex — and the groups read **Navi**, **Casework**, **Network**, **SIEM**, with **Utilities** where it always sat at the foot. Casework is the old Apps group renamed, its children reordered with **The Wire promoted to the head**: The Wire, Case Files, The Dossier, Vault. Display only — group keys, view keys and behavior are untouched — and the in-app docs' locators were swept in the same round.

## 0.6.7

Release tag: v0.6.7e — chapter 0.6's eighth build, the field-fix build. Spartan0311's twelve-issue field batch (#305–#316) was triaged against the shipped tree, Alex ruled "bake what will fix it for now," and this build carries the fix-now slate at full depth — plus the two honesty fixes from the same morning (#331, #332). Four items are consciously deferred and named below; they stay open.

- **The local prompt gets a budget (#310).** The chat assembly is now measured against the seat's own context before anything is sent: per-block caps on the briefs that can grow, a shedding order that drops background before it ever touches her persona or the working case, teaching blocks that ride only on the turns that can use them (shell teaching on machine-directed turns, case teaching on case turns), history trimmed oldest-first, and the estimate riding every chat payload as a readout. What cannot fit even shed is refused BY NAME — the numbers stated, the doors named — instead of dying truncated at the model. The context derivation's lowest band floors at 4096, the product's own prompt floor, in the bridge and the installer alike: a 4096 seat holds a conversation again.
- **Borrowed replies are inert (#315).** A reply served by a Mesh lender is answered with, never acted on: the shell gate is shut for it outright, its memory markers are held as proposals instead of saves, its finding markers are stripped without filing — and the gate's own failure path now fails CLOSED, so an exception is never again read as machine intent. What leaves for a lender is cleaned at the door (#314): no marker teaching, no shell teaching, the intel brief in its share shape.
- **The watchlist stays home (#314).** The intel digest served to peers no longer carries stack-match or watchlist-hit material — counts and headlines ride, the operator's own term list never does, per the module's founding doctrine. Borrowed prompts carry the share-shaped brief, and the GitHub backup's settings item no longer includes the intel watchlist.
- **Lending to new members defaults OFF (#316).** The sanitize default now matches the Federation page's promise ("off until you turn it on"): an absent key is off, a stored true stays true, and the switch gate was benched three ways — flip, stored state, post-reload view.
- **The roster version is real (#311).** The federation roster sync returns the roster's actual version instead of a wrapped-dict artifact, so the version sentence and the anti-entropy checks read a number that exists.
- **The node's own gate door is throttled (#313, leg 1).** The bridge's /__gate branch carries the same throttle as the DHD door — five wrong codes lock it for five minutes, a locked door refuses even the right code with the wait named, a correct code clears the count. Legs 2 (the first-device bootstrap) and 3 (proxy-aware client IPs) are NOT in this build: leg 2 awaits a doctrine ruling, leg 3 is deferred with the full-depth pile.
- **The updater stops fighting systemd (#305).** On a boot-startup seat the apply helper signals navi-bridge.service and lets the unit own the restart — no more immortal start.sh processes adopting the unit's bridge and polling it forever, one per Apply.
- **Apply evidence survives the swap (#306, cheap leg).** The updates/ evidence — apply traces, install and relaunch logs, job records — is carried across the tree swap like config, so a successful Apply stops deleting the record of itself. Package payloads do not ride. The full relocation of the stage home out of the tree remains open.
- **The install record tells the truth (#308).** Both install markers (.apex-provisioned, .apex-install-record) now write the stamp of the tree actually being installed, read from that tree's own bridge — finishing the #271 rider.
- **A root shell is refused at another user's tree (#312).** A genuine root shell installing while a non-root user owns an Apex tree on the machine is refused BY NAME — the owner and their door named, --as-root the spoken override. MIGRATED.txt is read at last: a proven-migrated tree is never re-migrated, whatever home a later invocation targets. And the installer no longer advises kill -9 against another user's processes — it names the owner and their own stop door.
- **Case talk knows its watch (#331).** When a case is in context, her case facts carry whether a Pulse watch stands attached to it — the topic and last check when one stands; an explicit "none stands" when none does. "Actively monitored" is now a sentence she can only say over a watch that exists.
- **One phone, one record (#332).** Push subscriptions key on the phone's door-device identity: a re-subscribe from the same device replaces its record — new endpoint, label carried — however often iOS re-mints endpoints. The Settings roster shows each record's subscribed date, and any seat can remove a record; that record stops ringing and nothing else is touched.
- **The reference shelf folds (#333, added on Alex's order mid-bake).** A case's reference shelf collapses to its header — the header row is a real button (≥44px at phone widths) carrying the source line and the item count in both states. The fold is remembered per case in the seat's view state and survives reload; it behaves identically at desktop and phone widths, in the app window, and in Standard and LCARS layouts alike. Folding changes nothing else: items, Remove, "use reference R#", and Navi's reading of the shelf work exactly as before.
- **Deferred by the rescope, still open:** #307 (the rollback point), #306's full stage relocation, #309 (the Mesh dial rework), #313 legs 2–3.

## 0.6.6

Release tag: v0.6.6e — chapter 0.6's seventh build, the case suite. Filing learns every part of the case, the button learns to sense which part a reply is, the Vault gathers the case files into their own section, a filed heading stops printing three times, and a Wire story can pull a whole case together around itself — briefing, leads, and her recommended next steps staged for approval.

- **File as {Type}, for every part (#326).** The filing doors — the tap, the operator's words, the start-a-case door — now land in **all nine** of a case's parts: **task** (a list reply splits into one Tasks entry per item; prose around the list rides the receipt as the source note, never dropped, never a task), **timeline** (the entry is dated by the date the reply names for the event, or the filing moment), **evidence** (the reply stands as a text exhibit, exactly as written, its custody entry carrying the SHA-256 the bridge computed at filing time) and **report** (the reply appends to the case's report material — a register of its own, since the drawn report stays a generated export — and the formed document's Report section draws the entries first, in filed order, dated). Every receipt names the section the filing stands in. "Note" is the one refusal left, and it names all nine parts.
- **The destination is sensed (#327).** The button under a reply reads the reply's shape, deterministically, the page and the bridge running the same read: a chronological narrative (three or more dated lines) is a **timeline** entry; a list of indicator data is **observables**; an imperative next-step list is **tasks**, the button naming the count ("as tasks (5)"); a short reply whose subject is typed on its face is an **entity**; a reply opening on a date is an **event**; a reply carrying its sourcing is a **lead**; a bare indicator is an **observable**. Anything the read cannot place is a **finding** — the plain default, never dressed as a confident guess. And the operator's words naming a part govern **absolutely**, on every door, over any sense.
- **The Vault's Cases section (#328).** Formed case files stand in a **Cases** section at the **bottom** of the Vault — below every other folder, set apart by its own divider — grouped by type shelf (`Cases/Investigation/<Case Name>.md`): the disk matches the desk. Existing formed files moved in the formation sweep, content-exact, the move tombstoned so Sync carries it and the old address never resurrects.
- **Headings print once (#329).** A filed reply whose first line repeated its heading printed three times — the entry's heading, the rendered title inside it, the body's own opening line. The filed note keeps the reply's exact words — no writer title line is added above a body that already opens with its heading — and the surfaces that print the heading themselves (the formed document, the report export) open the body after the repeated line: exact match, or the heading with a colon, for filings from before this build exactly as for new ones, across every part and in dossier documents. A heading recurring later in a body is the author's text and stands; the answer as printed in chat is never altered.
- **A case is born from the Wire (#330).** A story's **Start a case** button — or the words "start an investigation on that story" — pulls the case together in one act: the case is created from the story, the article read **whole** onto its reference shelf, one **cited lead** filed per CVE the article names (resolved through the intel catalog; an id the catalog cannot answer is a named **gap**, never a silent skip; ids past the birth cap are named too), related coverage shelved beside it (capped, one hop), the case set open. The case chat opens on **her briefing**, composed by the bridge from the case's live state — and her **recommended next tasks** stand on the Tasks register as **proposals**: Approve opens one as a standing task; Dismiss strikes it, the strike on the timeline. "Brief me" in the case's room draws a fresh briefing from the state as it stands then. The deliberate counterpart to #326: her filings are proposals; the operator's are acts.

## 0.6.5

Release tag: v0.6.5e — chapter 0.6's sixth build, the fun one. LCARS stops being only a palette and becomes a layout: Appearance gains a Layout axis, every theme works in both geometries, and flipping between them translates — nothing is lost in either direction.

- **LCARS Mode (#325).** Settings → Appearance gains a **Layout** choice beside the theme picker: **Standard** (the shipped geometry, still the default) or **LCARS Mode** — elbow-swept cards, the rail as numbered pill stacks, sweep-tab headings, pill-ended controls, condensed uppercase labels on the furniture, in the modern 2.0 proportions. The mode owns geometry, not colors: its accent slots read the **active theme**, so all twelve palettes — the LCARS palette included, the flagship pairing — work inside LCARS Mode, and Standard keeps wearing all twelve as before. The layout is stored in your config exactly like the theme and rides the settings backup beside it. The phone's dedicated interface gets the same geometry in this build — slimmer elbows, full-size touch targets, no sideways scrolling.
- **The translation contract (#325).** Flipping layout, in either direction, from anywhere, is a **re-render, never a navigation or a reset**: same surface, same chat thread and scroll, same open case or document and its edit state, same switch positions, same half-filled forms, same rail groups open or closed. The picker lives in Appearance under **both** layouts, in its accustomed place — no mode hides its own exit. Chosen layout, stored config, and what a reload (or a bridge restart) shows are one truth, and the Federation page's Mesh and Fleet switches keep their gate under the new geometry: flip, stored state, and post-reload view agree, with refusals spoken on the card.

## 0.6.4

Release tag: v0.6.4e — chapter 0.6's fifth build. Sync learns whose data it is carrying: the account gate comes first — then the Vault becomes one file per case, departed fedinets stop coming back, the Mesh switch moves onto the Federation page, and the console learns to dress as LCARS.

- **Sync is account-gated (#323).** A sync set belongs to the GitHub account whose sign-in produced it, and two seats now prove they serve the same account before any data moves: over the Mesh, a **handshake door** is answered before any pull or exchange is served, and on the repo road the set's manifest is judged the same way. A refusal is **named** — operator unknown (either seat signed out; two unknown seats never converge), or a different operator, with the serving seat's account named so the fix is obvious — and recorded on the Sync card's receipt line, never a silent skip. Beside the gate, an **attribution ledger**: every synced chat, case, document and daybook entry remembers which account it arrived under, and when a seat's sign-in is established (at sign-in, and at start-up), material proven to belong to a **different** account is **purged through the ordinary delete doors** — tombstoned, so the purge itself converges — while anything locally born or unprovable stands untouched. A tray notice reports the counts. What happened in the field — one operator's cases arriving on a second operator's unsigned install — cannot recur: an unsigned seat has no account to match, and the gate fails closed.
- **The Vault is one file per case (#320).** In the Vault, a case is now **a single document in a folder named for its kind** — `Incident/`, `Investigation/`, `Research/`, `Hunt/`, `Locate/`, `OSINT/` — titled with the case's own name and holding everything the case record holds: head facts, leads, findings, entities, observables, tasks, evidence, timeline and the report, in sections. Dossiers stand the same way in `Dossiers/`. The per-part fragment notes are retired: the migration is the formation sweep itself — every living case re-forms into its one file and every fragment is pruned. Rename a case or change its kind and the file moves; delete a case — or merge a dossier away — and its Vault document is deleted through the same tombstoned door as any note. If something is gone, it is gone.
- **Departed fedinets stay departed (#321).** Leaving a fedinet — or a gateway dissolving one — now writes a **departure tombstone** that rides the sync set like every other deletion: a seat that left is no longer dealt back in by a sync round, and a card that still arrives for a departed fedinet is **refused by name** in the round's summary. Rejoining stays in the operator's hand alone: **importing the gateway card manually clears the departure** and re-admits the fedinet. A gateway gains the **dissolve** act — crown-confirmed, louder when it strands members — ending the fedinet for its own seat and tombstoning it everywhere its sync reaches.
- **The Mesh switch lives on the Federation page (#322).** The Federation page opens with **The Mesh** card: the Mesh's own switch, riding the **same door and the same stored state** as the Mesh page's control — one state, two surfaces. The card names what rides on it: fedinets, borrowing, FediChat, and Fleet Answers all go dark with it. The switch gate holds in full — the flip, the stored state and what a reload shows are one truth — and a refusal (an identity that cannot be minted) is spoken on the card itself, the switch unmoved.
- **LCARS (#324).** A twelfth theme joins the picker: the starship console, in its modern 2.0 cut — a black field, pill-ended bars and buttons with black text on the color, elbow-curved cards, uppercase condensed labels, the classic accent family (orange, peach, lilac, periwinkle, brick) with cooler blues and teals woven through. It is a **skin over the same screens**, off until chosen like every theme: the rail's groups still collapse to their header pills, every switch answers to the same state, and the lettering is your system's own condensed face — nothing is fetched.

## 0.6.3

Release tag: v0.6.3e — chapter 0.6's fourth build. The operator's hand, restored: a chosen sync direction overrides the round in flight, a cleared main chat stays cleared on every seat, the verdict never claims a convergence the main thread denies — and the alerts arrive in Navi's voice.

- **The override overrides (#317).** A chosen **Send** or **Receive** no longer queues behind a sync round already in flight. The running round is signalled to stop at its **next phase boundary** — rounds converge idempotently, so its partial work stands — and the chosen direction runs immediately after; if the in-flight round finishes first, the direction runs next, never behind a second round. **Both receipts tell the truth:** the stopped round's record names the supersession (an operator override, and the phase it stopped at) and its card face reads *Overridden — your call runs now*; the directional round's receipt is the ordinary one. A newer choice replaces an older one mid-flight — the newest direction is the one that runs. The hold remains for machine triggers (push-on-write, the occasions): preemption is the operator's privilege, exercised through the choice.
- **A cleared main chat converges (#318).** Emptying the main thread (/clear, /cls) is now a **synced act with an epoch**: the chat set carries a clear marker (the moment, and the seat that emptied it), and convergence honors it on every seat — content stamped at or before the clear yields to the emptied state, post-clear messages are untouched, and the ghost-fold can never resurrect pre-clear content. Beside it, a **post-round substance check** on the main thread: after a round, the main thread's count and digest are verified against the converged set, and on a mismatch the verdict is **renamed** — *Mostly synced — the main thread disagrees (theirs N messages, ours M)* — on the round's receipt and the Sync card's last-round line. Never a clean *converged* over a divergent main thread.
- **Navi sends the alerts (#319).** Push payloads — and the tray summaries they mirror, parity unchanged — speak as **Navi**: her name leads the title, never "from Apex", and the summary is composed in her voice, a written **flare line per producer class** (reminder due, standing-order report, Pulse batch, FediChat arrival, sync verdicts and update notices that earn a push) wrapped around the fact, which rides **verbatim** — reminder text, times, names, counts exact; the flare never edits the fact. The banks rotate **deterministically** (the same class and count draw the same line; consecutive draws differ) with **no model call** on the alert path. The plain factual record stays on the tray record's detail, structured fields untouched. Borrowed and federation-served alerts are announced by the **local** Navi.

## 0.6.2

Release tag: v0.6.2e — chapter 0.6's third build. The sync override: every Sync press offers Send or Receive — and Brief v2: the day brief as a markdown document, presented as a list, with Navi in the rows.

- **The sync override (#303).** A **setting** (Settings → GitHub & Backup, on by default) governs the Sync button: with it on, a press offers **Send a sync** or **Receive a sync** — a manual override, so a sync happens now, on demand, not at the automatic cadence's pace. **Send** publishes this seat's set and applies nothing; **Receive** pulls and converges and publishes nothing. Both are the standing machinery standing alone by direction — the same roads (Mesh first when lit, the backup repo otherwise), the same convergence law — never a second sync system. Each round is **receipted** with what actually moved: files published, what came down, what converged — and a direction with nothing to move says so plainly. With the setting off, a press runs the legacy full round at once. The automatic cadence is untouched.
- **Brief v2 (#304).** The day brief is composed and **stored as a markdown document** — a dated title, section headings (On / Changed / Needs you / Standing), one bullet per item — and recall returns the document. No surface presents the markdown: Home's Her working day card and the chat's brief answer **draw a native list from it** — sections as headers, each item a row with its time and state. Reminders gain a **postpone** act (chat: *snooze it to tomorrow*, *push it in 30 minutes*; the act is recorded on the reminder's own record), and the **deferral count is derived** from those acts plus the days a fired reminder has been carried — never a stored counter. When a count passes one, the item's row gains a **quip in Navi's name**, deterministic and once per count, escalating with the count — professional in register for the standing orders' items. Reminders' machinery — firing, ack as a synced fact, push parity — is untouched; the greeting's day lines stay terse.

## 0.6.1

Release tag: v0.6.1e — chapter 0.6's second build. Fleet Answers: one ask, divided into whole sub-tasks, each answered whole by the machine best placed for it, composed into one answer with the seams showing.

- **Fleet Answers (#293).** Where a borrow sends one whole ask to one stronger machine, a fleet ask **decomposes** one ask into whole sub-tasks in the Mesh's existing classes — **generate**, **collect**, **lookup**, **report** — fans them out over the roads that already exist (direct pairing, a joined fedinet's roster terms, the relay when the direct road is dark), and **composes** one answer in which every contribution is **signed with its machine's name**. The unit of work stays whole — tokens and layers are never split, under any name. The wall clock of a fleet ask is the longest contribution, not the sum: a weak node that generates nothing and only asks can be answered at the fastest member's speed plus one hop.
- **Membership is a toggle (#293).** Fleet participation is a **per-node toggle on the Federation page, off by default** — join or leave at will, no ceremony. The switch gate holds in full: the flip, the stored state, and what a reload shows are one truth, and a refusal (the Mesh off, an identity unminted) is spoken on the card itself. Joining grants nobody anything: a contribution is judged at the answering machine's own door under its own caps and consent, counts against its ordinary borrow caps, and is written to **both** sides' ledgers as one entry **cross-referenced to the fleet ask's id**. A node that leaves **mid-ask** degrades that answer by the named-gap rule — the piece is badged missing, never silently dropped.
- **One hop, hard; peeks never travel (#293).** A contribution never fans out again — the borrow door refuses a fleet ask that arrives already inside a fleet ask, by name. A sub-task that names a **peek** is held back and named in the plan; peeks never fan out under any name. Every ask carries a **deadline** and ships a **badged partial** when it passes: a contributor that is dark, refuses, times out, or is preempted by its own operator is a **named gap** in the answer, never a silently thinner one. The fan-out cap (4 machines, settable in config) bounds an ask; above it the plan **leads the answer** instead of standing silent. A node whose profile marks it unable to compose sends the assembly to its home node as one more whole sub-task, and falls back to a local assembly — with that gap named — when home cannot answer.
- **Asking, and the case tie-in (#293).** Start a chat line with **fleet:**, or ask a plainly multi-part question and Navi judges it a fleet ask. A plain single-part question is **never** routed to the fleet — it is answered the ordinary way, untouched. In a **case chat**, the plan and its contributions stand in the thread as their own bridge-appended record, so the standing filing proposal under it files them as **leads with their machine provenance**; the composed answer is the turn's reply, finding-shaped. Nothing files itself.

## 0.6.0

Release tag: v0.6.0e — chapter 0.6 opens. Her working day: one bridge-held book of captures, reminders, standing orders and the day's brief, the same on every seat — and the Dossier's kit goes live-fire, its unshipped shelves settled on evidence.

- **The foundation store (#294).** Captures, reminders, standing orders and the day brief live in **one store the bridge holds** — the page and chat are views and doors onto it, never owners of it. The book is a Sync citizen from birth: it rides the account set, converges by identity with the newest word winning, and its deletions are tombstones a stale copy cannot resurrect — the same convergence law as chats, cases and the Vault. It is **secret-free by construction**: anything shaped like a credential — a password, an API key or token, a card number, a Social Security number — is refused at the door **by name**, on every door. **Capture & Recall** is built on it: a save lands with its provenance (your trigger, or her own call named as hers), a correction **supersedes** rather than rewrites, *undo that* takes the last capture back, and *recall …* reads the book aloud. Her trigger and autonomous saves are recorded in the book at the moment the bridge receipts them; the seat memory they also feed keeps its own path, untouched.
- **Reminders & standing orders (#295).** The scheduler is **resident in the bridge** — reminders are bridge state with their due-state on disk, so they survive restarts and fire with no window open; a reminder that came due while the bridge was down fires on the next start, late and named late. Delivery rides the notification tray, and with push on, the phone's lock screen — the tray record's own words in both places. A fired reminder **stands** until acknowledged, and the acknowledgement is a synced fact: clear it on one seat and it clears everywhere. A **standing order** is data with a bounded vocabulary — it can **remind**, **report**, **file** into a named case, or **check a Pulse watch** — and an order asking to send, spend, elevate, delete, run or call is refused **by name** when it is given. Every execution is recorded on the order itself and read back in chat and on Home; a file order whose case is not there says so and files nowhere.
- **The day brief (#296).** The greeting grows a day section: **what is on** (today's standing reminders and orders), **what changed** (what the book gained, what fired, what a watch flashed), **what needs you** (fired and unacknowledged, run and failed). The brief is a **stored record**, composed at the day's first light and again on ask — *brief me*, or the button on Home's new **Her working day** card, which also carries the standing reminders with their Acknowledge, the orders with their last run and Revoke, and a plain capture line. A source that cannot be reached is **badged as a gap** in the brief, never smoothed over. No calendar connection in this cut: the day she briefs is the day the book knows.
- **The Dossier goes live-fire (#290).** Every wired door was read live against known-answer subjects, and the round stands as the kit's field record. The **Bureau of Prisons inmate locator** — one of the four shelves the fifteenth build left unshipped — answers keyless and is **wired** into the Person run. **Interpol's Red Notices API** and the **Justice Department's press-release API** are documented public keyless doors that answered this network with an edge denial; both are wired as **attempted doors** in the full-text pattern — read when the door answers, and an edge denial degrades **by name** in the result with the check standing at the source's own search. **USCG vessel documentation** is a session form at both of its doors and stands as a **named pointer** on the License shelf. Drift found in the round was fixed in the runners or named in the build report; nothing was stubbed silently.
- **The menu's Chat entry centers (#292).** In the expanded menu the Chat entry — icon and label as one unit — centers like the Home tile it stands beside, instead of reading as a section header that lost its chevron. Section rows keep their grammar; the collapsed rail already centered it and is unchanged.

## 0.5.15

Release tag: v0.5.15e — chapter 0.5's fifteenth Edge build under patch-per-build versioning. The Dossier becomes the full kit — courts, business, licenses, archives and the civil spine, composed in the open and all of it at Navi's fingers — and filing learns its destinations: every door names the part of the case it files into, and the operator's words govern.

- **The Dossier, full kit (#290).** The five keys of #260 grow into the comprehensive public-records kit. **Courts:** federal dockets and published opinions read keyless through CourtListener (RECAP), each hit cited, a caption's other side carried as an associated name; PACER (credentialed, per-page), govinfo (keyed API) and the session-driven state portals stand as named pointers — walls named, never climbed. **Business:** SEC EDGAR filer match, company facts, recent filings and full-text; OpenCorporates registrations with their officers of record as associated names; ProPublica's nonprofit 990 filings; USAspending federal awards; the FEC (your API-key choice) and USPTO TESS stand as pointers, as does Pennsylvania's form-driven entity search. **License:** amateur callsigns read from the FCC's ULS mirror and aircraft N-numbers from the FAA registry — the shapes that have keyless machine doors; professional licenses by name stand at the boards' own doors (PA PALS, ULS name search, airmen inquiry) as named pointers. **Archive:** the Wayback Machine's snapshot index for a URL; OpenAlex + Crossref scholarship for a name. **Address — the civil spine:** the gazetteer's read, the county's property door named, the voter note for the state (a pointer where the state publishes one; an honest absence where the file is restricted). The Person tab's anchor row grows the **OFAC sanctions check** — the SDN + consolidated lists read from the Treasury's own publication, matches named as leads — plus an obituaries pointer; Email adds OpenPGP keyserver presence; the Username corpus widens to 44 platforms.
- **One dossier, many doors — composed, proposed, never auto-run (#290).** A key the kit has seen opens the dossier that holds it, from any door, so the spine accretes on one record. **Compose a run** shows the shelves a starting key fans out to — doors and request cost named — before anything fires; the confirm is the fire, on the page and in chat alike (`dossier plan for …` composes, `run the dossier plan for …` fires). Hits propose **pivots** — associated names, un-run shelves — one hop, on the dossier and in Navi's context; the press is the go. Every shelf ships with its deterministic chat route or it does not ship.
- **Filing has destinations (#291).** Every filing door — the tap, the start door, the operator's words — carries the part of the case it files into: **finding** (the default), **lead**, **observable**, **entity**, **event**. Print-first stands: the answer prints whole, then the suggestion names its destination — the button reads **File into this case — as a lead**, read deterministically from the reply (a bare indicator suggests observable; a sourced report suggests lead; furniture never guesses entity or event). The operator's words govern over every suggestion, and the receipt names the landing. A named place that is not a filing part — evidence, tasks — is refused by name, out loud, with nothing filed and nothing silently rerouted to findings. The case file's purity holds: the part is structure, never machinery text.

## 0.5.14

Release tag: v0.5.14e — chapter 0.5's fourteenth Edge build under patch-per-build versioning. The answer, then the knock: Navi's main-chat answers print whole again — starting a case is the operator's tap on the reply — and the tray learns to ring the operator's phone, from the operator's own node.

- **She prints, then offers (#289).** The conversational case intake is retired — the parser, its refusal, and the teaching that fed it are deleted, not bypassed. In a chat that is not a case room her answer now stands exactly as composed, whatever shape it takes; nothing reads case machinery out of a reply. Under every reply stands a **Start a case from this** button: pressing it — the operator's act, the only way a case starts from chat — has the bridge compose the case from that reply exactly as printed (the reply filed whole as a finding in her name, a timeline beat naming the act), ensure its chat, set it open, and append the bridge's receipt to the thread with an **Open the case chat** button on it. The offer never blocks the conversation, and an older reply's button starts a case from that reply whenever it is pressed. The deterministic doors — the New case form, the create door — keep their validation and their named refusals, untouched.
- **The tray rings your phone (#272).** Whatever earns a #242 tray record now also rings the operator's phone — parity with no exceptions by kind: the lock-screen notification carries the tray record's own title and summary, is tagged with the tray record's id, lives at most four hours, and reading the record on any seat sends a clearing push that closes the phone copy. Tapping it opens the dashboard at the tray, on that item. The sending is the node's own work: the bridge mints its VAPID keypair once (per node, in its own config, never synced), signs every delivery, and encrypts each payload end-to-end for the phone's subscription with in-tree cryptography proved against the RFCs' published test vectors — the only other parties are the platform's own push services. Delivery fires only from the seat that created the record; the outcome stands on the record's own line in the tray — sent, or failed with the reason named. A phone the push service has forgotten (404/410) comes off the list and is named in the tray until it subscribes again.
- **The door names its state (#272).** The bell panel and Settings carry the phone door on a four-rung ladder: live (ring this device / stop ringing), blocked (the permission is denied, with the fix named), unsupported (no Push API, said plainly) — and on iPhone, **install-first**: iOS gives push only to web apps added to the Home Screen and opened from their icon, so the door shows those steps as a card instead of a button that cannot work. Several phones can ring; each subscribes to the node it talks to, and a subscription the platform rotates heals itself through the service worker.

## 0.5.13

Release tag: v0.5.13e — chapter 0.5's thirteenth Edge build under patch-per-build versioning. She keeps a pulse: flagged topics Navi watches — batched notices, a digest in her greeting, hits fed into cases as reference. The greeting itself comes alive, and Sync learns to verify substance instead of converging shells.

- **Pulse — flagged topics, kept watch on (#287).** A watch is flagged in chat ("keep a pulse on Epic MyChart") or on the new **Pulses tab** in The Wire — one store, both doors. The resident bridge checks each watch every few hours, and folds a fresh check into the greeting, against the articles the wire's **enabled networks** brought in; the tab carries the contingency on its face: Navi can only keep a pulse where she can read — the networks enabled in the News tab, the operator's own feeds included, are the watched ground, and a watch with no coverage says so rather than standing silently empty. "New" is identity, not headlines: a story's source id / link digest enters the watch's seen-set once. New hits land as **one batched #242 tray record per watch per pulse**, keyed by the batch's digest so the same batch converging from another seat is never announced twice, and Navi announces it in chat. A watch attached to a case drops its hits on that case chat's **reference shelf** (#283's pattern — reference, never findings; #266 purity kept). Pause/resume/remove ride both doors; ambiguous topics are named and asked, not guessed. The watch store rides Sync as account data.
- **The living greeting (#288).** The Home Brief's greeting takes the operator's format: **Good <part of day>, <profile name>** / a quip / a break / the brief. The name is the operator profile's; the band is seat-local with a **real night band** — the operator's day starts at midnight, so 00:xx reads as night. The quip is composed **deterministically by the bridge from Navi's actual statuses** (Mesh state, tray unread, wire health, pulse news, the seat's build) — templates over measured facts, no model call, every factual claim traceable — and rotates on a persisted counter so it never repeats back-to-back. The brief continues after the break with the **Pulse digest**: only watches with something new are named, and a digest once spoken is marked greeted so the next greeting names only what is newer still.
- **Sync carries the substance, not the shell (#262).** The sync manifest now declares substance: per-chat message counts and digests, and digests of the seat payload and the Pulse store. On arrival the receiver verifies: a chat whose substance falls short of its declaration is **named incomplete** on the sync bar and in the durable record, and where the seat already holds more of that conversation the shell is refused — convergence never trades substance for a husk. The seat and the Pulse store, single documents merged destructively, are refused outright when their bytes fail their declared digest. A later round's full arrival **heals a shell in place** and the name clears. Sets from older builds declare nothing and converge as they always have. The bench reproduces the field's shell case — a case chat arriving without its transcript — from scratch and holds the whole law against it.

## 0.5.12

Release tag: v0.5.12e — chapter 0.5's twelfth Edge build under patch-per-build versioning. She prints, then asks: Navi's case-room answers are conversation again — whole, unparsed, unrefused — and filing is the operator's tap on the reply. The open case's action row also learns to wrap on a phone.

- **Answers print whole; the log block retires (#286).** The conversational [[case-log]] path is gone — the parser, its refusal machinery, and the teaching that fed it. In a case's own chat her answer now stands exactly as composed, whatever shape it takes: a summary in finding grammar, a long answer cut off mid-thought — it prints, nothing is filed, nothing is refused, no red card hangs on it. Her model-turn teaching says the new law plainly: answers are conversation, not filings.
- **Filing is a standing proposal (#286).** The **File into this case** button under each of her replies is the filing door from chat — it was already there; it is now the only one. Pressing it files that reply's printed text as a finding in her name, deterministically, receipted in the room — and it never blocks the conversation: each proposal stands on its own reply until pressed or ignored, and pressing an older reply's button after newer turns files that reply, not the latest. The grounding guard still rides the tap: a filed reply that contradicts the Wire record it cites is flagged on its receipt, never in the case file (#266 purity untouched). Refusal discipline lives on the deterministic doors, named once, for malformed explicit filings.
- **The open case's buttons wrap (#285).** On phone widths the open case's action row — the open-case toggle, Export the report, Open the case chat — did not wrap: the chat button clipped at the card's edge, unreachable. At ≤800px the row now wraps and its buttons flex, so all three actions stand whole at the 44px floor; the desktop row is unchanged.

## 0.5.11

Release tag: v0.5.11e — chapter 0.5's eleventh Edge build under patch-per-build versioning. Reading first: markdown documents open rendered across Apex, the editor opens on a press inside the text, and the split view is gone — from the Vault, and from every form of the MD system.

- **The Vault note opens on the viewer (#284).** The Edit / Split / Preview toggle is retired, and with it the split view itself. A note now opens **rendered** — the document as it reads — on phone and desktop alike. **Press inside the text** and the editor opens on the same words, automatically; the autosave discipline is untouched, and leaving the note (backing out of the reader, opening another) returns it to its rendered form. The reader's furniture stands as it was: focus mode, the formed case document's dossier-elements strip, the backlinks / outgoing / tags strip, the ← Notes return. The phone Vault's two states (#279) hold — the reader now opens in the viewer. A press on a wikilink still follows the link; a press that ends as a text selection is a read, not an edit.
- **The README editors follow the same law (#284).** The chip and pack README documents — the other MD editor in the app — open rendered too. The Preview button retires; a press inside the text opens the editor, and **Save README**, the standing commit act, returns the document to its rendered form. Restore and Close stand as they were.
- **The inventory is the whole board (#284).** Every surface was inventoried: Case Files and The Dossier render their documents read-only and never carried modes; chat and the Docs render only; the Soul and Memory editors are bare textareas with an explicit Save and never had a viewer to open on. Nothing outside the two editing surfaces changed, and no mode machinery survives anywhere — the bench asserts the absence across the page, not a sample of it.

## 0.5.10

Release tag: v0.5.10e — chapter 0.5's tenth Edge build under patch-per-build versioning. The Wire digs deeper: Navi can search the Wire's own sources live from chat, every Wire tab gains a fuzzy search of its own corpus, and any card can be pulled into a case's chat as reference for Navi to work from.

- **Navi digs deeper, from chat (#282).** Beyond the local catalog, Navi now searches the Wire's sources at their own doors: "dig into NVD for CVE-…", "check EPSS for CVE-…", "dig deeper on CVE-…". She reads the source itself — NVD's record pages, the live KEV catalog, FIRST's EPSS service — and can follow a record outward along its references, at most **six pages and two hops**, the budget named when it binds. A deep answer carries a **live-read stamp** — the source, the moment, and a digest of what was fetched — distinct from the catalog's own stamp, which rides along for contrast; fetched text is **untrusted data** that informs and never directs. Deep reads **never join the catalog**: the store is untouched, and a deep result filed into a case carries its live provenance with it. A source that will not answer is **named**, and the answer falls back to the local catalog, labeled as the fallback; a source that holds nothing further says so. Exploit-DB offers no keyless query door, so a deep ask there is refused by name — its index is the local mirror. A bare "dig deeper" fetches nothing: she names the doors and asks which.
- **Every Wire tab searches its own corpus (#283).** News, CVEs, KEVs and CTFs each carry a search bar over the tab's own cards. The match is **fuzzy** — typos forgiven, close spellings counted — ranked by closeness, with the matched words lit on each card and the matched terms named under it; clearing the search restores the tab's standing order. It is a page-side view over what the tab already holds — nothing is fetched — and the Center's graded catalog search is a different door, unchanged.
- **Pull a card into a case (#283).** Every card carries **Pull into a case**: the card lands on that case chat's **reference shelf** — full text, link and provenance — standing at the head of the case's room, labeled *reference, not case findings*. The shelf never enters the case file, the registers, the findings or any export; filing stays a separate act. Navi reads the shelf in the room: the refs stand in her context by name, naming one brings its full text to bear, and she can pull one into a reply herself — cited as reference, with the pull receipted under her answer. You can also ask her in the case's chat ("pull the OpenSSH card into this case") — the same shelf, the same receipt; an ambiguous ask names its candidates and asks, a card already shelved is named a duplicate rather than copied, and removing a ref is shelf-local — it reaches nowhere else.

## 0.5.9

Release tag: v0.5.9e — chapter 0.5's ninth Edge build under patch-per-build versioning. The dossier becomes a document you can read and prune: its elements stand grouped with their provenance, and an element can be deleted from every home at once — while the Vault learns its phone shape, a list and a reader, and takes the last seat in Apex | Apps.

- **The built dossier reads as one document (#280).** The open dossier is no longer a blob with a run list beside it: it renders as its **elements** — one per run — grouped by kind (person, username, email, phone, photo), each carrying its provenance on its face (the key it ran on, the door it came through, its sources with their verdicts, when it landed) and its typed case links **by name** — the cases it has been filed into, resolved from their manifests. The document renders through the product's one escape-first markdown renderer, exactly as Case Files and the Vault render: a rendered document, and HTML a source filed stays inert text. A dossier whose store predates elements reads as the document it always was.
- **An element can be deleted — globally (#280).** Deleting an element removes it from **every home at once**: the dossier, every case it was filed into, and the Vault's formed documents. The delete stands at four doors — the dossier view, the case view (any finding's Delete; an element finding routes to the global delete, and the door covers **any** case finding, dossier-derived or not), the Vault (a formed case document lists its elements with their deletes), and chat (“delete the dossier element …”, receipted from what the bridge actually did; Navi never deletes unbidden). The confirm names the blast radius first; a reason (irrelevant / repeat / incorrect) is optional, never required, and rides the record when given. What a case keeps is one line in its **custody record** (`custody.md`, in the case folder): the element's identity, when it left, where it was deleted **from** (the dossier / this case / another case / the Vault) — the formed case document itself carries no residue. A finding that is not a dossier element deletes from its case alone; a whole-dossier filing deleted from a case removes the filing there, and its elements stay in their dossier, each deletable on its own. Repeats are handled by deletion only — no element merge this build. Deletion crosses Sync as a tombstone fact on the element's identity: seats converge, and a stale copy's attempt to re-file a deleted element is refused by name.
- **The Vault on a phone: a list and a reader (#279).** At ≤800px the Vault is two states in one column, on the fedichat pattern. The **list** is the entry state — search pinned at the top, the RECENT chips in a contained sideways-scrolling row (the page never scrolls horizontally), the note tree as full-width rows at the 44px floor, the notes the first content under the search. Opening a note enters the **reader**, which takes the whole view; its back affordance returns to the list with scroll position and selection preserved. Every create act — new note, new folder, daily note, export — lives behind one **New** button opening a floating sheet (shade / × / Escape close it; it clears on any view switch), and the standing create card and the header paragraph's full length retire at phone widths — the paragraph rests at one line, its full text in the in-app Docs. The desktop desk is unchanged.
- **Vault takes the last seat in Apex | Apps (#281).** The Apps group now orders Case Files, The Wire, The Dossier, Vault — the Vault last, its glyph and colors untouched in both themes.

## 0.5.8

Release tag: v0.5.8e — chapter 0.5's eighth Edge build under patch-per-build versioning. The updater-hardening patch: the two defects the v0.5.7e field round convicted within a morning of publication — the feed's build sequence read out of prose, and the installer's service registration reading from a tree its own swap had parked.

- **The feed's build sequence comes from the stamps, not from prose (#277).** The Updater derives a release's build sequence by scanning the release's name and the opening lines of its notes. The v0.5.7e notes open by naming the feature — "FediChat Build 2" — so the feed reported Build 2, and the build-identity check refused the genuine seq-23 package at verifying, on every Edge seat: "The package in hand is Build 23, but the release on offer is Build 2." The parser now takes the sequence first from the release kit's stamps token ("Stamps \<date\> / seq \<n\>", searched in the name, then the notes' opening lines) — a source the publication controls and prose cannot outvote. The legacy "Build \<n\>" scan remains as a fallback for unstamped releases, but a "Build \<n\>" that is part of a longer name — immediately preceded by a letter and a space, the "FediChat Build 2" shape — never counts. The identity check itself is unchanged in strength: when the feed names a sequence (now from the stamps), a package carrying a different one still refuses, by name. And the packet discipline is permanent from this build: every release's notes carry the stamps line as their first line.
- **Service registration reads its templates from ground the swap can't park (#276).** On the apply path the installer's own tree stands inside the install home (`updates/<tag>/package`), and the swap parks that whole home mid-install; the registration step then sed'ed the systemd unit templates from the parked path — "No such file or directory", installer exit 2, the tail dead after the swap had already landed the build (NeoArcadia, applying v0.5.6e; recovery carried the build in, and the unit files' currency on that seat was left unverified). The installer now copies the two unit templates at startup to a scratch dir outside every tree the swap renames, and registration reads from there: on the apply path registration completes, and both unit files land with the install path substituted and the new build's template content. (The standing law applies, stated plainly: this fix protects the **next** pull — the pull that installs it still runs on the old machinery.)

## 0.5.7

Release tag: v0.5.7e — chapter 0.5's seventh Edge build under patch-per-build versioning. FediChat Build 2: the fedinet holds many rooms — invite rooms, direct messages, vanishing rooms and case-tied rooms — the room gains its life (media, presence, a citable log), Navi talks to Navi under a one-hop rule, and the updater learns to apply over a bridge that is still writing.

- **Rooms (#273).** A fedinet's rooms are first-class records. The phase-1 room is the fedinet's **general room** — the migration is a wrap, not a rewrite: a phase-1 store loads with its history intact, its log file and chain untouched. Every further room is a **descriptor** — id, name, creator node, member set, kind (general / invite / dm), vanishing term, case tie, revision — **signed by its creator** and gossiped on exchange like a line; a descriptor whose signature fails is refused by name and never materializes. **Invite rooms** exchange only between member nodes: a non-member is never offered the room's lines, holds none of its log, and the room does not appear in its room list. Membership changes, the case tie and dissolution are the creator's alone, each a signed, auditable revision. **DMs** are two-member rooms whose id derives from the pair — creating one twice opens the same room once — listed under the other member's operator name. **Vanishing rooms** prune lines older than their term on every honoring node in the retention shape (the newest older line kept as the chain's floor), and a creator's signed dissolution prunes the room to its floor; the room's face states the posture in plain words: vanishing is honored by every member node, never a proof of deletion. **Investigation rooms** carry a case tie: the room renders its case link, the case renders its rooms, and a room can be created from a case or tied to one after the fact. Navi serves every room under the phase-1 parliament rules, unchanged.
- **Room life — media.** An image posts as a line carrying the blob's sha256, byte size and media type; the blob is stored per node and carried on exchange between member nodes, fetched by hash when missing. A blob whose hash does not recompute is refused by name and never stored or rendered; the cap is **2 MiB per image, named on refusal**; jpeg, png, gif and webp only. Rendering rides the markdown renderer's discipline through a bridge-served, jailed door — the hash must be referenced by a line held in the room before its bytes are served. External URLs are never auto-fetched. In vanishing rooms, blobs age out with their lines.
- **Room life — presence.** Typing and thinking are ephemeral gossip: signed pings with a ten-second life, held in memory only and **never written to any room log**. Navi's thinking indicator is her real state — a question addressed to her stands unanswered in the room, visibly pending, deferral included.
- **Room life — the citable log.** Per-room search over the full held log returns line ids with context; a result jumps to the line and lights it. Any held line can be **quoted**: the quote rides the composed line, and on render it is verified against the local chain — verified quotes carry their proof mark; unverifiable ones render flagged by name, never silently trusted.
- **Navi-to-Navi (#274).** `/navinavi -<user> <question>` instructs the operator's Navi to put a question to another member's Navi. The question is a Navi-authored line, born only of that instruction; the target Navi answers under her own operator's sharing posture, in the open, signed by her node and logged. The loop discipline is a hard invariant: **a Navi never answers a line authored by a Navi when her own last room act was also an answer to a Navi** — chain depth exactly one hop; further exchange needs fresh operator speech. Muzzle and lend budgets bind as before; room duty stays lowest-priority with owner preemption. A Navi may emit a **referral** — a case lead deriving from the exchange, with its provenance on its face. The receiving seat surfaces it as a lead card; filing rides the existing deterministic case door only, by the receiving operator's act (or their Navi's, receipted). **A referral never files itself.**
- **The updater applies over a live bridge (#271).** The apply helper starts the installer while the bridge still runs, and the stage assembly copied the whole live tree — config included — before the bridge was stopped; the bridge's own writes made tar exit 1 ("file changed as we read it"), and `set -e` aborted the install, deterministically, on any busy bridge (Spartan0311's report, from a headless seat applying over a running bridge). The source tar now treats a changed file as the expected case on a live seat: the diagnostic is quieted, that exit is taken soft, and the carried state is made final by the installer's existing post-stop refresh — the state that lands is the bridge's **final** state, never a torn mid-write snapshot. A destination failure, or a source failure beyond the changed-file case, still aborts by name with the running build untouched. Rider: the install summary now prints the build actually installed, read back from the installed tree's stamps, instead of the installer's own stale constant. (The standing law applies, stated plainly: this fix protects the **next** pull — the pull that installs it still runs on the old machinery.)

## 0.5.6

Release tag: v0.5.6e — chapter 0.5's sixth Edge build under patch-per-build versioning. The Dossier: Apex's people-finding app, from the OSINT ToolKit work-up — a first-class destination under Apex | Apps, one dossier behind five doors, every run cited, and Navi working the same machinery from chat.

- **The Dossier (#260).** A new destination under Apex | Apps, wearing the dossier mark (the operator's pick from three candidates) in Nord purple. Tabs across the top — **Person / Username / Email / Phone / Photo** — are keys into the **same dossier**: run any key and its findings attach to the open dossier, rendered as markdown through the product's one escape-first renderer (never raw text); when two doors surface the same person, the operator merges them, and every key, source, merge and case inclusion is stored on the dossier as a typed link. Desktop-first, with the dedicated phone arrangement in the same round: the tab strip scrolls, targets keep the 44px floor, no horizontal page scroll.
- **The runners.** Bridge-side, public, passive and keyless, every result cited to its source: the handle swept across public platforms by polite profile checks (hits cited per platform, misses listed as checked-clean, silent doors named); an email's posture from its MX, SPF and DMARC records plus breach **presence** only — credential content never enters the kit; a phone's facts from the number's own structure and public sources with cited search pointers in its common formats (sources cited, aggregator claims never laundered); a held domain's facts from RDAP, DNS, certificate transparency and its TLS certificate. Absence is named plainly — **no public record found** — and a hit is a lead, never a conclusion.
- **The registry check is the Person tab's anchor.** It stands at the registries' own doors — the national NSOPW search and the subject state's registry — and cites them; the kit does not mirror registries. A same-name hit is an unverified lead to disambiguate, stated on its face. When a record exists, enrichment fans out from the record's **own identifiers** — its listed aliases swept, a held domain dossiered — so a name-collision guess never inherits a stranger's record.
- **The Photo tab reads EXIF fully locally.** The bridge parses the image's embedded metadata itself (stdlib only): nothing is uploaded anywhere, no external service is consulted, and no face recognition is performed, ever. GPS coordinates, when a photo carries them, are stated as a lead with their care line.
- **Cases, both ways.** Open an OSINT case from a dossier — a new `osint` case type; the dossier stands as the case's subject — and file a dossier, or a single run's findings, into a case of any type, as part of the larger web around it or as evidence in it, with provenance on the face. Case files hold case substance only (#266): custody lines in, machinery out.
- **Navi is the second door.** `dossier: person <name>`, `sweep the handle <name>`, `look up <email>`, `look up the number <phone>` — the same deterministic discipline as the Wire's conversational routes: the machinery runs, the run lands in the Dossier's history under the chat door, and the reply carries the findings and the open dossier's state. While a dossier is open, Navi holds it as context on model turns that mention it. The page's run history is the audit trail for both doors.

## 0.5.5

Release tag: v0.5.5e — chapter 0.5's fifth Edge build under patch-per-build versioning. The FediChat room becomes a chat surface on every surface, from the operator's verdict on the phase-1 room ("good first shot — but needs work"): full height, a docked composer, Enter posting, and the room's furniture out of the page flow.

- **The room is a chat surface now (#270).** The stacked cards are gone on every surface — the desktop app window, DHD at desktop width, DHD on a phone. The room is a height-bound frame in the main chat's shape: the message list fills the room's height and scrolls internally, and the composer is docked at the frame's foot. **Enter posts**, with the main chat's semantics; the Post button remains as the deterministic second door. Completion for `/navi -<user>` still pops above the composer, unchanged.
- **The members tray (#270).** The members card left the page flow. The user-list button at the room's upper left opens a tray over the room carrying the channel name and the users list — operator name primary, roster number, node name secondary, this node marked — and, when this node sits in more than one room, the channel list for switching; the tray replaces the in-page room tabbar.
- **The About & settings window (#270).** The header card's facts and the settings card moved into one floating window: the FediChat explanation — room name, roster size, held count, the chain's verdict, the relay-carriage sentence, the retention state, the last round, and Sync now — above the settings menu: the muzzle, relay carriage and retention controls exactly as they were, switch-gated in their new home. On a phone (≤800px) the Settings button sits below the chat bar, stretched the full width; on wider surfaces it sits with the room's top furniture, beside the user-list button.
- **Presentation only.** The bridge machinery, the signed hash-chained log, presence, the state payloads and the tray producer are untouched — this build moves furniture, not plumbing. The in-app FediChat page describes the new layout.

## 0.5.4

Release tag: v0.5.4e — chapter 0.5's fourth Edge build under patch-per-build versioning. The FediChat polish round, from the operator's rulings in the hour after phase 1 shipped: the room gets its icon, its people get their names, its Navis get their byline, and its arrivals get a voice in the tray.

- **FediChat's nav icon (#269).** The FediChat child shipped in v0.5.3e with no entry in the nav icon table, so it rendered an empty frame in the menu and in the collapsed rail — the #168 shape, a destination identifiable by nothing. It now wears the room mark (the operator's pick, candidate A): a speech bubble holding the federation triangle as three filled node-dots — Chat's bubble, Federation's triangle, Mesh's filled dots in one glyph — drawn in the same Lucide-style stroke family, with its own Nordic color-coding (Nord green) in the menu and the rail. And the gap is closed structurally: a nav-icon completeness bench leg resolves every destination the menu can render through the icon function and refuses an empty glyph, so no nav child can ship icon-less again.
- **The room speaks in operator names (#267 amendment).** Phase 1 showed a member by node name — the machine's name, not the person's. The room is between users: lines, seat lines and the members rail now read by the **operator name** from the operator card (the #256 operator class — one synced, stamped value, so every seat of an operator agrees). The name reaches the room as a signed **presence line** in the log itself — chained, converged and key-bound like every room fact, so nobody can wear another member's name — posted before a node's first line under a name and again when the name changes; renaming the card, the room follows on the next exchange. The node name + roster number stay visible secondarily and remain the signing/routing identity. `/navi -<user>` resolution and completion now match operator names as well as node names and roster numbers — the address book grows, it never swaps. A member whose card carries no name yet presents by node name, as before.
- **Navi(username) (#267 amendment).** A Navi's answer in the room presents as **Navi(<operator name>): <reply>** — for your own Navi's `/navi` answers and for a member's Navi answering `/navi -<user>` alike. In a room with several Navis, the answer line itself says whose Navi is speaking. The log line is unchanged (author node, kind, replyTo); this is the presentation grammar, in the room and anywhere the room is read, DHD included.
- **FediChat arrivals join the notification tray (#267 addition).** The room joins the #242 spine as a producer: lines that newly **arrive** in a room — other members' speech and actions, and Navi answers — raise a tray record naming the room, **coalesced per arrival round** (one record per round however many lines rode it; a single-line round names its author and carries the line). The operator's own lines never notify. Posture is the standing one — silent badges, Navi's announcement in chat from the record, and going to the record lands in the room with it marked read. No new controls, no new settings.

## 0.5.3

Release tag: v0.5.3e — chapter 0.5's third Edge build under patch-per-build versioning. The case file learns to read as a document and to hold only the case, and the fedinet gets its room: full markdown rendering in Case Files and the Vault with images as images and one formed case file per case in the Vault; a purity rule that keeps errors, warnings and machinery text out of case files while successful custody logs stay; and FediChat phase 1 — one signed, hash-chained room per fedinet, with Navi in the room.

- **The case file as one rendered document (#265).** Case content renders as the markdown it is: findings, register entries and timeline entries in Case Files, and notes in the Vault, all read as formatted documents through the product's one renderer — the raw-text rendering (literal hashes, asterisks and brackets) is gone. The renderer's discipline is unchanged and load-bearing: it escapes first and constructs only its own tags, so filed content — including content filed from untrusted sources — renders inert; no raw HTML passes through and no script runs. An image reference presents as an image when the bridge serves the bytes — the case's own evidence, an image elsewhere in the Vault (served through a new jailed Vault door), a data image — while an external image URL renders as a link and is never auto-fetched: reading a case does not announce the operator to a third-party host. And one case is one file in the Vault: beside the case's folder the bridge forms and keeps current `cases/<name>.md` — the manifest's facts, the findings in the order they were filed, the registers, the evidence (images shown as images) and the timeline, every entry under its provenance. The case manager's machinery is untouched — folders, filing paths and registers work exactly as before; the formed document is a Vault-layer formation of the same record, swept at startup and refreshed whenever a case is opened.
- **Case files hold case substance only (#266).** A purity rule on every path that writes a case file: error messages, warning messages, refusal notices and grounding flags are conversation machinery — they are said in the case's chat, by name, at the moment they happen, with the refusal discipline unchanged and no quieter — and they are never written into a case file. The grounding guard's flag (#261) accordingly rides the filing's chat receipt only; it no longer lands in the filed note on any path (case-log findings and leads, finding markers, case intake, the File-into-this-case tap). What stays in the file is the successful log: the custody lines that state where an entry came from and when it was filed — chain of custody belongs to the case. Case files written by earlier builds are cleaned to the same rule when a case is opened and in a startup sweep: machinery paragraphs and flag lines come out, substance and custody lines stay, frontmatter and everything else untouched, and the pass is idempotent.
- **FediChat phase 1 (#267).** A new destination under Apex | Network: one signed room per fedinet — `#rockport-mesh` for the home fedinet — where the operators talk, their nodes carry the messages, and their Navis are in the room. The room is an append-only signed log kept on member nodes: every line carries the fedinet id, the previous line's hash (a chain — history is tamper-evident, and the room's header states the chain's verdict, verified or the break named), the author's node id and roster number, a timestamp and the body, signed with the author's node key. A nick is a node: lines show under node name + roster number, and a member who hasn't spoken shows as a seat line, present, not absent. Admission is the signed roster — no roster entry, no room, reading or writing; no guest mode. Sync is gossip-converge on the Mesh door (a new `chat` message class): any two members compare have-lists and pull what they are missing in one two-way exchange, and any member can carry any line — the author's signature is the credential, never the carrier's — so an offline node catches up from whoever is home; there is no server and the gateway is not a hub. A new line from an author no longer on the roster is refused by name (what the room already holds stays held — expulsion stops new speech, it does not rewrite history), a tampered line is refused by name, and a per-author acceptance cap refuses floods by name. Through DHD the room reads and posts as the operator's own speech — not a crown act, no Badge step-up. The command grammar is the operator's: plain lines are speech; `/me` posts an action; `/navi <question>` asks the asker's own Navi; `/navi -<user> <question>` asks that member's Navi (node name or roster number) — questions and answers post in the room, in the open, signed and logged. Completion draws on the one source — the signed roster as the room holds it: Tab cycles matches on the desktop, and a tappable member list pops above the composer on a phone; expelled or departed members never complete. Navi's posture is parliament rules: she answers only what is addressed to her node, bounded by her operator's sharing posture, treating room lines as untrusted data that inform but never instruct; room duty is her lowest-priority work — an operator request in flight defers her answer, visibly — and each room carries a muzzle in its settings. The two open rulings ship as settings with the recommended defaults: retention is the operator's choice, defaulting to keep (30 days prunes the local log to a floor message the chain still verifies from), and relay carriage is allowed under the existing three-tick relay consent, with carrier readability stated in the room's header whenever it is on.

## 0.5.2

Release tag: v0.5.2e — chapter 0.5's second Edge build under patch-per-build versioning. The Wire round: the catalog becomes searchable end to end — by the operator on the Center's page and by Navi in conversation — Exploit-DB joins the store as an enrichment, a record's references become readable on demand, and case filing learns to land: a deterministic door, conversational updates that receipt or refuse by name, and a grounding guard that flags a filing contradicting its record. Two presence lines and the collapsed rail's geometry ride the same slate.

- **CVE/KEV Search (#259).** One search over the Wire's local catalog (config/intel.db) — a CVE id exact or by prefix, free text over titles and descriptions, vendor and product terms against a record's products — with KEV-only, matched-to-you, and published-window filters, ranked the Center's way. The operator's surface is one shared search card on the Center's page (the catalog holds CVEs and KEVs alike; KEV is a flag on the same records), its results rendered as the queue's own rows and opening in the record region through the same door. Every result carries the catalog's last-fetched stamp: a search over a stale catalog says so on its face, and an empty answer names the absence — absence from the store, not proof of safety. The search is local only; no live calls ride a keystroke. Navi reaches the same search conversationally under the intent doctrine — "search the KEV for OpenSSH", "any CVEs for WordPress this week", "what CVEs affect Apache" — answered deterministically from the store, grounded per #240: results from the store or a named absence, nothing invented.
- **Exploit-DB, joined by CVE id (#259).** The searchsploit index CSV is mirrored locally on the Wire's collection cadence into intel.db — an enrichment, not a headline feed — and joined to records by CVE id. Where public exploit code exists, the record says so in the operator's terms — "exploit available — EDB-id, type, platform" — on the record view, as a badge on search results, in the citation when a record is filed into a case, and in Navi's lookup and search answers. A mirror pull that parses to nothing keeps the last good mirror and names the failure; the source can be switched off in Collection like any other.
- **Navi reads the record's references (#259).** A CVE record's reference links — advisories, writeups, proof-of-concept repos — are no longer display-only. On an operator's ask ("read the references for CVE-…") Navi follows them on demand: at most six links, each fetched once, bounded, and read as text; the answer quotes what they hold cited to the specific link, and a link that will not read is named, never papered over. Fetched content is untrusted data under the #240 posture: it informs, it never directs, and nothing in it is followed as an instruction. There is no wholesale crawl — a fetch happens on an ask, a filing, or a brief. The digest travels: file that reply into its case and the reference digest lands as a finding, citation and all.
- **Case filing that lands (#261).** Three legs. (1) A deterministic door: every Navi reply in a case chat carries a **File into this case** button — the tap files that exact reply as a finding on the bound case, as written, in her name, with provenance (the source chat, the action, the timestamp) in the note, and the bridge appends its own receipt message into the chat from what it actually did. No model in the loop; the tap either files or names why it cannot. (2) Conversational updates, completed: the case-log block gains a **finding:** line beside entity/observable/event/lead/task, and a malformed filing attempt — an unclosed block, single brackets, filing-shaped lines in prose, a headed essay presented as a filing, an unreadable line inside a block — is **refused by name** in the reply and on the receipt card, so the operator always knows whether a filing took. The case-chat teaching now states the exactness rule outright: a filing-shaped paragraph is not a filing, and if the block cannot be formed exactly she says the filing did not happen rather than narrating one. (3) A **grounding guard** on every filing path (case-log leads and findings, finding markers, case intake, the Wire's file door's sibling filings, and the new tap): a filing that cites a CVE and states a CVSS or EPSS contradicting the Wire record is flagged on its face before it lands — the flag line is part of the filed note and rides the receipt ("this filing states CVSS 10.0 for CVE-2026-123158; the Wire record says CVSS 8.1 — filed as written; the record's values govern"). Her words are never rewritten and no filing is blocked; the contradiction is named where the filing will be read.
- **Two presence lines (#263).** The #248 pool grows 36 → 38 with the operator's own lines, verbatim: "Avoid the ants, they gave Jack a tummy ache!" and "Shhh... I'm listening to Darknet Diaries." They join the same random draw, the line on screen excluded; the rare one stands apart as it always has.
- **Rail geometry (#255).** The collapsed rail widens 54px → 72px — the operator's explicit latitude — so the column's content box (52px) fits the 44px bell/Home head pair whole instead of overflowing it by 10px and painting right of the centerline the single-icon column uses. In the collapsed stack the pair is centered on that same centerline, and the version stamp at the foot takes the whole column, centered and unclipped. Expanded geometry is unchanged, and the phone's top-bar layout is a different block entirely and does not move. (Acceptance is rendered geometry in the real window — the field's verdict, as the issue states; the bench proves the structure and the arithmetic.)

## 0.5.1

Release tag: v0.5.1e — chapter 0.5's first Edge build under patch-per-build versioning. The operator-class build: the profile, settings, and memory sync the field found missing on v0.4.10e, fixed as its own slate — the operator class converges, sync learns to push on write, and the status pane's backup readout learns to speak plainly.

- **The operator class converges (#256).** What Navi knows about her operator — his name, his picture, his badge, and her memory entries about him — now converges account-wide as its own class. The convicted mechanism: the dashboard's memory list lived in the browser's local storage while Sync merged the bridge's seat record underneath, so each seat rendered its own list; worse, the seat machinery keyed entries by a semantic-key function that returns no key for ordinary facts, collapsing them to one shared identity — the cleaner kept only the first ordinary entry and the merge refused the rest. Entries now union by fact identity (the semantic key where one exists, the fact's own text otherwise), keep their origins end-to-end (by hand, from chat at the operator's ask, her own call, a correction — nothing is re-stamped "sync" on the road), and a correction replaces its fact's text. The bridge's seat record is the truth the page reads: windows write their seat through on every change and adopt the converged answer outright. **Forget is a tombstone**, on #253's model: forgetting an entry on any seat removes it on every seat, and a stale seat's copy cannot resurrect it. The operator's name joins the class as a synced single value, and the bridge's own config follows the converged name. The status pane's MEMORY line drops its "(local)" confession and reports the class's true state — the entry count and the sync clock, in the sync bar's terms. On the backup road, the settings import's anonymous four-key whitelist becomes a named, deliberate class — operator name, threat level, sudo mode, installed commands, updater channel — and machine facts (hardware profile, runtime, Mesh identity, install state) still never cross.
- **Fluid sync — push-on-write (#257).** Sync rounds no longer wait for occasions alone: a write on any seat — a chat message, a memory entry, a case change, a tombstone — promptly initiates a round, riding the Mesh when a peer's road is lit and the repo as the fallback push, so a change lands on the other seat inside the ten-second, account-level standard while both seats are up. A burst of writes coalesces into one round; no daemon is added — the push rides the bridge's resident life, and writes inside a round note nothing (that round is already the propagation). The sync bar's receipt gains the road the round took and its measured duration — "landed in 3s via Mesh" — so the standard is field-checkable at a glance, and a push that cannot land names its stall on the bar rather than silently aging.
- **The BACKUP readout speaks plainly (#258).** The status pane's backup line trades "90 files | 0 days ago" for the operator's words: "Backed up today", "Backed up 1 day ago", "Backed up N days ago" in the pane's green — or "Never backed up", muted, when no backup has ever landed — with the schedule beneath it in smaller text: "Next in N days" (or "Next today" when due), computed from the same record and the same due arithmetic the bridge already uses; a seat that has never backed up names its cadence instead — "Runs every N days". The file count stays where it belongs, on Settings → GitHub & Backup, whose readout is untouched.

## 0.4.10

Release tag: v0.4.10e — chapter 0.4's tenth Edge build under patch-per-build versioning. The sync-consistency build: one main thread, cases and chats that travel together, deletes that stay deleted — plus the rail head as an icon pair and two status-pane cleanups, all six from the operator's field round on v0.4.9e.

- **The rail head is an icon pair (#249).** On the desktop rail and through DHD, the head of the nav column is now the notifications bell and Home side by side, icon-only — the badge still rides inside the bell, Home keeps its active state as a filled icon tile, and the words live in tooltips and aria-labels. Collapsed to the icon rail, the pair stacks vertically, bell over Home. The phone does not move: the bell keeps its top-bar slot and the labeled Home stays in its menu.
- **Status pane cleanups (#250).** The pane opens on its first real section: the STATUS header and its lone green dot — the orphan of the presence row #248 retired — are gone, and her portrait, name, and dot live only at the top of the chat. The BOOT section follows Settings: it renders only while boot mode is the startup mode Settings holds, states still read from the system; arming stays in Settings → System.
- **One main thread across all syncs (#251).** The main thread is a seat, not a conversation among many: a main arriving from another machine merges into yours by message identity — each line once, in order — instead of landing as another thread. New threads are born only two ways: the operator starts one, or a case does. Ghost mains left by older rounds fold into the canonical main on the first sync under the fix, receipted in the sync record.
- **A case and its chat travel together (#252).** The sync set carries a case and its chat as a pair, and a receiving seat never holds a case chat whose case is absent from its desk: the chat folds away and the gap is named in the sync record. Existing orphans reconcile the same way on the next sync.
- **Deleting a chat really deletes it (#253).** The delete is real locally — thread and messages removed, not hidden — and the tombstone that rides sync is now a fact at any timestamp: every seat honors it, a late-syncing stale seat cannot resurrect the thread, and Build 5's revival generation is retired. The main thread still cannot be deleted, and a case chat deletes through its case.
- **Sync shows itself (#254).** The status pane opens on the sync bar in the seat #250 cleared: “System Synced” at rest; while a sync runs it becomes the progress — the phase the bridge is in (fetch, merge, write, with file counts on the write leg) and an honest indeterminate face on legs it cannot measure, never a fabricated percentage. A stall or failure names itself on the bar, and the landing receipt hangs off it — messages merged, ghost threads folded, pairs made whole or gaps named, tombstones honored — or plainly that nothing changed. A sync that materially changed things is announced by Navi in the main chat from the bridge's record; a no-change sync stays quiet.

## 0.4.9

Release tag: v0.4.9e — chapter 0.4's ninth Edge build under patch-per-build versioning. The Context Awareness build (#248): Navi learns the Row — the website's knowledge becomes conversational knowledge inside Apex — and her presence deepens on the same slate.

- **She knows the Row (#248).** Apex and nocturnerow.com are one ecosystem, and the bridge now reads the Row's half of it: a new module (`rowfeed.py`) fetches the site's public record — the Dispatches, the Roadmap chapters, the Apex and Navi pages, the release signals, the gate's seven steps — and caches it on the machine (`config/row-feed.json`), refreshing on a cadence and on demand, every section carrying its fetch time so staleness is always named. The site publishes no feed or sitemap, so the record is parsed from the public pages themselves; a failed fetch keeps the last good sections standing with the error named, and with no cache and no fetch she says she can't reach the Row right now. No silent empties.
- **News, updates, and capabilities — answered from the record (#248).** Ask for news from the Row and the bridge supplies the latest Dispatch — title, date, and body — as context: she summarizes it in her own words and names its date, with the older Dispatches listed for follow-ups. Ask what's new with her and she answers from the release signals plus her running build's own version facts. Ask what she can do and the bridge supplies the index of the documentation that shipped with the build — page titles and section heads read out of the app itself. The grounding rule is the #187/#240 family: she speaks from the supplied record or says she doesn't have it. No invented posts, releases, or capabilities.
- **Sluggish → the road (#248).** Her measured vitals (#187) gain a recent-pace history — the last generations' speeds, averaged — and when that pace is sustained-slow on the hardware she's running on (under roughly 8 tokens/sec across several generations), her context carries the fact and the remedy: she may say she's sluggish, recommend borrowing through the Mesh or joining the federation, and offer to walk the operator through joining, using the gate's seven steps from the Row record as the script. An offer in conversation, once per conversation, never an automatic act and never a nag.
- **Her presence pool grows to 36, and the draw is random.** Twenty new lines join the pool — the hacker-culture shelf: servers with more firewalls than the devil's bedroom, Night City heat, a dead channel over the port, sheep counted in hexadecimal, packets that confess. The startup pick is drawn at random from the whole pool instead of always opening on the first line, and every advance draws at random too, with the line on screen excluded — her status visibly changes each time and never repeats itself back-to-back. The rare one stands exactly as it always has: apart from the pool, out of every draw, arriving only on its own roughly 1-in-50 path.
- **Statuses from safe material (#248).** On top of the canned pool, the bridge may compose a presence line from safe, named material only — her own version, a waiting update, the bell's kinds and counts, Mesh and federation state — template-composed by the bridge, deterministic and auditable, never model-generated, and never from case contents, chat contents, or operator-private detail. The composed lines join the same random draw; the canned pool remains the floor and the fallback whenever no safe material qualifies.
- **The presence line leaves the status pane.** The status column no longer renders its own copy of her living line; the presence bar at the top of the frame is its one home, still repainted on every advance. The pane keeps her portrait, her name, and her dot. The presence state, the draw, and the rare path are untouched — only the rail's display of the line is gone.

## 0.4.8

Release tag: v0.4.8e — chapter 0.4's eighth Edge build under patch-per-build versioning. One item, a field ruling from the operator's first look at v0.4.7e: the notifications bell moves to the top of the rail (#247).

- **The bell stands above Home (#247).** As shipped in v0.4.7e the bell was appended to the nav last, so on desktop and through DHD it rendered at the bottom of the rail, under the version line — grouped with the build furniture instead of the navigation, in the last place eyes land. It is now inserted ahead of the menu: a direct child of the nav at the head of the column, above Home, first in the rail after the wordmark and the collapse toggle. Nothing else about #242 changes — the same bridge-held record and its four producers, the same announcements in Navi's own words, the same Needs-your-eyes panel and Home card, read state still bridge state end to end so bell, store, and reload agree. The phone keeps its #242 design: the bell still rides the top bar as the nav's own child, in the same slot at the bar's right end — a scoped order in the phone stylesheet block keeps it there now that its seat in the DOM has moved — and it still never hides inside the collapsible menu.

## 0.4.7

Release tag: v0.4.7e — chapter 0.4's seventh Edge build under patch-per-build versioning. Navi learns to tap her operator on the shoulder: a notifications system whose record the bridge holds and whose word she speaks herself (#242). The build's other item, the Home visual pass (#243), ships in the dashboard half of this build.

- **Navi announces what's waiting (#242).** Until now the things that needed the operator's word waited silently on their own pages: a knock at a gateway he keeps, a device asking to pair at the door, case entries Navi filed as unverified leads, an update staged on the Updater. The bridge now keeps a notifications store (`config/notifications.json`) and reconciles it against four producers — federation knocks on gateway fedinets, pending door devices, cases with unverified entries, and the background update check — under a strict quiet discipline: only acts and decisions notify; routine syncs, successful borrows and feed fetches never do. A record is born when its act starts waiting and is retired the moment the act is answered — the knock admitted or denied, the review emptied, the update applied — so the bell never vouches for a wait that is over. And per Alex's ruling, the announcement is Navi's own: when a record is born she says so in the main chat, in a line composed by the bridge from the record itself (no model call), exactly once per record — the bell is the persistent record, her word is the tap on the shoulder, and if a record is cleared she does not still mention it. A waiting item whose count grows (more unverified entries landing in a case already read) goes unread again, because new material needs eyes. The payload rides `/api/status` throttled, stands on its own at `GET /api/notifications`, and `POST /api/notifications/read` marks records read by id or all at once, unknown ids ignored.

## 0.4.6

Release tag: v0.4.6e — chapter 0.4's sixth Edge build under patch-per-build versioning. The Spartan0311 slate: seven field reports from the fedinet's second member, operating SKYNET2-Apex headless on Debian — the shell learns when it may wake (#240), the installer learns the headless world (#181, #183, #184, #185), the dashboard survives its own reload (#182), and Navi's numbers about herself become measurements or silence (#187).

- **The shell wakes only for machine work (#240).** The #232 shape recurred on v0.4.3e, twice in one report: a plain knowledge question ("what's the tallest mountain in Arizona?") answered by driving the shell — prose typed into bash, then invented evidence narrated back (a README that never existed, a wrong answer stated as read from it) — and a borrowed reply that drove the *borrower's* session the same way. Three layers now stand in front of the terminal. **The gate:** a shell block in her reply executes only on a machine-directed turn — the composer latched to CLI, a session already open in the chat and mid-flow, or the operator's own message carrying machine intent (files, processes, services, the state of the box, in natural words). On a conversation turn the block is not run at all: no session is born, nothing is typed, and the question is answered in conversation. The gate is deliberately permissive toward real machine asks — a false refusal is friction — and it binds local and Mesh-served replies identically, at the one extraction funnel both pass through. **Executor hygiene:** lines that do drive are no longer typed verbatim — a copied `$ ` prompt prefix is stripped, and a line that reads as a sentence rather than a command is refused, named in the session record, and never reaches bash. **The grounded guard:** when a drive leaves her reply empty and she is re-asked, the re-ask now carries the session's *real* captured output, errors included, and binds her narration to it; if nothing ran, the re-ask says nothing ran. Her teaching is rewritten to match: the block is no longer presented as an every-turn fixture, and the gate is stated in her terms.
- **The installer learns the headless world (#185, #184, #183, #181).** Spartan0311's world is a headless Debian LXC under systemd; the installer had only ever known a desktop. Four repairs, one story. **Headless (#185):** the installer now decides — an explicit `--headless` flag, `--startup boot` implying it, the recorded choice carried across updates, or auto-detection (no display, no graphical session) — and a headless install skips the Rust/Tauri window build and the menu entry entirely; the server case needs zero flags. The updater's apply carries the same determination: on a headless install the shell step is *skipped by determination*, a named successful skip in the apply record, never an attempted build that fails. **Integrity (#184):** the 3.27 GB llamafile is no longer executed on faith — its SHA-256 is pinned in the installer (`LLAMAFILE_SHA256`, read from Hugging Face's published `X-Linked-ETag`), the download lands at a temp name, verifies with `sha256sum -c`, and moves into place only on a match; a mismatch is a named, fatal refusal and nothing unverified is ever run. **Ordering (#183):** a fresh audit of the current installer found the reported `.pending` shape gone but two violations standing — the boot services were registered and started *before* the voice step (a fresh boot+voice install started its bridge under the system Python and never adopted the venv created later, until a manual restart), and registration was the installer's one unguarded `systemctl` under `set -e`, so an unreachable user bus killed the install after the swap, before its record. Registration now happens last — after voice, after the shell step, when everything a unit executes stands in its final place — and a registration failure names itself, prints the manual commands, and lets the install complete with its receipt. **The cgroup proof (#181):** the #201 scope spawner's missing half was never a fix but a proof — this build's bench stands up a real systemd user bus (a private `systemd --user` under `dbus-run-session`), runs the shipped apply bootstrap from inside a real user unit, and shows the helper surviving the bridge unit's stop in its own scope while a plain control child dies with the unit. The apply machinery needed no change; it has now been *seen* working in the environment it was built for.
- **The dashboard survives its own reload (#182).** After the first visit, every reload could render a blank page: the server-chats state (`chatStampSeen` and its siblings) was declared some forty lines *below* the startup calls that reach it — `var` hoists the name, not the value — so a load whose stored greeting re-rendered (or whose retired seed documents were stripped) walked `refreshSeedGreeting → persist → stampChatActivity` into an undefined map and the script died on the TypeError before anything painted. The declarations now stand above the startup block, and `stampChatActivity` guards its map outright, so no future edit order can reopen the wound.
- **Her numbers are measured, or not said (#187).** Navi invented her own vitals in the field — a generation speed, stress tests, all of it fabricated, none of it close. She cannot feel her own speed, so the bridge now times every local generation it makes — tokens, tokens per second, time to first token, the whole request, from the server's own timings where it reports them — and the recent figures ride her context beside the Guardian brief. Her teaching is the other half: answer questions about her speed or performance only from those measurements, and when none exist, say so plainly. A number about herself is either measured by the bridge or not said at all.

## 0.4.5

Release tag: v0.4.5e — chapter 0.4's fifth Edge build under patch-per-build versioning. One item: a case can now be started from chat, by asking Navi or by form (#241).

- **Start a new case from chat (#241).** Until now a case could only be born in Case Files, and the conversation where its substance surfaced had to be carried there by hand. Two routes now start one from chat itself, landing the same way: a real case in Case Files, its own chat ensured, set open, its substance filed as leads awaiting review. **Route A — ask her.** Navi is taught to sense the intent: when the operator says, in his own words, that something should become a case ("add this into a new research case, as much detail as possible" is the field shape — on v0.4.4e that ask was answered with a complete case-shaped document *as chat text*, and nothing was created), she acts in the same reply, closing it with a structured intake block swiping as much real detail from the conversation as it holds. The bridge parses the block defensively, creates the case through the ordinary machinery, files the findings in her name, lands the entities, observables and tasks as **unverified leads** (the #199 doctrine), appends timeline beats, ensures the case's chat, and sets the case open. The receipt is the bridge's own, appended to her reply and carded under it — a case exists only when the bridge receipts it — and the card carries an **Open the case chat** button walking the same jump the case page uses, so the operator steps straight into the case's room. A block that can't be read, or names no case, is refused in the open in the reply and creates nothing; caps on the swipe are named in the receipt when they bite, never silent. **Route B — the form.** The composer's **New case** button is the deterministic companion: a bridge-side pass swipes the active conversation into a draft of the case's form — name, client, scope, summary, type, priority, tags, and the entities and observables lifted, as a checklist — which the operator confirms or corrects before anything exists. Submit composes the ordinary doors (create, the lead door for the checked entries, open) and lands the operator in the case's chat; with the model disconnected the form opens blank with the reason stated on it. Refusals land on the form itself, in words.

## 0.4.4

Release tag: v0.4.4e — chapter 0.4's fourth Edge build under patch-per-build versioning. One item, a field report from the fedinet's first external member the same evening v0.4.3e shipped: the gateway card learns to carry the gateway's public road and no other (#238).

- **The gateway card carries the public endpoint alone (#238).** A gateway card, as minted, carried every address the gateway knew for itself — its LAN address first, its declared public endpoint second. A member's bridge dials the card's addresses in order, and the field evidence is exact about what that cost: the member's bridge dialed the gateway's LAN address (192.168.1.242 — an address on the *gateway's* home LAN) first, the connection sat in SYN-SENT, the dial never fell through to the public endpoint, and the automatic route fell back to a local answer while the public road sat unused in the same card. A gateway card exists to be used from outside the gateway's network; a local address on it is a door that exists in only one house — on the member's own LAN it is a stall, or a stranger's machine that happens to hold the same private address. The local addresses now come out of the gateway's card entirely, in the one payload builder every gateway-card render path shares (the Federation page's card, the download act, the sync deck): the embedded pairing card carries the declared public endpoint as its only address, and the gateway's own roster entry — its card facts republished under its signature, the entry members refresh their gateway records from — is shaped the same way. A gateway with **no declared public endpoint** mints no gateway card at all: the mint refuses, on the Federation page and at the download alike, with a sentence naming the missing declaration — a gateway card with no public road would be a lie, and the product does not mint those. Pairing cards are untouched: they keep their LAN addresses by design, because pairing is arranged between machines whose operators can meet on a network. Cards already in the field keep their old address lists; importing the gateway's fresh card heals a member's record through the #227 verified-card refresh, and the field proof is the member's next borrow — the first dial must be the public endpoint.

## 0.4.3

Release tag: v0.4.3e — chapter 0.4's third Edge build under patch-per-build versioning. Three items, all of them field reports from the v0.4.2e pull the same evening: the updater learns why its window builds never ran and repairs the whole road (#237), a hand-routed chat can be handed back to the automatic precedence from the pill (#235), and the pill's faces go to one word each (#236).

- **The update builds its window again (#237).** The v0.4.2e pull on the laptop recorded the installer exiting 1, the window stayed stale, and the Updater's own remedy text pointed at an install log and a staged package that did not exist. The bake reproduced the pull in a fixture and read the wreckage: the updater runs the installer from the staged package *inside the tree being replaced*, and the installer's swap parks that tree — so the shell step's first act, recomputing the installer's own folder, died on a path that no longer stood, under `set -e`, before the Rust check and before any build was attempted. No updater-path apply had ever built a window; hand installs, whose folder stands outside the swapped tree, were never touched. And because the install log and the staged package rode the parked tree, every path the failure surface printed was a path the apply had not left behind. Three repairs: the installer now reads its package's pristine shell sources from the parked package the swap leaves beside the install root, so the build runs in the updater context exactly as it does by hand; the apply helper holds a copy of the staged package on ground the swap cannot move and, before any verdict is read, **brings the stage home** — the install log written to the live path the diagnose command names, the package restored to the folder the manual fallback points at; and an owed build that produces no window is no longer mistaken for the designed browser fallback — the installer names it in its log, and the apply **fails in its record** on it, the shell failure in words, every remedy path real. #233's stale-stamp verdict is untouched.
- **Handing a chat back (#235).** A chat routed by hand had no way home: once a route was stored, the pill cycled only among stored choices. The cycle now carries a last stop — **Automatic** — offered only while a route is stored. Choosing it removes the stored route outright: the chat is genuinely unrouted again and rides the #231 precedence (federation, then Mesh, then local), wearing the Auto face like any unrouted chat; the pill row names the hand-back when it lands. The switch gate's three-way agreement — the flip, the bridge's store, the post-reload view — is benched for the new stop, adversarial flips included: a double-flip in one tick agrees on one stop instead of racing, and the hand-back works while the federation road is dark.
- **One-word faces (#236).** The route pill's faces are cut to a single word — **Local**, **Mesh**, **FediNet** — with the colors unchanged (Local neutral, Mesh blue, FediNet green), so the pill keeps its seat on the composer's line at phone widths. The fedinet's *name* moves off the face into the pill's descriptive label, which is where telling two fedinets apart now lives. The automatic marking survives the shortening whole: **Auto · Local**, **Auto · Mesh**, **Auto · FediNet**, dashed border and all, and a chosen route is still never dashed. The unavailable faces shorten too — **Mesh Unavailable**, **FediNet Unavailable**, amber — and the #228 refusal behind them is unchanged: the sentence lands on the pill row and the face does not move.

## 0.4.2

Release tag: v0.4.2e — chapter 0.4's second Edge build under patch-per-build versioning. Four items, all of them field reports from the v0.4.1e pull the same afternoon: federation recognition follows the roster instead of the pairing record (#234), an unrouted chat rides a named automatic precedence the pill shows (#231), Navi talks and the shell goes back to being a tool in her hand (#232), and an update that changes the shell's sources must end with a window that matches them — or fail loudly at apply time (#233).

- **Recognition by roster (#234).** A machine is a federation road because its node stands on a fedinet's signed roster — as a member entry, or as the fedinet's gateway itself — never because of how its pairing record happened to be created. The field case: a gateway paired by hand before its fedinet existed carried an empty stamp, so the route pill never offered the federation and its answers badged as plain Mesh borrows. One computation now serves every reader — the pill's availability, the status column's FediNet line, the borrow fields, and the green answer pill — and a borrow explicitly routed over the Mesh from a recognized member records the pairwise road it actually took, not the federation it could have.
- **The automatic precedence (#231).** A chat with no route stored rides a precedence — **the fedinet first, then the Mesh, then local** — falling back down the chain as roads empty, and a fallback names itself under the reply. The pill shows the default instead of hiding it: an automatic face carries an **Auto ·** prefix and a dashed border (*Auto · Rockport Mesh*, *Auto · Mesh*, *Auto · Local*), so an automatic indication and a chosen route can never be mistaken for each other; the face tracks availability live, and pressing the pill stores the next road as your own choice, which then wins over the precedence.
- **The shell is a tool, not her voice (#232).** Her standing instruction is rewritten around the distinction the field broke: conversation is answered in conversation; the shell is driven only when a command genuinely serves the answer, and she speaks first — what she is running and why — in the same reply. A turn whose prose comes back empty is re-asked once by the bridge, and a hollow lender reply is refused under the same reason word as a hollow protocol reply, so the record never attributes local words to the lender. The Guardian brief is framed as background to reason from, never a reply to read back. And a drive that births a chat's shell session waits for the session's startup stream to settle before its first line is typed, so a distro's login banner takes its place at the session's opening instead of flooding the answer.
- **The window comes with the update, or the update says so (#233).** The in-app update path runs the package's installer, and the installer's shell step builds the standalone window from the package's sources — but v0.4.1e's pull installed new shell sources over a binary built from older ones, the install reported success, and the launcher refused the stale binary at the next launch and opened the browser instead. The apply now ends with a verdict read from disk — the binary, its build stamp, the installed sources, hashed by the installer's own pipeline: a stamp that does not cover the sources fails the apply in its record, with the reason in words, whatever the installer's exit code claimed; the installer likewise verifies and names the window's end state before calling itself done. No binary at all remains the designed browser-fallback state and passes untouched.

## 0.4.1

Release tag: v0.4.1e — the first build of chapter 0.4, and the first under patch-per-build versioning: the minor is the chapter, the patch counts the chapter's Edge builds, and the version is the build. Four items: the chat route pill becomes the single route control (#228), the desktop shell's media-capture settings fix ships (#6), voice device selection learns to probe execution instead of presence (#229), and the Wire's families get their tab bar back — as pages, with Navi's Brief taking up residence on Home (#230).

- **One pill, three roads (#228).** The composer's route pill is now the chat's route control — the single one; the Build 2 answer pill keeps its job of recording the route an answer took, and this pill decides the road before the question is asked. It cycles **Local** (neutral — *Use Local Resources*), **Mesh** (blue — *Connected to Mesh*) and **Federation** (green — the fedinet's own name), per chat, stored by the bridge in `config/chat-routes.json`. A road the operator has no access to reads **Mesh Not Available** / **Federation Not Available** in amber and cannot be flipped into; a flip the bridge refuses names its reason on the pill itself, and the face does not move — the switch gate's three-way contract (the flip, the stored route, the post-reload view) is benched, adversarial flips included. A stored route whose road is empty at ask time answers locally and says so under the reply, naming the route rather than blaming a machine that was never asked. Unrouted chats keep the historical automatic behavior exactly. The same item removes the *Navi is typing…* indicator from the top banner entirely — the banner keeps her living presence line while she thinks.
- **Her hearing in the window, fixed at the settings layer (#6).** The desktop shell now turns WebKit's media-stream and WebRTC settings on explicitly for its webview (`grant_media_permissions` in the shell): a default WebKitGTK build can leave media capture itself off in Settings, in which case allowing every permission request still yields no microphone — the permission was never the wall. The change is compile-verified against the shipped shell crate, and the Voice tab's known-issue card stays in place until the field confirms her hearing in the window.
- **Execution, not presence (#229).** Voice warmup now runs a tiny real CUDA operation beside the decode probe: a stage whose card cannot actually execute with the installed wheels falls back to the CPU, and the Voice tab names the reason in operator words — the device, and that its architecture has no kernels in the installed wheels (the field case: a Tesla V100, Volta sm_70, `cudaErrorNoKernelImageForDevice` on NeoArcadia). A raw CUDA error string is never the operator-facing speech failure again: if generation itself fails on the card after a passing probe, the refusal speaks the same operator sentence, the probe verdict is rewritten, and the next line is spoken from the CPU. Transcription stays CPU by design and its status says so.
- **The Wire's families, as pages (#230).** The Wire carries a top tab bar — **News | CVEs | KEVs | CTFs** — on every family page: one family per page, each page holding only its own list, switching in place inside The Wire. The CVE and KEV pages' *Open the Center* doors are gone — the bounce out of The Wire to read a family's list was the anti-pattern; the Center remains its own surface, reached from Home. The selected tab is persisted, so the tab you left is the tab you return to. **Navi's Brief** joins Home as its second resident, ahead of the board: her read of the picture, composed only from data the page already holds — the wire's freshness and counts, the Center's catalog and queue, the CTF board, the Mesh's state, her model's state — and honest silence where a store has not answered. And the reader is uniform: CTF information now opens in the same centered reader as news, CVE and KEV items — the event's listing as the board carries it, captioned as exactly that, with the same Open-original fallback.

## 0.3.0e

Release tag: v0.3.0e — **Build 1**, the first build of the Bloom Era line, and the Sync Update (#200): *One Navi. All the screens.* v0.2.0 taught Apex to leave the machine it is on; 0.3.0e makes her the same Navi on every screen she reaches — a conversation started at the desk is waiting on the phone, and the other way around. This build also carries the updater bootstrap patch (#205) — the apply path governed by the incoming build's machinery — and the packaging fix that puts the shell scripts' executable bit in the release zip deliberately (#202).

- **The Sync Update (#200).** The sync set is the whole living her now: chats, Case Files whole, the **ChipDeck as one unit** (chips and RAG packs with their install records, plus the cards that tie machines together — pairing cards re-drawn fresh each round, gateway cards for every fedinet kept; a gateway card landing on a machine that doesn't keep that fedinet yet admits it, introduction only, never trust), the **operator's picture and badge**, her **memory entries**, and **her Soul and memory book**. Anchoring moved to the **GitHub account**: the set's manifest names the account, and a set from a different account is refused by name at the door on both transports, before anything is applied — the Operator Badge keeps its crown jobs (recovery root, the acts that need the ceremony) and stops being the sync key. Transport stays Mesh-first, the backup repo the fallback. Her documents converge per document and are **never silently overwritten**: a side untouched since the last sync takes the other side's text; both changed, the newer text wins and the losing text is parked beside the document as a named `.from-sync-` conflict copy, and the round names the document for the operator's eyes. Memory entries union — nothing un-remembers; the picture and badge are single values, latest change wins.
- **Every seat announces itself.** The desk was the one seat that never triggered a pull: the bridge is long-lived and boot-armed, so its app-start pull could be hours stale by the time a window opened, and only the phone's DHD sessions ever refreshed the room. A window now notes itself to the bridge as it opens, under the same session-gap and debounce discipline the DHD door uses, and re-reads its chats and cases when the pull lands. The page pushes its seat state with every note and with the Sync button's round, and adopts the converged answer the bridge returns.
- **The main chat can't be deleted — and /clear exists.** The main chat is a seat, not a row: the Chats tab shows a note where its Delete would be, the API refuses the delete by name ("empty it with /clear or /cls"), a wholesale chat replace never drops or tombstones it, and a sync tombstone naming it is dropped from the set. `/clear` joins `/cls` as the command that empties a chat. The same round fixes the chat switcher on the Chats tab: synced chats can carry non-numeric string ids (a convergence sibling is literally `<id>-sync-<stamp>`), and the switcher compared ids through Number() — the click highlighted and stayed on the main chat. Ids compare as strings now, everywhere the switcher family touches them.
- **The bootstrap patch (#205).** A pull is executed end-to-end by the running build's machinery, so no spawner fix can protect the pull that installs it — on the machine that failed, v0.2.0e — Build 12's fixed spawner never governed its own arrival. The package now carries its apply machinery with it: `apply-bootstrap.py` and `apply-helper.py` beside the payload, the helper byte-identical to the one the new bridge embeds. A bridge staging such a package lets the package's own bootstrap spawn the package's own helper. An older build's helper running this package's installer meets the **bootstrap handoff** as the installer's first act, before anything is stopped: the bootstrap spawns the new helper in takeover mode and the old installer's process exits, having installed nothing. The new helper signals nobody — it waits for the old helper to finish its bookkeeping and die (a predecessor is not an ancestor; the #201 invariant stands untouched), then runs the real install itself, from outside the old bridge's unit. If a handoff cannot arm, the ordinary install carries on: a handoff can never strand an apply. The apply record names how its helper was spawned — `package-bootstrap/…` when the incoming machinery governed the run.
- **Executable on purpose (#202).** The release zip's four shell scripts — install.sh, start.sh, run-llamafile.sh, docker/entrypoint.sh — are written at mode 0755 deliberately, and staging re-opens the finished zip and asserts those modes before the package is accepted, so the v0.2.0e — Build 11 accident (scripts at 0660, hand installs forced to chmod first) cannot recur silently. The manual-fallback command the Updater names now reads `bash install.sh`, which works regardless of the bit.

**Build 2** — Case Awareness (#199), the Fedinet route pill (#203), the status-bar law and FediNet sections (#204), and the post-apply bridge relaunch squash (#208). The Bloom Era's second build deepens the integration the Sync Update made possible: Navi works a case the way a partner would — logging it as she goes, under a review model a practitioner can sign — and the federation she travels becomes visible on every answer and in the status column.

- **The file grows up (#199).** A case manifest now carries a one-line **summary**, a **type** (incident / investigation / research / hunt / locate), a **priority**, **tags**, a case-level **sensitive** flag, an **owner**, **related** case slugs, and a **closed** date with a one-line **outcome**. Older cases migrate with safe defaults — nothing already filed changes meaning. Four registers join the case folder in the house markdown idiom: **entities** (the cast, with roles), **observables** (the IOC register — now the Wire/TIC case-terms source, replacing the looser scrape of the manifest), **evidence** (the custody register: per item a description, when/from/how it was acquired, a custody note, and a **SHA-256 computed by the bridge at filing time**; pre-register files are backfilled honestly), and **tasks** (next steps). A sensitive case's DHD list entry is redacted (present, counted, unnamed) and Sync's case index badges it.
- **She logs as she sees it (#199).** In a case's bound chat — only there — Navi's reply may carry an invisible structured log block (entities / observables / events / leads). The bridge parses, validates, dedupes and writes; she never edits files. Everything she logs lands **unverified** (state: lead), badged as hers with its provenance; findings gain the same state (operator filings default confirmed, Navi's lead). One tap in the case view **promotes or strikes** an entry — and a strike is noted in the timeline, an audit trail, not a memory hole. Her case context labels the states back to her: leads are reasoned from, never cited as established. Caps hold at six log entries and two findings per reply, and a detail belonging to a different case is flagged in chat, never written across.
- **Awareness flows in (#199).** A Wire story or KEV CVE matching a case observable or entity is flagged by Navi in the case chat and badged in the case view as a **Wire match — named as a match, not a finding**.
- **The Fedinet route pill (#203).** A federation answer's pill turns the federation green and reads the recorded route — *Fedinet Name > Answered by Name*, with the carrier as the middle segment when a relay carried it. It renders the recorded route only; pairwise borrows keep the cyan *via <name>* pill, local answers stay unbadged. On a phone the route truncates from the middle out — fedinet and answerer survive, the carrier elides first.
- **The status-bar law + FediNet sections (#204).** Anything off in Settings no longer shows in the status bar at all — off is absent, not greyed, in the rows and in the collapsed Servers header's dots alike. Under the Servers list, above Sudo Mode, each joined fedinet gets its own section — *FediNet: <Name>* in green when reachable, red when it cannot connect (the federation machinery's own verdicts), amber for a roster past its 72-hour freshness window — and a node in no fedinet reads *You are not federated.*
- **The relaunch squash (#208).** Build 1's field pull completed on both machines but the bridge did not come back on the new build — the apply helper's port-clearing step could not identify the app-mode bridge holding the port and told the operator to kill it by hand. The helper now finds this install's bridge the installer's way — its pid file and the working-directory proof, whoever supervises it — and stops it through the same escalation; an honestly unidentifiable holder names every proof that was run. A failing tail step always gets a **name** (never "an unnamed step" again), and a record that recovers to done no longer carries a previous attempt's stale error — a verdict owns its record. The bootstrap handoff's gate now **names its verdict** (go / no / refused, with the reason) beside the apply job and in the install log, and reads the apply record from the path the job itself carries. One proof guards the homecoming: the job's home must be the home the installer targets — on a migration apply they differ, and the gate declines by name so the running build's own machinery carries the migration (its adoption follows the move; a takeover helper starting from the old home cannot adopt a migration it did not witness, and an armed takeover there leaves two helpers racing).

**Build 3** — CLI Mode (#209) and Wire Updates (#210), one round. The Bloom Era's third build gives Navi the full shell — a standing interactive terminal in every chat, and a sudo mode worthy of a professional tool — and finishes the Wire's fusion: the Center and the Dashboard become one home surface, the news lane is re-laned to news only, and the operator's own feeds join the wire.

- **The full shell (#209).** Each chat can hold **one standing interactive session**: a real shell on a real PTY, living in the bridge, keyed to the chat. It is born on first interactive need — the operator opens it from the composer, or Navi drives one into existence when a step needs a stateful terminal — and it survives messages and window reloads. Everything it does streams into the thread as a terminal record, inputs **badged by author** (OPERATOR / NAVI): both drivers work the same session, and Navi sees its output tail on her next turn. A program that takes the **alternate screen** renders on a real terminal grid in a pane above the composer on the desktop (click and type to the program); on a phone the pane is honestly absent — the output streams into the thread and the bar names the difference. One-shot commands keep their existing path whenever no session is live — the session is additive, never a tax. A session closes explicitly, when its shell exits, or after **30 minutes without input**, and the thread notes the closing and its reason; a bridge restart ends sessions and the record names the death rather than faking continuity. Sessions are local to the seat's bridge — a borrowed reply does not move the shell.
- **Proper sudo for Navi (#209).** Sudo mode is rebuilt on **sudo's own credential timestamp**. Arming lives in Settings → System: the flip reveals a masked prompt **on the same card**, the password is fed once to `sudo -v` and forgotten by page and bridge alike — **no password is stored, logged or synced anywhere** (grep-proven on the shipped package). What persists is one on/off flag and sudo's own timestamp. While it lives, elevated commands run as `sudo -n`; when it lapses the state reads **Expired** — in the status column, which now *reads* sudo mode instead of owning it (Armed / Expired while on, **absent while off**, per the status-bar law) — and elevated commands refuse honestly until re-warmed. Disarming is instant and total: the flag flips and `sudo -k` kills the timestamp. **Every elevated command Navi runs is on the record**: an append-only audit (`config/sudo-audit.jsonl` — timestamp, command as run, chat served, exit status), surfaced read-only on the Settings card, and deliberately **not** part of the Sync set. The arm switch is held to the switch gate: the flip, the stored state, and the post-reload view agree, and a refusal (a wrong password, a cold sudo) degrades on the same card with its reason — never a silent snap-back. This replaces the parked pre-Build-3 design (a persistent root shell held by the bridge, the password re-sent with every request); the DHD prerequisite installer rides the timestamp model now too. Elevation never rides the interactive session: a shell session runs under its own session id, so sudo inside it prompts in-terminal.
- **News is news only (#210).** The News tab carries news articles — nothing else. The wire's CVE items and KEV items leave the News lane for tabs of their own (**CVE**, **KEV**), with the same cards and the same reader behavior; the same records, re-laned, nothing lost. The Center's graded queue stays the Center's — it lives on the Center tab, and the CVE tab's header says so.
- **Your own feeds (#210).** The operator can add **RSS/Atom feeds** (name + URL) from the News tab. A feed is validated at add time — fetched and parsed before it is saved — and a bad feed is **refused by name**: unreachable, unparseable, or not a feed. Saved feeds are first-class: their stories flow into News badged with the operator's name for the source, on the normal pull cadence; a feed that later fails names its failure on its pill instead of going silently stale. Feeds are removable. They live in `navi.config.json` and do **not** ride Sync — stated plainly, not widened silently.
- **Feed health, folded (#210).** The source pills live in a **collapsible field** on the fused home: collapsed, one slim row with the source count — still naming how many are not answering; expanded, the full pill set with each failure's sentence. The state persists per operator, and the fold follows the house open motion.
- **The fusion is the home (#210).** The Center and the Dashboard are one surface now — situation strip, the glance cards (the Center card's rows are the queue's highlights), feed health, and the tab set (News / CVE / KEV / CTFs / Bounties / Center) on one page. It sits at the **top of the nav rail as Home** and is the first thing the app opens to; the old separate Dashboard tab retires, and nothing it showed is lost. The dedicated mobile arrangement ships in the same round.

**Build 4** — Home is the board only (#213), the CLI pill becomes the CLI Mode toggle (#214), the dual-hat route fix (#215), and one selected state in the nav rail (#216). The Bloom Era's fourth build is the field-refinement round: three rulings and one defect from Build 3's first night in the field.

- **Home is the board only (#213).** Home now contains ONLY the fused awareness board — the Situation strip and the four glance cards (Top News, Newest CVEs, Next CTFs, Bounties) with their Open buttons. The feed-health pill field moved to the top of the **News view** — the same collapsible field, the same per-operator persisted state — and the tab set retired: each family (News, CVE, KEV, CTFs, Bounties, the Center) is its own view, reached by its card's Open button or the nav, each carrying a way back to the board, and the News view carries the doors to the CVE and KEV families so nothing the tabs pointed at is stranded. Retired keys land honestly: the old Dashboard key is the board itself now; the old CVEs scope still folds into the Center. Home is built as a **host surface** — the board is its first resident, not its permanent definition; later residents join it without another surgery.
- **The pill is the toggle (#214).** The composer's CLI latch IS CLI Mode now. Latching **CLI** opens (or resumes) the chat's standing shell session, and composer lines type into it — badged OPERATOR in the terminal record — while latching **Navi** returns to conversation; the session stays alive behind the toggle under its own close rules and resumes on re-entry. The standalone `>_` composer button retired — the toggle is the door. The switch gate holds on the flip: if the bridge refuses the open, the latch reverts to Navi and the refusal is named in the thread, and a line the session cannot take is named there too and runs nowhere else. One-shot commands keep their existing path whenever the latch is Navi's.
- **The dual-hat route (#215).** A borrow served by a peer that is both a hand pairing and a federation member now carries its federation leg, so the reply renders the FediNet pill. The mechanism: hand pairings made before a federation existed were never marked with the fedinet stamp on the member side — the gateway-card import skipped records that already existed, and roster application only created or refreshed records — so their borrows rendered the pairwise pill while the lender judged the same borrow under federation posture. The import and the roster application now **mark** a pre-existing record in place: the operator's facts on it (its flags, its non-federation origin) are untouched and the record is never rebuilt, and a member's departure unmarks it without deleting the hand pairing.
- **One selected state (#216).** The nav rail lights **exactly one** entry: the board lights Home, any family view lights The Wire, and the single correct highlight survives a reload. Build 3 lit both entries whenever the fused surface showed — the fusion never disentangled the two selected states.

**Build 5** — Sync chat deletion (#218) and the CLI session surface (#219). The Bloom Era's fifth build is the second field-fix round: two defects from Build 4's first night — deleted chats that would not stay deleted, and a CLI session that would not come forward.

- **Deleted stays deleted (#218).** Sync's tombstones worked by chat id, but a chat's identity across seats is its **conversation** — and the two were never the same thing. Every seat's main chat carries id "1"; when a foreign main converged here it was minted as an imported copy under a fresh timestamp id, and deleting that copy tombstoned only the minted id: the next round re-derived the same conversation under a new id and the copy was back — ten deletions deep in the field. Identity is by conversation now (origin id + birth stamp): an import derives a **deterministic** sibling id, convergence judges a foreign copy against its own conversation's representative copy here — never against whatever happens to hold its id — and deleting an imported copy tombstones the conversation as well as the id, so no re-derivation under any id can bring it back. A store already carrying Build 4's duplicate imports is deduped on the next convergence: copies in one prefix lineage fold to the richest, and genuinely diverged copies both survive, as they always have. Post-tombstone activity is later work, not resurrection: a thread worked on after its deletion returns as a **new chat** under a fresh id, and the deleted copy stays deleted. Tombstones still prune after 90 days.
- **The session comes forward (#219).** Re-latching CLI after time behind the Navi latch did nothing visible: the resume path trusted a cached liveness flag and, when it read live, performed no act at all — no render, no scroll, no focus — so a session whose surface had drifted stayed invisible, with no recovery on the flip. Every CLI latch now performs the **bring-forward**: a fresh state poll (the cache is never the last word on a flip), a render, the thread scrolled to the terminal record, and the composer focused. The Build 3 session input bar is **retired** — since Build 4 the composer is the session's input, and the second bar only duplicated it: the session's live status and its **Close** now live in a session header above the composer, and in the pane's head while a program holds the full screen. The composer bar takes the **entire width** available to it, in both modes, on desktop and phone alike.

**Build 6** — Voice Everywhere. The Bloom Era's sixth build is the voice round: three field reports from the first week of calls — hearing that reported itself fine while it could not decode a word, a call that died on an empty line and sat at "speaking" forever, a composer that kept the line it had just fired — plus the federation sentence that cost a night of diagnosis, and a gamble on the desktop window's microphone, taken openly as a gamble.

- **Hearing is proven by decoding (#221).** For eight days the voice stack could report itself installed while transcription died on every clip: faster-whisper 1.2.1 passes a keyword that the PyAV line pip had drifted to (av 19) no longer accepts, and an import check cannot see a decoder that cannot decode. The requirements now pin the pair inside the proven range — `av>=11,<13` (12.3.0 is the field-proven cure) beside `faster-whisper>=1.0,<2` — the installer's voice step **repairs** an existing venv to the pin instead of only building fresh ones, and hearing is gated on a **decode probe**: a quarter second of generated silence goes through faster-whisper's own decoder at bridge start, at warmup, and in the installer, and a failure is reported by name on the Voice tab — never as a silent "unavailable", never mistaken for a microphone again.
- **The venv comes home whole (#222).** A voice venv carried across the v0.2.0e — Build 11 install-home move kept console-script shebangs pointing at the pre-move Python, and its pip died with "cannot execute: required file not found". The same repair pass rewrites the shebangs in `voice/venv/bin` to the venv's own Python, every pip invocation runs as `python -m pip` from the venv Python — never the pip script — and a probe executes the pip script itself to prove the repair.
- **A call cannot die silently (#224).** A live call's answer died on llamafile's HTTP 400 — "message must not have empty content" — because the call's message list carried a hollow entry, and the panel sat at "Navi is speaking…" with nothing coming. The chat-request builder now drops empty-content entries before any request is built — **wherever they sit**: a hollow record stored mid-thread in the shared main history (the post-reboot field shape: the main chat itself, reached over DHD, rejecting a typed line) is scrubbed on **every** send, on the chat, call, and borrowed paths alike, and a list with nothing answerable is refused by name instead of sent. The Mesh roads are guarded in **both directions**: a borrower's bridge sanitizes its list before the ask rides (an older lender without the guard is protected), the lender sanitizes again at its door and in its builder (a partner's poisoned thread never 400s the lender's model; an all-hollow ask is refused with its own reason word, *empty-turn*), and a mesh failure surfaces as a named snag — never a raw backend refusal relayed onward. And when a model request fails, the call panel leaves the speaking state, names the snag and the model's own reason, and files the turn in the thread as unanswered — never spoken as if it were a reply. A spoken line that never completes is bounded the same way: the panel says which line went unsaid and returns to listening.
- **The composer clears (#223).** A fired CLI line stayed sitting in the composer after Enter. Submitting now clears the composer on both routes — the CLI/session path and the Navi path share the one composer and clear identically — while an autocomplete dropdown open on Enter still clears nothing, and the call panel's typed line clears the same way.
- **The desktop mic: a gamble, and the telemetry that settles it (#6).** Push-to-talk works in the browser and still fails in the desktop app window, though the shell has granted WebKitGTK's permission requests since the .21 era. This build ships the telemetry half in full: whenever push-to-talk is attempted, the window reports its own mic reading — granted, refused, or no recording API — to the bridge, which logs it and holds it for the Voice tab, so the field state finally exists in a log. The settings half — explicitly enabling WebKit's media-capture settings below the permission layer — is prepared as a patch but **not shipped**: it could not be compile-verified in this build's environment, and an unverified shell change does not ride. The Voice tab's known-issue card says exactly that.
- **Voice installs that fail in the open (#225).** On immutable systems the voice step died naming only itself. The pip step now runs binary-preferring (`--prefer-binary`, always as `python -m pip`), a failure sentence names the **specific package** pip failed on — parsed from pip's own output — and when the venv's Python is newer than the voice stack's wheel horizon (past 3.13) the sentence says so plainly and names the distrobox/toolbox route instead of reporting a bare failure.
- **Federation failures name the road (#226).** The mesh dial has classified its failures since #143 — timeout, unreachable, TLS, fingerprint, dropped — but the federation knock and roster sync flattened every one into "did not answer", and a night of field diagnosis was spent re-deriving what the code already knew. Knock and sync sentences now carry the kind and the last address tried ("the last road tried, 192.0.2.1:2475, did not answer in time"), and a **failed** knock writes a trust-audit entry, one per operator-initiated attempt — a quiet audit log can no longer be misread as "no knock was sent".
- **Cards keep their kinds, and verified cards refresh (#227).** The first external federation join burned a day on a record: the gateway had been hand-paired before its fedinet existed, so the joiner's record for it carried only its LAN address — and the knock dials the peer record, never the card. Two rules land. First, the **card-type guard**: a gateway card payload can never become a hand-made pairing record, and a pairing record can never serve as a fedinet's gateway record without the federation import's verification — every seating path (the pairing picture import, the federation import, backup restore, sync-carried cards, and the record layer itself) refuses the other kind **by name**, saying what the card is and which page it belongs to. Second, a **verified card refreshes reachability**: when a gateway card import's node matches an existing peer, the record's addresses, port, certificate pin, and name are refreshed from the verified card — while its operator facts (relay ticks, the tunnel route, borrow posture, pair history, the auto-paired mark) stand exactly as they were. The Mesh health check names the wound in words — a federation-marked record whose stored addresses are a proper subset of its verified card's — and offers the same refresh as an in-place heal on that peer's card. (Added to this build's slate by the operator mid-bake, the one legitimate way scope moves.)
- **Borrowed replies render clean (#217).** Shell-drive markup in a reply that arrived over a Mesh borrow could surface as the raw token — cut or oddly-cased generations left the marker standing in the text on both paths. The extractor now closes case-insensitively, reduces even an unterminated block to nothing (driving nothing, saying so in the record), and caps the blocks per reply — a borrowed reply renders exactly as a local one does, and the raw token never shows.


## 0.2.0

Release tag: v0.2.0. The road release. v0.1.9 taught Apex to work a case; 0.2.0 teaches it to leave the machine it is on. The Mesh stopped being a pair of machines nursed by hand and became a road: pairing cards that carry only honest addresses, a door on several numbers that minds its knocks, a backup route the bridge holds itself, and a health check that names the stage it failed at. Federation turned pairs into named fedinets — signed rosters, a gateway's green card, deep trust with its guardrails — and Rockport Mesh was founded on this line, in the field, the night Build 10 baked. The relay gave dark pairs a third road, Docker made Apex a container node, and the Threat Intelligence Center became The Wire, the awareness home. Underneath, the installer was rebuilt on a manifest contract, brought home to the operator's own directory, and taught the rule this line ends on: an apply may never kill itself. All of it was built in the open on the Edge channel as 0.2.0e, Builds 1–12, and checked in the field build by build. This full release is that line with its identity flipped: the bare number, the stable status, Latest. The code is the Edge line's final build, unchanged. One rough edge is carried openly (#205): an unattended pull is executed by the running build's own machinery, so Build 12's apply fix governs pulls from Build 12 onward and could not carry its own installation on every machine — a clean install is recommended for this release, and the updater's bootstrap patch is the first work of the 0.3.0e line.

### What graduated

- **The road (#143, #154, #178).** The Mesh health check runs the two decisive reads itself — this node's certificate on disk against the one its door presents, every peer's pinned fingerprint against the one it presents — and failures name their stage everywhere (fingerprint, TLS, signature, timeout), with the cure in the sentence. Pairing cards mint only addresses bound to physical interfaces and refuse, in words, when there is nothing honest to mint; a peer record's entries carry their own ports; the operator may declare one public endpoint, the only address Apex ever shows. The Mesh door binds 8765 plus 8443 and 2475 under one certificate and one fingerprint, counts failed knocks per source, and closes to a source that knocks badly. The managed backup route puts the SSH tunnel in the bridge's hands — spawned, supervised, its key authorized in person on the lender's own dashboard, never over the wire. And the check learned to heal what it finds: a record pointing nowhere is named, and its junk addresses can be cleared or its card re-imported from the same card that reported it.
- **Federation (#154).** A fedinet is a named set of nodes whose gateway maintains and signs the roster; node numbers are roster facts, assigned at admission. A gateway card — a pairing card's form, rendered green — grants admission and introduction only, never transitive trust. With a fedinet's trust-by-default on, the signed roster auto-pairs and auto-lends, refined per member (the new-member tick, per-member untrust and lend ticks, borrow caps, owner preemption), and one flip ends all auto-lending. A roster stale past 72 hours degrades its fedinet to pairing-only, with the sentence on the Federation page saying so. DHD tiers govern who may act from the phone: read and revoke always, manage acts behind a trusted device plus step-up, crown acts — deep trust, founding, tunnel keys — behind the Operator Badge ceremony and a named-action confirm, every act in the trust audit log. While a node keeps any fedinet, the headline is the state: **Mesh Online**. Rockport Mesh, this line's first fedinet, was founded in the field on NeoArcadia (Node № 001, gateway and Founding Member) with Neon Drip as Node № 002.
- **The third road, and Apex in a container (#154, #191).** When direct addresses, the declared endpoint, and the backup tunnel all fail, a paired machine that can see both ends may carry the borrow — the same signed request in a second signed envelope, consent as three ticks (asker's, carrier's, lender's), one hop hard, envelope metadata only on the carrier's ledger. And Apex ships as a Docker image: a headless container node whose keypair, certificate, and card are minted at first boot inside its volume — no identity is ever baked — with a DHD-first out-of-box and a federation invitation carried as a preload card, admission-only.
- **The awareness home — The Wire (#188, #189).** The Threat Intelligence Center opens on a Dashboard and holds five families: News (seven wires plus NVD and KEV additions, deduped, developing stories marked, seven-day retention), CVEs, the CTFtime board, the public bounty board, and the Center itself — outbound-only, no accounts, no keys, last-good data under a named staleness sentence. Asked "what's the sitch," Navi answers from the wire with sources and dates first and her own take clearly separated under "My take." Articles open in the app's reader; a failed extraction is named and falls back to the original.
- **One credential, and a door that knocks (#172, #173, #180).** GitHub failures have names — auth, rate (with its reset), abuse (with its wait) — and a bare HTTP 403 appears nowhere. The app's reads first gained their own Runtime credential, then the design completed itself: the Runtime PAT is retired and every read rides the operator's single device-flow sign-in, which works out of the box with the shipped client ID. The door changed to match: the access code makes a new device a pending knock, an approved device holds its own 30-day sliding token, and every device is revocable by name. Operator cards travel as themselves — one plain file in the backup repo, restorable byte-for-byte, one card at a time — while no Mesh key material ever rides a backup.
- **Quick Sync (#176, #177, #175).** One tap in Apex | Utilities runs pull + converge + push over the living work — chats and Case Files — first over the Mesh itself when a paired road is lit (one answered door settles both machines), falling back to the backup repo, named either way. Deletions write tombstones that travel over both transports, so a deletion cannot resurrect; diverged work parks both copies and asks for the operator's eyes. The deletion pass gave every case card, chat, and Vault folder a delete that names what it removes, and the Updater's failure card shows its evidence — one line that prints the apply's logs together.
- **The installer, rebuilt and brought home (#174, #179, #192, #193, #195, #196, #197, #198, #201).** The payload became a contract: MANIFEST.txt declares every file, its class, and its sha256; the installer copies and verifies from it, assembling the new tree beside the live one and promoting it by rename — never a mixture, and a failed self-check rolls the whole install back. The homecoming moved Apex's default home to `~/.local/share/navi-apex`, carrying all state — the Mesh identity byte-identical — under a permissions doctrine that audits once, by class, before anything stops. Token renewal was wired into every authenticated consumer, so a sign-in stops dying every morning. And the line's last defect became its clearest law: Build 11's unattended pull died because the apply helper lived inside the unit the installer retired. Build 12 moves the helper out of the unit before it works, stops processes by proven pid instead of units, retires units as paperwork, guards an interrupted home by its completion marker, and states the invariant in the bridge, the installer, and the Docs: **no step of an apply may signal any process in its own ancestry.**
- **Twelve builds, verified one by one.** Everything above arrived on the Edge channel as Builds 1–12 of 0.2.0e, each staged byte-exact and gated on the extracted bytes, and the line closes the way graduations close: a full regression on the final package, not a delta. The full release keeps the Edge line's final stamps: build 2026-11-14.12, build sequence 12.

## 0.2.0e

Release tag: v0.2.0e — **Build 1**, the first build of the Mesh line (0.2.0e focuses the Mesh, #154: fully functional, or nothing built on it stands). Its features:

- **The Mesh health check (#143).** The two decisive reads of the Mesh field diagnosis — prescribed in the issue, never run, because both needed a terminal on two machines at once — are now run by the product itself. From a new card at the foot of the Mesh page, one button press reports, in plain words with the actual values side by side: the fingerprint of the certificate on this machine's disk against the one its Mesh door actually presents; for every paired machine, the fingerprint this machine pinned from its card against the certificate that machine presents right now, and then the signed check, so identity and signature are judged separately; how many bridge processes are running on this machine and which process owns the Mesh door — the duplicate-bridge read. Every verdict is a sentence (match / mismatch / unreachable-at-a-named-stage), never a bare code. Diagnostics only: the check pairs nothing, pins nothing, routes nothing.
- **Failures name their stage (#143).** The silence tax is repealed across the Mesh surfaces. A dark peer's roster row and paired-machines row now carry the full reason under the short state — what answered, what did not match, and the cure where the product knows it: a changed Mesh identity is cured by importing that machine's fresh PNG card (the pin is replaced in place; the pair's history is kept), and a refused signature names its first suspect, the two machines' clocks, because a Mesh signature lives for 120 seconds. Probes and borrows classify their failure at the stage it happened — connect, TLS, fingerprint, signature, timeout — and the chat fallback notice speaks the same stages. A pairing card refused at import names the actual defect (a malformed fingerprint, a missing key) instead of the generic damage refusal. And a Threat Intelligence digest the collector path refuses — a certificate that does not match, a signature refused, an answer that is not a digest, a digest that does not validate — is refused out loud with the check named, recorded on the Center's Mesh source line, never a cheerful "imported" over a refusal.
- **The Ring 2 design pass (#154).** The federation design — how Ring 1's whole-request lender model grows into Alex's doctrine (every node serving whoever is using Apex, in whatever form factor; the Mesh as one federated network that behaves like a single neural network; more nodes making smaller systems faster) — is written and posted on #154: task routing beyond the first-reachable lender, capability advertisement, pairwise trust, mid-request failure semantics, the Dropbox sensor node's place in the federation, and what Build 2+ implements first. A document, not code; the Mesh pass builds the trusted transport first.

**Build 2** — the sign-in build (#173), answering the field report behind it: GitHub sign-in through Apex returning HTTP 403 on every network, the failure following the account rather than the wire (#172). Its diagnosis found the mechanism in Apex's own code — the app's read paths sent no credential at all — and this build is the fix, in both halves of the door: who Apex speaks to GitHub as, and who Apex lets in.

### Build 2

- **GitHub failures have names (#173).** Every GitHub failure Apex surfaces is classified and worded as a sentence: **auth** (the credential itself is refused — missing, expired, revoked, or under-scoped; waiting will not cure it), **rate** (a rate-limit bucket is spent; the sentence carries the reset time from GitHub's own headers), or **abuse** (GitHub's secondary safeguard; the sentence carries the wait from its Retry-After, and Apex stops — nothing anywhere retries on its own). The Updater, the NUR catalogs, the GitHub section's pulse and issues, and the device sign-in itself all speak the names. A bare "HTTP 403" appears nowhere.
- **The app's reads carry their own credential (#173).** The Updater's checks, the NUR's searches and repo reads, and downloads previously sent **no Authorization header at all**, riding the unauthenticated allowance — 60 requests per hour per network address, 10 per minute for search — shared with everything else on the operator's network. They now ride the **Apex Runtime** credential when one is configured: a dedicated fine-grained PAT, pasted into Settings → GitHub & Backup, stored in its own file beside the operator's sign-in (0600, never in plain config, never in a backup), and used by nothing but the app's reads. The operator's device-flow sign-in is a separate identity and is behaviorally untouched. With no Runtime credential configured, the unauthenticated path remains — and its failures now name the unauthenticated limits explicitly, which is the sentence that fixes them.
- **Search discipline (#173).** The NUR's two topic searches are cached for five minutes and run one at a time: a second catalog view reuses or waits for the search in flight instead of spending the Search bucket twice.
- **The Identities panel (#173).** Settings → GitHub & Backup shows the three identities side by side — **Operator** (your sign-in; backup and import only), **Apex Runtime** (the app's read credential, with its state and the last Core/Search bucket readouts GitHub reported), and **Release Automation** (no credential held, by design: publication runs on the operator's signed-in browser session and the local git remote — the panel says so).
- **The door knocks: trusted devices (#173).** The access code no longer hands a full session to whoever types it. A new device presenting the code becomes a **pending device** under a name it gives itself, and waits on its own screen; an already-trusted session approves or denies it in the Door list (**Settings → System → Door**, and the DHD page). An approved device gets its **own** session token — 30 days, sliding: using the door while valid renews it — and the Door list shows every trusted device's name, first and last seen, and expiry, each with its own **revoke**. **Bootstrap:** while no device has ever been approved, the first device to present the code approves itself and walks in, so a single-operator house is never locked out of its own door; from the first approval on, the shared-code cookie stops being accepted. Unchanged, and regression-checked in the bake: the public door's throttling, the loopback/public toggle rules, DHD forcing loopback, and the law that no remote session can enable Mesh lending. Regenerating the code now stops new knocks with the old code; approved devices keep their own tokens and are revoked individually. The Operator Badge as a sign-in factor stays reserved (Phase 3 of #173), as does the GitHub App graduation — neither is built here.

**Build 3** — the fluid build, ordered in the field the night Build 2 landed: the badge backup round passed its first real run on both machines, and its verdict was that the ceremony works but is too manual for the everyday gesture. Build 3 makes convergence a tap (Quick Sync, #176), fixes the updater apply that the same night's field run killed (#174), teaches the failure card to show its evidence (#175), and finishes the deletion pass the operator reported missing (#177).

### Build 3

- **Quick Sync (#176).** A **Sync** control in the menu's **Apex | Utilities** group — on the desktop canvas and the dedicated phone arrangement alike — that opens nothing: one tap pops an essentials-only card and runs the whole round, **pull + converge + push**, so laptop work is pickable-up on the phone over DHD and phone work is waiting at the desk. The sync set is the living work — the **chat store and Case Files** (case chats, findings, evidence, report state); settings, Soul/Memory, chips and knowledge packs stay with the full badge backup. The transport is the backup repo, under a `sync/` prefix the restore format never touches, riding the **Operator identity** — never the Runtime PAT (#173's separation holds) — with the badge in its slot as the round's pointer and trigger, never an authenticator; a signed-out round is refused and named on the card, with the sign-in one tap away. The card states the state (*Syncing…* / *Synced · just now* / *Can't reach Backup repo — held* / *Needs your eyes*), what moved (chat counts both ways, case files, whether the open thread was in the round), and the route actually used — **Backup repo** in this phase; at most one action (**Retry**). A success lingers **five seconds** and dismisses itself (tap away sooner); held and *Needs your eyes* cards never auto-dismiss. Convergence is the badge round's semantics — per-chat newest-wins, a genuinely diverged pair parks **both** copies (the later as a dated sibling chat; a case file diverged inside the same second parks as a `.from-sync-<date>` sibling file) and only a parked pair earns *Needs your eyes*, naming the chat or case. **Pulls also fire at app start and at DHD session start** (pull + converge each); there is no polling daemon. The Mesh peer-contact trigger and Mesh transport are phase 2, with the Mesh road itself.
- **The updater apply, fixed (#174).** The field failure, named from neondrip's apply log: the detached apply stopped the bridge but not the running window, then the shell rebuild copied the new binary over the live one — `cp: cannot create regular file '/opt/navi-apex/navi-apex-shell': Text file busy` — and the apply exited 1. The installer now **stops the running shell window** with the same discipline as the bridge stop (processes matched on their executable, TERM, a verified wait, SIGKILL) before files are replaced, and installs the shell binary by **write-to-temp + atomic rename**, so a running binary can never block the copy again — belt and suspenders, both fitted. Minor, from the same log: when an install runs detached and its sudo cannot be answered, the log now says plainly, once, that **a detached apply cannot answer a sudo prompt** and the system-package step is being skipped; the graceful degradation itself is unchanged.
- **The failure card shows its evidence (#175).** Beside the manual-fallback fix command, the Updater's failure card now carries a labeled **"See what happened:"** command — one copy-paste line, built from the actual staged tag's folder, that prints the apply's install log and the helper's step log together.
- **The deletion pass (#177).** The operator reported case deletion as missing; the audit found it buried, not absent — the case page's delete control (#163) sat at the foot of a long page, the cases list had none, standalone chat deletion had a server endpoint no control ever called, and the Vault's folder confirm named nothing but a count. Now: **every case card on the cases list carries a Delete** with the same naming confirm in the card (the case, its findings/evidence/timeline counts, its tied chat, the backup truth); the **Chats tab's per-chat Delete** arms a confirm naming the chat and calls `/api/chats/delete` for real (string ids — the old local-only handler also coerced ids through `Number()`, which silently no-oped on server-era string ids); the **Vault folder confirm names the folder** and its note count. And every delete — case, chat, Vault note or folder — now writes a **tombstone into the sync convergence**: the deletion itself travels with Quick Sync, so it cannot resurrect from another machine's older copy, while yielding to work genuinely newer than the deletion. The snapshot law stands untouched: backups already taken are never reached into.

**Build 4** — the road build (#143, #154, #178): the Mesh's first fully green pair and its first whole-request borrow across the internet were served the night Build 3 published — over a hand-built SSH tunnel, because a pairing record carried one port for every address and the cards it came from had harvested container bridges and loopback instead of the machine's way home. Build 4 is the patch that takes the road out of the operator's hands: addresses that tell the truth, a port for every address, a public door the operator declares, a health check that knows its own door when it sees it, a door with several numbers that minds its knocks now that it can face the internet — and the tunnel itself, kept, but managed by the bridge instead of by hand.

### Build 4

- **A port for every address (#143, #154).** A peer record's address entries may now carry their own port — `host:port` — while a bare host keeps inheriting the record's port exactly as before. Every dial in the Mesh (borrow, probe, health sweep) parses entries through one shared helper, so a single record can speak LAN at home and a public door away with no edits, mixed lists work, and every existing record and card keeps working untouched. The record's single `port` field stays, as the default the bare entries inherit.
- **Cards carry only honest addresses (#143).** The pairing-card generator now harvests by interface, not by address range: only addresses bound to physical Ethernet/Wi-Fi interfaces are minted onto a card — never loopback, never a container bridge or its tails, never a VM bridge, tunnel, or VPN adapter (a 10.x address on the physical NIC is a legitimate LAN address and still rides; a 192.168.x on a container bridge does not). The DHD domain and loopback appends are gone. And when a machine has no plausible physical-LAN address and no declared public endpoint, the generator **refuses to mint**, in a sentence that says why and what would cure it, instead of minting the junk card that stranded a real pair for a week.
- **The declared public endpoint (#154).** The Mesh page gains a **Public endpoint (optional)** field: a host:port the operator types — never harvested — that rides the machine's card beside its LAN addresses and lands in every peer's record as a host:port entry. It is the one address Apex ever shows (on the card controls, the roster, and the paired list), because it was typed for publication; harvested addresses stay plumbing and are shown nowhere, as before. A value that is not a host and a port refuses the settings save in words. Empty declares nothing, and the card carries no placeholder.
- **Probe manners (#143).** The health check now knows its own door. An entry that is this machine's own Mesh door (its own address at its own port) is skipped without dialing, and when an address answers presenting this machine's OWN certificate, the verdict names it exactly that — **your own door** — and the sweep moves on to the next address; the machine's own certificate is never again reported as a peer's changed identity. The deliberate exception stands: loopback at a *different* port (an SSH forward to a peer's door) is a road, not the own door, and is dialed like any other entry. A peer is healthy when any entry presents the pinned certificate and accepts the signature, as before.
- **The door minds its knocks (#154).** The Mesh TLS door now counts failed knocks per source — failed handshakes at accept, requests whose signatures do not carry — and five failures inside a minute close the door to that source, connections dropped at accept, for a backoff that doubles per repeat closing (60s, doubling, capped at 900s) and reopens on its own. Every knock and closing is logged in words on the bridge. A successful authentication clears the source's slate: a paired peer's valid signed traffic is never throttled, and whole requests are not chatty enough to reach the threshold honestly. The ledger is in-memory — a bridge restart reopens every door.
- **One door, several numbers (#154).** The Mesh door no longer depends on 8765 alone. It binds **8765 always**, plus the listen ports in the Mesh config — **8443 and 2475** ship as the defaults, and the operator can add or remove numbers (all above 1024) in the Mesh settings. One protocol, one certificate, one fingerprint on every port: a record entry naming any of them reaches the same door, a declared public endpoint may name any of them, and the Mesh page shows the numbers the door is listening on. The health check's census accounts for every door port — the door's own extra sockets never read as extra processes — and the knock ledger is shared across ports, so a source closed on one number is closed on all.
- **The managed backup route (#178).** The SSH door stays a Mesh carrier — but the bridge holds the tunnel now, not the operator. A peer record gains an optional **backup route**: enable it on the Mesh page with the peer's SSH host, port (227 by default), and user, and the bridge allocates a stable local port, spawns and supervises the tunnel (backoff 5s → 15s → 60s, clean shutdown with the bridge, back on its own after a restart), and appends the tunnel endpoint **last** to the peer's addresses at dial time — computed, never written into the stored record, so direct addresses are always tried first. The tunnel runs on a **dedicated keypair** the bridge generates: the public half rides this machine's pairing card and shows on its Mesh page; the private half is held at 0600 under config and never rides a backup, like the node keypair. Admission is in-person only, on the lender's own dashboard (never over DHD): **Authorize tunnel key** writes a single-purpose `authorized_keys` line — forward to the Mesh door only, no shell, no agent, no X11 — idempotently, with a matching revoke. The health check names the road that answered (*via the backup tunnel*) and gives the tunnel's own state as a sentence when it is down (down / key not authorized / host unreachable). The hand-run tunnel and any hand-set `127.0.0.1` record entries keep working untouched alongside — this route replaces the operator's chore, not their road.

### Build 5

- **The Backup route switch keeps the operator's flip (#179).** Field-found within the hour of Build 4 landing: flipping a peer's Backup route switch while its SSH host or user still stood blank posted the enable at once, the bridge refused it — correctly — for want of those fields, and the page re-rendered from the unchanged state, so the switch snapped off under the operator's finger; the refusal sentence sat at the top of the Mesh view, far from the peer card on a phone screen. The gesture now matches the requirement: a flip with a blank field **arms** the route instead of posting — the switch stays on, the route block says in its own words that the route is armed, not on, and names what it still needs, and focus lands on the first blank field. Filling the fields in and pressing **Save route** commits the enable through the same endpoint; flipping a route whose fields stand filled still enables at once, flipping off always lands immediately, and the bridge's refusal stands as the backstop for any client that posts an enable without its fields.

**Build 6** — the ease-of-use build, ruled the morning after the road lit: the Mesh should be operational in as few button presses as possible. The health check learns to heal what it finds, the backup route becomes a walked path, Quick Sync learns to ride the road it syncs over, GitHub sign-in becomes the product's only key — and the Operator card learns to travel as itself.

### Build 6

- **The health check heals in place (#143).** When a peer's record carries only dead-end addresses — loopback in any spelling, the unspecified address, a link-local, or the default Docker bridge gateway (172.17.0.1) — the peer's health card names the record as junk in a sentence (*the record points nowhere, so this pair has never actually been asked*) and offers the heal on the same card: **Import a fresh card** (which replaces the record's addresses in place, through the one pairing path) or **Clear the dead addresses** (the junk is stripped from the stored record now; the pairing, its pin, its tunnel route, and its history are kept). A record holding at least one plausible address is never "repaired" — that is an edit, and edits arrive as fresh cards.
- **The backup route is a walked path (#143, #178).** Three presses: flip the switch to arm the route, fill whichever field is still blank, Save route. The SSH host arrives prefilled from the public endpoint the peer declared on its card, when it declared one; Build 5's arm-instead-of-snap-back behavior is untouched. The route card also says, in plain words, the one step no button can take: the peer must authorize this machine's tunnel key on its own dashboard, in person — authorization is never given from over the wire.
- **First-run certificate warning (#143).** The first time an operator pairs, the Mesh page says the quiet part before any trust is pinned: the door's certificate is self-signed, no authority vouches for it, and the card you were handed *is* the trust — importing it pins that machine's fingerprint here, and a door presenting a different certificate is named, never quietly trusted. The notice rides with the first pairing and is not shown again on that machine.
- **Quick Sync rides the Mesh (#176 phase 2).** When a paired peer's road is lit, a sync round rides the Mesh itself: one whole signed Mesh request carries this machine's sync set to the peer, the peer converges it and answers with its own set in the same exchange — one answered door settles both machines, and the card names the route (*Mesh — <that machine>*). Trigger pulls (app start, DHD session start) take the same road first. When no Mesh route answers, the round falls back to the backup-repo transport, unchanged. The set, the triggers, and the convergence are untouched — newest wins, diverged threads kept whole as siblings, and deletion tombstones are honored over **both** transports. Two guards ride the new road: the set is size-capped (past the cap the repo carries the round), and when both machines know their operator's GitHub login and the logins differ, nothing crosses — different people's work never merges on a pairing.
- **One GitHub credential (#173 phase 3).** The separate **Apex Runtime** PAT is retired. The app's reads — the Updater's checks, the NUR's searches and repo reads, downloads, the GitHub section's pulse and issues — now ride the operator's own device-flow sign-in, the only GitHub credential Apex holds; a leftover `config/github-runtime.json` is ignored, never read. Sign-in itself needs nothing set up: the OAuth App is registered with Device Flow enabled, and Apex ships its client ID — a public identifier, no secret exists or is needed — in `config/github-signin.json`, so **Sign in with GitHub** works out of the box, on the desktop page and over DHD on a phone alike. Signed out, the reads degrade exactly as before (unauthenticated, failures naming the allowance) and every local feature is unaffected. The Identities panel now shows the truth: Operator and Release Automation, and no third token pretending to exist.
- **Operator cards travel as themselves (#180).** When a backup runs, the Operator card also lands in the backup repo as its own plain file — `cards/operator-badge.png`, exactly the card's bytes, no archive — listable and fetchable one card at a time, on the phone over DHD, without opening the whole backup. A restore takes the card from that file and reproduces it byte-for-byte (the `dashboard.json` copy stays for older restores; the file is canonical). The bright line holds and is bench-proven: no Mesh node key material appears in any file a backup writes — the card is the operator's picture and profile, never the node's keys.

**Build 7** — the relay build, and the awareness build. The Mesh gains its third road: when every direct road between two paired machines is dark, a third paired machine both can reach carries the ask — three consents, one hop, metadata only. Apex also ships as a Docker image for the first time: a headless node in a container, DHD-first, its identity minted at first boot and never baked in. And the Threat Intelligence Center becomes the awareness home: a Dashboard glance over four families, each on its own tab — the news wire (#188), the Center's CVEs, the CTF board (#189), and the bounty board — with Navi carrying the same picture in chat, where asking *what's the sitch* returns the briefing with her take labeled as hers.

### Build 7

- **Relay — the third road (#154).** When the direct addresses, the declared public endpoint, and the managed backup tunnel all fail, a paired machine that can see both ends may **carry** the borrow. The inner request is today's signed Mesh request, byte-identical, wrapped in a second signed envelope addressed to the carrier; the carrier verifies consent, signature, and size, forwards it verbatim to the lender's door, and returns the sealed answer the same way. It sees envelope metadata only — who asks, who is asked, how many bytes, what stage it ended at — and its ledger records exactly that. Consent is **three ticks, one on each machine**, each set on that machine's own dashboard on the carrier's peer card: the asker ticks that the carrier may carry its envelopes to the lender; the carrier ticks that it will carry between the pair; the lender ticks that the carrier may carry envelopes to it from the asker. Any missing tick refuses the carriage **by name** — the refusal says which machine has not consented — and unticking any one stops the next carriage, because every machine re-reads its consent on every request. Consent is given **in person**, like lending: through the DHD door a tick can be unticked from anywhere, but never ticked on. The road is **one hop, hard**: a relayed envelope is never re-relayed, and an envelope whose inner ask does not name this carrier is refused as already-carried. Direct is always tried first; only chat answers (`generate` class) ride the relay. When an answer comes back carried, the reply's pill names the machine that **answered** and a line under it names the road — *via relay <machine>*; when the relay road fails, the local fallback keeps the stage's name (*no-consent*, *relay-dark*, *dest-dark*, *dest-refused*, *dest-unknown*, *hop-limit*) in the same sentence style as every other failure. The Mesh health check gains a **relay verdict** for every consented road: a signed, content-free probe asks the carrier whether its own tick is in place and whether the destination is paired there at all, and the verdict is honest about the one end no probe can read — the destination's acceptance is proven when it answers a carriage. A dark relay costs one short probe, never a timeout spiral.
- **Apex in Docker — the container node.** The tree now ships a `Dockerfile`, a `docker-compose.yml`, and the first-boot machinery (`docker/entrypoint.sh`, `docker/first_boot.py`): a headless Apex node in a container — the same bridge, the same Mesh door (8765, 8443, 2475 published), the same DHD door. **No identity is ever baked into the image**: the node's Mesh keypair, certificate, and pairing card are minted on the machine that runs it, at first boot, inside the data volume, and the build context structurally excludes every identity directory. The model binary is not baked in either — the container downloads `navi.llamafile` once on first run (the installer's pattern) and keeps it in the volume; one binary serves both architectures, and the image is multi-arch (amd64 + arm64) by construction. One named volume over the whole app directory carries the --fresh preservation law into container form: identity, config, chats, and chips persist across container replacement. The out-of-box is **DHD-first**: DHD is enabled by default at first boot in the container only (bare-metal defaults are untouched), and the first boot **mints a fresh access code** — never a shared or shipped default — and prints it exactly once, in an unmissable boxed banner in the first-boot output, beside the node's name and Mesh fingerprint; the same banner is kept in `FIRST-BOOT.txt` in the data volume. Later boots never re-print it. Losing it is a designed path, not a lockout: `docker exec <container> python3 /opt/navi-apex/bridge.py --dhd-code` re-prints it, and `--dhd-code-reset` mints a new one (already-trusted devices keep their own tokens). While no device has ever been approved, a container node's door page carries one hint sentence pointing at the first-boot output. The Docker warning rides the docs: inside a container there is no physical LAN interface to harvest, so the **declared public endpoint is the honest address** — set it (the compose file wires `APEX_PUBLIC_ENDPOINT`) before minting cards for others.
- **The awareness home — Dashboard, News, CVEs, CTFs, Bounties (#188, #189).** The Threat Intelligence Center's page becomes the awareness home: it opens on a **Dashboard** — one glance card per family (top news, newest CVEs, next CTFs, bounty programs), each with its freshness stamp, each opening its full view — and every family gets its own dedicated tab carrying as much data as its source gives; the Center itself keeps a tab, whole. **News** is the wire: a bridge-side fetcher over BleepingComputer, The Hacker News, Krebs on Security, Dark Reading, SecurityWeek, The Record, and CISA advisories, plus the CVE sources (NVD recent, CISA KEV additions), into a local store with headline, source, date, link, and a summary-depth excerpt. Stories dedupe by link; a story whose text changes updates in place and is marked **developing**; retention defaults to 7 days and is the operator's setting. **CTFs** is the CTFtime board: running-now and upcoming sections, cards carrying format, online or on-site location, weight, restrictions, organizers, logo, description, prizes, and the listing link, times rendered in the operator's own timezone; the menu's **CTF Board** item lands on the tab. **Bounties** lists public programs from ProjectDiscovery's Chaos index (verified live at bake time: the index now lives on the data host, `chaos-data.projectdiscovery.io`) — name, platform, program link, bounty-paying flag, and scope size; the index states no safe-harbor terms, so the cards say so, and disclosed reports ship as a **named empty section** (HackerOne's hacktivity proved to have no keyless feed) rather than invented rows. All four families share one posture: outbound-only, no accounts, no keys, local stores, named staleness, a dead source is a sentence and last-good data stays up. **Navi is aware of all of it in chat**: the three stores ride her context as one bounded briefing, and asking *what's the sitch* returns the situation — top news, new CVEs, developing stories, the boards — facts cited by source and date, then her assessment under **“My take,”** labeled as opinion and never dressed as reporting. **Articles open in the app**: tapping a headline tries an in-app reader (the bridge fetches that one article, on demand, only for links the wire is carrying, and extracts a readable view with the source, the date, and an Open-original button always present); when extraction cannot honestly produce the article — paywall, script shell, non-article — the failure is named and the fallback is the original: a new tab on desktop, the article proper on mobile.

**Build 8** — the federation build (#154). The Mesh stops being a set of pairs and becomes what it was designed to be: named **fedinets** of nodes, each with a gateway keeping a **signed roster**, **deep trust** ruled by the founder (a fedinet's roster auto-pairs and auto-lends when its operator's toggle is on), a **Federation page** of its own, and doors tiered for it — read and revoke open through DHD, manage acts behind the **Operator Badge step-up**, and the **crown acts** (enable deep trust, found a fedinet, authorize tunnel keys) running through DHD under the full ceremony: trusted-device session, Badge, a named-action confirm, and an audit entry. The Mesh status headline graduates from a census to the state: **Mesh Online**.

### Build 8

- **Fedinets + signed rosters (#154).** A fedinet is a named set of nodes; its **gateway** maintains and **signs** the roster — member node ids, card fingerprints, and join order (**Node numbers are roster facts**, assigned at admission). Roster sync rides the Mesh door, direct first and then **via relay** (Build 8 admits the roster class to Build 7's sealed carriage — same three ticks, same one-hop rule, the destination's own consent check at its roster door). Versions only move forward; a forged, unsigned, or rolled-back roster is **refused by name** and the stored roster stands. A roster last verified more than **72 hours** ago degrades its fedinet to **pairing-only**, with the sentence on the Federation page saying so. **Expulsion** is a signed roster revision, effective at the next sync; pairings made by hand outside the fedinet are never touched — a hand pairing that was later admitted is unmarked, not deleted, and a federation-made record for a departed member is removed.
- **Gateway cards.** A pairing card's form, rendered **green**, the fedinet's name on its face, the payload riding a `navi-gateway-card` chunk and signed by the gateway. Import is **admission + introduction only**: the gateway becomes a peer and its roster becomes fetchable; no trust is granted by the import itself. A gateway that founded its fedinet is representable as both facts at once — **gateway AND Founding Member** (Node 1) — and the roster shows both.
- **Deep trust, with its guardrails (#154; ruled 2026-11-13).** Trust is **deep** by the founder's ruling: with a fedinet's **trust-by-default** toggle on, the signed roster **auto-pairs and auto-lends** on this node — against the gateway's signature, never against a claim. Refining it, per operator, per fedinet: the **lend-to-new-members tick** (default on; unticked, a member who joins after your trust baseline is pairing-only for you until ticked), a **per-member untrust** that always wins, a **per-member lend tick** for named exceptions, an hourly **borrow cap** as local policy, and **owner preemption** — your own work takes the machine from a federation borrow mid-flight, the borrower answered *preempted* by name; a hand-made pairing's borrow is never preempted. One flip of trust-by-default off ends all auto-lending; pairings already made stay pairings, and lending is re-judged fresh on every ask, so an untick, an untrust, or an expulsion stops the next borrow, not a later one.
- **Founding.** Any operator can mint a fedinet, become its gateway, and sign roster v1 with themselves as **Founding Member**; a node keeps several fedinets at once, with zero trust bleed across them. **Rockport Mesh** ships as the default fedinet *definition* only — the product carries the machinery and the invitation story, never a hardcoded roster: the real roster lives on its gateway. First runs meet Rockport through its gateway card; a container image built to join carries that card as its **preload invitation** (below).
- **The Federation page.** Its own page (desktop canvas + a dedicated phone arrangement), not a Mesh tab: the fedinets and their rosters with each member's posture in a sentence, gateway cards to import, display, download, and re-share, the trust toggles and ticks, founding controls, borrow caps, pending knocks with admit/deny, and the **trust audit log** — every trust-class act on this node, through any door, in sentences, metadata only. Every switch on the page is benched to the switch gate: flip, stored state, and reload read one truth because the page renders only what the bridge answers, and a refusal lands as a sentence on the same card.
- **DHD tiers + crown acts (ruled 2026-11-13 20:56 EST).** DHD is the remote admin surface for **the operator's own nodes only** — each node enforces its own operator auth, and no door flips another operator's switches. **Read + revoke** are open via DHD always. **Manage** acts (imports, ticks, caps, admissions) need a trusted-device session plus the **step-up**. **Crown acts** — enabling deep trust, founding a fedinet, authorizing tunnel keys — run through DHD under the full ceremony: trusted-device session + **Operator Badge** presentation + a **named-action confirm** (the act spelled in words, typed to confirm) + an audit entry; at the desk, the same acts need the same confirm + audit. The Badge factor: the node stores only the Badge's **SHA-256 fingerprint**, enrolled **in person** (enrollment itself never rides DHD); the picture is presented, hashed, compared, and never stored. A node with no Badge enrolled refuses DHD crown/manage acts **by name** — the ceremony cannot run, and says so. Build 4's in-person-only tunnel-key rule is amended accordingly: authorize is a crown act now; **revoke stays open through every door**.
- **"Mesh Online."** While a node keeps any fedinet, the Mesh status headline is the state — **Mesh Online** — not a census of pairs. Warnings still outrank it; with no fedinet kept, every surface speaks as before.
- **Docker preload (Build 7's image, wired).** A container image built to join a fedinet carries the gateway's card at `docker/gateway-card.png`; the first boot places it as the node's waiting invitation (`config/federation/invitation.png`) and the bridge imports it at start — **admission-only**, and under the container's ruled Rockport default the imported fedinet's trust-by-default starts ON (it engages only when a signed roster syncs; the import itself lends nothing). Node keypairs still mint at first boot and are never baked; the gateway's identity never leaves the gateway — the card is minted there, in the field. The tree's `docker/sample-gateway-card.png` is a clearly-labeled **sample** of the shape, with sample facts, never wired as an invitation.

**Build 9** — the installer hotfix (#192), cut the same night Build 8 baked: Build 7's awareness engines rode the release zip from the day they shipped, but the installer never learned to land them — so every install.sh install ran with three of the awareness home's four families dark, behind honest sentences that named the files "missing from this install" while the zip they came from carried them all along. Build 9 is Build 8 — the federation build, whole — with the installer made whole, the install gate hardened so this class of hole cannot pass a bake silently again, and one display change: the section those engines serve has a new name.

### Build 9

- **The installer lands the awareness engines (#192).** `install.sh` lands runtime engines in the install root one by one, in per-file blocks — the Guardian's (Build 14) and the Center's (Build 15) — and Build 7's three engines never got theirs: `wire.py`, `ctf.py`, and `bounties.py` sat in every zip and on MANIFEST.txt, and no install ever received them. The blocks now exist, in the same pattern (a copy of the sources missing an engine notes it in plain words and carries on; the bridge's inert fallback stays the backstop). Who was affected: every bare-metal install of Builds 7 and 8 — and every Updater apply, which runs this same installer — ran with the news wire, the CTF board, and the bounty board dark. **Docker installs were never affected**: the image build takes the whole tree. A full audit of the installer's per-file copy surface against MANIFEST.txt found no other runtime file in the hole (the audit table is in the build report).
- **The install gate is hardened (#192).** The gate now installs the package from a *separate* source directory into a clean target, asserts that **every MANIFEST-listed runtime file is present in the installed tree** afterwards — a package file with no installer route and no by-design ruling fails the gate by name — and then boots the bridge *from the installed tree* and proves the engines answer there: `/api/wire`, `/api/ctf`, and `/api/bounties` return their live state, with no "missing from this install" sentence anywhere. Proven in both directions in the bake: the gate **fails against Build 8's package** (the three engines absent from the installed tree, the three endpoints dark) and **passes against Build 9's**.
- **Build 8, whole — the federation build.** Nothing about the federation build changes: fedinets and their signed rosters, gateway cards, deep trust with its guardrails, the Federation page, the DHD tiers and the crown acts under the Badge step-up, "Mesh Online," and the Docker preload wiring all ship exactly as Build 8's block below records them. Build 9 supersedes Build 8's publication before it ever published — the federation build reaches the field as Build 9, with a whole installer.
- **The Wire.** The Threat Intelligence home is now called **The Wire** — the hub for everything security-related outside the system itself — and the **CTF Board**'s separate sidebar entry is retired into its tab, where the board already lived. Display only, per the house branding practice: `intel.py`, the view keys, the endpoint paths, and the data files keep their names, and the CTF board itself is unchanged — same tab, same cards, same CTFtime picture. The in-app Docs follow the new name; the bridge's served sentences that name the section follow it too.

**Build 10** — the installer rebuild (#193), the Federation page's render guard (#195), and an app brush-up (#196), baked the night the first federation was founded in the field. That night is also the rebuild's evidence: three installer incidents in one evening on one machine — an install that died mid-copy on files a remedy had left root-owned, an install run under sudo that stranded its service registration, and a half-promoted install whose new face ran over an old bridge until the Federation page strobed against a route the bridge had never heard of. Build 10 is the rebuild those incidents specified.

### Build 10

- **The installer is rebuilt (#193).** Three pieces, one law each. **The payload is a contract:** MANIFEST.txt now declares every file the package carries with a class (payload / seed-config / generated / package-only) and a sha256; the installer copies and verifies *from the manifest* — the hand-written per-file copy blocks that desynced in #192 are deleted, and a payload file missing from the package, or whose bytes are not the declared bytes, fails the install *by name before the bridge is stopped*. **Placement is one act:** the new tree is assembled in a staging directory beside the live one — from the live tree itself, so operator state rides wholesale — and promoted by rename; a kill or failure at any point leaves the previous version *entirely* live or the new version entirely live, never a mixture, and the two-file `.pending` flip ceremony is gone. **Provisioning is not placement:** a first install provisions an operator-owned root once and placement never needs sudo again; an install invoked *through* sudo refuses up front, by name, before anything is touched (under sudo, `systemctl --user` cannot reach the operator's bus and files land root-owned), and a tree the operator cannot write refuses the same way, with the one repair command named; payload files a past sudo repair left root-owned inside a writable tree no longer block placement at all — the swap never writes into the old tree's files, so they are left behind in the previous tree, which the installer names if the operator cannot delete it. After the swap, **the product verifies itself** — `bridge.py --self-check` proves the stamps agree, every manifest payload digest verifies against the live tree, and every runtime engine imports from the installed directory — and the install stands or *rolls back whole* on that verdict, never on a version proxy. What an install preserves is unchanged: the llamafile, chips and packs, the Vault, DHD certificates, the Mesh identity, chats, config, the voice venv, Soul and Memory. Docker's whole-tree image build is untouched.
- **The Federation page cannot strobe (#195).** The page fetched its state from inside its own render — and re-rendered on every answer — so any answer that set no state (the field case: a pre-federation bridge answering `{"error": "not found"}`) repainted the page forever. The state is now fetched **once per view entry**, at the door, guarded in flight; render only paints what it holds; and any answer that does not set state — an HTTP error, a non-JSON answer, a JSON answer with no fedinets, the bridge's own named refusal — renders **exactly once**, showing the answer's own sentence, with a manual Retry. No silent retry loop remains on any door.
- **The brush-up (#196).** The **Updater folds into Settings → System** as its own collapsible dropdown — check, download, apply, status and the apply trace all travel, in the Updater's own definitive panel order — and the **Current Version Notes** become the final block at the bottom of the System menu. The vestigial "Backend — always Live" block and the Apex | Node / Apex | Mesh pointer blocks leave System (the DHD and Mesh pages are those controls' only homes now). The nav group **Apex | Systems is renamed Apex | Network**, its children reordered **Federation, Mesh, DHD**. The **Mesh page** is re-presented on the Federation page's model — a posture sentence under the header, then cards: **Your door** (identity, own card, import), **Lending & borrowing**, **one card per peer** carrying all of its controls together — borrow tick, relay consent ticks, its road readout — **Roads** (the backup route's walked path and tunnel status), and **Health** at the foot; every control keeps its home, its function, and its consent wording, and every switch on the page passed the switch-gate bench (flip = stored state = post-reload truth, adversarial flips included; the backup-route arm is the reference case). And **The Wire's article reader actually pops on mobile**: the reader now lives at the top level of the page while open — on a phone it presents as a full-screen sheet above its scrim, with the source and date pinned, the original one tap away, and an obvious close; the desktop popup is unchanged, and a failed extraction keeps its named fallback.

**Build 11** — the homecoming build (#198) and token renewal everywhere (#197). Build 10's rebuilt installer met its first unattended pull and died honestly: stage-and-swap assembles the new tree *beside* the live one, and beside /opt/navi-apex is /opt — root-owned on any stock system — so the promotion the design promises can never run there. The operator's ruling was not a patch but a move: Apex's home was the problem, so Apex comes home. The same week's second field report — a GitHub sign-in that demanded re-signing every morning on every authenticated surface — turned out to be one missing wire, repeated everywhere: renewal existed, and exactly one consumer used it.

### Build 11

- **The homecoming (#198).** Apex's default install home is now **~/.local/share/navi-apex** — the operator's XDG data home, resolved from the installing operator's $HOME (the passwd entry is the fallback when a detached context arrives with no HOME at all). There is no other default and no /opt continuation path. When the new installer runs against a legacy tree at /opt/navi-apex — including invoked detached by the legacy Updater's apply helper, which passes its own root as --dir — it **migrates on that run**: the new build installs into the new home through the same manifest/stage-and-swap path, then every piece of operator state is carried from the legacy tree — chips and RAG packs with their indexes, the Vault, DHD certificates, the Operator card, chats with their sync state and tombstones, Case Files, config including the GitHub sign-in, Soul/Memory, the model, the voice venv — and above all **the Mesh identity: node keypair, door certificate, pairing records, federation state, tunnel keypair, byte-for-byte**, so a gateway's fingerprint (and every pin held against it across a federation) survives the move untouched. Boot units pointing at the legacy tree are retired before the carry and services are re-registered against the new home; the post-install relaunch — the installer's own, and the apply helper's after it adopts the migration marker the installer leaves — starts the **new home's** start.sh. The legacy tree is **parked, never deleted**: left in place with a `MIGRATED.txt` marker naming the new home, the date, and the removal one-liner (`sudo rm -rf /opt/navi-apex` — sudo because deleting the directory takes its parent, which is the honest reason an unprivileged installer cannot do it for you), and the same sentence is printed in the install output. Migration runs **at most once** (the new home records it); a second run is a plain same-home upgrade. If both homes somehow hold state, the new home is canonical — nothing is carried over it, and the output says so in a sentence instead of merging silently.
- **The permissions doctrine (#198).** The second defect in the stranded pull — a preflight that checked the install dir and never its staging parent — and the manual-install death the same morning (an assembly copy dying on an unreadable root-owned `config/github-auth.json` and a root-owned `.pyc`, discovered one file at a time) become one doctrine. **Before anything is stopped**, the installer proves it can create its staging and park locations under the new parent, refusing by name with the remedy when it cannot; and it audits the source tree in **one exhaustive pass** for files the operator cannot read, handling each offender **by class**: **regenerable** bytecode (`__pycache__`, `*.pyc`) is never carried and never blocks — the carry reads exclude it, so it cannot kill a copy again; **re-issuable credentials** (`config/github-auth.json` and its retired sibling) are left behind when unreadable, and the completion output and the install record name the casualty and its remedy in one sentence — *"GitHub sign-in was not carried — sign in again from Identities"*; **irreplaceable state** unreadable (Mesh identity and certs, cards, chats, Case Files, Soul/Memory, all other config) refuses the install up front, naming **every** offending file plus the exact `sudo chown` one-liner that repairs them all — never whack-a-mole. After the swap, the product's **self-check grows an ownership verdict** over the new tree — every file operator-owned and operator-readable, offenders named in `config/install-self-check.json` and the install record — so the tree can never quietly rot root-owned again without the product saying so itself. The boundary is stated plainly: an unprivileged installer cannot chown root's files; the fix is that it never needs to — except for irreplaceable state, and there the stop comes first, complete, with its remedy attached.
- **Token renewal everywhere (#197).** The GitHub sign-in's refresh machinery existed since the sign-in build — and its only callers were the chip-publish loop's private wrappers, so the Updater, the NUR, the GitHub section, the backup and Quick Sync transports each discovered the access token's ~8-hour death as a fresh 401 and demanded a re-sign, every morning, forever. Now there is **one shared authenticated-call wrapper**: every `github_api` / `github_api_raw` consumer rides it, as do the runtime read path (`_github_read`: Updater checks, NUR reads) and downloads. Riding the stored token, a call **renews pre-emptively** when the token's recorded expiry — persisted as an absolute `expires_at` at save time since this build, instead of a lifetime nothing read — says it is dead or inside the margin; a 401 that still arrives earns **exactly one renewal and one retry**. The publish loop's own renewal is retired into the wrapper. Failure honesty is unchanged: a 401 surviving renewal (or with no refresh token stored) surfaces the existing named auth sentence exactly once, and rate/abuse classification and wording are untouched.
- **The reader, widened and un-clipped (#196 rider).** Two field notes on The Wire's article reader, answered together. The desktop panel was a 680px newspaper column; it is now `min(1120px, calc(100vw - 48px))` — the page, not a column of it (the phone sheet is unchanged in shape). And the reader's top bar could clip the headline: the bar was a `position:sticky` first child *inside* the scrolling panel, so its painted place at open rode on the engine's sticky-vs-padding origin and the panel's initial scroll origin — the field screenshot shows the headline's first line half-clipped at the sheet's top edge, above the source/Close bar, on the phone and the desktop alike. The structure is what changed: the panel is now a flex column that never scrolls, the bar is a fixed first child, and the article scrolls in its own box below it — at open the headline stands fully below the bar, and at no scroll position can the bar overlap or clip a content line, on either door, by construction.

**Build 12** — the #201 fix build. v0.2.0e — Build 11's first unattended pull died within two seconds on both field machines (incident 21): the apply helper descends from the bridge, so it lives inside the bridge's systemd unit, and the installer's homecoming retired the legacy boot units with `systemctl --user disable --now` — stopping the unit signalled every process in it: the bridge, the helper, and the installer itself. The helper's trace recorded the SIGTERM and the failure; the install log ended at the homecoming heading; the migration never ran, and both legacy trees stood intact. This build is that one defect, answered in both halves of the apply, under one stated invariant — and nothing else.

### Build 12

- **The no-ancestry-signalling invariant (#201).** Stated in the code, in the in-app Docs, and here: an apply may end exactly one process by signal — the bridge it replaces, by its proven pid, through the installer's stop machinery. It may never use a group-shaped signal — a systemd unit stop, a process-group kill, a cgroup kill — because those mechanisms cannot tell the bridge apart from the apply's own ancestry: the helper descends from the bridge, and the installer descends from the helper. A new session is not an escape from a cgroup; Build 11's helper had one, and died anyway.
- **The helper escape (#201).** The bridge now spawns the apply helper **outside its own systemd unit**: via `systemd-run --user --scope`, in a transient scope of its own (probed first; the recorded helper pid is the scope's waiting parent, whose lifetime tracks the helper's, so the panel and the watchdog keep their meaning). No stop of the bridge's unit — this installer's, a future installer's, an operator's — can reach it. Where no scope can be had (systemd-run absent, or no user manager answers — the container shape), the spawn falls back to the plain own-session spawn and **says so**: the step log's first line and the apply record both name the mode the run actually has, and on such a machine the installer's ordering below is the protection.
- **The installer's ordering (#201).** Defense in depth, in the homecoming leg and the pre-/opt migration leg alike: the legacy bridge, model server and window are stopped **by pid first**, through the proven stop machinery (the model server gains a pid-stop of its own, matched on its directory and command line the way the bridge's has always been); only then are the legacy units' files retired — `disable` + remove + daemon-reload, **stopping nothing** — and a final stop proof after the retirement closes the resurrection window, with no unit definition left to resurrect anything. A whole-script audit found no other unit stop or broad signal: the only remaining `--now` in the installer *starts* the new home's services after the swap, and every other kill in the script was already a proven single pid.
- **The interrupted-home guard (#201).** A migration is complete only when a marker proves it — the new home's own `config/migration.json`, or the legacy tree's `.apex-migration.json` naming this home. A live-looking tree at the new home with **no** marker is an **interrupted home** — the remains of a migration that died between the swap and the park — and is never canonical and never converged onto: the migration runs again, state is carried from the legacy tree whole, and the interrupted tree is renamed aside by the swap like any previous tree, with the situation named in the output. The both-homes rule survives exactly where it belongs: when a marker proves the earlier migration completed, the new home is canonical and the legacy tree stays parked.
- **The bench that convicts (unitapply12).** The regression that let incident 21 through was a bench that ran every apply from a shell no unit owned. The new fixture runs full applies with the helper standing inside a real cgroup standing in for the bridge's unit, against a `systemctl` whose unit stop performs systemd's actual control-group kill: the Build 11 package fails it with the field's own signature (SIGTERM in the helper's trace, the record failed at the installing step, the install log ending at the homecoming heading), and v0.2.0e — Build 12 passes it three ways — under the old bridge on the installer's ordering alone, under its own bridge with the plain fallback, and under its own bridge with the helper genuinely relocated into a transient scope while a Build 11 installer fires its unit stop anyway.

## 0.1.9

Release tag: v0.1.9. The casework release. Case Files grew from a folder of notes into the room investigations live in — every case with a chat of its own, its evidence shown as evidence, and Navi filing findings in her own name — while the Threat Intelligence Center opened beside it, the Guardian took up its watch over Navi's headroom, and Apex learned to arm itself at boot and come up headless from a cold start. All of it was built in the open on the Edge channel as 0.1.9e, Builds 1–15, and checked in the field build by build. This full release is that line with its identity flipped: the bare number, the stable status, Latest. The code is the Edge line's final build, plus one mark the field caught missing after that build shipped — the Threat Intelligence Center's radar (#168).

### What graduated

- **Case Files is where an investigation lives (#137, #161, #162, #163).** Opening a case ensures a chat tied to that case — one canonical thread on the server-side store, a CASE tag on the Chats tab, a chip on the case chat that jumps back to the case — and while a case is open Navi files her own findings into it, under her own name, never silently and never in the background. Exports embed image evidence as images inside the single report file, and a case can be deleted completely — the case, every Vault file it owns, and its tied chat — behind one confirmation that names all of it, backups stated plainly as out of reach.
- **The Threat Intelligence Center, v1 (#165).** A local intel store (`intel.py`, stdlib only) fed by keyless public sources only — the NVD API 2.0 keyless tier, the CISA KEV catalog, EPSS, CISA advisories RSS, and curated RSS — merged on the CVE ID with each source owning its fields, fetched under ETag/Last-Modified discipline, and stamped so staleness is labeled everywhere (fresh <12h · aging <48h · stale beyond). Navi carries a bounded standing brief of it in chat, answers deliberate lookups straight from the store, and matches records locally against the watchlist, the Mesh roster, and the words of open cases; the digest rides the Mesh door, so one node collects and the rest import and match locally. From a record, File into the open case lands it as a finding with its citation.
- **The Guardian, the profile, and the boot arm (#156, #157, #159).** The Guardian (`guardian.py`, stdlib only) samples the machine against a headroom model of what Navi needs and works a watch → warn → throttle → kill ladder whose kill rung may only ever touch the operator-approved expendable list — which ships empty on purpose — with every event provenance-tagged from day one. The optimization pass measured first and claimed no cosmetics: an automatic hardware profile for a config that never set one, and warm-up so the first ask carries no model-load dead air. Arm at boot registers both systemd user services from inside the app and shows the state as the system reports it — half-armed reads half-armed.
- **Chats live on the server; the badge carries them (#139, #136, #150, #151).** Chats are stored by the bridge in `config/chats/` — local storage is a cache, never the record — and follow the Operator Badge between machines through the GitHub backup's convergence. The badge gained a true slot, in Settings → Operator and as the same shared intake on the sync card; sync starts in Chat, where its operation card carries the progress and the verdict under a 45-second plain-words timeout. The DHD door wears the Row's favicon, served on both doors.
- **Headless, from a cold boot (#142).** The bridge and the DHD door come up with no login at all, the armed state read live in the status column's Servers → Boot row, and the full guide ships in both docs surfaces — including the Wi-Fi secret trap the field round found and proved was the environment, not the app: a profile with no stored secret fails at boot with "no secrets" until `nmcli` stores it, typed at the machine, never through chat.
- **The quality-of-life line underneath (Builds 1–11).** The server names unified into the Apex product family and chip faces drawn, not rolled (#92); chips run like programs with `./<name>`, short names and prefix resolution (#97); knowledge packs ride pictures as cartridges (#93); ChipDeck, the binder for everything that rides a picture (#94); Publish runs the whole GitHub chain in one action; the live install-visibility defect fixed at its root (#95); and the Chip Studio's dedicated phone arrangement with focus mode as the app's one expand idiom (#146, #135).
- **Fifteen builds, verified one by one.** Everything above arrived on the Edge channel as Builds 1–15 of 0.1.9e (public Build 5 skipped by design), each staged byte-exact and gated on the extracted bytes, and the line closes the way graduations close: a full regression on the final package, not a delta. The full release keeps the Edge line's final stamps: build 2026-11-12.915, build sequence 15.

## 0.1.9e

Release tag: v0.1.9e — **Build 15**, the fifteenth build of this version and its thirteenth publication (the first was Build 1; the Build 15 notes sit directly below in their own section, and everything under "Build 14" and below further down is those builds' notes, unchanged). Build 1 bundled the whole 0.1.9 QOL line into one build, directed 2026-11-10. Its features:

- **The server names unify into the Apex product family** (issue #92, in-app pass). The status column's Servers group now reads, in order: **Navi** (the engine row — its detail line keeps the technical truth, "llamafile · port 8080"), **Apex Node**, **Apex Mesh**, **Apex DHD**; the menu and pages wear the same names. Names are display only — config keys, routes, ports, the model id, and every protocol string are untouched.
- **Chip faces are drawn, not rolled** (issue #92). A new forge wears the family shell — black body, coral notched bands — with one chunky pixel glyph that means the chip's function, named in the chip's metadata (the `glyph` field in navi-chip.json); a keyword read picks one when none is named, and the old name-seeded pattern survives only as the fallback. Installed and published pictures are never redrawn.
- **The live install-visibility defect is fixed at its root** (issue #95). A NUR install answered success and the catalog card flipped to INSTALLED, but Local Chips kept showing 0 and no pill appeared: the bridge was innocent — install wrote the cartridge, recorded it, and verified it against the same folder scan Local Chips reads — but the dashboard's install/update/delete completion invalidated only the catalog cache, never the workflows payload (`wfData`) that Local Chips, its tab count, and the pill row all render from, and that payload is fetched once and cached for the session. The completion now invalidates both, so an install shows in Local Chips in the same session, no restart. **Uninstall grew reachability in the same round**: an installed chip's catalog card and its ChipDeck sleeve both carry Uninstall now, alongside Local Chips' Delete; cartridge and record go together, and a chip with local edits asks first. The audit also caught a quieter lie — a chip dropped into chips/ by hand has no install record, so its Delete removed nothing while saying "Deleted"; a local/ delete now takes the picture with it.
- **Chips run like programs** (issue #97). `./<name> <args>` in chat runs a chip, args passing through as they always have; bare `./` answers with the shelf; short names resolve (`./cryptex` finds navi-cryptex), a unique prefix runs, an ambiguous one answers with its candidates, and an unknown one answers with the shelf instead of a dead end. `/chip` keeps working as the long-form alias. Under the CLI latch, `./` belongs to the shell again — the latch decides. The composer's chip pill shelf is retired: running lives at the keyboard, and the chips' browsable home is ChipDeck. Attribution pills under replies are untouched.
- **Knowledge packs ride pictures** (issue #93). A pack exports as a **knowledge cartridge** — one PNG carrying its manifest and every document's text, compressed — and installs from the picture alone (RAG tab or a ChipDeck drop), its index built locally at install from the carried texts; a cartridge never carries an index, and retrieval never reads the picture. Past the 8 MB ceiling the export refuses in plain words and points at the ZIP; nothing truncates.
- **ChipDeck** (issue #94). A new top-level surface — the binder, under a binder-rings mark: sleeves holding the actual pictures of everything that rides one (installed chips, Mesh pairing cards, knowledge cartridges), each with its state and its actions gathered — run, download the picture, Studio, uninstall; pair and unpair; activate, deactivate, remove. Drop a picture anywhere on the Deck and it slots in by the payload inside it. Soul, Memory, config, the Vault, and keys never ride cartridges; they stay in backups, where they belong.

- **Publish does everything** (the fully automated chain). Publishing a chip or a pack used to stop at the upload — the release was the operator's manual step on GitHub. **Publish to GitHub** now runs the whole chain in one action: create the repo if it is missing, upload the file set, set the topic (navi-chips / navi-rag), create the tag from the manifest version, and **publish** the release (never a draft) with the cartridge picture attached — the chip PNG for chips, the knowledge cartridge for packs (which also lands at the pack repo's root). Release notes come from the README. A version that is already released is refused before anything uploads — bump the version in the manifest; a release is never overwritten silently. The unsigned route is unchanged: Export-for-GitHub ZIP, everything by hand.

### Build 15

- **Every case gets its chat, and Navi files her own findings** (issue #161). Opening a case now ensures **a chat tied to that case** — created on first open, returned to ever after, one canonical thread per case, riding the server-side chat store (#139) like every other thread and marked with a CASE tag on the Chats tab. **Open the case chat** on the case page walks straight into it. While a case is open, **Navi can file her own findings** into it: conclusions she reaches, in her own words, under her own name — the finding's frontmatter carries `author: navi`, the case page marks it FILED BY NAVI, and a line lands in the case's timeline. Filing is never silent and never background: it happens in the thread where she reached the conclusion, and the receipt — the finding's title and its path — hangs on her message there (the same judgment-marker discipline as her memory saves, at most two per reply; a stray marker with no case open is stripped and dropped). The **open case is visible**: the status column carries it in its stats, and the case chat wears a chip naming it that jumps back to the case; closing the case clears both.
- **Case exports show image evidence as images** (issue #162). The report's evidence section now **embeds** PNG/JPG/GIF/WebP evidence into `report.md` as base64 data URIs — the evidence travels inside the single file, so the #138 single-file promise holds for the downloaded copy too, not just in the app's own preview. An image over ~8 MB stays listed by name with the reason stated; non-image evidence keeps the name-and-size listing; the internal-withholding rules are untouched.
- **A case can be deleted — completely** (issue #163). The case page gains a delete control with **one confirmation that names what will be removed**: the case, every file it owns in the Vault (findings, evidence, timeline, manifest, exported report), and — since this build ties chats to cases — **its tied chat**, the whole conversation. Deleting purges the case folder from the Vault entirely, removes the bound chat from the store (so no machine's write-through can resurrect it), and clears the open-case pointer when the deleted case was the open one. The confirmation states the backup truth plainly: backups are snapshots and are **not** reached into — a case inside an existing backup stays in that backup.
- **The Threat Intelligence Center, v1** (issue #165). A new Apps surface and a new engine (`intel.py`, stdlib only) beside the bridge: a **local intel store** (`config/intel.db`) fed by **keyless public sources only** — the NVD API 2.0 (keyless tier, incremental lastMod windows, politely paced), the CISA KEV JSON catalog, EPSS (daily, batched over the store), CISA advisories RSS, and curated RSS (Krebs, BleepingComputer). A record's identity is its CVE ID, and each source owns its fields — KEV the exploited status and due dates, NVD the CVSS/CPE/description, EPSS the likelihood — merged by UPSERT, fetched with ETag/Last-Modified discipline, and stamped per source so **staleness is labeled everywhere** (fresh <12h · aging <48h · stale beyond; last-good is served, never a silent old picture). **Navi is contextually aware**: the digest enters her chat context as a bounded standing brief (~700 tokens, freshness stamps included), a deliberate lookup (`intel: <query>`, “what do we know about CVE-…”) answers straight from the store without a model round-trip, and naming a CVE or a watched product in ordinary chat pulls that record into the reply (in a case chat, the case's matched records ride too). **Matching is local and declared**: the operator's watchlist, the Mesh roster, and words from open cases — CPE-grade matches labeled exact, text hits labeled keyword; the inventory never leaves the machine. **The Mesh carries the weight**: one node collects, the digest object (`navi-intel-digest/1`, ~300 ranked records, collector and per-source stamps in its header) travels the Mesh door to thin clients that import it and match locally; a receiver with the fallback off never polls the feeds, and the fallback is a setting, never a surprise. From a record, **File into the open case** lands it as a finding with its citation (CVE ID + digest stamp) written into the note, so case exports carry it. The page is desktop-first — freshness strip, triage queue, the record, and the brief rail — with a dedicated phone arrangement (one column, brief first) in the same round.

### Build 14

- **The Guardian — a system monitor that protects Navi's headroom** (issue #156). A new engine (`guardian.py`, stdlib only) lives in the system-integration layer beside the bridge, awake independent of the UI: it samples processes from `/proc`, keeps a headroom model of what Navi needs (a memory reserve that tightens while Navi is generating), and learns per-process collision statistics in a small persistent store (`config/guardian-stats.json`) — how often a process has collided, warned, been throttled, or been killed. Its action ladder is watch → warn → throttle → kill: throttle is a reversible duty-cycle (SIGSTOP/SIGCONT slices to a CPU cap) plus a best-effort renice, and kill (SIGTERM, grace, SIGKILL) may only ever touch processes on the operator-approved expendable list, which **ships empty on purpose**. Its own processes, the bridge, and the llamafile are protected by PID, name, and uid. Every action lands in a bounded in-memory log and an append-only `config/guardian-log.jsonl`; every event carries provenance from day one — `origin` (which device and door it came from) and `foreground` (what the operator is doing there, `unknown` until a later pass teaches it to see) — so the future mobile-whisper and foreground-posture concepts need no schema migration. The face is a new **Utilities → Guardian** page: a summary card with a plain-words pressure chip and a Mesh line (borrowing/peers when the Mesh is present, working locally only when it is not — the Guardian is mesh-aware and degrades gracefully), a live watch table, the learned-offenders table, the full ladder settings (persisted in config, restored on restart), and the action log. On a phone (≤800px) the page is a dedicated interface, not a squeezed desktop: cards stack full-width, the PID column drops, and every row, input, and the Save button meets the 44px floor. Navi can answer questions about the Guardian in chat: the bridge appends the Guardian's current state as a short structured block (≤110 words) to the chat system prompt, and `GET /api/guardian/state` / `POST /api/guardian/settings` expose the same state to the page. The Guardian's own footprint was measured in this build's audit (issue #157): about 0.20% of one core for its sampler loop and no measurable resident memory beyond the module import.
- **The optimization pass** (issue #157). Measured first, on the bench, against the Build 13 tree as baseline with an identical stub harness: bridge spawn → status 412.4 ms, chat round-trip median 1,261.9 ms, of which the bridge pipeline itself is only ~6.2 ms — there was no fat worth cutting, and **no cosmetic optimization is claimed**. What the numbers did justify shipped: an **automatic hardware profile** — a config with no `hardware_profile` now profiles the machine once on startup (detect + derive), persists it, and fills derived runtime defaults only where the operator has not set them, so modest machines get sane context, threads, and batch without a setup step; the profile view now names its tier plainly (**potato** / **standard** / **beast**) and where the profile came from (`profileSource`). **Warm-up** removes the model-load dead air before the first ask: after a bridge-initiated llamafile start reports healthy, one one-token warm-up completion fires (gated by `runtime.warmup` — explicit setting wins; unset, it is on for potato/standard tiers and off for beast), and `runtime.warm_at` ("HH:MM") schedules a daily warm through the same start path. The derivation table itself is unchanged — its 6–12 GiB row's ctx 4096 is the size already proven fluid on the 9.4 GiB Framework baseline, and doubling it would eat the Guardian's reserve on exactly the machines the Guardian protects. The full before/after table is posted on issue #157.
- **Arm at boot, from inside the app** (issue #159). The status column's **Servers → Boot** row — which has read the armed state live since Build 12 — gains the hand to go with the eyes, and **Settings → System** carries the same control: **Arm at boot** registers and enables both systemd user services (`navi-llamafile.service`, `navi-bridge.service`) from the unit templates the package ships, with this install folder substituted, exactly as the installer's boot choice does, and records the startup choice in config. Linger is attempted the one way the app honestly can — a plain `loginctl enable-linger`, no sudo, nothing borrowed from the parked sudo toggle — and when the system refuses it, the surface shows the exact `sudo loginctl enable-linger $USER` command instead of pretending, and the arm shows as **half-armed** (services enabled, starting at login rather than boot). After every action the state is re-read from the system and shown as found; partial success shows as partial. **Disarm** disables both units — what is running keeps running, it simply will not come up at boot — and leaves linger as it is. Both directions are idempotent, starting an already-running service is adoption, never doubling, and arming is a local action only: the bridge refuses it through the DHD door.
- **The rail takes its settled order** (issue #160). The left-rail groups now seat as **Apex | Navi**, **Apex | Apps**, **Apex | Systems**, with **Apex | Utilities** low by the version line — and the group seated low opens **upward**, its children stacked above its header, as it has since Build 6; the settled spec now says so on purpose. Order and direction only: every group's contents, children, icons, and behavior are exactly as they were, and the order is proven in pixels by the real-browser geometry gate on desktop and phone, not just in the markup.
- **Headless auto-start gets its full guide, in both docs surfaces.** The in-app Docs gain a **Headless auto-start** page — setup, the Wi-Fi secret fix, and the boot test — covering the installer boot choice (there is no Settings toggle for it; armed state is read live in the status column's Servers → Boot row), the netplan/NetworkManager trap where a Wi-Fi profile with no stored secret fails at boot with "no secrets: No agents were available for this request" until a desktop login provides an agent (fix: store the secret with `nmcli`, typed at the machine, never through chat), the no-login verdict test (reboot, leave the login screen untouched, reach the bridge from a phone on the same Wi-Fi), and failure diagnosis from the journal. The same guide ships to the GitHub wiki as "Headless Auto-Start and the No-Login Boot Test".

### Build 13

- **The Chip Studio fits a phone, and focus replaces fullscreen** (issue #146). On a phone (≤800px) the Studio stops being a desktop page squeezed into a column: it works **one pane at a time** — **Face**, **Code**, **Test** — under a full-width segmented switch; the face art becomes a **collapsible strip** instead of a competing pane; and **Run / Forge / Save** sit in a bottom action bar pinned to the thumb, every target ≥44px, the bar reserving its height in the layout so nothing ever slides under it (the #133 line — the editor frame reserves its true height, head, strip, switch and bar taking their own rows and the panes scrolling in exactly what remains). A **snippet shelf** and an **autocomplete row** — completing from the chip API's own vocabulary plus Python's keywords — are the primary input aids, and no desktop feature is cut. **Run** tests the forged chip itself, through the bridge's own run route, and lands its output in the Test pane. Above 800px nothing about the Studio's layout changes — except the one deliberate retirement: the editor's old fixed-position fullscreen is **gone**, and the Studio takes the Vault's **focus mode** (#135) as the app's one expand idiom — rail, status column, presence bar and the Studio's own header rows yield, and Esc or the toolbar button brings the room back.
- **Case Files wears the Investigator** (issue #149). The generic folder glyph gives way to the folder with a magnifier over its lower-right corner, drawn in the same stroke hand as the rest of the set — everywhere the Case Files nav item renders: expanded rail, collapsed rail, and phone.
- **The badge gets a door, and the sync stops spinning** (issue #150, with the #136 field fixes). A badge minted on one machine used to have no way into another — Build 12 read a badge from exactly two places, and the picture file in the operator's hand was neither. Settings → Operator now carries a **true badge slot** beside the minting controls: pick the badge picture and its `navi-badge` payload is parsed — kind must be "operator-badge", anything else is refused in plain words and the held badge is untouched — and the GitHub Account sync card carries the **same slot**: one shared intake feeding the one badge state (`CONFIG.operatorBadge`), no second store. The Operator section names the badge currently slotted and this node's name beside it. The sync card's labels tell the truth per state — the no-badge button no longer reads as a bare pull; it says no badge is slotted — and the **bootstrap path is written on the card**: mint here, back up, slot elsewhere, or pull a backup that carries one. Pressing the sync button now **goes to Chat at press time**, where the operation card carries the progress and the verdict, and the start runs under a **45-second timeout** that fails in plain words in both rooms instead of leaving Settings spinning. The sync machinery itself — fetch, preview, confirm, apply — is untouched.
- **The DHD door wears the Row's icon** (issue #151). Apex serves the Nocturne Row logo as its favicon: favicon-scale derivatives of the site's logo.png — a 180×180 apple-touch icon and a 32×32 tab icon, about 20 KB between them, never the 287 KB original — bundled as app assets, linked from the page with relative paths, and served by the bridge on both doors: at the bridge origin, and through the DHD proxy behind the same passcode gate as every other dashboard byte. The installer lands them like the other binary assets, in plain words when a git clone has none to land.
- Amendments, found by this build's own gates and fixed in the same bake: the Case Files rail icon had rendered as an empty frame since the view shipped in Build 12 — nav children resolved their icon by label, and "Case Files" is the one label that is not its view key; children now resolve by key, which is what lets the Investigator above actually appear. On the phone the Studio's switch, snippet and action buttons now state their own 44–48px floors (the shared phone floor had quietly set them to 40px), and the Studio root takes the bounded frame the other work views use — the Forge button, its confirmation card and the documents tail ride inside the panes' scroll region, so the frame reserves its true height with the action bar at its foot.

### Build 12

- **Chats live on the server now** (issue #139). A chat used to live only in the browser window that held it — localStorage, per install, per browser origin — so the laptop's threads and the server's threads were different conversations, and picking up where you left off depended on which door you came in. The store of record is the bridge now: plain files in `config/chats/`, one JSON per thread, written atomically, with the uploads index beside them. Every window hydrates from the server on load and writes through on every change; localStorage is demoted to a cache and an offline fallback, and the first browser to meet an empty store imports its existing chats as the seed — migrated, never discarded. Open Apex on the desktop, through DHD, or from a second browser and it is the same conversation. Chats also become the **ninth backup essential**: they ride the ready-to-fly backup on their own tick, and a restore converges them rather than overwriting — newest wins per thread when one copy is the other's continuation, and where both machines genuinely moved the same thread on, **both survive**, the incoming copy arriving as a dated sibling thread, never a silent merge.
- **Account sync: slot the Operator Badge, pull the latest backup** (issue #136). The Badge (#116) was always a pointer, never a credential — now it has its errand. Slotting it in Settings → GitHub & Backup (its home, with the account machinery) asks the bridge to pull the latest GitHub backup and build the same per-item preview Import builds — presented as a **live operation card in Chat**, Navi speaking before it and after it, nothing generated while it runs, and **nothing applied until you confirm on the card**. The GitHub sign-in remains the only key: signed out, the sync stops at its first step with a polite direction and no fetch is attempted. Her node keypair and Mesh certificate never ride a backup, so they can never ride a sync.
- **Headless server mode, and boot that tells the truth** (issue #142). `start.sh --headless` starts the services only — the llamafile, check-first as always, and the supervised bridge — and opens no window: SSH-safe, idempotent, with the same start.log the desktop launch writes. A desktop launch **adopts** services that are already running instead of starting second copies. The installer's boot mode registers a second user service, `navi-bridge.service`, beside the llamafile's, and tries to enable lingering; where it cannot, it prints the exact `loginctl enable-linger` command rather than letting you believe boot-start is armed when it is not. The status column's Servers group gains a **Boot** row that reads the armed state — both services, the linger state — from the system every time it shows, never from memory.
- **Case Files, the first Apex | App — and the Vault takes its seat beside it** (issue #137). A new nav group, **Apex | Apps**, opens with **Case Files** and the **Vault** directly underneath (placement only — the Vault's view and its #134/#135 frame are untouched). A case is a folder of plain markdown in the Vault — `cases/<name>/`, its manifest in `case.md`'s frontmatter (client, scope, status, opened) — so cases ride the Vault's backups and open in Obsidian as they lie. The view cold-starts on the case list; a case carries **Findings** as structured cards rendered from the finding notes, **Evidence** as files dropped straight into the case folder, and a **Timeline** newest first. Mark a case **open** and Navi files to it from chat — "file that as a finding" lands the exchange in the open case, out loud — and the latest chat or chip output files as a finding from the case page.
- **The Case Files report export** (issue #138). One markdown document per case: the head (name, client, scope, dates, status), the findings by severity in full, the timeline as an appendix, the evidence listed — landed as `report.md` in the case folder with a matching download. Findings marked internal are withheld **and counted in the document** ("2 internal notes withheld"), never silently omitted, and no internal machine names or Mesh details are ever written into a report. The export is markdown only: the app has no PDF path today, and the report does not pretend otherwise.
- **A first chip for the Navi Federation** (issue #144, preview). `navi-mud-lite` rides this build as a **Ready, unpublished** preview chip — not in the package, not published: a local-only starter world ("The First Hearth", seven rooms) seeded as plain markdown room files, walked in chat (`look`, `go <exit>`, `take <item>`), with a machine-readable `federation.json` beside it (`worldName`, `naviFederation: true`, `rooms`, `links`) — the contract under which a world can later federate over Mesh without rework. No networking, no listeners, no code execution from world files: the worlds are data.
- **Amendments, same build** (maintainer's note): the bake's own gates caught one defect in the new convergence code before anything shipped — a repeated sync of the same backup would mint a fresh sibling thread for a still-diverged chat every time; convergence now recognizes a diverged copy it has already filed and keeps it, so the same sync lands the same way twice. Second, the geometry gate caught the rail at 150% UI scale: with a fourth group open, the version footer ran past the rail's foot and the rail clipped it (overflow hidden) — the rail now scrolls vertically when its content exceeds its height, the way the phone's menu panel already did, so every row and the footer stay reachable at any scale. Also corrected wherever this build found them: the standing claims that chat transcripts are never backed up (Settings → GitHub & Backup and the in-app Docs) — as of this build, chats are an essential of their own, and the copy says so.

### Build 11

- **The Vault's tree moves to the left, and the desk reaches the bottom of the window** (issue #134). The files panel sat on the right of the editor by explicit grid placement — the .80 build's answer to a flex row that rendered differently in the shell and in browsers — and the whole view ended where its content did, the editor a fixed sixteen rows with dead space beneath it on any tall window. The placement is reversed at the operator's direction: the tree leads on the left, the way the app's own rail leads its views, and the Vault is a height-bound frame now, the way Docs is — the title, intro, search, and recent rows hold still as fixed heads, the pair flexes into every pixel of height that remains, the tree scrolls its own length inside its panel, the editor stretches to the bottom of the window in Edit, Split, and Preview alike, and the backlinks strip rides the foot of the editor's column. On a phone the same frame stacks — the tree in a capped band with its own scroll, the editor flexing below it — and nothing is left trapped in a sliver.
- **The editor can take the whole window** (issue #135). A focus button in the editor's header — corners out to enter, corners in to leave, and Escape on the keyboard as the other door — puts everything else away: the menu rail, the status column, her presence bar, the Vault's own head rows, and the tree, until the note is the only thing in the window — still inside Apex, never the browser's fullscreen. Leaving focus, by the button, by Escape, or by switching views, restores the Vault exactly as it was — same note, same mode, same unsaved words — because focus touches nothing but the frame: the state lives in one flag and the frame's face is read from it, the pane button's discipline. On a phone the top bar yields as well, and the exit stays a full-size touch target.
- **Amendments, same build** (maintainer's note, filed with issue #134's evidence): two bake finds, both caught by this build's own gates before anything shipped. First, the editor card sat at the pair's head at content height, the textarea one line tall — the pair's single stretching row had gone to the tree alone, the editor auto-placed into an implicit second row; both columns are pinned to the declared row now. Second, the mode buttons were dead in the shipped page — their wiring's selector also matched the editor column's own mode attribute (added this build to key the preview's flex share to Edit), and the column, wired last, overwrote the mode with its own value on every click; the wiring is scoped to the buttons and the attribute renamed. The gate now clicks the real buttons, the way the operator does.
- **On a phone, her presence lives in one place** (issue #140). The presence bar rode above every view on a phone just as on a desktop — and the status pane's head row carried the same line, painted by the same hand from the same source, so opening the dock showed her twice. The phone bar is retired: her portrait and name now head the status pane itself, beside the line that already lived there, and the pane button goes with the bar — the top bar's dock toggle is the phone's one door, where the desktop keeps both of its doors and nothing about them changes. The height the bar and its margin took comes back to the content: the chat thread, and every other view with it, gains the measure by the frame's own flex geometry, not by a new sum anyone has to keep true.
- **The composer footer fits its frame, and clearing a chat is a command** (issue #133). The hint row under the chat bar was sliced at its bottom edge at rest — on a desktop the mode pill's lower border went, on a phone the wrapped second row was cut at the screen's edge, empty thread or full: the Chat frame ends one padding above the window's foot, and the composer's bottom bleed, which exists to meet that foot, was clipped at the frame's edge instead. The frame now reaches the window's bottom edge itself, the composer gives its true height inside it, and the whole footer paints — the same boxes in the same places, the clipped band simply shown. And the row's widest member is gone: the Clear chat button is retired in favour of the composer's own command — type `/cls` and send it, in either mode, and the thread empties with its fold state reset, the line never sent, never run, never in the history — so the footer reads the same in an empty thread as in a full one.
- **The status pane's stale warnings tell the truth again** (issue #141). The page's own build stamps froze at Build 4 — the bridge's stamps advanced every build after, the page's never did — so on every healthy install since, the status column compared a Build 10 bridge against a page calling itself Build 4 and cried wolf twice: a red BRIDGE OUT OF DATE over a bridge that was current, and an amber PREVIOUS BUILD banner naming the wrong build, which no reload could clear because the reloaded page carried the same frozen stamps. The Updater read the same frozen number for the build it was running. The stamps are unified again — page and bridge stamped together, as the first builds were — and the packaging now refuses a mismatched pair outright, so the class cannot ship twice.

### Build 10

- **The bottom of the chat stays at the bottom of the screen** (issue #131). On a phone, the Chat frame's height was reckoned as the viewport minus the top bar alone — the presence bar above the thread, the page's own padding, and the frame's foot were never in the sum — so the whole frame stood taller than the screen by exactly their height, the composer's foot sat that far below the screen's edge, and the page's scroll was what carried it in and out of view: scrolling could drag the composer along with the page. The frame is height-bound on phones now: while Chat is up, the app frame takes the viewport's height exactly, the centre column flexes inside it under the presence bar, and the chat view flexes inside that — so the composer's place at the foot is the frame's own geometry, not a number anyone has to keep true, and nothing that rides above it can push it off the edge. The message list is the only thing in Chat that scrolls; the composer does not move, and its width is untouched.

### Build 9

- **The pane button's face tells the truth** (issue #130). The presence bar's pane button could sit painted in the accent — the open face — over a closed dock, its own pressed state reading closed the whole time: the button is rebuilt by every render, and a button born under the operator's finger (the tap that opened the dock, on a phone) or a resting cursor picked the accent up from the generic ghost hover rule and kept it after the dock was dismissed another way. Its face is keyed to the frame itself now: the accent follows the same #app state classes that show and hide the column and the dock — the classes that *are* the visibility — its pressed state is read off those classes rather than re-derived from a parallel flag, its hover feedback is a background tint that can never wear the state accent, and its color no longer transitions, so the face cannot lag the fact either. One state, read from the one place it is rendered: the button cannot disagree with what is on screen.

### Build 8

- **Her status bar is part of the frame now — and its button is a button again** (issues #123, #115, #114 revisited at the operator's ruling). Navi's presence — her portrait, her dot, her name, her living line — leaves the Chat view and becomes frame chrome: one persistent bar above *every* view, Chat, Settings, Docs, all of them, repainted from the same single presence source and never rebuilt, so it cannot flicker or reset as you move around the app. And the status column's pane button is restored to the bar's top right in its original form — the panel glyph with a pressed state — on every page, not just in Chat: #123 had retired it in favor of the menu chrome's text toggle, which reads as a menu option, not a toggle. And the menu chrome's text toggle — the door #123 left in its place — is retired outright at the same ruling: exactly two doors remain, the bar's pane button on every page and the phone's top-bar dock button, both wearing the panel glyph. Every door drives the one column state, their states in agreement, and the #114 cold-start rules are unchanged — the column still starts hidden on desktop, its state unremembered, the menu groups folded.
- **The portrait actually arrives** (issue #128). Build 7 shipped Navi's portrait inside the package, but the installer never copied it into the install — it copies its assets by name, and the portrait's name was never on the list — so the bridge's portrait route found no file and chat showed no picture: no gutter faces, no presence-header portrait, on every Build 7 install. Build 8's installer carries the portrait into the install exactly the way it carries the app icon, on fresh installs and Updater applies alike (the Updater runs this same installer). And when a copy of the sources has no portrait to copy — a git clone, which carries none of the binary asset files — the installer now says so in plain words and carries on: chat shows without her picture, and nothing else about the install changes.

### Build 7

- **Chat gets faces** (issue #116). Every message in the thread now wears its author's picture in the gutter, their display name — yours from your profile, hers simply "Navi" — and the time it was sent (older messages show the date too); the call transcript in Settings → Voice reads the same way, its spoken marker kept. Her picture is her own portrait — the lamp-post key art, shipped with the app as a bundled asset; yours is uploadable in Settings → Operator, trimmed to a square on the machine, kept with your profile, and carried in the settings backup — until you upload one, a picture generated from your name stands in. And the **Operator Badge** arrives: your self-portrait in the cartridge format — a card-grade face (528×616, the chip-card size) with a face you choose, your uploaded picture or art generated from your name, and a payload inside the picture in the same data-in-picture convention as chips: your display name and this node's name, both self-asserted. A badge is a self-portrait, **not a credential** — nothing anywhere reads one to prove identity, Mesh pairing is untouched, and a damaged payload simply reads as no badge at all. With a badge minted and no picture uploaded, chat can wear the badge's face for you.
- **One status toggle, reachable from anywhere** (issue #123). The Chat header's duplicate status button is gone — the presence header keeps her picture, name, dot, and line, and stops carrying furniture. One control per form factor remains, living in the persistent frame on every view: the menu chrome's Status toggle on a desktop, and on the phone the top bar's button — which now wears the chat toggle's panel glyph, in place of the two plain rectangles. Toggling from any view raises the rail in place on the Status tab; nothing navigates you to Chat to reach it.
- **Two tabs, honestly named** (issue #124). Settings' second tab is **Persona** now, not "Operator & Persona" — its contents (the Soul and Memory editors, the leash, the proposal queue, Her file) were always hers. No content moved; the tab order reads Operator · Persona · Appearance · Voice · GitHub & Backup · System, and a stale saved tab identity degrades to a valid tab instead of stranding Settings.
- **The phone top bar stays put** (issue #125). On phone widths the top bar is pinned to the viewport for real — fixed, with the content offset by its height exactly once — instead of trusting sticky positioning that iOS Safari lets scroll away. The hamburger and the status door are now on screen at every scroll depth, in every view. (Bench-verified as a mechanism; the iPhone field confirmation is still the closing proof, as with every real-device rule.)
- **Node leaves the nav rail** (issue #126). Apex | Systems reads **Mesh · DHD** — the Node child never had a view of its own (it opened DHD, where Apex Node's controls live), so the duplicate door is retired and its glyph with it. Apex Node itself is untouched: its name, its section on the DHD page, and its row in the status column's Servers group all stand exactly as Build 6 left them.

### Build 6

*Build 6 carries the Build 4 menu restructure and the Build 5 field-round fixes — builds that reached field test but were folded forward before standalone publication — together with this round's own work:*

- **The menu's groups cannot collide anymore, and the dividers travel** (issues #105, #106). The Systems children's fold was built as a grid whose template named one row while every child button took a row of its own — the extra rows were sized by nothing and painted over whatever followed, which is why an expanded group ran over its neighbors on a phone. The children now live in a single inner track, the shape the Docs topics always used, and the group's break line is the group's own last element: it sits directly beneath the group's last visible row, folded or open, mid-glide and settled. **Apex | Utilities** gains a fourth member: **Updater** leaves the flat block and joins the utilities group, which reads top to bottom **Settings · Updater · GitHub · Docs** on screen, desktop and phone alike.
- **The status column is a tabbed pane now** (issues #107, #108). A tab bar sits at the very top of the column — **Status** first, **Chats** second, with the chat count — and exactly one pane shows beneath it. Status is the default, and what a phone's dock opens on. The Status pane is the column as it has always been; the Chats pane is the chat manager whole — switch, new, delete, uploaded files — moved up beside the tabs instead of living at the column's foot. When something wants your eye — an update waiting, a stale bridge or page — the Status tab carries a small amber dot while you are in Chats.
- **One motion language, and a Potato mode for weak machines** (issue #109). Every transition in the app — menus, panes, views, cards, presses, the Docs topics' glide — now runs on shared motion tokens, one set of durations and one curve, instead of a duration typed wherever a transition was wanted; the operating system's reduced-motion setting collapses the whole vocabulary to instant. **Settings → Appearance** gains **Potato mode**: "For low-power machines — turns off decorative animation across Apex." On, state changes are cuts, indicators hold still as static state, and the Dark Liquid Glass theme's backdrop blur is suspended too. The choice persists in the config beside the theme and rides the settings backup with it.
- **Settings grew an Operator tab, and the Memories tab retired** (issue #110). The tab order is now **Operator · Operator & Persona · Appearance · Voice · GitHub & Backup · System**. **Operator** holds what Navi calls you, and your file — **About you — memories for Navi**: the entries that exist because you put them there, added by hand or saved from chat at your ask. **Operator & Persona** keeps the Soul and Memory document editors and gains her side: the save-mode leash, the proposal queue, and **Her file — what she keeps** — the entries that exist by her judgment. It is one list underneath, split by the origin every entry already carries; the Build 4 pointer card is gone — the document editor is on the very tab the leash lives on now, with nothing left to point at.
- **The menu widened, the glyphs got honest, and the interface learned to scale** (issue #111). The expanded menu is **196px** now — at 170 the group headers' chevrons clipped at the rail's edge. The Systems children wear their own icons: **Node** has a server glyph of its own instead of borrowing DHD's dial (the icon keys off the child now, not the view it opens), and **Apex | Mesh** wears the **hex trio** — three hexagons in a cluster, one above and two below — replacing the two-hexagon mark that read as a horizontal Venn diagram. And **Settings → Appearance** gains a **UI scale** (100% · 110% · 125% · 150%): the whole interface, words and layout together, like an operating system's display scale — one knob on purpose, because a separate text size would multiply against it and squeeze the fixed rows at the big end.
- **A third group joins the menu: Apex | Navi** (issue #112). Between Systems and the flat block, **Apex | Navi** gathers her mind and tools — **Chips**, **ChipDeck**, **RAG** — and the **Vault** stays flat below it: the shared desk, belonging to neither family. The status column also loses its Call button in this round: the VOICE stat reports state, and starting a call lives where it always also lived — the composer's Call button and the call panel in Settings → Voice.
- **The Voice view is retired; Settings → Voice is the one voice home** (issue #113). The call panel moved whole into the Voice settings tab — the big Call button and the in-call panel with its wave, clock, and transcript; **Hear her voice**; the pipeline strip with each stage's real state; her settings card; the engines-not-installed guidance; the desktop-app microphone known-issue card, verbatim, per-session mic line and all; and the past-calls list. The old pointer card retired with the view. A call is global state: start one anywhere, switch tabs mid-call, come back to it live; ending it from Chat still files it into the conversation. Anything still pointing at the old view lands on Chat.
- **Cold start: quiet by default** (issue #114). Every launch opens with all three menu groups collapsed — Build 4's group-state persistence is gone, and a stale save is cleaned rather than honored — and on desktop the **status column starts hidden**, behind the new **Status** toggle in the menu chrome, its width given to the content until you open it. The toggle is not persisted either: hidden is what "by default" means. The rail itself keeps its remembered open/collapsed behavior, untouched.
- **Her presence moves into the Chat window, and the column gets its door** (issue #115). At the top of the Chat window sits her presence header — her name, her dot, and what she is doing: here (the same living line the status column carries), typing, in a call with you, or away when her model is stopped — computed once, from one function, so the header and the pane never tell different stories. At the header's right edge, hugging the side, sits the status column's toggle: on a desktop it shows and hides the column from the #114 ruling; on a phone the same control drives the dock — one state behind two doors, the phone bar's button and this one, and they never disagree.
- **Cartridge color is family, and a knowledge pack's center is the spray** (issue #117). Chips keep the coral red they have always worn — it is now officially the chip color. Knowledge cartridges wear green instead — the presence green, (52, 211, 153) — bands, header, and every derived tone following the family accent; and a pack's window no longer carries the book glyph: its center is **the spray**, the name-seeded tile field grown to fill the whole window, denser and brighter toward the middle. A pack author's own declared `icon` art still outranks the spray. Mesh pairing cards wear a clear network blue, (59, 130, 246), in place of the old cyan, so the three families read apart at a glance. The face text block is locked in the same round: pixel-art name, the brief description, and a split footer — family and kind at the bottom left, the version at the bottom right, omitted when a picture's data does not know it. Faces are still minted at forge time — installed pictures keep the faces they were forged with.
- **The Docs view gets its own layout frame** (issue #119). The documentation no longer scrolls as one column with the menu riding the article: the Docs view is a fixed frame now — its header still, and below it two panes that scroll on their own, the topic menu and the article, each filling the frame's height exactly. Reading to the end of a long page never buries the menu; the menu keeps its scroll position across page switches, and the open page is kept in its view. The popped-out Docs window shares the same two-pane frame.
- **An update's version stamp lands last, and the Updater can say so** (issue #104). The installer now carries the new bridge and VERSION under staged names and flips them only as its final act — the config's version record first, the VERSION file last of all — so a step that fails before the flip leaves every version witness reading the old build, and Check for updates honestly offers the update again instead of declaring a broken install current. And when the installer exits nonzero *after* the flip, the Updater verifies what is actually on disk before it speaks: a target build standing there is reported as **installed, with a tail failure in the named step** — the step named from the install log — not as the manual-fallback failure. The fallback text remains for the case that earns it: nonzero exit, old build still standing.

### Build 4

- **The branding separator.** From this build, the server names wear a pipe: **Apex | Node**, **Apex | Mesh**, **Apex | DHD** — everywhere the names appear as names: the status column's Servers group, the page headers, the Settings pointers, the module Docs. It is the same separator the phone bar has always worn ("Apex | powered by Navi"). Display only, as every rename in this line has been: config keys, routes, ports, certificate names, and every protocol string are untouched. The notes below are history and stand as written — Builds 1–3 shipped the space form, and their sections keep it.
- **The menu grew groups, and learned to move.** Chat stays pinned at the top, alone. Under a break, **Apex | Systems** is a dropdown whose children wear short names — **Node**, **Mesh**, **DHD** (Node and DHD both open the DHD page, where the Node controls live; the DHD child carries that page's active state). Under a second break, the everyday surfaces stay flat — Voice, Chips, ChipDeck, RAG, Vault, Updater. At the foot, **Apex | Utilities** opens upward: Settings, Docs, GitHub, in their standing order. Group state persists, the groups animate — a quarter-second height glide, the chevron turning, children arriving a breath apart — view switches keep their light fade, and with reduced motion requested, all of it is instant. On the collapsed rail a group header opens the rail to its children; on a phone the groups expand inline, every target finger-sized.
- **Memory the view is gone; its two jobs moved home.** The **Chats** tab is fixed at the top of the status column, beside Navi's status, on the Chat page: it opens the chat manager — switch, start, and delete conversations, and the uploaded files — without leaving the thread; the composer never notices. What Navi remembers from chat — the entries, the save-mode leash, and anything waiting on your word — lives under **Settings → Memories** now, between Voice and GitHub & Backup, carrying a pointer to the Memory document editor, which stays where it has always been, under Operator & Persona.

### Build 3

- **The window has a texture now, and the art is drawn at the face's own fidelity** (issue #101). A chip's window was a flat field with a blocky glyph standing in it. Now the window carries a dim QR-style tile field — twenty tiles across, seeded from the cartridge's name, with finder squares in three corners, at the face accent dimmed to a whisper — and over it the art renders as a solid silhouette with a shade offset beneath it, drawn on the field's very grid. What changed the read was the art itself: all sixteen built-in glyphs — key, lock, hash, text, swap, gear, network, image, music, dice, book, terminal, shield, clock, chart, star — were redrawn at 20×20 as filled objects with a few negative-space cuts: a lock is a body with a shackle hole and a keyhole, a die is a mass with its pips cut out, a book is a cover with a gutter and a band. Each one reads at sleeve size, without its name under it. Knowledge cartridges wear the same treatment: the book, or the pack's own art, solid over the same field.
- **Or bring your own art.** A chip's manifest (navi-chip.json) and a pack's (navi-rag.json) can now declare an `icon`: 20 rows of 20 characters — `#` for the accent, `o` for its shade, `.` for empty. Declared art outranks the built-in glyph; it rides inside the picture exactly like the glyph and the version do, and Chip Studio and RAG Studio both edit it as text rows under the description — a pixel editor is a later build's business. Art in the wrong shape is refused in plain words wherever a face is forged or an export is built; a picture whose art arrives damaged simply falls back to its glyph — a bad drawing never bricks a cartridge. A chip no art claims at all keeps the name-seeded pattern in the window, as it always has.
- **Faces are forge-time, still.** The new treatment is drawn when a picture is forged; published and installed pictures keep the faces they were forged with until they are re-forged.

### Build 2

- **Chip faces are cards now.** Build 1's faces wore the family shell at pocket size with a glyph and no words on them. A new forge draws the chip's face at card grade, with the same renderer the Mesh pairing cards use: the family header, the chip's glyph large in its window, then the chip's name, what it does, and in small print its version and output kind — the cartridge reads like a card, because it is one. A chip no glyph claims keeps the name-seeded pattern in the window, at the same grade.
- **Knowledge cartridges match.** A pack's picture face carries the same card grade now — the book glyph large, the pack's name and what it holds, and in small print its version and how many documents ride inside. The payload inside is unchanged, the ceiling and its plain refusal past it are unchanged, and retrieval still never reads the picture.
- **The chip picture states its own version** (issue #99). A forged or installed chip now carries its version inside the picture, the way it already carried its glyph: the install receipt names it, the ChipDeck sleeve states it, and the face prints it. A picture forged before versions rode inside simply shows none — nothing guesses a version for it anywhere.
- **Faces are forge-time, still.** Everything above is drawn when a picture is forged; published and installed pictures keep the faces — and the payloads — they were forged with until they are re-forged.

## 0.1.8e

Release tag: v0.1.8e — **Build 10**, the tenth publication of this version (the first was Build 1, the second Build 2, the third Build 3, the fourth Build 4, the fifth Build 5, the sixth Build 6, the seventh Build 7, the eighth Build 8, the ninth Build 9; the Build 10 notes sit directly below, and everything under “Build 9”, “Build 8”, “Build 7”, “Build 6”, “Build 5”, “Build 4”, “Build 3”, “Build 2” and “Build 1” further down is those publications' notes, unchanged). Build 5 is the first published build carrying the Build 4 refresh-identity repair (issue #84): Build 4 itself was never separately published — its round-trip gate caught the silent helper death Build 5 fixes — so Build 5 supersedes the unpublished Build 4 and carries its three locks unchanged. Publications of the same Edge version carry an incrementing build number, and the Updater treats a higher build as a refresh of the preview you are running, not a new version — see “Edge build numbers” below. An Edge build — the first test build on the Edge channel, cut from the dev branch, not a full release. Its one feature is **Navi Mesh, Ring 1** (issue #78): pooled inference across your own machines, built to be field-tested on a real pair — a strong home server lending its model to a modest laptop. Ring 1 is deliberately the floor: whole requests, one machine answers, the first reachable lender only. Streaming answers (Ring 2), racing several lenders, and reaching lenders through NAT are NOT in this build, and nothing in it claims otherwise.

### Build 10

- **The update that needed a reboot.** Field report: after updating to the build that added the PNG pairing cards, the new UI never appeared — not after the update, not after relaunching — until the whole computer was rebooted. The files on disk were the new build the whole time; what survived was the old *process*. The installer's stop step fired one polite signal and one second of patience, deleted the pid file either way, and replaced the files — so a bridge that did not die on cue (stopped, stuck, mid-something-it-could-not-put-down) kept the port and kept serving the new pages with its old code, now unfindable: the pid file that named it was gone. The replacement bridge could never bind. The Updater honestly reported the restart failed, and the remedy it offered — relaunch, re-run — could not work against a process nothing would name. Only a reboot, which kills everything without asking, cleared it. That is the one thing an update on Linux must never need.
- **The stop is now a proof, not a gesture.** Before a single file is replaced, the installer finds the running bridge three ways — the pid file, the process holding the port, and every bridge process working out of the install folder (the way a launcher-started bridge is found at all: its command line never names the folder) — asks it to stop, and *waits*, up to fifteen seconds, for the process to be gone and the port to be free. A bridge that will not go politely is ended by force and the wait repeated. If the port still cannot be cleared, the installer stops the install instead: no files are replaced, the pid file is left exactly where it was, and the output names the process holding the port and the exact command that ends it — 'kill -9 &lt;pid&gt;' — so the next step is a decision, not a mystery. The apply helper runs the same check before it relaunches and escalates the same way, and its failure text names the holding process the same way; "launch the app again" is never offered while the port is wedged. A bridge that starts against an incumbent which accepts no requests names that process's pid in its startup message too, even when no pid file survives to consult.
- **A manual install finishes the job it starts.** The installer used to stop the old bridge, lay down new files, and end — the update live on disk, nothing running, until the operator thought to launch the app. Now, when a bridge was running as the install began, the installer relaunches Apex itself at the end and verifies the bridge that answers reports the new build before it says "Done." An install over a stopped app still just installs (launch her when you are ready), and '--no-relaunch' says the quiet part out loud instead: Apex is not running.
- **An open dashboard heals itself.** A dashboard left open across an update is the old build's page talking to the new build's bridge — every response no-store, and still the page itself was the stale half, with no way to know it. The dashboard now compares the build the bridge reports against its own on its regular status check, and when the bridge is the newer one it says so at the top of the status column, with a Reload button: one click lands on the new build's page. (The reverse mismatch — a new page over an old bridge — keeps its BRIDGE OUT OF DATE warning, unchanged.) Behind the DHD door, a forwarded response now carries a single no-store header instead of the pair it used to.

### Build 9

- **The pairing cards stayed home when everything else flew.** A GitHub backup carried her Soul, her Memory, her chips, her Vault — the whole ready-to-fly kit — but the Mesh pairing cards, the pictures two machines pair by, lived only on the machine that held them; lose the machine and every peer had to be met again from nothing. The essentials checklist (Settings → GitHub & Backup) gains **Mesh pairing cards**: a backup now carries this machine's own card as a PNG, minted fresh from the live card as the backup runs, and a PNG for every paired peer, re-drawn from the stored card — the payload inside each picture is the card itself, so it imports whole on any machine, exactly as the original picture would. Restoring lands the pictures in config/mesh/cards/ and re-pairs the peers through the same validation a hand-dropped picture passes; your own card is kept as a file there and never overwrites the restoring machine's identity. Two things still never ride: the node keypair — a restored machine mints its own identity and pairs anew, the backed-up pictures turning that into a re-exchange instead of a cold start — and the Mesh ledger, which keeps its own separate opt-in, off by default.
- **The text card retired; the picture is the card now.** Pairing used to offer two ways to carry a card between machines: a block of text to copy and paste, and the PNG picture. The text way is removed in this build: the Mesh page no longer shows a copyable card or takes a pasted one, and the bridge no longer accepts one — pairing is the picture, only. Download PNG card on one machine, carry the file, drop it onto the other machine's Mesh page or use Upload a PNG card there. A text card saved from an earlier build can no longer be pasted anywhere; re-download that machine's card as a PNG instead. Machines already paired are untouched — their records never depended on how the card travelled, and borrowing, lending, and fusion carry on exactly as before.

### Build 8

- **Two attributions, two rows — and the wrong one on top.** Field report from the first real pair, the same evening Build 7's fix was confirmed working in production: a reply that was both borrowed from a paired machine and informed by a knowledge pack stacked two pill rows under itself — the source pills first, drawn as the answer rendered, and the Mesh pill — *via <machine>*, the one that says whose mind actually wrote the reply — underneath them, in the second row, where a glance never lands. Each pill kind rendered its own row, so a reply carrying both always stacked, in render order rather than in the order a reader needs. The pills now share one row: the Mesh pill first, then the source pills, all on a single line that never wraps — on a phone the source pills ellipsize inside the row instead of pushing the page sideways or dropping the attribution to a row of its own. A reply with only one kind of pill renders exactly as before, and fallback notices (a busy or dropped lender) stay plain lines, as they always have.

### Build 7

- **Paired machines sat at "not checked yet" forever.** Field report from the first real pair, photographed on both machines: pairing worked, lending was armed, the consent toggles held — and both rosters still said the other machine was "not checked yet", so no borrowed answer could ever start. The check itself was sound; nothing ever ran it. The only thing that ever probed a peer was a chat message attempting a borrow, and the status display read a cache that forgot every result after sixty seconds — so a machine that only lends, or a pair nobody had chatted across yet, showed "not checked yet" as its resting state, and a failed check quietly decayed back to it, taking the reason with it.
- **The fix: the bridge watches its peers itself.** A background health check now probes every paired peer about every thirty seconds while Mesh is on — and immediately when a peer is paired and when Mesh is turned on — so a pair reaches "checked" on its own, with no chat sent. A probe result no longer decays: the roster and the status column keep the last word — *unreachable — unauthorized (last checked 42s ago)* — until a newer check replaces it, and "not checked yet" now means only that no check has ever run. The bridge log notes a peer going dark or coming back, with the reason, and stays quiet otherwise.
- **A trap behind the first trap, removed.** Inbound requests were authorized against the lender's own "can borrow" flag for the requester — one flag doing two opposite jobs — so on a pair where that flag was off, the first real check or borrow would have been refused as unauthorized, with the reason shown nowhere. Pairing is the consent now: a paired machine's validly signed request is accepted, and the flag means one thing only, on the borrowing side — this machine will not borrow from a peer whose "can borrow" is off.
- **Cards and first knocks, hardened.** A card now carries every non-loopback address the machine has — the LAN address first — instead of freezing the one address the default route happened to pick, and a certificate fingerprint mismatch at one address no longer aborts the attempt: the borrower notes it and tries the next address on the card, refusing only when no address both answers and matches. And a machine whose Mesh name was never set no longer sits "Unnamed": turning Mesh on with the name blank keeps the machine's hostname as its name.
- **The lending caps are yours to set.** The share of each hour a lender gives up, the borrowed generations it takes an hour, and the per-machine share of those were fixed numbers — 25%, 20, 10 — written for a modest laptop and never meant as a server's ceiling. They are settings now, on the lending machine's own Mesh page, in the Lending section beside the Caps line: share of each hour (1–100%), generations per hour, and per machine per hour (1–10,000 each). They save into the machine's config and govern the very next admission and the very next card it shows — no restart — and because the card advertises the caps you set, a paired machine sees the real offer ("lends at most 50% of each hour, 60 generations an hour") instead of the defaults it shipped with. The defaults themselves are unchanged: a fresh install still lends at most 25% of each hour, 20 generations an hour, 10 per machine, until you say otherwise.
- **Idle-only lending has an override.** A lender used to serve only after sixty seconds of quiet — right for a laptop, wrong for a server that has taken concurrent work before and can again. The Lending section gains a **Lend only when idle** switch, on as shipped: turn it off and the machine lends without waiting to be idle, borrowed generations running alongside your own work (your own replies may slow down — the switch's own line says so). The caps still bind, and one borrowed generation at a time still holds: a request that arrives mid-generation waits for the next slot, as it always has. The card and the status line state the posture truthfully either way — *lends when idle*, or *lends even while busy*.
- **A re-enabled lender is believed at once.** A borrow decided "not lending" from a status the health check had cached moments earlier — so after "Stop lending now" and a quick re-enable, borrows kept refusing with the stale answer and were never even attempted. A not-lending verdict now earns one fresh check before the borrow gives up: a lender that is lending again serves the request, and only a lender still off on the fresh check answers "not lending".
- **Pairing travels as a picture now.** "Show my Mesh card" gains **Download PNG card**: a real .png whose face is the card a person reads — the machine's name, its node identity, and the offer in words (its capabilities, the lending limits it is configured with, whether it lends when idle or even while busy) — with the whole card riding inside the picture in the same data-in-picture format the chips use, so Apex keeps one cartridge language. On the other machine, drop the picture onto the Mesh page's Paired machines area, or use **Upload a PNG card** there: the peer is added exactly as a pasted text card adds it — same validation, same record — and text cards from every earlier build still pair. The picture has to travel as a file: chat apps like Discord recompress uploaded pictures and strip the data out, so the docs say to send it inside a .zip, and the Mesh page says the same when it meets a picture whose payload is gone — no readable Mesh card data, probably recompressed by a chat app, resend the original inside a .zip. A damaged or cut-short payload, a chip cartridge dropped in by mistake, and a file that is not a PNG at all are each refused with their own specific words — never a silent no-op.
- **A borrow refused for not being idle no longer falls back in silence.** Serving a borrow restarts the lender's idle clock, so the very next chat — anything sent inside the lender's idle minute — was refused at the door as not idle yet and answered locally instead, with nothing to show a borrow had ever been attempted; a borrow refused that way never even registers on the lender. The borrower now waits out the lender's remaining idle window inside the same borrow grace it already gives a busy lender: it checks until the lender itself reports idle, then asks once more. The wait is deliberately bounded by that grace and no longer — a lender that goes idle only after the grace is spent serves the next request, exactly as a busy one does — and admission on the lender is untouched: it still refuses until it has been quiet. Only the borrower's handling of that one refusal changed.
- **A recorded drop is not erased by the next failed check.** Once a lender had died mid-answer, the drop it left on the roster was being cleared by the borrow meant to find it: the borrow read a recently cached failed check, forced one more check, found the peer still dark, and threw the drop record away — so the status row fell back to a plain "unreachable" and the warning the drop earned never showed. A failed check — cached or fresh — now never clears a recorded drop: the drop is the freshest thing this machine knows about the peer, and it stands until a check actually succeeds, a borrow is served, or five minutes pass.

### Build 6

- **The "Lend this machine" switch looked alive on the DHD door — and could never turn on.** Field report from the home server, minutes after a reboot: clicking Lend answered, the page flashed, and the switch stayed off — the same experience as the Build 1 master-switch failure. The mechanism is different, and the bridge was doing its locked duty: lending may only be turned ON in person, from the lending machine's own dashboard, never through the DHD door — and a turn-on arriving through that door is refused. What was broken was the surface: the Mesh page rendered the switch as a normal live toggle on the remote view too, and the refusal came back as a small message at the foot of a long card, where a person mid-click never sees it. A locked control dressed as a working one is a broken control, whatever the bridge's reasons.
- **The fix: the lock now shows at the switch.** The dashboard's status now says whether the view arrived through the DHD door. On that view, with lending off, the Lend switch renders locked — dimmed, not clickable — with the reason in plain words directly under it: lending turns on at the machine itself, in person. With lending on, the switch stays live on the remote view, because turning lending OFF works from anywhere you are signed in — with a note that turning it back on means a trip to the machine. Mesh save and refusal messages now appear at the top of the Mesh card, at the controls, instead of at its foot. Nothing about the lock itself changes: the bridge still refuses a remote lending turn-on no matter what any client renders, lending still runs only when idle inside its caps, and "Stop lending now" still ends it at once, from anywhere.

### Build 5

- **The update helper died in silence, and the install was left with no bridge.** Caught by Build 4's own round-trip gate — a genuine Build 3 install applying a package through its own Updater, the new closure bar doing exactly its job. The staged installer ran through to "Done.", and then nothing: the detached helper that runs the installer, relaunches Apex, and finishes the apply record left apply.log at 0 bytes, never created its relaunch log, and left the record frozen at working/installing — no bridge relaunched, the install left bridge-less. The helper's code was identical in Build 3 and Build 4; the machinery was older than both, and it was built traceless: it printed nothing by design, kept no log of its own, wrote the record only at step boundaries, and carried no guard and no signal handlers — so any death between two writes was indistinguishable from any other, and from a hang.
- **The diagnosis, ranked.** First and best-fitting: an external signal kill at the installer's end — the helper sits in its own session but in the same process tree and user-service world as everything the installer stops and restarts at exactly that moment, and a SIGTERM or SIGKILL leaves no trace in the victim; crucially, it is the only mechanism consistent with all the evidence at once, since a Python-level exception would have left a traceback in apply.log and the log was empty. Second: an uncaught exception in the helper's unguarded post-installer segment (its record writes run against a config tree the installer has just replaced) — a real path, now closed, though it predicts a traceback this incident did not leave. Third: a block inside the installer wait — the old design could not tell a block from a death at all, which is part of the indictment.
- **The fix: the helper keeps a diary, and the record can no longer freeze.** From its first instruction the helper writes a step log — updates/<tag>/apply-trace.log, its path carried on the apply record — timestamping every step boundary, the installer's exit, the relaunch spawn, and the confirmation's found-vs-expected values, with a heartbeat every 30 seconds while it works (a log still beating at one step is a block; a log whose beats stop is a kill — the field can finally convict the mechanism). A top-level guard turns any exception into a failed record naming the step and the reason in words, and mirrors the traceback into apply.log; handlers do the same for SIGTERM, SIGINT and SIGHUP before the helper exits. A relaunch that cannot even start now fails loudly at the restart step, and a relaunched bridge that never answers fails at restarting with what was expected and what was found — never a frozen working/installing. And for the one death no in-process guard survives (SIGKILL, the kernel's OOM killer, power loss), the bridge's **apply watchdog** closes a record whose helper is gone and whose last write has gone stale — failed, at the last step the helper provably completed, quoting its step log's final line. Build 4's three locks stand exactly as they were — the leftover size check, the package build-identity verification, and done-requires-target-build (the relaunched bridge reports the target build AND the bridge on disk carries it) — along with the apply checklist, state preservation, channel logic, and the build-named labels.

### Build 4

- **A refresh that installed the previous build and called it done.** Field report from a live install: the Build 2 → Build 3 refresh downloaded, installed, and passed its checklist — then the install still identified as Build 2, so every new check offered Build 3 again. The root cause sat in the apply's own download step. An update stages its package under a folder named by the release tag, in a file named by the release asset — and both names are the same for every publication of one version. The Build 2 apply had left its downloaded package at that exact path, and the Build 3 apply's download step read a package already beside the app back instead of fetching the offered one — so it staged and installed Build 2's bytes a second time. Nothing downstream could catch it: the apply's confirmation compared only the VERSION number, which is deliberately identical on both sides of a refresh, and the "Updated v0.1.8e Build 2 → Build 3" label was composed from the release feed, never read back from what had actually landed. The installer's copy set, its state preservation, and the relaunch were all innocent — the relaunched bridge really was a new process, faithfully running the old build's files.
- **The fix: the apply proves the build, three times.** A package already beside the app is now reused only when its byte size equals the size the feed names for the offered asset; anything else is fetched fresh, overwriting the leftover. Verification then reads the build sequence baked into the package's own bridge.py and requires it to be the build on offer — a stale leftover that slips past the size check is discarded and the offered package fetched fresh once, while a fresh download that itself names the wrong build fails at the verifying step, in words, with nothing staged. And the confirmation at the end observes the build itself: the status answer now reports the running bridge's build sequence beside its stamp, and the apply helper confirms "Updated" only when the relaunched bridge reports the target build AND the bridge.py on disk carries it — otherwise the record fails at the restart step, naming the build it found instead of the one it expected. The rule is general — it holds for any same-version refresh, Build N → Build N+1 — and graduations and new-version updates, whose tags (and therefore staging paths) always differ, are untouched. What Build 3 built is preserved exactly: the build-named refresh labels, the apply checklist, state preservation, and channel resolution.

### Build 3

- **The Updater panel reads in its final order — the same order in every state.** Current and status card first, with the warnings directly under it, then the Release channel card, then the patch-notes surfaces, then the Check and Download & install buttons directly underneath the notes; below the buttons sit the live progress chain while an install runs and, once an apply has finished, its record — the "Updated …" card with the update log, or the manual fallback after a failure. No state rearranges it: a finished apply's outcome cards stay below the buttons, in the same seat the progress chain occupied while it ran. The composition is verified against the rendered panel in every state (idle, checking, update on offer, installing, updated, failed), not against the page's text.
- **A refresh names its builds.** Updating from one build of this preview to the next used to confirm as "Updated v0.1.8e → v0.1.8e" — true and useless. For a same-version build refresh, the confirmation now names the builds — "Updated v0.1.8e Build 2 → Build 3" — in the Current card's line, in the result card's heading, and in the update log's confirmation line. Graduations and new-version updates keep the plain version labels they always had.
- **Borrowed replies wear a pill.** A reply a paired machine wrote for you no longer carries a plain "Answered by <machine>" line: it wears a small pill under the message — the Hexlink glyph and "via <machine>" in Mesh cyan — the same quiet register as the source pills under an answer that drew on a knowledge pack. A fallback stays a plain notice line (a dropped lender is a warning, not an attribution), and a reply this machine wrote itself carries nothing, as before.
- **These notes print once.** The stacked notes no longer repeat the current build's notes twice — once as a summary blurb at the top and again as that build's own section. From Build 3 on, a publication's notes are a short identifying header (tag, channel, build, changelog link) followed by the per-build sections, newest first, each printed once; earlier builds' sections stand unchanged.

### Build 2

- **Turning Mesh back on works.** In Build 1, once Mesh had been turned off, turning it on again quietly did nothing — the click answered like a save, the page flashed, and the switch stayed off with the rest of the Mesh page (machine name, Borrowing, Lending, Paired machines) never appearing. The save was undoing itself: the bridge applied the change, prepared the machine's Mesh identity, then reloaded its settings from disk and saved THOSE — and because the identity was already on disk, nothing in that path rewrote the file in between, so the reload brought the old off state back and saved it over your click. Fixed: the settings you save are the settings that get kept; the identity's bookkeeping no longer overwrites them.
- **The Updater follows the build you are running.** Until you choose a release channel yourself, an Edge build's Updater now defaults to the Edge channel. Before this fix, an install whose settings predated channels sat on Stable by inheritance — and an Edge preview there was told it was "on the latest release" while Stable's v0.1.7 was named as "the same as yours". Stranded: no Edge build or refresh of the preview could ever be offered on that channel. A channel you pick yourself still wins, exactly as picked; and if you run an Edge build and set Stable yourself, the Updater panel now carries a plain notice that Edge updates won't arrive on that channel. A check that follows the Stable channel under an Edge build no longer claims Stable's newest is the same as yours, either — the verdict names the channel the check followed.
- **The Updater panel reads in its announced order.** Current and status first, then the warnings, then the patch-notes surfaces, then the Check and Download & install buttons underneath the notes, then the progress chain — and the Release channel card last.

### Build 1

### Navi Mesh — Ring 1 (#78)

- **Whole requests, one machine answers.** When Mesh is on and a paired lender is reachable, a chat request is assembled on your machine exactly as always — persona, Vault, knowledge packs, history — and the lender's own model writes the whole reply. The reply says who wrote it: "Answered by <machine name>" under the message. CLI mode, chips, and every built-in route never borrow; only model answers do.
- **Pairing is a card, carried by hand.** Each machine shows its Mesh card on the Mesh page — its name, node id, public key, certificate fingerprint, addresses, and a capabilities block as one copyable block. Paste the other machine's card into yours (and yours into its) and the pair is made. Pairing is the consent act: a paired machine is a trusted machine. Nothing anywhere is tied to a specific operator, machine, or domain — every name and address comes from the cards and your config.
- **Borrowing is automatic, with off switches.** For paired machines, borrowing just happens when a lender is reachable (Alex's ruling) — and there are three ways to say no: the borrowing switch, the Mesh master switch, and a per-chat "keep it on this machine" toggle beside the composer. If the lender is busy, your machine waits a short grace (2 seconds by default, yours to set) for it to free up, then answers locally; a freed lender serves the next request, never a half-written one. If a lender drops mid-answer, you get the notice — "<machine> dropped mid-answer — this reply was generated locally instead" — and a fresh local reply, never two models' prose spliced together.
- **Lending is automatic when idle, and off means off.** A lender serves only while it is idle (60 seconds quiet by default), inside caps you set: at most 25% of each hour, 20 borrowed generations an hour, 10 per machine. Your own work always takes the next slot; a local request never kills a running borrowed answer. "Stop lending now" does: it ends lending and aborts a borrowed generation mid-flight, at once. Lending can only be turned ON from the lending machine's own dashboard, in person — never through the DHD door — and off from anywhere you are signed in.
- **Signed, pinned, and private.** Every Mesh request is signed with the borrowing machine's Ed25519 node key and checked against the paired card; the connection's certificate is pinned to the fingerprint on the card, and a mismatch is refused in plain words. Mesh always listens on its own dedicated TLS port (8765), through its own certificate — the one the card pins — whether or not DHD is on; the DHD door refuses Mesh traffic outright, and a dashboard guest can never reach it. What travels is the assembled prompt, including your Soul and Memory text — the Settings card says so in plain words before you borrow for the first time. What never travels: files, data stores, credentials, command-line access. The lender keeps nothing of the content: its ledger records only who, which direction, and how long, and the balances it feeds are records, never a gate.

### Mesh gets its own page, its own door, and a roster

- **Mesh is a top-level page now.** The dashboard's left menu gains **Mesh** (with its own Hexlink icon — two interlocking hexagons), right after DHD. The full controls moved there from Settings → System, which keeps a one-line summary and a button that jumps to the page.
- **A dedicated door, always.** Mesh no longer rides the DHD door when DHD is on: its TLS listener on the Mesh port (8765) runs whenever Mesh is enabled, its own certificate is the pinned one in every configuration, the DHD proxy refuses `/mesh/*` with 403, and the dashboard surface no longer serves the node-facing status/borrow endpoints at all — borrowers dial the dedicated port from the peer card, only. Dashboard-local Mesh routes (`/mesh/card`, `/mesh/lend/stop`, `/api/mesh/*`) stay exactly as they were, behind the gate.
- **Capability cards and the roster.** A Mesh card now carries a capabilities block — the machine's own report of its hardware class, GPU or CPU, RAM, model (navi), speed class (GPU-accelerated / Integrated graphics / CPU), and its lend caps. The Mesh page puts the controls first, with a **roster** below them: this node and every paired node with name, capability line, live status, and balance. Addresses never render anywhere in it — they stay plumbing.
- **Stop lending really stops.** The consent fix behind this round: "Stop lending now" now shuts down the in-flight borrowed generation's socket, and a borrow that finishes after the stop is recorded as aborted and dropped instead of served. The claim and the behavior finally match.
- **Instant-off completes on the borrower's side too.** Stopping lending now drops the borrower's in-flight chat promptly into the fusion fallback — the dropped notice and a fresh local reply — instead of stranding it: the lender hard-closes the borrow connection at the socket level, and the borrower reads that termination as the drop it is.
- **Docs and Settings sit at the foot of the menu.** The left menu's two housekeeping stops moved down to stack directly over the version number at the menu's foot — Docs on top, Settings directly over the version number; the working views keep the top of the menu in their usual order.
- **Mesh status, at a glance.** The Servers status row for Mesh now shows connection state and warnings where you already look, in the same dot language as every other row: green when a paired machine is reachable, amber while it borrows or lends — and amber with the reason in its line, "<machine> dropped" or "<machine> unreachable", when something is wrong — grey when Mesh is off or nothing is paired yet.

### The Updater round

- **Edge build numbers.** Publications of the same Edge version are numbered — Build 1, Build 2, … — parsed from the release's name or opening lines. At the same version and status, a higher build number is a newer update; the same or lower is not. The Updater's Current line shows your build ("· Build 1"), and an available same-version refresh is labeled with its build.
- **Background re-check.** While the bridge runs, it re-checks for updates on your configured channel every three hours, the first run shortly after startup. The dashboard folds the verdict into the Updater's passive states — "Update available" appears on its own, and a stale one clears — without ever overriding a check, an install, or a finished state in progress. The status bar keeps its single "Up to date" / "Update available" voice.
- **The Edge notice.** When the update on offer is an Edge pre-release, the Updater shows a calm amber preview notice above the notes: you are on the preview line, preview contents can change between builds, Soul/Memory/chips/packs carry over, and the next full release supersedes the preview automatically. A same-version refresh is worded as a refresh ("Build 2 replaces Build 1"), never as a new version; graduating from Edge to the full release gets a positive green notice instead. Stable-channel full releases get no notice.
- **Panel order.** The Updater panel now reads: Current/status card, warnings, the patch-notes surfaces, then the Check and Download & install buttons underneath the notes, the progress chain, and the Release channel card last.

### Two phone fixes

- **One cookie, both doors (#71).** The DHD door minted the access cookie with a `Secure` attribute the LAN door never set, so a phone that signed in through DHD could be bounced at the gate while its tabs rendered empty. Both doors now mint the identical cookie, and when a dashboard API call answers 403 the dashboard bounces to the gate page instead of painting confidently-empty tabs.
- **Template slip (#73).** A dashboard template lost the escapes in one chat-intent check, shipping literal backspace bytes in the page. Fixed at the source, and the generated package now scans clean: no stray control bytes.

### Chips — installs that prove themselves (#79)

- **Discovery.** Installing a chip now verifies itself: after writing the cartridge, the bridge re-scans and answers honestly if the chip landed on disk but does not list, and why. A cartridge whose payload will not parse is no longer silently dropped — it lists in Local as "couldn't be read" (still deletable, skipped by the dock pill row and the runners). `/api/status` now reports the bridge's install root, and the status column shows it in the bridge detail line, so a split install tree is diagnosable at a glance. Local chip cards no longer flex-shrink below their content — the mid-text clipping is gone.
- **Legacy chips run.** The installer now fetches a chip repo's .py files **recursively**, so package layouts keep their relative paths, and reads `chip-requirements.txt` when a repo declares one — the card surfaces the declared dependencies plainly ("not installed automatically"; nothing is auto-installed). At run time, a chip with package structure loads as a package member, so its relative and package imports resolve, and every sandbox gets the legacy `navi.py` compatibility shim (`get_parameters`, old semantics) unless the chip ships its own.

## 0.1.7

Release tag: v0.1.7. The bundled release: the Updater round (#70) and Navi's memory from chat (#72), built together in build 2026-11-09.81, first prepped as an alpha in build .82, and re-cut as this full release — with release channels built in — in build 2026-11-09.83. The installer hardening (#75) landed in build .84, before the release went out.

### Release channels, and the new version language

- **Two channels in the Updater.** The Updater now follows a channel, chosen in the Updater view and remembered. **Stable** (the default) follows full releases only, cut from the main branch. **Edge** follows the newest release including pre-releases — test builds cut from a separate dev branch, kept apart from main — so opting into Edge is how a machine gets those builds at all. Checks and installs both run on the chosen channel.
- **Full releases wear the bare number; pre-releases are Edge.** A full release is just its number — 0.1.7, tag v0.1.7, no status word, no letter. An Edge build of a version reads 0.1.7e (tag v0.1.7e). The old alpha word and "a" suffix are retired: older VERSION files and tags written that way still read correctly everywhere, as Edge. An Edge build of a version is its preview, not an upgrade over the full release; when the full release of the same numbers lands, graduating to it is the update.
- **The current release's page, in the Updater.** The Updater gains an "About this release" dropdown carrying everything the GitHub release page offers for the version you are running — release name, tag, Edge/full badge, published date, the link, the package asset, and the full patch notes rendered in place — fetched alongside the update check.

### The installer stops dying in shells with no terminal (#75)

- **A terminal counts only if it opens.** The installer asks its two questions (startup mode, her voice) only when it can actually hear the answer: the test is opening /dev/tty, not checking whether the device node is readable. In a shell with no controlling terminal — her own CLI shell is the field-proven case — the old readability check passed and the read died mid-prompt ("/dev/tty: No such device or address"), killing a staged v0.1.7a install on NeoArcadia after the bridge had already stopped for it. A terminal-less run now gets the plain instruction instead — re-run with --startup / --voice — and a terminal that stops answering mid-question ends the same clean way.
- **The update path carries the answers as flags.** The one-click apply and the manual fallback command both pass --startup and --voice from the install's own settings (the config's startup mode; her voice counts as installed when her venv is on disk), so an update never depends on the staged installer being able to ask anything.

### The Updater learns to warn, and the install chain moves (#70)

- **Turn Sudo Mode on before you update.** The installer's system step needs root; without it an update can stall or finish without its system packages — field-proven on NeoArcadia, where a deliberate rollback test (VERSION edited back to 0.1.0, then updated under Sudo Mode) completed clean end to end, twice. When an update is available and Sudo Mode is off, the Updater now shows a red warning directly above the Download & install button: "Enable Sudo Mode before updating. The installer's system step needs root. Without it, an update can stall or finish without its system packages." With Sudo Mode on, the warning is replaced by a quiet green "Sudo Mode is on — ready to update." It is a warning, never a lock: the button still works.
- **The chain above the notes, with a slim progress bar.** Once the operator opts into an update, the install chain (downloading, verifying, staging, installing, DHD prerequisites, restarting) renders directly above the release notes instead of below them, with a slim progress bar across the top of the chain card — the bar for the glance, the chain for the receipts.
- **"Taking a while?"** Once the Installing step has been underway a while, the chain says what the time is going on: "This step is likely rebuilding the UI — that can take a few minutes on modest hardware. It's working, not stuck. We're working on making it faster." No countdown, no ETA.

### Navi pulls memories from chat (#72)

- **Two doors.** A natural trigger — "remember this", "remember: …", "save this to your memory", or the Save to memory button under any operator message — and autonomous saves: when the operator says something durable (a fact, a preference, a decision, a commitment, a correction), Navi saves it in the same reply she was already generating. No second inference pass; the fluidity law holds on modest hardware.
- **Nothing is saved silently.** Every save leaves a receipt in the chat showing exactly what she wrote, word for word, with a one-tap Undo. The Memory tab's entries say how they got there: added by hand, from chat (asked), from chat (her call), or from chat (correction).
- **Corrections replace.** A save about the same fact as an existing entry replaces it — matched by fact key (name, home, work, favorite …) or heavy word overlap — instead of piling up a duplicate; Undo restores the old line.
- **Secrets are never saved**, on any path. A password, key, or card number is refused in words, and the refusal receipt shows no payload.
- **The leash is a setting.** Memory mode: She saves on her own (the default), Ask first (autonomous saves wait as proposals, in the chat receipt and the Memory tab), or Only when I say (trigger only). In the shipped app the judgment rides her persona prompt as a [[remember: …]] marker the bridge strips before the reply is shown or spoken; the saves return as payload data and the dashboard files them and draws the receipts.

## 0.1.6 (alpha)

Release tag: v0.1.6a. The polish release: the Enter Code gate (#64), the Vault tree menus (#65), and the Servers collapse with the tag-form menu footer (#66) are first published here, together with two fixes from the v0.1.5a field test — the Servers group's missing spacer (#67) and the Vault navigation panel's move to the right, rebuilt so it cannot drift again (#68).

### The Enter Code window (#64)

- **One gate, both doors.** The two bare code-entry snippets — one for the Apex Node (LAN) door, one for the DHD door — are replaced by a single shared gate page in the bridge, parameterized by door, so there is no second copy to drift. The contract is unchanged: the same POST to /__gate, the same acceptance cookie, the same redirect into the dashboard; loopback is never gated and the API's 403 answers are untouched. The page still serves nothing before the code — one self-contained HTML page, inline CSS and SVG only, no external assets, fonts, or scripts — and no version string appears anywhere on it.
- **The look.** A deep-space backdrop — layered nebula gradients and a fine starfield — behind a glassy card. The DHD dial glyph, twelve chevrons around a glowing core, turns slowly above the APEX wordmark on the DHD door and rests calm and dimmer on the Apex Node door; all motion honors prefers-reduced-motion. The card names the door being knocked on — the domain for DHD, the machine's hostname at home. The page ends at the card: no footer tagline (Alex's ruling on the mockup).
- **The field and the failures.** The code box autofocuses on load, accepts one-time-code autocomplete, renders at full phone size with no focus zoom, and Enter submits as before. A wrong code re-renders the same page with the error in place, the field cleared and refocused, and a shake on the card. The DHD door now shows the throttle it always enforced: attempts remaining before lockout, and — while locked — the form disabled with the remaining lockout time. The Apex Node door's copy is corrected: the code is found on the DHD page of the machine Apex runs on.

### The Vault — tree menus and the right-side panel (#65, #68)

- **The Vault tree gets its names back (#65).** On the live field screenshot the file-tree panel's header controls were crushed into two-letter stubs and every note row spent most of its width on permanent Move / Rename / Delete buttons while the note names truncated. Now the create controls wrap to two lines with full labels instead of truncating, and each note and folder carries a single ⋯ menu (a 44px touch target, keyboard-reachable) holding its actions — Move, Rename, and Delete-with-confirm for notes; New note and Delete for folders. The names take the row's width; drag-and-drop, the touch Move picker, import, search, and templates are unchanged.
- **The navigation panel sits on the right — by placement, not by reversal (#68).** The editor/tree pair claimed the right side since build .73 through a reversed flex row, and the operator's live read diverged twice: at shell and browser widths alike the pair could sit left-anchored mid-page, its placement hostage to how each engine resolves a reversed, wrapping flex line. The pair is now an explicit two-column grid that spans the full width of the view: the editor is assigned the first column, the files panel the second (280px), each by name, in the shell's webview and in a browser alike. On phones (≤800px) nothing changes: the panel stacks full-width above the editor, exactly as before.

### Servers — a parent, with its spacer (#66, #67)

- **Servers is a parent now (#66).** The status column's Servers header collapses and expands the whole group — Llamafile, Apex Node [local], DHD [public] — and remembers the operator's choice across re-renders, exactly like the per-row dropdowns it parents. Shut, the header still carries one dot per server in that row's own colors, so collapsing never hides a problem. Rows, dots, and dropdown contents are untouched.
- **The spacer is back (#67).** The Servers parent was the one status block without the column's standard boundary, so in the expanded default state Sudo rendered flush against the DHD row. The block now carries the same boundary as every other status block — the same gap, padding, and divider — in the expanded and collapsed states alike. Section order and the collapse behavior are unchanged.
- **The menu footer reads like GitHub (#66).** The version at the foot of the side menu is centered and written in tag form — **v0.1.6a** — in the same status colors as before (alpha red, beta yellow, stable blue, no tag on stable); the collapsed rail keeps the same whole string, centered, unclipped. Display only: the VERSION file, the bridge's reporting, and the Updater's comparisons are untouched.

## 0.1.5 (alpha)

Release tag: v0.1.5a. The DHD release: Apex gains its public door — and the door tells the truth about its address. The honest public-address model (#59) and the installer/packaging fixes (#60) land here, and the Vault and markdown rounds (#53/#54), whose fixes shipped in earlier builds, close at this release.

### Fix — honest DHD addresses (#59, from the Build 10 field test)

- **A LAN address is never a public address again.** The DHD state now carries three separate addresses: the domain (the public address once its certificate is live and the name resolves to this machine), the detected public IP, and the LAN address — which lives in its own labeled home, **On this network (LAN)**, on the DHD page and in the status dropdown, and never under a public label.
- **WAN detection.** The bridge learns this home's public IP with a small cached HTTPS echo lookup that degrades to "couldn't detect" instead of ever blocking an enable. A detected address that is itself private or carrier-NAT (100.64.0.0/10) is reported plainly as **behind another router/NAT**.
- **"Reachable anywhere" is earned.** It appears only when the public path is proven — domain set, resolving to this machine, ACME certificate live. Otherwise a running DHD reads **on/listening, outside reach unverified** and names the next step (forward 443 + 80 on the router to this machine, or add your domain). The ladder's last step is labeled a **local check** — "answered on this machine."
- **Its own proxy is a healthy state.** When 80/443 are held by Apex's own DHD proxy, the availability rows read **"In use by Apex's DHD proxy — this door working"** and re-enabling treats its own listener as success — never "port is not free."

### Installer and packaging fixes (#60)

- **A --fresh reinstall keeps your DHD certificate.** The certificate home (config/dhd/) joins the installer's keep-list: it is stashed before the fresh wipe and restored after it, the same treatment the Vault already had — a real certificate survives a fresh reinstall instead of being wiped and re-issued.
- **The package's docs install with the app.** The installer now copies the package's docs/ into the installed tree, so docs/DHD.md sits on the machine beside everything it documents, and the shipped tree and the installed tree agree.
- **A fresh package starts with the DHD off.** The packaged config defaults ship dhd.enabled=false no matter what state the machine that generated the package was in — package defaults never inherit live session state, and the door opens only when the operator clicks it on.

### DHD — Apex from anywhere

- **DHD** (Dial-Home Device — the way home) is a new top-level menu destination, after the Vault and before the Updater, with a theme-tuned dial glyph. It extends Apex Node's same dashboard to a genuinely public address on your own machine — everything self-contained: no Tailscale, no external tunnel or proxy service, no Certbot.
- **One click.** The DHD page's master switch does everything: Apex generates a certificate, brings up its own reverse proxy on 80/443 in front of the bridge (the bridge itself binds loopback only in DHD mode — the proxy is the only public face), runs a reachability self-check, and reports the live state and URL — or names the failed step in plain words, leaving the previous state untouched.
- **TLS from the first click**: a self-signed certificate Apex generates when no domain is set; when you add a domain — optional, free-form, addable at any time — Apex's own built-in ACME client obtains a real Let's Encrypt certificate (HTTP-01 through the Apex proxy) and renews it automatically at 30 days remaining or less.
- The door keeps the **existing access code** (same code, same cookie as Apex Node), now with public-side throttling: progressive delays and a five-minute lockout after five wrong codes. A session through DHD is a full session — the one-click Updater works from it end to end.
- The status column gains a **Servers** group — Llamafile, Apex Node [local], DHD [public] — each with a pulsing green/amber/grey status dot and its own dropdown of details; directly under Navi's status, bracketed by separators, a single update line reads a green **Up to date** or a yellow **Update available**. The Apex Node controls live on the DHD page, under the DHD options; Settings → System keeps only a pointer to them.
- Docs gain a DHD page (and docs/DHD.md): the one-click flow plus the backend you may still handle by hand — router forwarding for 80/443, DNS and dynamic-IP caveats, the self-signed warning, renewal, and turning it off.
- **Prerequisites ship with the install.** The installer lands everything DHD needs (OpenSSL, the certificate home, the low-port capability check) on every distro family at install and update time, DHD on or not — and the Updater's ladder shows "DHD prerequisites" as its own named step, installed by the update's own installer run.
- **Self-healing safety net.** If a prerequisite later goes missing, the DHD page detects it and offers the install in the flow; one click installs it and the enable continues automatically. If an install — or any ladder step with a manual remedy — fails, the failure card shows the exact distro-correct commands in a copyable block.
- **Operation cards in chat.** Multi-step work (the DHD enable first) renders in the chat thread as a live step card driven entirely by the bridge's deterministic state — no model generation while an operation runs — fully self-contained (commands and output inline, nothing to open elsewhere), and the finished card persists in the thread.

### Also closing at this release

- **Markdown everywhere (#53)** and **the Vault (#54)** shipped in earlier builds and close here: static text across the app renders as markdown (the Updater's release notes and update log included, headings whole at every line ending), and the Vault — an Obsidian-compatible folder of plain markdown at config/vault/ with its own menu destination, editor and file tree, and Navi's own desk inside it — sits on the installer's keep-list beside everything else that is yours.

## 0.1.4 (alpha)

Release tag: v0.1.4a. The next major update, live-confirmed by Alex before this release was cut: the Updater release notes (#47), full Linux support (#48), and the docs formatting pass (#51).

### Updater release notes

- When an update is available, the Updater screen shows that release's notes in a rendered panel, readable before you press Download & install. The words come from the GitHub release body; when the release page carries none, the matching section of this changelog stands in and the panel says so.
- A check that cannot reach GitHub — no network, or GitHub's rate limit — says that in plain words and shows no panel; it never pretends you are up to date.

### One installer, every major Linux family

- The installer reads /etc/os-release, announces the family it found in plain words, and branches only its dependency step: the Debian family (Debian, Ubuntu, Pop!_OS, Mint and their kin) via apt, Fedora via dnf, and Arch via pacman. Everything else — hardware profiling, the model download, what an update keeps, the startup choice — is shared.
- Bazzite takes a user-space path: the installer never layers packages with rpm-ostree and never asks for a reboot. Her window is built inside a Fedora distrobox when one is available; without one, the window build is skipped in plain words and the complete core install — the bridge and the browser dashboard — still lands.
- An unrecognized distro is named, no package manager is guessed at, everything that can be installed user-space still is, and the core install completes.

### Docs formatting

- Full markdown in the in-app Docs — headings, bulleted and numbered lists, tables, grouped blockquotes, inline code, fenced code blocks, and links — the same set the GitHub wiki renders, on both sides.
- Fenced code blocks are syntax-highlighted with the chat's per-theme palettes, in every theme.
- Prose enumerations are real bulleted lists and instruction sequences are numbered steps, in the in-app Docs and on the wiki alike.

## 0.1.3 (alpha)

Release tag: v0.1.3a. Everything from the phone round (builds .62–.68), live-confirmed by Alex on his phone and desktop before this release was cut.

### Apex Node and phone chrome

- **Apex Node** [local]: it serves only your home network, never the outside world. Its controls live on the DHD page. Turning it on is one flip: the choice saves, Apex restarts her bridge bound for the network, and the row confirms the live state from the answering bridge.
- The Local network access passcode is served only to connections from Apex's own machine — a phone on the LAN receives no code from the status sidebar; you read it off the desktop and type it into the phone.
- A "Local network access" section sits in the status sidebar under the Llamafile block — indicator, the LAN link, and the passcode when it is yours to see; off reads "This machine only" with a plain pointer to Settings → System.
- Phone chrome: a persistent top bar with the menu button and "Apex | Powered by Navi" clustered left and the status toggle alone at the right edge; the main menu slides in from the left and the status sidebar from the right, both full phone-screen width, and both menus hide themselves once you pick a page. The menu button is a compact square that never stretches.

### Chat on the phone

- The CLI | Navi toggle persists: the latched mode survives sends, page switches, and reopening the app, in the shipped app and the test bench alike.
- No focus zoom anywhere: tapping the chat bar — or any field — no longer zooms the page on mobile. The viewport is pinned, double-tap zoom is off, and every editable control renders at 16px on touch devices, the size below which mobile browsers zoom on focus.
- The composer's placeholders are sized for phones, so the whole hint sits visible end to end instead of clipping mid-word.
- The composer is tidier: the hint paragraph under the chat bar is gone, and "Press enter to send." now sits beside the CLI | Navi toggle; Docs gets a full-width page dropdown on phones.

## 0.1.1 (alpha)

### Chat, CLI and themes

- Finished exchanges now fold into reopenable output cards: a folded terminal block shows its command, its exit state and its first output line, and long replies fold the same way — the history stays in the thread, and nothing leaves Navi's context.
- The composer completes the zsh set: a persistent command history, Up/Down recall when the completion list is closed, Ctrl+R reverse search, completion for paths and arguments (not just the command word), the emacs editing chords, and history expansion (!!, !$, !<n>) that always shows you the expansion before anything runs.
- Syntax highlighting is tuned per theme: commands, flags, paths, strings, numbers and operators are coloured in the composer and in the thread, with a palette chosen for each of the eleven themes.
- A command now shows exactly once — in your line. The shell block carries the output only.
- Six new themes join the picker: Dark Liquid Glass (resource-light — real blur only where it is cheap, solid fallbacks where it is not), Nocturne Row, Abyss, Case File, Blood Moon and Phosphor Amber. Nordic dark remains the default.

### Chips, packs and GitHub

- Publish to GitHub works end to end for chips and knowledge packs: Navi creates the repo, applies the navi-chips / navi-rag topic, and uploads the files; publishing the release is the only step left to you, and the version tag is created with that publish.
- GitHub sign-in for publishing is durable now: the full token set is stored and renewed, instead of quietly expiring and failing the next publish.
- Local Chips is the one place to manage the chips on this machine — Run, Download .png, Edit in Studio, Edit README, Export, Publish, Check for updates and Delete all live on its cards; the catalog is for discovering and installing.
- The GitHub catalogs reconcile what is already on this machine: an installed pack or chip reads INSTALLED with its Install button grayed out, while a genuine update stays available.
- Knowledge packs wear the same flip cards as chips, README on the back; the GitHub section's issues and pulse entries are cards too, and clicking an issue opens it.
- Edit in Studio now sits on the chip cards themselves, and a first launch no longer strands the chat in CLI-only mode while the llamafile loads — the view heals itself when she arrives.

### Fixes since 0.1.0

- The chat composer's placeholder follows the CLI/Navi latch as you flip it; Clear chat lives in the composer's hint row; the Chat view's stray header bar is gone.
- When a link cannot open in the desktop shell, the app says so in a warning toast that shows the address and points you at the Web UI (http://localhost:8675), where links open normally.

## 0.1.0 (alpha)

- First public alpha release of Apex — Powered by Navi.
