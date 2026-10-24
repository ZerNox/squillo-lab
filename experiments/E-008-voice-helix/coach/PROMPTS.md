# Coach clips: prompts

Optional, behind a feature toggle: the drawn figure is the default coach, and
the filmed one shows only with `?coach=video` in the page URL.

Eight short silent loops of one voice coach performing the physical cue for
each exercise. With the toggle on, the page plays `page/coach/<pose>.mp4` in the coaching panel
(cropped to 3:4) whenever that pose is active, and falls back to the drawn
figure for any pose without a clip.

## How to make them (Gemini with Veo)

1. **Make the coach once, as a still.** In Gemini, generate an image with the
   *Coach* prompt below. Regenerate until you like her; save that image.
2. **Make each clip from that still** so it is the same woman every time: in
   Gemini choose *Videos* (Veo), attach the still as the starting image, and
   paste the *Shared style* line followed by one pose prompt.
3. Save each result as `<pose>.mp4` (the names below) in one folder, then run
   `./add-clips.sh <that folder>` from this directory. It strips the sound,
   crops and compresses the clips, copies them into `page/coach/` and lists
   them in the page.

Any other generator works the same way (Sora, Runway, Kling): starting image
plus prompt, 16:9 with the coach centred (or 9:16 if offered), 5 to 8 seconds.

## Coach (the still)

> Photorealistic portrait of a warm, confident female voice coach in her late
> thirties, standing in a calm, softly lit rehearsal room with a plain
> warm-grey wall. Shoulder-length dark hair tied back, simple charcoal
> long-sleeve top, no jewellery, no text or logos. Medium shot from the waist
> up, centred in the frame, with clear empty space above her head and both
> hands and elbows fully visible. Facing the camera, arms relaxed, gentle
> closed-mouth smile. Horizontal 16:9, natural skin texture, shallow depth of
> field.

Landscape on purpose: the video tool makes 16:9 clips and crops a portrait
still, which cuts off her head. `add-clips.sh` cuts a centred 3:4 portrait out
of the landscape clip, so keep her centred with room above her head.

## Shared style (start every clip prompt with this)

> Same woman, same room, same clothes and framing as the image. Medium shot
> from the waist up, her whole head and hair always in frame with space
> above, hands always visible. Locked-off camera, no cuts, no zoom, no
> reframing. She demonstrates a singing exercise silently: no sound, no
> singing, no speech, no music, no captions. Slow, clear, calm movements, as
> if showing a student. The clip starts and ends in the same relaxed pose so
> it loops seamlessly. Horizontal 16:9.

Copy the prompt text without the leading `>` (that is only Markdown quoting).

## Poses

| File | Used for | Prompt (after the shared style) |
| :--- | :--- | :--- |
| `idle.mp4` | waiting, clean singing | She stands relaxed, breathes slowly and visibly low into her belly, shoulders still, and gives a small encouraging nod and smile to the camera. |
| `belly.mp4` | shaky pitch | She places both hands flat on her lower belly, breathes in slowly so her hands move outwards, then holds the belly firm and steady while her mouth stays softly closed as if humming one long note; her hands do not move during the hold. Then she relaxes. |
| `breath.mp4` | breathy | One hand on her belly. She makes a small, crisp inward press of the hand exactly as her mouth opens to a clear "uh" shape, then holds the open vowel steadily, hand pressing gently. Then she relaxes and closes her mouth. |
| `yawn.mp4` | pressed / strained | She rests two fingertips lightly on the front of her throat, then does a slow, relaxed yawn: soft palate lifting, jaw dropping, throat visibly loosening downwards, ending in an easy open "ah" mouth shape with relaxed shoulders. Then she closes her mouth calmly. |
| `point.mp4` | scooped onsets | She raises her index finger and points forward at eye level as if marking a note in the air, pauses, then opens her mouth directly into a clear "ah" shape exactly when the finger taps forward once, with no sliding movement. She lowers the hand. |
| `lift.mp4` | monotone, vocal fry | Her open hand rises in a smooth arc from chest height to above her shoulder and back down, twice, as if lifting her voice on the stressed word; her eyebrows and face lift with the hand and her other hand rests on her belly. |
| `jaw.mp4` | mumbled vowels | She rests her fingertips on her chin, lets her jaw drop two finger-widths for an open "ah", then rounds her lips forward for "oo", then smiles wide for "ee", slowly and exaggerated, then returns to a relaxed closed mouth. |
| `nose.mp4` | nasal | She places one finger horizontally just under her nose, opens her mouth wide to an "ah" shape and holds it, looking calm and checking with the finger, then lowers the hand. |

The cue texts shown next to each clip are in `page/index.html` (`FLAWS`).
