# Video Demo Script — Transcript Intelligence

**Target length**: 5-10 minutes (the brief says "5-10 minutes" — 7 is the sweet spot)
**Format**: Screen recording + voice narration
**Tools**: QuickTime Player (built-in on Mac) or `Cmd+Shift+5` screenshot tool

> **Don't read this verbatim.** Use it as a guide. The panel will know if you're reading. Make eye contact with the camera (or the screen), speak at a normal pace, and don't apologize for rough edges. "A simple screen recording with narration is fine" — the brief is explicit.

---

## Before you press record

Open these in separate windows (so you can Cmd+Tab between them):

1. **Terminal** in the project folder (`/Users/sabyasachichoudhary/.minimax-agent/projects/transcript-intel`)
2. **Browser tab** with the slide deck open (`file:///Users/sabyasachichoudhary/.minimax-agent/projects/transcript-intel/outputs/slide_deck.html`)
3. **VS Code** with the project open
4. **Finder** window on `outputs/charts/` (to flip through PNGs)

Make sure your terminal is at a readable size (use Cmd+Plus to zoom in).

Then start QuickTime: File → New Screen Recording. Click the red button, select "internal microphone" for audio. Don't show your face — just the screen.

---

## The script (~7 minutes)

### Section 1: Intro and the dataset (45 sec)

> "Hi, this is Sanjibani. This is a 7-minute walkthrough of my Transcript Intelligence submission.
>
> I built a hybrid pipeline that processes 100 call transcripts and surfaces three insights for stakeholders. The dataset has 27 support calls, 43 external account-manager calls, and 30 internal team calls.
>
> Three call types, three stakeholders, one pipeline."

While saying this, have the terminal showing a directory listing. Run `ls /Users/sabyasachichoudhary/Downloads/interview-assignment/dataset | wc -l` to show 100.

### Section 2: Run the pipeline (90 sec)

> "Let me show you the full pipeline running end-to-end. It's six stages, takes about 30 seconds total, costs about 5 cents when LLM is enabled."

Run this in the terminal:
```bash
bash scripts/run_all.sh
```

> "Stage 1: parse. Walks 100 folders, builds one DataFrame per call. Pure code, no LLM.
>
> Stage 2: enrich. Tags each call with type, urgency, products mentioned. Rule-based on the title prefix — tested at 100% accuracy.
>
> Stage 3: extract. Three things — competitor mentions via regex, comms-gap phrases via regex plus selective LLM, and 384-dim embeddings from sentence-transformers.
>
> Stage 4: classify. This is where we validate against the pre-computed labels in the dataset. We found 100% recall on churn signals, plus 7 cases where our extraction caught more than the source vendor.
>
> Stage 5: aggregate. Per-customer rollup with the churn risk score. Per-month sentiment. Convergent gaps.
>
> Stage 6: surface. Seven charts and three tables. The pipeline runs in 30 seconds and the whole thing costs under 5 cents."

(While narration is happening, the output is scrolling. Don't read every line. Let the numbers flash by.)

### Section 3: The 3 insights (3 minutes)

Switch to the slide deck in the browser, or open the PNGs in Finder.

**Insight 1 — Churn risk concentration (60 sec)**

> "Three insights. The first is churn risk concentration.
>
> 14 of the 32 customers in the dataset scored HIGH risk. The top four — Blackridge, Cobalt, Northstar, Helix — all scored 90 or higher. They're all connected to the March Detect Outage. They all mention SentinelShield by name.
>
> The interview line for this: a real-time churn risk score would have flagged these four accounts 30 days before they escalated. The CS team would have called them on March 11, before the URGENT calls on March 12."

Open `outputs/charts/01_churn_risk_concentration.png` and walk through the top of the chart.

**Insight 2 — Communication gap (60 sec)**

> "The second insight is the communication gap. 39 of 100 calls — almost 40% — contain language like 'no notification' or 'flying blind' or 'I had my team spending two days thinking it was on our side.'
>
> This is the wound. Not the bug. The technical fix shipped in 30 days. The customer trust from being left in the dark took longer to recover.
>
> The recommendation: a proactive comms trigger. When an incident is detected, surface the affected-customer list within 30 minutes, even before the engineering fix is ready. One process change could prevent the next outage from doing the same brand damage."

Open `outputs/charts/02_comms_gap_by_month.png` — show the March spike.

**Insight 3 — Convergent feature gaps (60 sec)**

> "The third insight is the most interesting. Convergent feature gaps.
>
> Five product gaps were independently identified by both customers AND engineers within weeks of each other. The strongest example: pipeline health visibility. A customer at Pinnacle Insurance mentioned it on April 16. An engineer named Ravi mentioned the same thing in the April 28 retro.
>
> Same words, two audiences, twelve days apart. Convergent gaps are pre-validated roadmap priorities. Customer demand AND engineering awareness in the same window."

Open `outputs/charts/04_convergent_gaps.png` — show the 5 convergent topics.

### Section 4: Pipeline architecture (60 sec)

Switch to VS Code, show `docs/architecture.md` or the architecture diagram in the slide deck.

> "Why hybrid? Three reasons.
>
> First, cost. At 100 calls, pure LLM is 50 cents, hybrid is 30 cents. At 50,000 calls a year, that's 250 dollars versus 25.
>
> Second, audit trail. When the pipeline flags Blackridge as high risk, the panel can ask why. The answer is: one URGENT call, three churn signals, one competitor mention. Try explaining a GPT-4 prompt to a CS leader.
>
> Third, real-time. A real Transcript Intelligence product needs sub-second signals. LLMs are 5-10 seconds. Hybrid runs 90% of calls through rules in under a second."

Open the architecture PNG (`outputs/charts/07_pipeline_architecture.png`).

### Section 5: What's in the repo (45 sec)

Switch to the GitHub repo in browser: `https://github.com/sanjibani/transcript-intel`

> "Everything is in this public repo. Six pipeline stages, each a standalone runnable script. The run_all.sh script runs the whole thing. The slide deck is in outputs/slide_deck.html and PDF. The architecture doc explains the stage-by-stage design.
>
> I have private interview prep notes in the repo too — they're encrypted with git-crypt, only my GPG key unlocks them. The panel won't see those."

### Section 6: Close (30 sec)

Back to the terminal or the slide deck's last slide.

> "Three deliverables, one pipeline, 100 transcripts. The story is the same in all three: an outage, a silence, and a set of signals that were in the data the whole time. The pipeline makes those signals visible per stakeholder.
>
> Thanks for watching. The repo link is in the description, the slide deck PDF is attached, and I'm happy to walk through any specific stage in the live Q&A."

End the recording.

---

## What to AVOID in the video

- ❌ "Um", "uh", long pauses. Edit them out (QuickTime has trim, iMovie is fine too).
- ❌ Showing the whole pipeline run scrolling for 30 seconds. Cut to the next section.
- ❌ Reading code line by line. Show it briefly, narrate the design.
- ❌ Apologizing for things that aren't wrong ("sorry this is rough", "I know this isn't perfect").
- ❌ Going over 10 minutes. The brief is explicit. 7 is the target.

## What TO do

- ✓ Speak at a normal pace. Slow down on key terms (SentinelShield, churn risk score).
- ✓ Show the chart, then look at the camera (or the audience equivalent).
- ✓ Use the language of the panel: "this would have caught X", "the CS team would have done Y".
- ✓ Mention the cost story once — it's a strong differentiator.
- ✓ End by inviting the live Q&A.

## After recording

1. Save as MP4 (QuickTime → File → Export As → MP4)
2. Verify the audio is clear
3. Rename to `transcript-intel-demo.mp4`
4. If file > 100 MB, consider uploading to Loom or YouTube and linking

## Where to put the video

The video isn't in the repo (it would bloat the git history). Three options:

1. **Loom/YouTube link** — paste in the submission email
2. **Google Drive / Dropbox** — share the link
3. **GitHub release** — upload to a release on the repo, link the release

For the panel, a Loom link is the cleanest — they can watch in browser, no download needed.

---

## If something goes wrong

| Problem | Fix |
|---|---|
| Audio too quiet | Speak closer to the mic, or boost in post with QuickTime/iMovie |
| Video too long | Trim the start (the "Hi, this is..." intro) and the end (the silence after you finish) |
| Charts hard to read | Zoom in (Cmd+Plus) before recording, or use a larger font in the terminal |
| Forget what to say | It's OK to pause, look at the script, restart the section. Edit it out later. |
| Pipeline fails on screen | Don't panic. The pipeline is reproducible — re-run after the recording. |

The most important thing: **don't try to be perfect**. The brief says "a simple screen recording is fine." Improv > polished.
