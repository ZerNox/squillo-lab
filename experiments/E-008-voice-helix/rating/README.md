# Take rating (experimental, behind `?rating=1`)

`build-anchors.mjs` measures a pool of reference recordings with the page's
own take analysis (`window.helixAspects`) in headless Chrome, plays a round
robin between them on the rated aspects (intonation, steadiness inside held
notes, clean onsets; win 1, draw 0.5 within a tolerance, loss 0, averaged)
and fits Elo ratings so the median conservatory-trained singer is 2000. The
page rates a take against `page/rating/anchors.json` the same way.

Pool (2026-10-24): 101 VocalSet song excerpts ("Caro mio ben", "Dona nobis
pacem", "Row, row, row your boat", straight and vibrato) by 20
conservatory-trained singers (CC BY 4.0), plus the two Amazing Grace
reference takes. Rebuild:

    node build-anchors.mjs http://localhost:8000/ <vocalset-excerpts-dir> ../page/rating/anchors.json \
      "amazing-grace/usaf-soloist=../page/ref/polished.mp3" "amazing-grace/amateur-duo=../page/ref/rough.mp3"

## Why it is off by default

Checked on a separated live vocal by an Idol finalist (pop, "Girl on Fire",
4 min, used locally only and never committed):

- First version: 1496, "better than 1 % of the pool". Steadiness counted runs
  and ornaments as wobble (122 ¢), and tone clarity compared a reverberant,
  separated TV vocal with dry studio takes.
- After measuring steadiness only inside held notes and taking tone clarity
  out of the rating: 1843, still below the amateur Amazing Grace take (1892).
  Her intonation (16 ¢) and steadiness (2.0 ¢) are on a par with the trained
  pool; she loses on slides into notes (0.27 per note), which are a pop style,
  and the faster line costs some intonation.

So the aspects describe a take but do not yet rank singers across styles. The
summary without the rating sets each aspect against the trained median and
names slides as a possible style choice.

## What a real rating needs

- Ground truth: human judgements of singing level across styles (expert
  ratings of a few hundred takes), and a rating validated against them
  (rank correlation with its uncertainty), per the lab's honesty rule.
- A pool that spans styles and recording conditions (pop, soul, musical
  theatre, live and separated vocals, amateur to professional), with licences
  that allow at least lab use.
- Style-aware aspects: slides, runs and vibrato as choices, measured for
  control (landing the target note, rhythm) rather than penalised.
