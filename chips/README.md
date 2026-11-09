# Chips

Chips ship as chips, the way PICO-8 ships games: each chip is a
single .png file. The image looks like a Mega Man Battle Network battle
chip; the chip's entire codebase is embedded inside the PNG in a tEXt
chunk with the keyword "navi-chip" (JSON: name, description, code,
output).

- Share the image and you share the chip — no separate code file.
- Navi loads a chip by reading the code back out of the image.
- **This folder starts empty.** Apex ships with no pre-installed
  chips — the shelf fills only with chips you install from GitHub or
  forge yourself in Chip Studio.
- Chips in this folder survive everything: updates, reinstalls, and
  even a --fresh install keep them (along with the llamafile and your
  Soul/Memory documents). Only a first install creates things fresh.

## The Chips screen — three tabs

- **Navi User Repo (NUR)** searches GitHub for every public repo carrying the
  navi-chips topic — each one is a Navi chip — and lists them with
  their repo metadata and latest release. Install downloads the
  chip's own code — every Python file in the repo, fetched
  recursively so package folders keep their relative paths — from
  the release being installed (or the default branch for repos
  with no releases yet), reads chip-requirements.txt when the repo
  declares one (the chip's card shows the declared dependencies;
  they are not installed automatically), and forges it into
  a chip in this folder, recording the install in
  installed.json: from that moment the chip is a folder chip like
  any other, on the chat pill row and runnable from chat. Delete removes
  the record and the chip; and when a repo cuts a newer release
  than the one installed, the chip offers an **Update**, which
  re-downloads the code and re-forges the chip. Repos with no
  releases offer an update when they have been pushed to since the
  install.
  Chips living in this folder are listed here too, with Run
  buttons.
- **Chip Studio** is a full code editor (syntax highlighting, find &
  replace, bracket matching, structure checks) with one button that opens the
  Docs at the Navi Chip Functions page — the chip API's methods live
  in the documentation, complete and kept current, not in panels
  inside the Studio.
  Forging writes the chip into a chip .png in this folder. Open
  any chip from the folder to edit and re-save it.
- **Workflows** chain chips together: each chip's output becomes the
  next chip's input, step by step, with the whole pipeline shown as
  it runs. Saved in workflows.json in this folder.

## Running chips from chat

Loaded chips line the bottom of the Chat screen as pills — click one
and it runs right in the conversation. You can also type
`/chip <name>`, "run the <name> chip", or just the chip's name, and
Navi runs it: the bridge reads the code out of the chip and
executes its run() against a stub of the real navi_internal API
(print_message, llm_chat, and the rest), so real chips work. Output
lands in the chat as a shell-style result. Type `/chip` on its own
and she answers with the shelf — every installed chip and a line on
what it does — or tells you the shelf is empty and where chips come
from.

To publish a chip for everyone: put its code in a public GitHub repo
as a Python file in the repo root (named for the chip, the way
cryptex.py sits in navi-cryptex), add the navi-chips topic, and cut
a release; Navi User Repo (NUR) finds it from there, and installing it
downloads that file and forges it into a chip here.
