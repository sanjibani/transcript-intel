# Video Demo Script — Transcript Intelligence

**Target length**: 5-7 minutes (the brief says "5-10" — 7 is the sweet spot)
**Format**: Screen recording + voice narration
**Tools**: QuickTime Player → File → New Screen Recording (built-in on Mac)

> **Use this as a guide, not a script to read.** Speak at a normal pace. Don't apologize for rough edges. If you stumble, pause and restart the sentence — you can edit later. The brief says "a simple screen recording with narration is fine."

---

## Before you press record

Open these windows so you can Cmd+Tab between them:

1. **Terminal** in the project folder
2. **Browser tab** with `outputs/slide_deck.html` open (or the PDF)
3. **Finder** window on `outputs/charts/`

Make the terminal readable — Cmd+Plus to zoom in if needed. Then start QuickTime's screen recording, pick "internal microphone" for audio. Don't show your face.

---

## The script (~7 minutes)

### Intro and dataset (45 sec)

Terminal showing the dataset directory.

> "Hi, I'm Sanjibani. This is a 7-minute walkthrough of my Transcript Intelligence submission.
>
> The dataset is 100 call transcripts from a fictional B2B security company. There are three types: support calls where customers reach out with issues, external calls between account managers and customers, and internal team calls. About 27, 43, and 30 respectively.
>
> The product I'm proposing would help different stakeholders see what matters in these calls. Here's what I found."

### Pipeline running (45 sec)

Run this in the terminal:
```bash
bash scripts/run_all.sh
```

> "I'll run the full pipeline once so you can see the end-to-end. It takes about 30 seconds. The output will land in a few tables and charts."

(Let it run. Don't narrate every stage — the output scrolling is its own demo.)

When it finishes, scroll up briefly to show the "TOP 10 CUSTOMERS BY CHURN RISK SCORE" output.

> "Here's the headline. Four customers — Blackridge, Cobalt, Northstar, Helix — all score 90 or higher. They're all connected to the same outage in March. Let me show you what that means."

### Insight 1 — Churn risk (60 sec)

Open `outputs/charts/01_churn_risk_concentration.png`.

> "The first finding is that churn risk concentrates in a small number of accounts.
>
> 14 of the 32 customers in the dataset scored HIGH risk. The top four all scored 90 or higher. They're all connected to the March Detect Outage. And critically — they all name a competitor by name. SentinelShield keeps coming up.
>
> This is the kind of thing that, in a real product, would surface as a daily digest for the CS team. 'Here are the four accounts you need to call this week, and here's what they're saying.' If this had existed during the outage, the CS team could have called Blackridge on March 11, the day before they escalated."

### Insight 2 — Communication gap (60 sec)

Open `outputs/charts/02_comms_gap_by_month.png`.

> "The second finding is about communication, not the bug itself.
>
> 39 of the 100 calls — almost 40% — contain language like 'no notification' or 'flying blind' or 'I had my team spending two days thinking it was on our side.' The technical fix shipped in 30 days. The customer trust from being left in the dark took much longer to recover.
>
> The lesson: a proactive comms trigger — even before the engineering fix is ready — could prevent the next outage from doing the same brand damage. The process change is cheaper than the engineering change, and arguably more valuable."

### Insight 3 — Convergent feature gaps (60 sec)

Open `outputs/charts/04_convergent_gaps.png`.

> "The third finding is the one I found most interesting: convergent feature gaps.
>
> Five product gaps were independently raised by both customers and engineers within weeks of each other. The clearest case: pipeline health visibility. A customer at Pinnacle Insurance mentioned it on April 16. An engineer named Ravi mentioned the same thing in the April 28 retro.
>
> Same concept, two audiences, twelve days apart. When customers and engineers independently surface the same gap, that's a pre-validated roadmap priority. You don't have to argue for it — the signal argues for itself."

### What I'd build next (60 sec)

Open the slide deck, scroll to the "what we'd build" section, OR just keep talking over the terminal.

> "If I were building this for real, four things would go first.
>
> A real-time churn risk dashboard for the CS team — top accounts daily, with the actual quote from the call attached so the CSM knows what to say when they call.
>
> A proactive comms trigger that fires when an incident is detected — surfaces the affected customers within 30 minutes.
>
> A weekly convergent-gap digest for the head of product, so the roadmap is built on signals the data already validates.
>
> And a per-account health score that combines everything — sentiment trend, churn signals, action items closed, all in one place for the next QBR.
>
> The architecture supports all of these. The pipeline outputs structured tables that any of these views can query."

### Close (30 sec)

> "That's the work. Three insights, one pipeline, 100 transcripts. The story is the same in all three: an outage, a silence, and a set of signals that were in the data the whole time. The pipeline makes them visible to whoever needs them.
>
> Thanks for watching."

End the recording.

---

## What to AVOID in the video

- ❌ Technical jargon the panel might not know (regex, embeddings, recall, LLM-as-verb, etc.)
- ❌ Sales-pitch numbers ("100% accuracy", "5 cents", "30 seconds") — say what you did, not how good it is
- ❌ Self-references ("the interview line", "the panel will see", "in this video I will...") — just talk
- ❌ Apologizing for things that aren't wrong ("sorry this is rough", "I know it's not perfect")
- ❌ Going over 7 minutes. The brief says 5-10. Stay in the lower half.
- ❌ Reading line-by-line. Use the script as a guide, speak in your own words.

## What TO do

- ✓ Speak at a normal pace. Slow down on the customer names (SentinelShield, Blackridge, etc.).
- ✓ Show the chart, then look at the camera while you talk about it.
- ✓ Use language the panel will recognize: "this would have caught X", "the CS team would have done Y", "the recommendation is Z".
- ✓ End clean. No "that's all" or "hope that helps" — just "thanks for watching."
- ✓ If you mess up a sentence, pause, restart it. You can trim in post.

## After recording

1. Save as MP4 (QuickTime → File → Export As → MP4)
2. Watch it back once. If anything feels off, re-record just that section.
3. Trim long pauses at the start and end.
4. Rename to `transcript-intel-demo.mp4`
5. Upload to Loom (cleanest — they watch in browser, no download needed). Or YouTube/Drive.

## If something goes wrong

| Problem | Fix |
|---|---|
| Audio too quiet | Speak closer to the mic, or boost in QuickTime/iMovie post |
| You went over 7 min | Cut the "What I'd build next" section shorter, or drop the architecture details |
| Charts hard to read | Zoom in (Cmd+Plus) before recording, or use larger terminal font |
| Forget what to say | Pause, glance at the script, restart the sentence. Edit out in post. |
| Pipeline fails on screen | Don't panic. Re-run after the recording. |

**The most important thing**: don't try to be perfect. The brief says a simple screen recording is fine. Improv > polished. If you sound like a smart person explaining their work to a smart colleague, the panel will see that. If you sound like someone reciting a sales script, they will too.