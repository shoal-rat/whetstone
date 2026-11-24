# Research first: take the highest as your model

> Aim at the highest and you reach the middle; aim at the middle and you reach the bottom.
> (Chinese proverb, after Tang Taizong's *Difan*)

GPT left to itself builds from what it already "knows", which in craft domains means the average of the internet: grey boxes, flat light, symmetrical faces, sparse scattering. The fix is cheap: before it builds, make it study how the best practitioners solve the same problem, extract techniques with numbers, and apply them.

## Contents
- When research is required
- What counts as a good source
- Starting points by domain
- Checking the research
- Learn methods, make original work

## When research is required

Before the first build turn in any craft domain the contract lists, and again whenever the same quality gap survives two review rounds. Also for engineering domains where known solutions exist and naive ones fail later: networking, physics stepping, rendering pipelines, streaming and LOD, save systems, parsers, concurrency, databases.

## What counts as a good source

In rough order of trust:
1. Official manuals and documentation for the engine, library or tool in use.
2. Talks by the studios or engineers who shipped the thing: GDC, CEDEC, SIGGRAPH (including the Advances in Real-Time Rendering course), Unite, Unreal Fest, and written postmortems.
3. Art and tech breakdowns by the artists themselves (studio blogs, 80.lv interviews, ArtStation breakdowns).
4. Canonical books.
5. Respected educators with worked examples.
6. Real-world data when imitating the real world: forest stem densities, building heights, street widths, light levels, animal gaits.

Weak: listicles, SEO blogs, AI-generated summaries, forum answers without reasoning, "top 10 tips".

## Starting points by domain

These are seeds, not limits. GPT should search for the best current sources for the project's exact engine and style.

**Characters, faces, hair (stylized / anime 3D)**
- Arc System Works, "Guilty Gear Xrd's Art Style: The X Factor Between 2D and 3D" (GDC 2015): edited normals for clean face shading, hand-placed shadow thresholds, limited animation.
- Andrew Loomis, *Drawing the Head and Hands*: head construction and facial proportions.
- Polycount wiki (wiki.polycount.com): face and body topology, edge loops for deformation.
- Hair: clump/card workflows in the engine's docs; Thorsten Scheuermann, "Hair Rendering and Shading" (GDC 2004) for anisotropic highlights.
- Search: "<engine> anime toon shader face shadow", "stylized hair clumps modeling breakdown", "character turnaround proportions <style>".

**3D modelling and sculpting**
- The Blender Manual (docs.blender.org) for tool behaviour; Polycount wiki for topology and baking.
- Artist breakdowns on 80.lv and ArtStation for the target style.
- Procedural modelling in code: the engine's geometry docs, Inigo Quilez's articles (iquilezles.org) for SDFs and noise, *The Book of Shaders*.

**Materials, lighting, colour**
- Google's Filament documentation (physically based rendering explained in depth).
- *Real-Time Rendering* (Akenine-Möller et al.) and the SIGGRAPH "Advances in Real-Time Rendering" course notes.
- The engine's own lighting guides (Unreal and Unity both publish scene-lighting tutorials).
- James Gurney, *Color and Light*: light ratios, atmospheric perspective, warm/cool relationships.
- Search: "<engine> stylized lighting breakdown", "<game in the target style> rendering GDC".

**Level and world design**
- Nintendo's *Breath of the Wild* talks: GDC 2017 "Breaking Conventions with The Legend of Zelda: Breath of the Wild" and the CEDEC 2017 field-design sessions (the triangle rule, gravity, landmarks).
- Kevin Lynch, *The Image of the City*: paths, edges, districts, nodes, landmarks; why a map is readable.
- Christopher Totten, *An Architectural Approach to Level Design*.
- Red Blob Games (redblobgames.com) for maps, grids and procedural generation.

**Environment density and foliage**
- Guerrilla Games, "GPU-Based Procedural Placement in Horizon Zero Dawn" (GDC 2017): rule-based placement by ecotope.
- Real ecology data for the biome being imitated (stems per hectare, canopy cover, undergrowth).
- The engine's foliage/instancing and LOD documentation.

**VFX**
- Real Time VFX community (realtimevfx.com) and its style breakdowns.
- Studio VFX talks (for example "The VFX of Diablo", GDC 2013).
- The engine's particle system docs (Niagara, VFX Graph, or the library in use).
- Search: "stylized fire VFX breakdown", "impact VFX timing anticipation".

**Animation and game feel**
- Thomas & Johnston, *The Illusion of Life*: the twelve principles.
- Steve Swink, *Game Feel*.
- "Juice It or Lose It" (Jonasson & Purho, 2012) and "The Art of Screenshake" (Jan Willem Nijman, 2013).
- Masahiro Sakurai on Creating Games (hit-stop, telegraphs, readability).
- David Rosen, "An Indie Approach to Procedural Animation" (GDC 2014).

**UI and typography**
- *Refactoring UI* (Wathan & Schoger); Butterick's *Practical Typography*.
- Apple Human Interface Guidelines; Material Design.
- Game UI Database (gameuidatabase.com) for genre conventions.

**Audio and music**
- The engine's audio docs; Winifred Phillips, *A Composer's Guide to Game Music*.
- Search: "adaptive music layers <engine>", "game audio mixing loudness".

**Engineering**
- Robert Nystrom, *Game Programming Patterns* and *Crafting Interpreters*.
- Glenn Fiedler, Gaffer on Games ("Fix Your Timestep!", networking articles); Valve's "Source Multiplayer Networking".
- "Overwatch Gameplay Architecture and Netcode" (GDC 2017).
- Martin Kleppmann, *Designing Data-Intensive Applications*.
- web.dev for web performance.

## Checking the research

Before you accept a research note:
- **It happened.** The turn digest lists the web searches and the domains returned. Sources with no searches behind them were written from memory.
- **It is primary.** Most sources are manuals, talks, breakdowns or books, not listicles.
- **It has numbers.** Proportions, densities, ratios, timings, budgets. A note with no numbers rarely changes the build.
- **It maps to work.** Each technique names where it applies in this project and which acceptance item it serves.
- **Spot-check one source yourself** if anything looks off (fetch the page, confirm it says what the note claims).
- **It changed the result.** The proof capture shows a class change, not a tweak.

## Learn methods, make original work

Research is for techniques, proportions and principles. GPT must not copy others' models, textures, characters, logos, level layouts or music, and must not ship reference images. References the user supplies privately stay out of the repository. When the user asks for a style "like" a known work, take the visual grammar (shading model, palette logic, proportions) and make original assets.
