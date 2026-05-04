# Future Edo Cranes — FAL Video to Breathing ASCII Video

Generated: 2026-05-04

A 5-second 720p FAL text-to-video generation of a futuristic Japanese cityscape with cranes flying overhead, converted into high-quality ASCII video and a second generative "pulse/breathe" ASCII variant.

## Creative score

A rain-dark Future Edo city is seen through a terminal shrine gate. Neon towers and canal ribs converge toward a Fuji-like ridge. White crane glyphs cross the sky. The first ASCII pass preserves the generated source; the second makes the city breathe with slow luminance, glow, scanline, and architectural ripple modulation.

## Source generation

- Tool: `falimg`
- Endpoint/model: `bytedance/seedance-2.0/text-to-video`
- Prompt: cinematic futuristic Japanese cityscape at blue hour, neon Edo-Tokyo skyline with pagoda rooftops integrated into glass megatowers, reflective canal, holographic paper lanterns, rain-slick streets, Mount Fuji silhouette far behind, flock of white cranes flying gracefully overhead across the sky, elegant camera drift forward, atmospheric mist, high contrast, no text, no logo, no subtitles
- Resolution: `720p`
- Duration: `5`
- Aspect ratio: `16:9`
- Audio: disabled
- Seed: `1843799664`

Source output: `1777894707-bytedance-seedance-2.0-text-to-video-1.mp4`

Verified with ffprobe: `1280x720`, `24 fps`, `5.041667s`, H.264.

## ASCII conversion workflow

The renderer is `render_ascii_city.py`.

Pipeline:

1. Decode source video with OpenCV.
2. Sample to a 160 x 72 character grid for a 1280 x 720 output canvas.
3. Combine luminance, Canny edges, central perspective masks, and skyline density.
4. Render colored glyphs with Pillow/DejaVu Sans Mono.
5. Add art-directed elements so prompt-critical concepts survive ASCII:
   - explicit white crane glyph silhouettes
   - torii-like canal gate
   - Fuji/roofline contour
   - neon kana-like sign marks
   - cyan perspective/canal ribs
6. Encode two MP4s and two GIFs with ffmpeg.

## Outputs

- `future_edo_cranes_ascii.mp4` — high-quality 720p source-to-ASCII video.
- `future_edo_cranes_ascii_breathe.mp4` — 720p pulsing/breathing generative variant.
- `future_edo_cranes_ascii.gif` — GIF preview of ASCII video, 960x540.
- `future_edo_cranes_ascii_breathe.gif` — GIF preview of breathing variant, 960x540.
- `contact_sheet_ascii_video.png` — QA contact sheet sampled across both variants.
- `poster_ascii_2s.png` — poster frame from the ASCII version.
- `poster_breathe_2s.png` — poster frame from the breathing variant.
- `source_preview_2s.jpg` — preview of the generated source video.
- `source_ffprobe.json` — source ffprobe metadata.
- `manifest.json` — file sizes and SHA-256 hashes.

## QA notes

- Source preview clearly showed futuristic Japanese city, canal, Fuji, neon skyline, pagoda-like roofs, and small white birds/cranes.
- First ASCII pass made the city readable but cranes and Japanese cues were too subtle at contact-sheet scale.
- Renderer was revised to add explicit crane glyphs, a torii-like gate, Fuji ridge, and kana-like neon marks.
- Final visual QA passed: cranes are readable, futuristic Japanese cues are clear, and the breathing variant is controlled and acceptable.

## Local path

```text
/home/kuiqs/fal-outputs/futuristic-japanese-city-ascii-video-2026-05-04
```

Windows/WSL path:

```text
\\wsl.localhost\Ubuntu\home\kuiqs\fal-outputs\futuristic-japanese-city-ascii-video-2026-05-04
```


## GitHub Pages

Open `index.html` via GitHub Pages to view all outputs inline.


## Clean / no-overlay alternate version

Added after review feedback. This version removes the stylized foreground red gate lines, white angled Fuji/roofline lines, kana marks, and white text-bird/crane overlays.

- `assets/future_edo_cranes_ascii_clean.mp4`
- `assets/future_edo_cranes_ascii_clean_breathe.mp4`
- `assets/contact_sheet_ascii_video_clean.png`
- `assets/CLEAN_VERSION.md`


## Bare buildings-and-cranes version

Published a stripped-back alternate version focused on buildings and minimal crane forms. It removes the extra graphic overlays: red foreground gate lines, white angled roof/Fuji lines, kana/data-rain clutter, foreground ribs, and stylized text-bird overlays.

Direct files:

- `assets/future_edo_cranes_ascii_bare.mp4`
- `assets/future_edo_cranes_ascii_bare_breathe.mp4`
- `assets/contact_sheet_ascii_video_bare.png`
- `assets/future_edo_cranes_ascii_bare_outputs.zip`
- `assets/BARE_VERSION.md`

Bare ZIP SHA-256: `05a5f812c799e718dafe46e0a67e2943f6bd3fb476b2830a851d094eca34fd73`
