#!/usr/bin/env python3
"""One-time inventory of photograph URLs on the original owner studio website."""
import re,urllib.request,urllib.parse,html,collections
URL="https://etnika-studio.ru/"
req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 (compatible; EtnikaPhotoAudit/1.0)"})
with urllib.request.urlopen(req,timeout=35) as r:
    source=r.read().decode("utf-8","replace")
print("ORIGINAL_PAGE_BYTES",len(source),flush=True)
print("TILDA_OCCURRENCES",source.lower().count("tildacdn"),flush=True)
print("SAMPLE_TILDA_PATHS",re.findall(r".{0,70}tildacdn.{0,110}",source,re.I)[:5],flush=True)
# HTML contains both raw 20px thumbnails and full-size, lazy-loaded Tilda media.
pattern=re.compile(r'(?:https?:)?//(?:[a-z0-9-]+\.)*tildacdn\.com/[^\s"<>\\)]+',re.I)
found=[]
for match in pattern.finditer(source):
    value=html.unescape(match.group(0).replace("\\/","/")).rstrip(".,")
    if value.startswith("//"):value="https:"+value
    if not value.startswith("http"):continue
    url=urllib.parse.urlsplit(value)
    path=url.path
    ext=path.rsplit(".",1)[-1].lower()
    if ext not in ("jpg","jpeg","png","webp","avif"):continue
    if "/tild" not in path:continue
    # All Tilda preview variants of one same source photo map to one ID.
    t=re.search(r'/tild([a-z0-9-]+)/',path,re.I)
    fid=t.group(1) if t else path
    normalized=path.split("/")
    filename=normalized[-1]
    full=f"https://static.tildacdn.com/tild{fid}/{filename}"
    found.append((fid,filename,full,value,match.start()))
print("PHOTO_URL_REFERENCES",len(found),flush=True)
group=collections.defaultdict(list)
for fid,name,full,raw,pos in found:group[(fid,name)].append(pos)
print("UNIQUE_TILDA_IMAGE_FILES",len(group),flush=True)
for i,((fid,name),positions) in enumerate(group.items()):
    print(f"PHOTO {i:03d} references={len(positions):02d} file={name} URL=https://static.tildacdn.com/tild{fid}/{name}",flush=True)
