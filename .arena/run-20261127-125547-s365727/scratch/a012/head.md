# Turning a 2D floor plan into a 3D model: build plan

## 1. Recommendation in one paragraph

Do not go straight from picture to 3D. Go **picture -> a small, human-checkable JSON description of the plan ("plan IR": walls, openings, rooms, in metres) -> 3D**. Every 3D output (a three.js web viewer, a `.glb` file, Blender renders) is generated from that one JSON file. This is what makes the walls accurate: you can check and fix the JSON, which you cannot do with pixels or with an AI-generated image. Computer vision proposes the JSON, a vision LLM (Claude reading the plan image) supplies what CV is bad at (room names, dimension text, door/window type), and you correct the rest in a thin editing step. The first version (section 9) is already built and was run in this container: it turns a raster plan into `plan.json`, then a three.js scene, a `.glb`, and PNG renders, with no Blender needed.

## 2. Assumptions (nothing was stated, so I chose these)

1. Input is a **clean architectural plan** (CAD/PDF export or good scan, mostly black walls on white), one storey, one image per floor. Hand sketches and photos of paper are Phase 3.
2. Walls are **axis-aligned (horizontal/vertical)** in the MVP. Diagonal and curved walls are Phase 2.
3. The plan has a **known scale**: a printed dimension, a scale bar, or at least one length you can type in. Without scale there is no true 3D size; the pipeline refuses to guess silently.
4. "3D model" means: an explorable model plus standard files (`.glb`, optionally `.blend`) and still renders (top-down, isometric, eye-level). Not a BIM/IFC model with structure and MEP (mentioned as an extension).
5. Ceiling height defaults to 2.7 m, door height 2.05 m, window sill 0.9 m, window height 1.2 m when the plan does not say. Every defaulted value is flagged in the JSON so it is never mistaken for a measurement.
6. You work in this cloud container: Linux, Python 3.13, Node 22, headless Chromium via Playwright, outbound traffic through a proxy that allows some hosts only.

## 3. What I checked in the container (evidence, not assumption)

| Check | Result | Consequence for the plan |
|---|---|---|
| `which blender` | not installed | Blender is not the MVP renderer |
| `download.blender.org` | HTTP 403 from the egress proxy | Do not plan on downloading Blender tarballs. Try `pip install bpy` instead (PyPI lists bpy 5.1 to 5.3 for this interpreter; **I did not install or run it**, treat as untested) |
| `cdn.jsdelivr.net` | HTTP 403 | A three.js page must not load libraries from a CDN here. Install `three` from npm and serve it locally (the MVP does) |
| `pip install opencv-python-headless` | works (OpenCV 5.1.0) | CV step is feasible with pip packages |
| `npm i three@0.160.0` | works | local three.js is feasible |
| Playwright + Chromium, software GL (`--use-gl=swiftshader`) | rendered a 1280x800 WebGL scene and exported a GLB | renders and screenshots work headless |
| `tesseract` binary | not installed | Do OCR with Claude's vision (read the image), or pip OCR such as `rapidocr-onnxruntime` (untested here) |
| Preinstalled Python libs | numpy, pillow only | everything else is `pip install`ed |

I ran the MVP code in section 9 on a synthetic 6 m x 4 m two-room plan (wall 0.15 m, one 0.9 m door gap, one 1.2 m gap in the opposite wall, a thin dimension line and text). It found 5 walls (thickness 0.15-0.16 m) and 2 openings (widths 1.21 m and 0.91 m, i.e. gap measurement is within about 0.01 m of the 1.2 and 0.9 drawn, plus an anti-aliasing margin), removed the dimension line and text, and rendered the walls, holes and floor with no mirroring (window stayed on the top wall, door on the bottom). Real, messy plans are untested; section 8 lists where I expect failure.

## 4. Options considered

Scores 1 (poor) to 5 (good). Criteria: **Acc** dimensional accuracy; **Open** doors/windows/semantics; **MVP** speed to a first working version; **Here** works in this container as verified in section 3; **Out** editable, standard output files; **Look** ceiling on visual quality; **Per-plan** effort for each additional plan.

| Option | Acc | Open | MVP | Here | Out | Look | Per-plan | Total |
|---|---|---|---|---|---|---|---|---|
| A. AI image generator turns the plan into a "3D render" (img2img) | 1 | 1 | 5 | 2 | 1 | 4 | 5 | 19 |
| B. Fully automatic CV -> three.js, no human step | 3 | 2 | 4 | 5 | 4 | 3 | 5 | 26 |
| C. **CV + vision LLM propose a JSON, human corrects, JSON -> three.js/glTF now, Blender later** | 5 | 4 | 3 | 5 | 5 | 4 | 4 | **30** |
| D. Pretrained deep floor-plan segmentation model (CubiCasa5K-style) then vectorize | 3 | 3 | 1 | 2 | 4 | 3 | 4 | 20 |
| E. Fully manual tracing in a browser (click corners, type widths) | 5 | 5 | 4 | 5 | 5 | 3 | 2 | 29 |
| F. Same as C but Blender (bpy) as the only backend | 4 | 4 | 2 | 2 | 5 | 5 | 3 | 25 |

Why C: A cannot be trusted for geometry (image generators redraw walls, change room sizes and invent furniture; fine as an optional mood picture, never as the model). D needs model weights, a GPU for comfortable use and a licence check (CubiCasa5K's data is published for research use; verify terms before building on it), and it still outputs raster masks you must vectorize. B has no place to fix errors, so one wrong wall silently ships. E is accurate but costs minutes per room, so it is kept as the **fallback editing mode inside C**. F is the best-looking but the least runnable here today. Because everything hangs off the JSON, choosing C does not lock you out of F: Blender becomes a second exporter (Phase 2). Totals are close for C, E and F, so treat the matrix as a ranking of risk, not a precise measurement; the tie-breaker is "works in this container today, and improves per plan".

## 5. Architecture

```
 plan.png / .pdf / scan
        |
 [0] normalise: PDF -> PNG at 200-300 dpi, deskew, crop, scale calibration
        |
 [1] geometry (OpenCV): wall mask -> wall bars -> gaps = candidate openings
 [2] semantics (Claude vision / OCR): room names, dimension strings, door vs window, swing side
        |
        v
   plan.json   <-- single source of truth (metres, y down like the image)
        |   ^
        |   +-- [3] validate + human fix (overlay on the plan; edit JSON or a small web editor)
        |
   +----+---------------------+-------------------------+
   v                          v                         v
 three.js viewer      model.glb (GLTFExporter)     Blender bpy (Phase 2)
 + Playwright PNGs    opens anywhere               model.blend, Cycles renders, walkthrough MP4
```

### The plan IR (`plan.json`)

```json
{
  "units": "m", "height": 2.7, "source": "plan.png",
  "scale": {"method": "dimension-string", "ppm": 100, "check_error_pct": 0.4},
  "walls":    [{"id": "w0", "a": [0.94, 1.01], "b": [7.1, 1.01], "t": 0.16, "h": 2.7}],
  "openings": [{"id": "o0_0", "wall": "w0", "type": "window", "offset": 1.69, "width": 1.2,
                "sill": 0.9, "height": 1.2, "confidence": "low"}],
  "rooms":    [{"name": "Living", "polygon": [[1,1],[4.5,1],[4.5,5],[1,5]], "floor": "oak"}]
}
```
`a`/`b` are a wall's centreline ends, `t` its thickness, `offset` the distance from `a` along the wall to the opening's centre. Only `walls`, `openings` and `ppm`-derived metres are produced by the MVP script; `scale`, `rooms` and `type` are filled by the semantic step or by hand.

## 6. Step-by-step pipeline and how each accuracy problem is handled

**Step 0. Normalise and calibrate scale (the step that decides all accuracy).**
- PDF: rasterise at 300 dpi (`pymupdf`: `page.get_pixmap(dpi=300)`), pick the plan page, crop to the drawing. Use vector extraction instead if the PDF is a CAD export (its lines are real vectors; `page.get_drawings()` gives exact wall lines and removes the CV step entirely).
- Scale, in order of trust: (1) two points on a dimension line with the printed value, (2) a scale bar, (3) a typed-in length of one wall, (4) a standard door leaf, about 0.9 m, as a last-resort sanity check only. Compute `ppm = pixel_distance / metres`.
- Cross-check: read at least two or three printed dimensions (Claude vision, or OCR) and compare each with the measured distance in the extracted model. If any differ by more than 2%, flag the plan: either the scan is skewed/non-uniformly scaled or the dimension was misread. Store the worst error in `scale.check_error_pct`.
- Deskew: detect the dominant wall angle (Hough lines or minAreaRect on the wall mask) and rotate so walls are axis-aligned.

**Step 1. Walls.** Binarise (Otsu). A morphological opening with a kernel about the thinnest real wall (0.08 m in pixels) removes text, hatching and dimension lines, which are thinner than walls. Open again with long 1-pixel kernels to keep only long horizontal bars and long vertical bars; each connected component is one wall, giving centreline and thickness directly from its bounding box. This is the code in section 9. Plans that draw walls as two thin parallel lines (hollow walls) need the gap between the lines filled first (close with a kernel of the wall thickness), or use vector extraction for PDFs.

**Step 2. Openings.** Where two collinear wall bars are separated by 0.5 to 2.6 m, treat the gap as an opening and merge the bars into one wall (done in the MVP). The *type* is not decidable from the gap alone, so the MVP labels every opening `door` with `confidence: low`; type comes from: a door swing arc (quarter circle plus a leaf line; `cv2.HoughCircles` is unreliable on arcs, so use Claude vision on a crop of each gap) or three thin parallel lines in the gap (window). Defaults: door sill 0 / height 2.05; window sill 0.9 / height 1.2; override with annotations such as "W1200x1500" when present.

**Step 3. Rooms and floors.** Rasterise the wall mask, flood-fill the free space, and polygonise each connected region (`cv2.findContours`); doors close the topology, so close each opening with a thin virtual segment first, otherwise all rooms merge into one. Assign names by finding the label text inside each region (vision/OCR). The MVP skips this and uses one rectangular floor slab.

**Step 4. Validate and correct (human in the loop).** Draw the JSON back over the source image (walls red, openings blue with ids, rooms tinted) and save `overlay.png`. Checks that run automatically: every wall end touches another wall or is within 1 wall thickness of one; no wall shorter than 0.3 m; no opening wider than 85% of its wall; every room closed; total area within 5% of any printed area. Failures are listed, never auto-fixed. You fix them by editing the JSON (or in a small canvas editor, Phase 2) and re-running only the 3D step.

**Step 5. Build the 3D (geometry rules).**
- Each wall is a rectangle `length x height` in its own vertical plane, with one rectangular **hole per opening**, extruded by the thickness. This gives true, watertight openings. (Verified in the MVP render.)
- Coordinate convention: plan `(x, y)` -> world `(x, 0, y)`, plan y down maps to +z. Looking from above with the camera up-vector `(0,0,-1)` shows the model in the same orientation as the plan, so nothing is mirrored. Mirroring is the most common silent bug in this kind of project.
- Corner joints: extractor bars already include the corner squares. For hand-drawn walls snap endpoints and extend each by `t/2` at T and L joints, otherwise corner notches appear.
- Floor: one slab per room polygon, lifted 0 mm; optional ceiling at `height`, hidden in cutaway renders.
- Door leaves and window glass: Phase 2, as simple boxes placed from the opening record.

**Step 6. Materials.** Map by room name through a small table (`kitchen`/`bath` -> tile, `living`/`bedroom` -> oak, walls -> off-white, exterior -> brick). Use plain PBR colours first (as in the MVP); add textures (CC0 sets from Poly Haven, downloaded once and checked for proxy access) in Phase 2. Never let an AI generator choose materials per wall; give it a fixed table so renders are reproducible.

**Step 7. Lighting and cameras.** MVP: hemisphere + one shadow-casting directional light. Phase 2 in Blender: sun + sky, one area light per window (placed from the openings list so lighting matches reality), interior point lights per room, Cycles with denoising at 128 samples for stills. Cameras: top-down orthographic (the "3D floor plan"), isometric cutaway (remove ceiling and near walls), eye-level per room at 1.6 m from each room's centroid looking at its longest wall.

**Step 8. Export.**

| File | Made by | Use |
|---|---|---|
| `plan.json` | extractor + your edits | source of truth, diffable in git |
| `overlay.png` | validation step | proof the model matches the plan |
| `model.glb` | three.js GLTFExporter (MVP), Blender (Phase 2) | opens in Blender, Windows 3D viewer, Quick Look, web |
| `render_top.png`, `render_persp.png`, per-room `render_<room>.png` | Playwright screenshots (MVP), Cycles (Phase 2) | client images |
| `model.blend`, `walkthrough.mp4` | Blender (Phase 2) | editing, video |
| `viewer.html` + `plan.json` | MVP | explorable model; must be served over http (not `file://`) |

## 7. Where a vision LLM and where CV should be used

Use CV (pixels, exact) for coordinates and thicknesses. Use Claude vision for meaning: room names, reading dimension strings, deciding door vs window, spotting that a plan has two storeys on one sheet. Do not trust an LLM's pixel coordinates; ask it to report *labels and counts*, then verify against CV (for example "3 doors, 4 windows" must match the openings found). I did not measure how accurate any LLM is at this on real plans; the count cross-check is there because of that.

## 8. Risks and failure cases

| Failure case | What goes wrong | Mitigation |
|---|---|---|
| No or wrong scale | Everything is the wrong size, plausibly | Refuse to export without `ppm`; two-dimension cross-check, 2% rule |
| Scan skew / photo perspective | Walls not parallel, scale non-uniform | Deskew; for photos, 4-point homography using a known rectangle; flag Phase 3 |
| Hollow (double-line) walls | Opening removes them, no walls found | Close mask first, or use PDF vector extraction |
| Hatched/poché or furniture drawn heavy | False walls | Min-length filter, manual delete in overlay review |
| Thin interior partitions drawn thinner than `--wall-min` | Walls missing | Lower `--wall-min`; the overlay shows the miss |
| Diagonal/curved walls | Dropped or staircased | Out of MVP scope; Phase 2 uses Hough + polyline simplification |
| Door gap misread as window and vice versa | Wrong openings | `confidence: low` default and review; swing-arc check |
| Doors left open in drawing leave no gap | Missing door | Arc detection, plan symbol check by vision |
| Stairs, columns, balconies, sloped ceilings, double heights | Not representable | Listed as unsupported; stairs as a placeholder block Phase 3 |
| Multiple floors on one sheet | Merged garbage | Split sheet first (manual crop) |
| Browser cannot load libraries (this container blocks CDNs) | Blank page | Serve three.js from local `node_modules` (done) |
| `file://` fetch of `plan.json` blocked | Blank page | Always serve through a local HTTP server |
| Software GL is slow and noisy | Slow shadows | Keep scenes small; use Blender Cycles for quality |
| Copyright / client confidentiality of plans | Plan uploaded to external services | Keep processing local; only use external image APIs with permission |
| AI-image "render" shown as if it were the model | Misleading sizes | Label any AI picture "illustration, not to scale" |

## 9. The minimal first version (runnable now)

Time to build: about half a day including your own plan. Folder `plan3d/`.

Setup:
```bash
mkdir plan3d && cd plan3d
python3 -m venv v && ./v/bin/pip install opencv-python-headless numpy pillow
npm init -y && npm i three@0.160.0 playwright     # if Chromium is missing: npx playwright install chromium
# put your plan in plan.png, then (ppm = pixels per metre, from step 0):
./v/bin/python plan2ir.py plan.png --ppm 100       # writes plan.json (review it!)
node render.mjs                                   # writes render_persp.png, render_top.png, model.glb
```
Calibration for `--ppm`: if a printed 5.00 m dimension spans 612 px between its ticks, `ppm = 612 / 5.0 = 122.4`.

Then open `plan.json`, set each opening's real `type` (`door` or `window`), and for windows set `"sill": 0.9, "height": 1.2`; re-run only `node render.mjs`.

### `plan2ir.py` (tested on a synthetic plan)

```python
@@PLAN2IR@@
```

### `viewer.html` (three.js, served locally; tested)

```html
@@VIEWER@@
```

### `render.mjs` (Playwright: tiny static server, screenshots, GLB export; tested)

```js
@@RENDER@@
```

### Known limits of this MVP code (so you are not surprised)

- Openings default to type `door` and height 2.05 m even if the gap is a window; you must edit them. (In my test the 1.2 m window gap rendered as a floor-to-lintel hole until edited.)
- One floor slab covering the walls' bounding box; no per-room floors yet. The slab is drawn at the wall centrelines' bounds, so it can sit under the outer wall edge; harmless visually.
- Axis-aligned only. Walls shorter than `--min-len` (0.6 m) are dropped.
- Image margin offsets are kept in the coordinates (my test plan has a 1 m margin); the viewer recentres, so it does not matter for display, but subtract it if you need origin-at-corner.
- The GLB exports the scene without the hemisphere light (the exporter ignores it and warns); geometry and materials are exported.

## 10. Roadmap after the MVP

1. **Semantics (1-2 days):** Claude vision pass per plan to produce room names, door/window types and printed dimensions as a JSON patch; auto-apply only if counts match CV; scale cross-check and `overlay.png`.
2. **Rooms and floors:** polygonise rooms, per-room materials, ceilings, cutaway toggle.
3. **Blender backend:** `pip install bpy` (test it first), a script that reads `plan.json`, builds each wall from its footprint with `bmesh`, cuts openings with Boolean difference of box cutters, adds door/window frames, sun + area lights, Cycles stills and `.blend`/`.glb`. Alternatively drive a running Blender through its MCP add-on if you have Blender on your own machine.
4. **Editor:** a small canvas page to drag wall ends and toggle opening types, writing back to `plan.json`.
5. **Hard inputs:** diagonal walls, hand sketches, photos with homography, multi-storey stacks, optional IFC export.

## 11. Acceptance test (how you know it works)

Take one real plan with at least three printed dimensions. Pass if: (a) every printed dimension agrees with the same distance measured in `plan.json` within 2%; (b) door and window counts in the render equal those on the plan; (c) the overlay shows no unmatched wall; (d) the top-down render, laid over the original, has the same orientation (not mirrored); (e) `model.glb` opens in Blender or another viewer at the right size (a 1 m cube-sized check: import and measure one wall).
