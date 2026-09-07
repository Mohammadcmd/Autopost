# Autopost

Plug in a camera or SD card, and Autopost finds the most recent event's worth
of photos, auto-edits them locally, lets you swipe through keep/delete, and
gets a captioned Instagram post + Facebook album ready for you to publish
with one click.

## How it works

1. **Detect** — a background watcher polls for newly-mounted removable
   storage (or any folder listed in `WATCH_PATHS`, which is how this is
   testable without real hardware). It reads each photo's EXIF capture time,
   groups photos by day, and — if the most recent day has too few photos —
   walks backward day by day until it finds one that does. Within that day,
   photos are split into time-gap "bursts"; the largest burst is treated as
   the event.
2. **Edit** — every photo in that burst is run through a local, fast
   auto-enhance pass (white balance, levels, exposure, deskew/crop). See
   [`app/editing/cleanup.py`](backend/app/editing/cleanup.py) for why
   automatic background-clutter removal is a documented follow-up rather
   than something bolted on here.
3. **Review** — a Tinder-style web UI shows each edited photo one at a time;
   keep, delete, or undo, with keyboard shortcuts (← delete, → keep, U undo).
4. **Match & caption** — the photo cluster's time window is matched against
   an events website (currently a local JSON stub — see
   [`app/events/`](backend/app/events)) to find the event's name, location,
   and any organizations involved. A caption is then drafted by a local AI
   model (see [`app/posting/local_llm.py`](backend/app/posting/local_llm.py)
   and **Caption style** below) in your own voice, falling back to a plain
   template if no local model is running. Either way, the location,
   organizations, and your configured hashtags are always guaranteed to be
   in the final caption.
5. **Post** — after you review the caption, one click posts an Instagram
   entry (single photo or carousel) and creates a Facebook album with the
   kept photos. Without Meta credentials configured, this runs in **dry-run
   mode**: it returns the exact API requests it would have made instead of
   sending them, so the whole flow is demonstrable today.

## Running it

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # then edit as needed
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/. To try it without a real camera, point
`WATCH_PATHS` (or the in-app "Scan" box) at any folder of photos with EXIF
timestamps.

Run the test suite with `pytest tests` from `backend/`.

## Configuration

See [`.env.example`](.env.example) for every setting. The two integrations
that need real-world setup before they do anything live:

- **Events website**: set `EVENTS_WEBSITE_BASE_URL` (+ `EVENTS_WEBSITE_API_KEY`
  if needed) once the site exposes an events API. Until then, edit
  `backend/app/events/sample_events.json` to test matching locally.
- **Instagram/Facebook**: set `META_ACCESS_TOKEN`, `META_PAGE_ID`,
  `IG_BUSINESS_ACCOUNT_ID`. Instagram's API requires photos to be reachable
  at a public URL (it fetches them itself), so real posting also needs
  `PUBLIC_BASE_URL` pointed at a publicly reachable instance of this app.
  Facebook album uploads work directly from local files.

## Caption style (the "local AI")

Captions are drafted by a locally-running LLM so no event details or photos
ever leave the machine:

1. Install [Ollama](https://ollama.com) and pull a model, e.g.
   `ollama pull llama3.2`.
2. Give it your voice, either way:
   - **Import it from your own account** — click **Import from Instagram**
     in the app's Caption style section (or `POST /api/style/import-from-instagram`).
     This reads your own connected Instagram Business account's own past
     captions via the Graph API — the same access token and account this
     app already uses to post, just reading instead of writing. It cannot
     read anyone else's account, and it's not scraping: pulling a Business
     account's own media is exactly what that API endpoint is for.
   - **Or write/paste it yourself** in the same UI section, or by editing
     [`backend/app/posting/caption_style.json`](backend/app/posting/caption_style.json)
     directly (or pointing `CAPTION_STYLE_FILE` at your own copy):
     - `tone_notes` — describe the voice in plain English (casual vs.
       formal, typical length, emoji habits, etc).
     - `example_captions` — real captions used purely as a style reference
       (tone, rhythm, structure). The prompt explicitly instructs the model
       to write something new, never to reproduce them — but a small local
       model follows a reference more literally than a larger one would, so
       only use captions from an account you're authorized to sound like.
3. Set `CAPTION_HASHTAGS` to whatever hashtag set you always want appended.

If Ollama isn't running, captions fall back to a plain template. Either
way, the drafted caption is guaranteed to mention the event's location and
every organization the events website lists as involved, and to end with
your configured hashtags — that enforcement happens in code
(`app/posting/caption.py`) rather than being left up to the model. Use the
review screen's **Regenerate caption** button to retry after changing your
style file, without re-scanning photos.

### Checking how close the AI's captions land

Once you have example captions loaded, every drafted caption gets a **style
match score** (shown next to the caption box) — the local model embeds both
the generated caption and each reference example, and the score is their
average cosine similarity. This measures how close the *voice* is (tone,
rhythm, structure), not literal text overlap, which is deliberately never
checked for or optimized toward. Use it to judge whether your `tone_notes`
and examples need adjusting before you trust the AI to draft unsupervised —
edit the style, hit **Regenerate caption**, and watch the score move.

## Known scope limits / follow-ups

- **Background-clutter removal** (garbage cans, brooms, etc.) is not
  implemented — it's a generative inpainting problem (object detection +
  segmentation + inpainting models), architected as a pluggable stage in
  `app/editing/cleanup.py` but left for dedicated follow-up work.
- **Camera protocols**: only storage that mounts as a filesystem (most SD
  cards, cameras in mass-storage mode) is supported. Cameras that only speak
  PTP/MTP would need a `gphoto2`-based ingestion path.
- **Events website**: the real API contract isn't known yet, so
  `WebsiteApiEventSource` is a best-guess skeleton to be adjusted once it is.
