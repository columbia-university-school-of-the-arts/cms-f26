---
name: tmdb
description: "Week 4 workshop: ask The Movie Database a question about film history, such as the rise and fall of a genre, after stating in one sentence how each thing is counted, then read the chart against that definition. Works in ~/cms-lab/tmdb, not in a repository, and keeps the API token in a .env file."
---

# Data is made

Help the student put a real question to a film database and see that the
answer depends on how they asked. Students have Claude Code but may be new to
it. Say what each command does in one sentence.

## Where the work lives

`~/cms-lab/tmdb/`, a plain local folder. Not the fleet repository: no clone,
commit, or push. If Claude Code is not running inside `~/cms-lab`, stop and
give the line `mkdir -p ~/cms-lab && cd ~/cms-lab && claude`, then have them
rerun `/cms-lab:tmdb`. If `~/cms-lab/lab-setup.md` is missing or `python3`
does not answer, send them to `/cms-lab:init` first.

## Step 0: is there a working token?

Before anything else, from `~/cms-lab/tmdb/` (create it if needed), run
`bash <skill dir>/assets/check_key.sh`. It looks for `TMDB_TOKEN` in the shell
and in `.env`, calls TMDB once, and prints only a status word. Never `cat`,
`grep`, or print `.env` yourself, and never ask the student to paste the
token here.

- **OK**: go on to Phase 1.
- **MISSING or EMPTY**: walk the student through getting one, below.
- **REJECTED**: the token is wrong or was copied with a stray character or
  the wrong kind (the short "API Key" instead of the long "API Read Access
  Token"). Have them re-copy it, then rerun the check.
- **UNREACHABLE**: a network problem; retry once, then have them carry on
  with a neighbour's session and ask in the room.

### Getting a token (when none is configured)

Say what a token is: a password that lets this program ask TMDB questions as
them. Then, one step at a time, waiting for the student to say each is done:

1. Open https://www.themoviedb.org/signup and make a free account. Confirm
   the email TMDB sends.
2. Signed in, open Settings, then **API** (https://www.themoviedb.org/settings/api),
   and request a key. Choose personal or educational use. Its form asks for a
   short description of the project: "a class exercise on film data for a
   university course" is honest and enough.
3. On that page, copy the long **API Read Access Token**.
4. Make the `.env` file. Copy `assets/.env.example` to `~/cms-lab/tmdb/.env`
   (`cp <skill dir>/assets/.env.example .env`), then have the student open it
   (`nano .env`), paste the token after `TMDB_TOKEN=`, and save (Control-O,
   Enter, Control-X). They do this in the editor, not in this conversation.
5. Rerun `check_key.sh` and continue only on OK.

TMDB's screens may have changed; if a step does not match, have the student
read what they see aloud to the room rather than guess.

Explain a `.env` file briefly: a plain-text file of `NAME=value` lines that
keeps a secret out of the code, which reads it by name. Read it from the
environment in code (`python-dotenv`, or parse it yourself, then
`os.environ["TMDB_TOKEN"]`). Never print, log, or echo the value, and never
write it anywhere but `.env`. Create `.gitignore` containing `.env` and
`data/` in the folder, in case they later move it into a repository. If the
student pastes the token into chat anyway, tell them to regenerate it on TMDB
and continue.

If the account or key is slow, carry on with a neighbour's session; never
share the token.

## Phase 1: the definition before the code

Before any code, ask the student to fill in, in their own words:

> Count ___ from TMDB, where a film is in the genre if ___, placed in a year
> by ___, leaving out ___. "Rise" means ___.

Raise what TMDB will not settle for them: a film carries several genres;
count versus share of that year's films (raw counts rise with production);
TMDB stores release dates per country, so whose release; and a vote-count
floor removes obscure entries and changes the answer. Do not choose for them.
Record the sentence in `experiment.md` before writing code.

## Phase 2: fetch, chart, compare

API notes (verify against developer.themoviedb.org before relying on them):
base `https://api.themoviedb.org/3`, header `Authorization: Bearer <token>`,
`/genre/movie/list` for genre ids, `/discover/movie` with `with_genres`,
`primary_release_year` and `vote_count.gte`, and the `total_results` field
for a count without downloading every film.

Before running, tell the student how many requests the program will make and
have them read the plan. Keep requests modest and pause between them; respect
rate limits and TMDB's terms. Cache each response under `data/` so a rerun
does not call again. Chart with matplotlib, save the image and the numbers.

Then have the student change **one** decision in their sentence, rerun, and
compare the two charts. Record both in `experiment.md` with the sentence that
produced each.

## Phase 3: read the chart against the definition

Ask: is this a rise in the genre, or a rise in what TMDB contains? What could
a film historian say the chart cannot show? Record the answer under a
**What this conceals** heading. TMDB is free and thin: no aspect ratio, no
film stock. Name one question it cannot answer.

## Attribution

Anything shared from this data carries TMDB's attribution notice (check the
current wording in their terms). Note it in `experiment.md`.

## From here to a skill

The second half of the workshop turns this session into a reusable skill the
student writes in their own repository. When they are ready, read
`references/skill-template.md` and help them draft it from what they just did.
Do not write their skill for them before they have chosen their own metric.
