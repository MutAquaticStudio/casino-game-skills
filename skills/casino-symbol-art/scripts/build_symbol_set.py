import sys; sys.argv=['x']
exec(open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'compose_layered_screen.py')).read().split("W,H = 1280,720")[0])   # reuse key_out, crop_alpha, imports
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

def components(im, closing=0, minsize=60):
    a = np.asarray(im.getchannel('A'))>10
    if closing: a = ndi.binary_closing(a,iterations=closing)
    lab,n = ndi.label(a)
    out=[]
    for sl in ndi.find_objects(lab):
        h=sl[0].stop-sl[0].start; w=sl[1].stop-sl[1].start
        if h>=minsize and w>=minsize*0.4: out.append(sl)
    out.sort(key=lambda s:s[1].start); return out

# --- ranks: split by column projection valleys
r = key_out(Image.open('gen/ranks.png')); r = crop_alpha(r)
al = np.asarray(r.getchannel('A'))>10
col = al.sum(0); H_=r.height
print('ranks size',r.size)
# find 5 groups by splitting at columns with smallest opaque pixel counts near expected cut points
W_=r.width; exp=[W_*i/5 for i in range(1,5)]; cuts=[]
for e in exp:
    lo,hi=int(e-W_*0.05),int(e+W_*0.05); cuts.append(lo+int(np.argmin(col[lo:hi])))
edges=[0]+cuts+[W_]; ranks=[crop_alpha(r.crop((edges[i],0,edges[i+1],H_))) for i in range(5)]
sp = key_out(Image.open('gen/specials.png'))
spc = [crop_alpha(sp.crop((s[1].start,s[0].start,s[1].stop,s[0].stop))) for s in components(sp,closing=4,minsize=120)]
print('specials',len(spc))
sy = key_out(Image.open('gen/symbols.png')); 
a=np.asarray(sy.getchannel('A'))>10; lab,n=ndi.label(ndi.binary_closing(a,iterations=6))
prem=[]
cells=[]
for sl in ndi.find_objects(lab):
    h=sl[0].stop-sl[0].start; w=sl[1].stop-sl[1].start
    if h>80 and w>80: cells.append((sl[0].start//200,sl[1].start,sl))
cells.sort(key=lambda c:(c[0],c[1]))
prem=[crop_alpha(sy.crop((c[2][1].start,c[2][0].start,c[2][1].stop,c[2][0].stop))) for c in cells]

def font(sz,b=True): return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if b else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',sz)
# wild badge number + scatter tag by code (text must be code-drawn)
if len(spc)==3:
    base=spc[0]; pad=int(base.width*0.08)
    wild=Image.new('RGBA',(base.width+pad,base.height+pad),(0,0,0,0)); wild.alpha_composite(base,(0,0)); d=ImageDraw.Draw(wild); bw=int(base.width*0.19)
    cx,cy=int(base.width*0.88),int(base.height*0.86)
    d.ellipse((cx-bw,cy-bw,cx+bw,cy+bw),fill=(20,40,70,255),outline=(240,200,90,255),width=6)
    f=font(int(bw*1.1)); t='x5'; tw=d.textlength(t,font=f); d.text((cx-tw/2,cy-bw*0.62),t,fill=(255,255,255,255),font=f)
    spc[0]=wild
    sc=spc[1].copy(); d=ImageDraw.Draw(sc); f=font(int(sc.height*0.12)); t='SCATTER'; tw=d.textlength(t,font=f)
    bx=(sc.width-tw)/2; by=sc.height*0.84
    d.rounded_rectangle((bx-14,by-6,bx+tw+14,by+f.size+8),10,fill=(20,26,40,235),outline=(240,200,90,255),width=3)
    d.text((bx,by),t,fill=(255,230,150,255),font=f); spc[1]=sc

cell=190
def fit(im,box):
    s=min(box/im.width,box/im.height); return im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))),Image.LANCZOS)
rows=[('RANKS',ranks),('PREMIUM',prem[:8]),('SPECIAL',spc)]
Wd=cell*8+40; Hd=(cell+34)*3+30
sheet=Image.new('RGBA',(Wd,Hd),(16,20,30,255)); d=ImageDraw.Draw(sheet)
y=14
for name,items in rows:
    d.text((12,y),name,fill=(200,170,100,255),font=font(16)); y+=26
    for i,it in enumerate(items):
        f=fit(it,cell-14); sheet.alpha_composite(f,(14+i*cell+(cell-14-f.width)//2, y+(cell-14-f.height)//2))
    y+=cell+8
sheet.convert('RGB').save('shots/symbol_set.png')
# readability test: all at 96 px, colour and greyscale
allsyms=ranks+prem[:8]+spc; n=len(allsyms)
t=Image.new('RGBA',(n*104+8,2*104+8),(16,20,30,255))
for i,it in enumerate(allsyms):
    f=fit(it,96); t.alpha_composite(f,(8+i*104+(96-f.width)//2,8+(96-f.height)//2))
g=ImageOps.grayscale(t.convert('RGB').crop((0,0,t.width,112))).convert('RGBA')
t.alpha_composite(g,(0,104)) if False else None
t2=t.convert('RGB'); gray=ImageOps.grayscale(t2.crop((0,0,t.width,112))).convert('RGB'); t2.paste(gray,(0,104)); t2.save('shots/symbol_readability.png')
import pickle; 
for i,it in enumerate(allsyms): it.save(f'gen/sym_{i:02d}.png')
print('ok',n)
