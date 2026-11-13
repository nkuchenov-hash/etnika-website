#!/usr/bin/env python3
"""Make eight B02 full-frame images without cutting the model.
Only background pixels on the extreme LEFT and RIGHT edges are continued.
The original photo is pasted untouched at full native resolution and centered.
"""
from pathlib import Path
from PIL import Image, ImageFilter
import math, hashlib
import re

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'site/assets/b02'
OUT=SRC/'framed'
OUT.mkdir(parents=True,exist_ok=True)
FILES=[
'b02-02-dark.webp',
'b02-06-red-blonde.webp',
'b02-03-cool.webp',
'b02-05-ivory.webp',
'b02-04-purple.webp',
'b02-07-bw.webp',
'b02-08-taupe.webp',
'b02-10-red-seated.webp',
]
# Desktop photo column observed ratios: 0.936-0.949. With 0.955, only
# a 0-2% outer BACKGROUND gutter could be cropped. Full subject remains.
TARGET_ASPECT=0.955
for name in FILES:
    img=Image.open(SRC/name).convert('RGB')
    w,h=img.size
    intended_w=max(w,math.ceil(h*TARGET_ASPECT))
    intended_h=max(h,math.ceil(intended_w/TARGET_ASPECT)) if w/h>TARGET_ASPECT else h
    left=(intended_w-w)//2
    top=(intended_h-h)//2
    # Flat studio backdrops and seamless studio floors: extend their exact
    # border color PER ROW instead of blurring, zooming or mirroring the model.
    out=Image.new('RGB',(intended_w,intended_h))
    if intended_w>w:
        left_col=img.crop((0,0,1,h)).resize((left,h),Image.Resampling.NEAREST) if left else None
        right_w=intended_w-left-w
        right_col=img.crop((w-1,0,w,h)).resize((right_w,h),Image.Resampling.NEAREST) if right_w else None
        # Only the ADDED backdrop strips are smoothed: suppress edge-column
        # compression noise that becomes horizontal streaks when stretched.
        # The real photograph and people remain pixel-perfect, untouched.
        if left_col:
            out.paste(left_col.filter(ImageFilter.GaussianBlur(radius=10)),(0,top))
        if right_col:
            out.paste(right_col.filter(ImageFilter.GaussianBlur(radius=10)),(left+w,top))
    if intended_h>h:
        # Rare landscape source: extend outer background vertically, no
        # crop. Subject at outer edge should be checked in the photo review.
        for y in range(top):
            out.paste(img.crop((0,0,w,1)).resize((intended_w,1)),(0,y))
        for y in range(top+h,intended_h):
            out.paste(img.crop((0,h-1,w,h)).resize((intended_w,1)),(0,y))
    out.paste(img,(left,top))
    dest=OUT/name
    out.save(dest,'WEBP',quality=95,method=6)
    # Verify middle contains precisely the original pixels BEFORE encoding.
    assert out.crop((left,top,left+w,top+h)).tobytes()==img.tobytes(),name
    print(f'FRAMED {name}: source={w}x{h} -> {intended_w}x{intended_h} '
          f'left/right={left}/{intended_w-w-left} top/bottom={top}/{intended_h-h-top} '
          f'output={dest.stat().st_size}B',flush=True)
