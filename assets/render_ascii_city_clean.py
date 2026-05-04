#!/usr/bin/env python3
from pathlib import Path
import cv2, math, subprocess, json, shutil, os, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

OUT = Path('/home/kuiqs/fal-outputs/futuristic-japanese-city-ascii-video-2026-05-04')
SRC = sorted(OUT.glob('*text-to-video-1.mp4'))[-1]
FRAMES = OUT/'frames_ascii_clean'
FRAMES_PULSE = OUT/'frames_ascii_clean_breathe'
for d in [FRAMES, FRAMES_PULSE]:
    if d.exists(): shutil.rmtree(d)
    d.mkdir(parents=True, exist_ok=True)

W,H = 1280,720
FPS = 24
DURATION = 5.0
N = int(FPS*DURATION)
# Cell size chosen to keep characters legible at 720p while preserving city detail.
CELL_W, CELL_H = 8, 10
COLS, ROWS = W//CELL_W, H//CELL_H

font_paths = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf',
]
font_path = next((p for p in font_paths if Path(p).exists()), None)
font = ImageFont.truetype(font_path, 10) if font_path else ImageFont.load_default()
small = ImageFont.truetype(font_path, 8) if font_path else ImageFont.load_default()
large = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()

# Theme-specific ramps. The early chars are sparse mist; the latter chars are hard keyblock/neon.
RAMP_CITY = np.array(list('  .`·,:;irsxvczXYUJCLQ0OZMW&8%B@$'))
RAMP_RAIN = np.array(list('  .:|¦┃╎╏╽╿┃╋'))
RAMP_NEON = np.array(list('  .,:;+=*#%@'))

cap = cv2.VideoCapture(str(SRC))
source_fps = cap.get(cv2.CAP_PROP_FPS) or 24
source_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1)

def read_frame(i):
    # Sample uniformly across actual source duration.
    src_idx = min(source_frames-1, int(i / max(1,N-1) * max(1,source_frames-1)))
    cap.set(cv2.CAP_PROP_POS_FRAMES, src_idx)
    ok, frame = cap.read()
    if not ok:
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0,source_frames-2))
        ok, frame = cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return cv2.resize(frame, (W,H), interpolation=cv2.INTER_AREA)

def tonemap(arr, gamma=0.78):
    f = arr.astype(np.float32)
    lo, hi = np.percentile(f[::4, ::4], [1, 99.6])
    if hi-lo < 10: hi = lo+10
    f = np.clip((f-lo)/(hi-lo), 0, 1)**gamma
    return (f*255).astype(np.uint8)

def add_scanlines(img, phase, strength=0.10):
    a = np.asarray(img).astype(np.float32)
    y = np.arange(a.shape[0])[:,None]
    line = 1.0 - strength*(0.5+0.5*np.sin(y*math.pi + phase))
    a *= line[...,None]
    return Image.fromarray(np.clip(a,0,255).astype(np.uint8))

def draw_crane(draw, x, y, s=1.0, alpha=230, color=(242,248,238)):
    # Explicit glyph-line cranes so prompt-critical birds survive ASCII abstraction.
    # Draw a dark halo first, then bright strokes: readable even at contact-sheet scale.
    wing = int(34*s); body=int(12*s); w=max(2,int(2.4*s))
    pts=[(x-wing,y),(x-int(11*s),y-int(10*s)),(x,y-int(4*s)),(x+int(11*s),y-int(10*s)),(x+wing,y-int(1*s))]
    halo=(0,7,15,185)
    ink=(*color, alpha)
    draw.line(pts, fill=halo, width=w+3, joint='curve')
    draw.ellipse([x-body,y-int(5*s),x+body,y+int(7*s)], outline=halo, width=w+3)
    draw.line([(x+body,y),(x+int(31*s),y-int(10*s))], fill=halo, width=w+2)
    draw.line([(x-int(3*s),y+int(6*s)),(x-int(12*s),y+int(24*s))], fill=halo, width=max(2,w))
    draw.line([(x+int(2*s),y+int(6*s)),(x+int(8*s),y+int(23*s))], fill=halo, width=max(2,w))
    draw.line(pts, fill=ink, width=w, joint='curve')
    draw.ellipse([x-body,y-int(5*s),x+body,y+int(7*s)], outline=ink, width=w)
    draw.line([(x+body,y),(x+int(31*s),y-int(10*s))], fill=ink, width=w)
    draw.line([(x-int(3*s),y+int(6*s)),(x-int(12*s),y+int(24*s))], fill=ink, width=max(1,w-1))
    draw.line([(x+int(2*s),y+int(6*s)),(x+int(8*s),y+int(23*s))], fill=ink, width=max(1,w-1))

def render_ascii(frame_rgb, idx, pulse_mode=False):
    t = idx / FPS
    u = idx / max(1,N-1)
    phase = 2*math.pi*u
    breath = 0.5+0.5*math.sin(phase)
    # Source preprocessing
    gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (3,3), 0)
    edges = cv2.Canny(gray, 65, 150).astype(np.float32)/255.0
    # Downsample values per cell.
    small_gray = cv2.resize(gray, (COLS,ROWS), interpolation=cv2.INTER_AREA).astype(np.float32)/255.0
    small_edge = cv2.resize(edges, (COLS,ROWS), interpolation=cv2.INTER_AREA)
    small_rgb = cv2.resize(frame_rgb, (COLS,ROWS), interpolation=cv2.INTER_AREA).astype(np.float32)
    # Density: keep skyline/edges; let sky be quieter except cranes/glyph dust.
    density = (1-small_gray)*0.72 + small_edge*0.85
    yy,xx = np.mgrid[0:ROWS,0:COLS]
    # Perspective avenue/canal glow down the middle.
    center = np.abs(xx-COLS/2)/(COLS/2)
    horizon = np.exp(-((yy-ROWS*0.55)/(ROWS*0.26))**2)
    avenue = np.exp(-(center/0.18)**2) * (yy/ROWS)**1.2
    density += 0.22*horizon + 0.15*avenue
    if pulse_mode:
        wave = np.sin(xx*0.19 + phase*2.0) * np.cos(yy*0.13 - phase*1.4)
        radial = np.sin(np.sqrt((xx-COLS/2)**2 + (yy-ROWS*.52)**2)*0.18 - phase*2.2)
        density += 0.11*breath + 0.08*wave + 0.07*radial
    density = np.clip(density, 0, 1)

    # Underpaint: dim source + cool blue paper/CRT ground.
    base = Image.fromarray(frame_rgb).resize((W,H)).filter(ImageFilter.GaussianBlur(0.55))
    base = ImageEnhance.Color(base).enhance(0.75)
    base = ImageEnhance.Contrast(base).enhance(0.82)
    bg = Image.new('RGB', (W,H), (4,10,18))
    canvas = Image.blend(bg, base, 0.32 if not pulse_mode else 0.38)
    canvas = canvas.convert('RGBA')
    d = ImageDraw.Draw(canvas, 'RGBA')

    # Tonal fog and vignette.
    d.rectangle([0,0,W,H], fill=(5,10,22,70))
    for k in range(9):
        y = int(H*(0.08+k*0.105) + math.sin(phase+k)*5)
        d.line([(0,y),(W,y+int(math.sin(k)*16))], fill=(65,110,150,18), width=1)
    # Draw glyph cells.
    for r in range(ROWS):
        y = r*CELL_H - 1
        # Skip some sky cells for air/ma but preserve pulse texture.
        for c in range(COLS):
            val = density[r,c]
            if val < (0.18 if pulse_mode else 0.22):
                continue
            x = c*CELL_W
            rgb = small_rgb[r,c]
            # neon palette roles from source color + designed cyan/magenta accents.
            b = float(np.mean(rgb))/255.0
            edge = small_edge[r,c]
            if r < ROWS*0.32 and val < 0.45:
                ramp = RAMP_RAIN
                color = (100+int(70*breath), 160+int(40*edge), 210+int(35*val), int(80+90*val))
            elif edge > 0.18:
                ramp = RAMP_CITY
                color = (210, 235, 245, int(150+85*min(1,val)))
            else:
                ramp = RAMP_NEON if (c+r+idx)%7==0 else RAMP_CITY
                # Futuristic Tokyo neon: cyan body, magenta signs, warm lantern sparks.
                if rgb[0] > rgb[2]*1.12 and (c+r)%5==0:
                    color = (255, 94, 132, int(110+100*val))
                elif rgb[2] > rgb[0]*1.05:
                    color = (72, 205, 255, int(105+105*val))
                else:
                    color = (190, 224, 214, int(95+95*val))
            j = min(len(ramp)-1, max(0, int(val*(len(ramp)-1))))
            ch = ramp[j]
            # Breathing mode displaces a little without destroying structure.
            dx = int((math.sin(r*0.37+phase*2)+math.sin(c*0.21-phase))*breath*1.4) if pulse_mode else 0
            dy = int(math.sin(c*0.13+phase)*breath*0.9) if pulse_mode else 0
            d.text((x+dx, y+dy), ch, font=font, fill=color)

    # Cyber-washi vertical sign strokes and city data rain, restrained.
    rng = np.random.default_rng(1234 + idx//3)
    for k in range(58):
        x = int((k*37 + math.sin(phase+k)*16) % W)
        y0 = int(H*(0.18 + 0.55*((k*17)%97)/97))
        h = int(16 + 80*((k*13)%31)/31)
        col = (60,220,255,42) if k%3 else (255,80,135,48)
        if pulse_mode:
            col = (col[0], col[1], col[2], min(105, int(col[3]*(1+0.75*breath))))
            h += int(18*breath)
        d.line([(x,y0),(x+int(math.sin(k)*5),min(H,y0+h))], fill=col, width=1)

    # Explicit skyline/canal perspective glyph ribs.
    for k in range(16):
        f = k/15
        x1 = int(W/2 + (f-.5)*W*0.16)
        spread = int((f-.5)*W*0.9)
        col=(80,185,230,36 if not pulse_mode else int(42+34*breath))
        d.line([(W//2 + x1//80, int(H*.57)), (W//2+spread, H)], fill=col, width=1)
    # Clean variant: no added stylized torii/Fuji/kana foreground overlays.
    # Clean variant: no added stylized crane/bird overlay silhouettes.
    # Pulse/breathe generative modification: slow glow, slight chromatic ghost, wave halos.
    if pulse_mode:
        overlay = Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(overlay,'RGBA')
        # City breath rings from Fuji/canal vanishing point (non-orb, architectural arcs).
        for k in range(7):
            y = int(H*(0.52 + k*0.075 + 0.01*math.sin(phase+k)))
            alpha = int(18 + 28*breath*(1-k/8))
            od.arc([W//2-220-k*80, y-60-k*12, W//2+220+k*80, y+70+k*26], 190, 350, fill=(92,220,255,alpha), width=2)
        # Paper-neon breathing wash.
        od.rectangle([0,0,W,H], fill=(8,30,48,int(12+16*breath)))
        canvas = Image.alpha_composite(canvas, overlay)
        canvas = canvas.filter(ImageFilter.UnsharpMask(radius=1.0, percent=105, threshold=4))
    # Border and title bug small enough not to dominate.
    d = ImageDraw.Draw(canvas,'RGBA')
    d.rectangle([18,18,W-18,H-18], outline=(180,235,245,82), width=1)
    d.text((30,H-34), 'FUTURE EDO // SOURCE ASCII SIGNAL // CLEAN', font=small, fill=(190,235,245,150))
    d.text((W-164,H-34), ' breathe' if pulse_mode else ' source-ascii', font=small, fill=(255,95,135,145))

    out = add_scanlines(canvas.convert('RGB'), phase, strength=0.06 if not pulse_mode else 0.09)
    return out

def encode(frames_dir, mp4, gif=None):
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate',str(FPS),'-i',str(frames_dir/'f_%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium',str(mp4)], check=True)
    if gif:
        vf='fps=12,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=160:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3'
        subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate',str(FPS),'-i',str(frames_dir/'f_%04d.png'),'-vf',vf,'-loop','0',str(gif)], check=True)

def main():
    for i in range(N):
        fr = read_frame(i)
        im = render_ascii(fr, i, False)
        im.save(FRAMES/f'f_{i:04d}.png')
        imp = render_ascii(fr, i, True)
        imp.save(FRAMES_PULSE/f'f_{i:04d}.png')
        if i % 20 == 0: print('frame', i, '/', N, flush=True)
    encode(FRAMES, OUT/'future_edo_cranes_ascii_clean.mp4', OUT/'future_edo_cranes_ascii_clean.gif')
    encode(FRAMES_PULSE, OUT/'future_edo_cranes_ascii_clean_breathe.mp4', OUT/'future_edo_cranes_ascii_clean_breathe.gif')
    # Poster frames/contact sheet.
    for name, dpath in [('ascii',FRAMES),('breathe',FRAMES_PULSE)]:
        Image.open(dpath/'f_0048.png').save(OUT/f'poster_clean_{name}_2s.png')
    thumbs=[]
    for dpath,label in [(FRAMES,'ASCII'),(FRAMES_PULSE,'BREATHE')]:
        for idx in [0,30,60,90,119]:
            img=Image.open(dpath/f'f_{idx:04d}.png').resize((320,180), Image.Resampling.LANCZOS)
            thumbs.append((label,idx,img))
    sheet=Image.new('RGB',(320*5, 180*2+54),(6,10,18)); sd=ImageDraw.Draw(sheet)
    for n,(label,idx,img) in enumerate(thumbs):
        row=0 if n<5 else 1; col=n%5
        sheet.paste(img,(col*320,row*207))
        sd.text((col*320+8,row*207+184),f'{label} frame {idx}',font=small,fill=(210,235,240))
    sheet.save(OUT/'contact_sheet_ascii_video_clean.png')
    # Manifest
    items=[]
    for p in sorted(OUT.iterdir()):
        if p.is_file() and p.suffix.lower() in ['.mp4','.gif','.png','.jpg','.json','.py']:
            items.append({'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    (OUT/'manifest_rendered.json').write_text(json.dumps(items,indent=2))
    print(json.dumps(items,indent=2)[:4000])

if __name__=='__main__':
    main()
