# E-005 — Intent inference: pitch accuracy without a reference

**Status:** open · **Serves:** VISION §3 (every song is your cover), §5 (reference-free), §12.4

## Question

Squillo never compares a singer with an original. For pitch accuracy it must
infer **the note the singer was aiming for** from the take itself. How reliably
can that be done, and how is the uncertainty of the inference carried into the
accuracy score honestly?

## Hypothesis

For most phrases, the intended notes can be inferred from a key or scale
estimate plus where the voice settles within each note, so that a note sung
sharp or flat by a few tens of cents is attributed to the right target.
Inference fails on deliberate blue notes, glides and non-Western tunings, and
must then say "intent uncertain" rather than score.

## Protocol

1. **Ground truth by construction:** synthesized sung phrases with known
   intended notes, then rendered with controlled errors (offsets, drift, scoops,
   vibrato), in several keys and scales.
2. **Real voices:** openly licensed sung datasets with note annotations, public
   domain songs only.
3. Candidate inference methods: nearest equal-tempered note; key or scale
   estimate, then nearest scale note; note segmentation plus per-note settling
   pitch; combinations.
4. Report attribution accuracy per error size and condition, and test how the
   inference's own uncertainty should widen the accuracy score's ±.

## Result

Not yet run.
