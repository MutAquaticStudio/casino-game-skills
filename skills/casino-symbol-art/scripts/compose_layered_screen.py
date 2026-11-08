from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
from scipy import ndimage as ndi

def key_out(im, tol=90):
    a = np.asarray(im.convert('RGB')).astype(np.int32)
    R,G,B = a[...,0],a[...,1],a[...,2]
    mask = (R>175)&(B>175)&(G<115)&(np.abs(R-B)<60)   # strict magenta key only
    # grow by 1px to catch anti-aliased halo, but only into pinkish pixels
    halo = ndi.binary_dilation(mask,iterations=2) & (R>150)&(B>120)&(G<150)&(R-G>70)&(B-G>50)
    mask = mask | halo
    alpha = np.where(mask, 0, 255).astype(np.uint8)
    out = Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), 'RGBA')
    # de-fringe: erode alpha by 1px and blur slightly
    al = Image.fromarray(alpha).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out.putalpha(al); return out

def crop_alpha(im): 
    bb = im.getchannel('A').point(lambda v:255 if v>10 else 0).getbbox(); return im.crop(bb)

W,H = 1280,720
bg = Image.open('gen/backdrop.png').convert('RGB').resize((W,H), Image.LANCZOS)
canvas = bg.convert('RGBA')

# frame: key out, crop, fit
fr = crop_alpha(key_out(Image.open('gen/frame.png')))
# window opening = enclosed transparent region; frame width target
fw = 860; fh = int(fr.height*fw/fr.width)
fr = fr.resize((fw,fh), Image.LANCZOS)
fx, fy = (W-fw)//2+150, 26
# darken reel window with dark tile behind frame
al = np.asarray(fr.getchannel('A'))
filled = ndi.binary_fill_holes(al>10)
hole = filled & (al<=10)
lab,n = ndi.label(hole); 
if n:
    sizes = ndi.sum(hole,lab,range(1,n+1)); big = lab==(1+int(np.argmax(sizes)))
else: big = hole
board = Image.new('RGBA',fr.size,(0,0,0,0))
ys0,xs0 = np.where(big); x0,x1,y0,y1 = xs0.min(),xs0.max(),ys0.min(),ys0.max()
tex = Image.open('gen/board.png').convert('RGB').resize((x1-x0+1,y1-y0+1), Image.LANCZOS)
# lift the pattern slightly so engraving is visible but still low contrast
tex = Image.eval(tex, lambda v: min(255,int(v*1.35)+6))
tile = Image.new('RGBA',fr.size,(0,0,0,0)); tile.paste(tex.convert('RGBA'),(x0,y0))
tm = np.zeros((fr.height,fr.width),np.uint8); tm[big]=255
tile.putalpha(Image.fromarray(tm))
board = tile
# column dividers (thin gold line with dark shadow) + inner vignette
bd = ImageDraw.Draw(board,'RGBA')
colw=(x1-x0)/5
for k in range(1,5):
    x=int(x0+k*colw)
    bd.line((x-2,y0,x-2,y1),fill=(0,0,0,150),width=3)
    bd.line((x,y0,x,y1),fill=(214,170,80,190),width=2)
    bd.line((x+2,y0,x+2,y1),fill=(0,0,0,120),width=2)
vig = Image.new('L',fr.size,0); vd=ImageDraw.Draw(vig); vd.rectangle((x0,y0,x1,y1),fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(28))
shade = Image.new('RGBA',fr.size,(0,0,0,150)); 
inv = Image.eval(vig, lambda v:255-v); shade.putalpha(Image.fromarray((np.asarray(inv).astype(np.int32)*np.asarray(tm)//255).astype(np.uint8)))
board.alpha_composite(shade)
canvas.alpha_composite(board,(fx,fy))
ys,xs = np.where(big); bx0,bx1,by0,by1 = xs.min(),xs.max(),ys.min(),ys.max()

# symbols: split sheet on connected components
sh = key_out(Image.open('gen/symbols.png'))
a = np.asarray(sh.getchannel('A'))>10
lab,n = ndi.label(ndi.binary_closing(a,iterations=6))
objs = ndi.find_objects(lab)
cells=[]
for sl in objs:
    h = sl[0].stop-sl[0].start; w = sl[1].stop-sl[1].start
    if h>80 and w>80: cells.append((sl[0].start//200, sl[1].start, sl))
cells.sort(key=lambda c:(c[0],c[1]))
syms = [sh.crop((c[2][1].start,c[2][0].start,c[2][1].stop,c[2][0].stop)) for c in cells]
print('symbols found',len(syms))
cols,rows=5,4
gw=(bx1-bx0); gh=(by1-by0); cw=gw/cols; ch=gh/rows
import random; random.seed(7)
for r in range(rows):
    for c in range(cols):
        s = random.choice(syms); sz=int(min(cw,ch)*0.9)
        s2 = s.resize((sz,sz),Image.LANCZOS)
        canvas.alpha_composite(s2,(int(fx+bx0+c*cw+(cw-sz)/2),int(fy+by0+r*ch+(ch-sz)/2)))
canvas.alpha_composite(fr,(fx,fy))

# hero left, outside reels
hero = crop_alpha(key_out(Image.open('gen/hero.png')))
hh=600; hw=int(hero.width*hh/hero.height); hero=hero.resize((hw,hh),Image.LANCZOS)
sh2 = Image.new('RGBA',hero.size,(0,0,0,0)); 
canvas.alpha_composite(hero,(-40,H-hh-6))

# bottom bar (code-drawn)
d = ImageDraw.Draw(canvas,'RGBA')
bar_y=H-84
d.rounded_rectangle((250,bar_y,1010,H-18),12,fill=(10,14,20,235))
try: f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',16); fs=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
except: f=fs=ImageFont.load_default()
for x,l,v in [(280,'BALANCE','$1,000.00'),(560,'WIN','$0.00'),(760,'BET','$1.00')]:
    d.text((x,bar_y+14),l,fill=(150,160,170,255),font=fs); d.text((x,bar_y+34),v,fill=(255,255,255,255),font=f)
cx,cy=1100,H-52
d.ellipse((cx-40,cy-40,cx+40,cy+40),fill=(10,14,20,240),outline=(255,255,255,255),width=5)
d.arc((cx-20,cy-20,cx+20,cy+20),40,330,fill=(255,255,255,255),width=6)
canvas.convert('RGB').save('shots/mockup_vn_myth_v2.png')
