#!/usr/bin/env python3
from pathlib import Path
import cv2, math, subprocess, shutil, hashlib, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

OUT=Path('/home/kuiqs/fal-outputs/futuristic-japanese-city-ascii-video-2026-05-04')
SRC=sorted(OUT.glob('*text-to-video-1.mp4'))[-1]
FR=OUT/'frames_ascii_bare'
FRB=OUT/'frames_ascii_bare_breathe'
for d in (FR,FRB):
    if d.exists(): shutil.rmtree(d)
    d.mkdir(parents=True, exist_ok=True)
W,H=1280,720; FPS=24; N=120; CELL_W=8; CELL_H=10; COLS=W//CELL_W; ROWS=H//CELL_H
font_path='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
font=ImageFont.truetype(font_path,10)
small=ImageFont.truetype(font_path,8)
RAMP=np.array(list('   ..,:;irsxvczXYUJCLQ0OZMW&8%B@$'))
EDGE_RAMP=np.array(list('   .:-=+*#%@'))
cap=cv2.VideoCapture(str(SRC)); total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1)

def read_frame(i):
    idx=min(total-1,int(i/(N-1)*max(1,total-1)))
    cap.set(cv2.CAP_PROP_POS_FRAMES,idx); ok,fr=cap.read()
    if not ok:
        cap.set(cv2.CAP_PROP_POS_FRAMES,max(0,total-2)); ok,fr=cap.read()
    return cv2.resize(cv2.cvtColor(fr,cv2.COLOR_BGR2RGB),(W,H),interpolation=cv2.INTER_AREA)

def draw_natural_crane(draw,x,y,s=1.0,a=185):
    # Sparse natural flying-crane line, not text-glyph bird; kept small and airy.
    col=(238,244,236,a); shadow=(0,5,10,90)
    pts=[(x-int(42*s),y+int(2*s)),(x-int(16*s),y-int(8*s)),(x,y-int(2*s)),(x+int(16*s),y-int(8*s)),(x+int(42*s),y+int(1*s))]
    for fill,w in [(shadow,max(3,int(3*s))),(col,max(1,int(1.5*s)) )]:
        draw.line(pts,fill=fill,width=w,joint='curve')
        draw.line([(x+int(9*s),y-int(2*s)),(x+int(30*s),y-int(11*s))],fill=fill,width=max(1,w-1))
        draw.line([(x-int(3*s),y+int(2*s)),(x-int(8*s),y+int(15*s))],fill=fill,width=max(1,w-1))

def render(fr,i,breathe=False):
    u=i/(N-1); phase=2*math.pi*u; breath=.5+.5*math.sin(phase)
    gray=cv2.cvtColor(fr,cv2.COLOR_RGB2GRAY)
    blur=cv2.GaussianBlur(gray,(3,3),0)
    edges=cv2.Canny(blur,55,140).astype(np.float32)/255
    # Building mask: de-emphasize sky and water; keep vertical architectural edge density.
    sg=cv2.resize(gray,(COLS,ROWS),interpolation=cv2.INTER_AREA).astype(np.float32)/255
    se=cv2.resize(edges,(COLS,ROWS),interpolation=cv2.INTER_AREA)
    srgb=cv2.resize(fr,(COLS,ROWS),interpolation=cv2.INTER_AREA).astype(np.float32)
    yy,xx=np.mgrid[0:ROWS,0:COLS]
    vertical_zone=1/(1+np.exp(-(yy-ROWS*.24)/4)) * (1-0.18*np.exp(-((xx-COLS/2)/(COLS*.17))**2))
    density=((1-sg)*.50+se*1.05)*vertical_zone
    # Keep skyline/buildings, less canal/foreground clutter.
    density*= (0.72 + 0.38*np.exp(-((yy-ROWS*.55)/(ROWS*.38))**2))
    if breathe:
        # Very slow, low-amplitude breathing: brightness/density only; no big overlays.
        density += 0.045*breath*np.exp(-((yy-ROWS*.48)/(ROWS*.35))**2)
        density += 0.025*np.sin(xx*.13 + phase)*np.sin(yy*.09-phase*.7)
    density=np.clip(density,0,1)

    base=Image.fromarray(fr).filter(ImageFilter.GaussianBlur(.35))
    base=ImageEnhance.Color(base).enhance(.55); base=ImageEnhance.Contrast(base).enhance(.78)
    canvas=Image.blend(Image.new('RGB',(W,H),(3,7,13)),base,.27 if not breathe else .30).convert('RGBA')
    d=ImageDraw.Draw(canvas,'RGBA')
    d.rectangle([0,0,W,H],fill=(2,6,12,54))
    # Bare city ASCII: only cells, no torii, no Fuji line, no kana, no data-rain columns, no foreground red lines.
    for r in range(ROWS):
        # avoid sky snow; leave cranes readable
        thresh=0.24 if r<ROWS*.30 else 0.18
        for c in range(COLS):
            val=float(density[r,c])
            if val<thresh: continue
            rgb=srgb[r,c]
            edge=float(se[r,c])
            ramp=EDGE_RAMP if edge>.13 else RAMP
            ch=ramp[min(len(ramp)-1,max(0,int(val*(len(ramp)-1))))]
            x=c*CELL_W; y=r*CELL_H-1
            if edge>.13:
                color=(215,240,246,int(140+105*min(1,val)))
            elif rgb[2]>rgb[0]*1.04:
                color=(76,185,222,int(75+100*val))
            else:
                color=(150,190,188,int(65+85*val))
            if breathe:
                color=(min(255,int(color[0]*(.92+.12*breath))),min(255,int(color[1]*(.94+.12*breath))),min(255,int(color[2]*(.96+.10*breath))),color[3])
            d.text((x,y),ch,font=font,fill=color)
    # Minimal non-text cranes only; fewer/lower contrast than previous stylized overlay.
    cranes=[(.10,.14,.55),(.31,.105,.42),(.57,.13,.48),(.80,.16,.62)]
    for j,(px,py,s) in enumerate(cranes):
        x=int(((px+.13*u+.006*math.sin(phase+j))%1.08-.04)*W)
        y=int((py+.018*math.sin(phase*1.1+j))*H)
        draw_natural_crane(d,x,y,s*(1+.03*breath if breathe else 1),a=int(120+42*(breath if breathe else .5)))
    # Bare micro border only.
    d.rectangle([20,20,W-20,H-20],outline=(120,190,210,38),width=1)
    return canvas.convert('RGB')

def encode(frames,mp4,gif):
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate',str(FPS),'-i',str(frames/'f_%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium',str(mp4)],check=True)
    vf='fps=12,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3'
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate',str(FPS),'-i',str(frames/'f_%04d.png'),'-vf',vf,'-loop','0',str(gif)],check=True)

for i in range(N):
    fr=read_frame(i)
    render(fr,i,False).save(FR/f'f_{i:04d}.png')
    render(fr,i,True).save(FRB/f'f_{i:04d}.png')
    if i%20==0: print('frame',i,'/',N,flush=True)
encode(FR,OUT/'future_edo_cranes_ascii_bare.mp4',OUT/'future_edo_cranes_ascii_bare.gif')
encode(FRB,OUT/'future_edo_cranes_ascii_bare_breathe.mp4',OUT/'future_edo_cranes_ascii_bare_breathe.gif')
Image.open(FR/'f_0048.png').save(OUT/'poster_bare_ascii_2s.png')
Image.open(FRB/'f_0048.png').save(OUT/'poster_bare_breathe_2s.png')
thumbs=[]
for frames,label in [(FR,'BARE'),(FRB,'BARE BREATHE')]:
    for idx in [0,30,60,90,119]:
        thumbs.append((label,idx,Image.open(frames/f'f_{idx:04d}.png').resize((320,180),Image.Resampling.LANCZOS)))
sheet=Image.new('RGB',(1600,414),(3,7,13)); sd=ImageDraw.Draw(sheet)
for n,(lab,idx,img) in enumerate(thumbs):
    row=0 if n<5 else 1; col=n%5
    sheet.paste(img,(col*320,row*207)); sd.text((col*320+8,row*207+184),f'{lab} frame {idx}',font=small,fill=(190,220,225))
sheet.save(OUT/'contact_sheet_ascii_video_bare.png')
items=[]
for p in sorted(out for out in OUT.iterdir() if out.is_file()):
    if p.suffix.lower() in ['.mp4','.gif','.png','.py','.md','.json','.jpg']:
        items.append({'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'manifest.json').write_text(json.dumps(items,indent=2))
print(json.dumps([x for x in items if 'bare' in x['name']],indent=2))
