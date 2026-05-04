# Clean/no-overlay version

This is the alternate version requested after the first published pass. It removes the added art-directed overlay geometry:

- no straight red torii/gate foreground lines
- no white angled Fuji/roofline lines above the foreground
- no stylized white text-bird/crane overlays at the top
- no kana-like neon marks added by the renderer

It keeps the core source-to-ASCII conversion and the breathing/pulsing generative variant.

## Files

- `future_edo_cranes_ascii_clean.mp4` — clean high-quality ASCII conversion
- `future_edo_cranes_ascii_clean_breathe.mp4` — clean breathing/pulsing variant
- `future_edo_cranes_ascii_clean.gif` — GIF preview
- `future_edo_cranes_ascii_clean_breathe.gif` — GIF preview
- `contact_sheet_ascii_video_clean.png` — QA contact sheet
- `poster_clean_ascii_2s.png` — poster frame
- `poster_clean_breathe_2s.png` — poster frame
- `render_ascii_city_clean.py` — clean renderer script

## Verification

`ffprobe`:

- MP4s: 1280x720, 24fps, 5.000s
- GIFs: 960x540, 12.5fps, 5.000s

Visual QA confirms the added foreground red lines, white angled lines, and stylized white bird/crane overlays are absent. The result reads as a cleaner source-derived futuristic ASCII cityscape, with a separate breathe/pulse variant.
