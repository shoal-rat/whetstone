# Aesthetic review

GPT can produce endlessly but seldom steps back and judges its output against a bar. That judgement is your contribution. Do it from real captures, in a fixed order, with numbers where possible, and write it so GPT can act on it.

## Contents
- How to look
- Order of diagnosis
- Scene rubric
- Character rubric
- VFX rubric
- Motion and game-feel rubric
- UI rubric
- Feedback template

## How to look

- **Capture what the user will see.** Real resolution, the normal camera distance (third-person play camera, flight height, phone width), normal settings plus the lowest supported tier. A close-up beauty shot hides the problems players meet.
- **Fixed cameras.** Keep a list of camera bookmarks (position, direction, time of day, weather) in the ledger and reuse them for every before/after. Comparisons across different cameras prove nothing.
- **Look at value before colour.** `python3 scripts/look.py shot.png -o sheet.png` shows each capture as colour, greyscale, three-value squint, and a thumbnail. If the squint is mush, no colour or texture work will save it.
- **Compare against the target.** `--ref target.jpg` puts a reference beside the capture with the same statistics. Use a reference for the style and level, not one to copy.
- **Measure light ratios.** `--patch lit=x,y,w,h --patch shadow=x,y,w,h` gives the linear lit:shadow ratio in stops. Feedback with a number gets fixed; "it feels flat" gets a cosmetic tweak.
- **Motion needs motion.** Review animation, VFX and camera from clips or frame strips (sample 10–15 frames per second of a clip into a grid), not stills.
- **Be honest.** When a capture still falls short of the bar, say so in the review and in your report to the user, even after many rounds.

## Order of diagnosis

Work top-down; fix the highest broken level first.
1. **Lighting and values**: is there a clear light direction, shadow mass and highlight mass?
2. **Colour**: palette logic, temperature relationships, saturation budget.
3. **Shape and silhouette**: big/medium/small rhythm, readable silhouettes.
4. **Density and composition**: layers, clustering, landmarks, leading lines, negative space.
5. **Materials**: roughness and colour variation, edge highlights, scale consistency.
6. **Fine detail**: where the eye goes, and nowhere else.
7. **Motion**: does anything live, and does it move with weight?

Good lighting rescues mediocre assets. Fine detail never rescues bad lighting.

## Scene rubric

| Area | What good looks like | Typical GPT default | Useful targets (starting points, adjust to style) |
|---|---|---|---|
| Light direction | One dominant key, shadows that describe form | Flat, even, overhead or ambient-only | Key 25–50° above horizon for daytime drama; low raking light at golden hour |
| Light ratio | Lit side clearly brighter than shadow side; shadows still hold colour | 1.5:1 or less, everything grey-lit | Sunny stylized: about 2.5–4:1 linear (1.3–2 stops); overcast 1.5–2:1 |
| Grounding | Contact shadows and ambient occlusion; objects sit on the ground | Floating props, no contact darkening | Visible AO under props and at wall bases at play distance |
| Depth | Atmospheric perspective: distance lightens, cools, desaturates | Same contrast near and far | Far layers lose 30–60% contrast toward the sky colour |
| Colour | Dominant palette plus accents; warm light with cool shadow (or the reverse) held consistently | Every surface saturated, no temperature logic | Save peak saturation for focal points; neutralise large surfaces |
| Shape | Big, medium and small forms in clear proportion | Evenly sized, evenly spaced objects | A few big masses, some medium, many small; avoid uniform sizes |
| Density | Clusters and clearings; layered foreground, midground, background | Sparse uniform scattering, bare ground | Match real-world density for natural biomes; ground cover on every "green" surface |
| Landmarks | Something tall and unique visible from afar to steer by | Flat skyline | At least one landmark visible from each major area |
| Materials | Roughness variation, worn edges catching light, macro variation | Uniform plastic sheen, visible tiling | Break tiling at 3+ scales; consistent texel density |
| Life | Wind in foliage, birds, particles, water motion | Static scene | Something moves in every wide shot |

## Character rubric

- **Silhouette:** recognisable as a solid black shape; costume and hair give a distinct outline.
- **Proportions:** consistent with the chosen style (stylized adult heroes are often around 6.5–7.5 heads tall, younger anime characters around 5.5–6.5); check front, 3/4 and side.
- **Face:** clean shading without noisy shadows across cheeks (edited normals or face shadow maps in toon styles); eyes set with believable spacing and placement for the style; nose and mouth small and coherent in 3/4 view; the 3/4 view is the hardest and most important one.
- **Hair:** built from clumps or ribbons with layered silhouettes, never a single helmet shell; an anisotropic highlight band; hair casts shadow on the face; secondary motion without clipping.
- **Skin:** reads as skin under daylight, shade and night; shadowed skin keeps warmth instead of turning grey or blue.
- **Costume:** folds that follow joints and gravity; layers with thickness; no clipping in idle, run, jump, sit, ride, attack and landing poses (capture each).
- **Expression and pose:** idle poses with weight shift; no locked knees or T-pose leftovers; the face can show the emotions the story needs.

## VFX rubric

- **Readable shape at gameplay distance**: the effect tells you what it does from its silhouette.
- **Timing**: anticipation, a fast impact, then a slower dissipation. Effects that fade in and out linearly feel weak.
- **Layering**: core, glow, sparks/debris, smoke or residue, light on the surroundings, and screen feedback (shake, hit-stop) where appropriate.
- **Value contrast**: the hot core brighter than anything around it; the effect reads against both bright and dark backgrounds.
- **Volume**: no flat camera-facing cards that show their edge from the side; crossed cards, meshes or volumetric techniques for fire, smoke and water.
- **Physical plausibility**: splashes follow the impactor's velocity and fall under gravity; debris scales with energy; scorch marks and craters persist where the design says they should.

## Motion and game-feel rubric

- **Principles**: anticipation, follow-through, ease-in/ease-out, arcs, secondary motion.
- **Responsiveness**: input to visible response within a frame or two; locomotion that accelerates and decelerates with weight.
- **Impact**: hit-stop on heavy hits (a few frames, scaled by damage), brief camera shake, enemy reaction.
- **Telegraphs**: enemy wind-ups long enough to read and react to (often a few hundred milliseconds or more for big attacks).
- **Camera**: smooth follow with lag, no clipping into geometry, framing that shows what the player needs.

## UI rubric

- One clear primary action per screen; visual hierarchy by size, weight and contrast.
- A spacing scale (multiples of 4 or 8 px) and an alignment grid, used everywhere.
- A type scale (ratio about 1.2–1.33), at most two typefaces, line length 45–75 characters for reading text.
- Text contrast at least 4.5:1 (WCAG AA).
- Every interactive element has hover, pressed, focused and disabled states.
- Transitions of 150–300 ms with easing; nothing pops without a reason.
- Fits at phone width and the largest target resolution; room for longer translated strings.
- Style matches the world: a fantasy game's menus should not look like an admin dashboard.

## Feedback template

```markdown
## Aesthetic review: <milestone>, turn <NNN>
Captures: <camera bookmarks, settings>; sheet: <path>.

Working (keep it):
- <specific element> works because <principle>.

Gaps, ranked by visual impact:
1. [Lighting] <observation, where, which capture>. Breaks: <principle>. Target: <measurable>. Study/try: <technique, source>.
2. [Density] …
3. [Character/hair] …

Re-shoot: <same cameras>; deliver a before/after sheet from look.py.
```

Three gaps per round is usually right. Name the most important one first; GPT gives the first item the most effort.
