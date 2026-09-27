# Microbubble visibility study

**No microbubble detector is implemented or enabled.** Low return-chamber water can
coincide with pump-injected bubbles in this tank, but bubbles have other causes. Video
cannot measure water level. Do not lower water or disable the ATO to create examples.

## Collect and label privately

Once the camera is connected, first review its existing 640×360, 2 fps view. Identify a
region around the return outlet and open water that is not dominated by fish, glare,
coral movement, or surface reflections. Preserve source-resolution exports from Eufy
when available, using only local files outside this checkout. Never upload owner footage.

Gather normal clips across separate days, daylight, ramps, blue lighting, feeding,
cleaning, and usual skimmer activity. Keep any **naturally occurring** bubble episodes
and label their visible onset/end. Mark ambiguous examples `uncertain`. No bubble episodes
are required to be manufactured; without them sensitivity cannot be measured.

## Prepare matched views

Run using the installed virtual environment; replace the sample path/date with the actual
local recording and date. The example is not an assertion that any such clip exists:

```bash
.venv/bin/python scripts/prepare-bubble-study.py /path/to/local-export.mp4 \
  --label normal --recorded-day YYYY-MM-DD --start 0 --seconds 20
```

The default private destination is
`~/Library/Application Support/Reef Watch/bubble-study/<random-id>/`:

- `source-detail.mp4`: source dimensions, 10 fps sampling, no audio or copied metadata.
- `prototype.mp4`: 640×360, 2 fps for comparison with the current processing budget.
- `review.json`: recording-day/label plus empty visibility, ROI, lighting, confounder,
  train/held-out split, and review-note fields for human review.

Source files are left intact. Output inside the checkout is rejected; sample directories
are mode 0700 and files 0600. FFmpeg input is restricted to local files/pipes. Failures
remove only the newly generated sample directory. These study clips are deliberately
outside automatic media retention; delete reviewed samples manually when no longer needed.

Sampling at 10 fps cannot restore detail or frames absent from an export. Check original
resolution/frame rate first. Samples run for up to the requested duration and end earlier
if the source ends. A synthetic test pattern verifies encoding, not bubble visibility.

## Evaluate before building a detector

1. Compare matched clips at native display sizes. Record whether individual bubbles and
   their movement are distinguishable in each version, including under blue light/night.
2. Select a return-region crop only after reviewing real footage. Determine whether a
   source-resolution crop/higher sampling rate is needed before changing live capture.
3. Review candidate bright-speck density and movement features against food, debris,
   reflections, fish, and skimmer bubbles. Do not use the existing low-motion rule.
4. Separate development and held-out recordings by **recording day**, not adjacent frames.
5. Report missed visible episodes, false events per day, detection delay, and lighting
   coverage. Record uncertainty where visibility is insufficient.
6. Only after agreement on measured sensitivity, implement sustained evidence,
   deduplication/recovery, maintenance suppression, and the proposed inspection prompt.

Current study status: tooling tested with synthetic video; no real normal or natural-bubble
footage has been supplied or evaluated in this Mac setup session.
