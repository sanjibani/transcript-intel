# PLAN — Code Repository Polish for Panel Review

## What the brief asks for

> "It should be well-organized and readable so we can review your technical approach. Include comments or markdown that explain your key decisions."

## Audit — current state

The repo is already 80% there. 9 source files, ~2,242 lines, all with module-level docstrings. What's missing:

| Issue | Where | Severity |
|---|---|---|
| Stage 4 docstring is one big block — no inner section headers | `pipeline/04_classify.py` | Medium |
| Stage 6 module docstring is short, no per-chart explanation in the file header | `pipeline/06_surface.py` | Medium |
| `_llm.py` has a thin module docstring — design decisions aren't surfaced at the top | `pipeline/_llm.py` | Medium |
| No top-level `PLAN.md` showing the reviewer what the file map is and where to find what | repo root | High |
| No "How to read this repo" pointer in README — reviewer lands cold | `README.md` | Medium |
| `INTERVIEW_PREP.md` is in repo but encrypted — reviewer can't tell what's there | `README.md` | Low |
| `SUBMISSION.md` exists — verify it's reviewer-relevant (vs personal) | `SUBMISSION.md` | Low |
| `LOCAL_SETUP.md` exists — verify it's reviewer-relevant | `LOCAL_SETUP.md` | Low |

The actual *code* (functions, regex, formulas) is already well-commented and explained inline. The gap is the **navigation layer** — what does the reviewer see first, and how do they get from the top into the right file in under 30 seconds.

## Plan

### Phase 1 — Top-level navigation (high impact, low risk)

1. **Add `PLAN.md` to repo root.** 2-3 page tour:
   - Repo layout diagram (already in README — reference, don't duplicate)
   - "Start here" map: which file explains which decision
   - Design decisions index: every "why" lives in file X, line Y
   - What's NOT in scope (pre-computed labels used as input, not validation)
2. **Add a "How to read this repo" pointer to README.** Three lines pointing at PLAN.md and docs/architecture.md.

### Phase 2 — File-level readability (medium impact, medium risk)

3. **Add section headers to `pipeline/04_classify.py`.** Same `# ---` divider style as Stages 1-2. Section markers: Configuration, Per-call classifier, Main, Output.
4. **Expand module docstring on `pipeline/06_surface.py`.** Surface the per-chart explanation list at the top so a reviewer can see "Chart 1 = churn concentration, Chart 2 = comms gap, ..." before scrolling.
5. **Expand module docstring on `pipeline/_llm.py`.** Surface the design decisions at the top: graceful fallback, safe key logging, why we picked this provider pattern.

### Phase 3 — Decision comment audit (medium impact, low risk)

6. **Verify every design-decision comment is present.** Walk each stage file, confirm:
   - WHY the technique was chosen (not just WHAT it does)
   - WHY a particular cost/complexity tradeoff was made
   - WHAT the next step would be (the "what we'd build next" pointer)
7. **No-stale-comments check.** Grep for "TODO", "FIXME", "XXX" — should be zero or have valid context.

### Phase 4 — Side files cleanup (low impact, low risk)

8. **`SUBMISSION.md` / `LOCAL_SETP.md`** — confirm content. If reviewer-relevant, keep. If personal, move to a `.private/` folder or out of repo.
9. **`INTERVIEW_PREP.md`** — already git-crypted, that's fine. Confirm README mentions it's encrypted (currently does, line 92).
10. **Final README pass** — ensure the "Project layout" section matches reality.

### Phase 5 — Verification (high importance)

11. **Run the pipeline.** `bash scripts/run_all.sh` — should still end with "TOP 10 CUSTOMERS BY CHURN RISK SCORE". Comments don't change behavior, but verify.
12. **Walk through with fresh eyes.** Pretend you're the panel. Can you find the formula for churn_risk_score in under 30 seconds? (Answer: PLAN.md → 05_aggregate.py line 111-115. Need to confirm.)
13. **Commit + push** so the panel sees the updated repo.

## Out of scope (deliberate)

- Refactoring working code. Comments and headers only — no logic changes.
- Renaming files. Panel may already be reading by path.
- Adding tests. The brief doesn't ask for them and adding them now could break the demo.
- Switching to a different framework. Pure Python + pandas is the point.
- Adding CI / GitHub Actions. Out of scope for a 100-call demo.

## Risk register

| Risk | Mitigation |
|---|---|
| Comments drift from code | Comments already match behavior; verification step confirms |
| Reviewer can't find the formula | PLAN.md lists every key formula with file:line |
| README/PLAN.md duplicate each other | PLAN.md is the index; README is the entry point. Cross-link, don't duplicate. |
| INTERVIEW_PREP.md looks like cheating | README already notes it's git-crypted and is "topic bullets, not scripted answers" |
| Adding headers changes line numbers referenced elsewhere | Use `# ---` divider comments (don't change existing function definitions or line numbers above 100) |

## Time estimate

30 minutes for Phase 1-3 if focused. Phase 4 is 5 min. Phase 5 is 5 min. Total: ~45 min.

## Done = ?

- [ ] PLAN.md at repo root, reviewer can read in 3 min
- [ ] README points at PLAN.md
- [ ] All 9 source files have module docstrings + section headers
- [ ] Every design decision in code is either (a) inline comment or (b) referenced from PLAN.md
- [ ] `bash scripts/run_all.sh` succeeds end-to-end
- [ ] Git commit + push (or commit only, since panel may already have the zip)