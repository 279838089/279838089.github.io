#!/usr/bin/env python3
"""Network probe for curated public radio sources (CI only)."""
import concurrent.futures, json, re, sys, urllib.request, urllib.error, urllib.parse
from pathlib import Path

GROUPS=json.loads(Path(__file__).with_name("probe_candidates.json").read_text())
UA="Mozilla/5.0 (compatible; MandiaoFMSourceProbe/1.0)"
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*","Icy-MetaData":"0"})
    with urllib.request.urlopen(req,timeout=8) as response:
        data=response.read(4096)
        return int(response.status), response.headers.get("content-type",""),data,response.geturl()
def check(task):
    name,url=task
    try:
        status,ctype,data,final_url=fetch(url)
        is_playlist=b"#EXTM3U" in data[:300] or ("mpegurl" in ctype.lower())
        if is_playlist:
            text=data.decode("utf-8","replace")
            candidates=[x.strip() for x in text.splitlines() if x.strip() and not x.startswith("#")]
            if not candidates:
                return {"station":name,"url":url,"ok":False,"detail":"Playlist empty"}
            next_url=urllib.parse.urljoin(final_url,candidates[0])
            status2,ctype2,data2,_=fetch(next_url)
            # Master HLS playlists have another nested playlist
            if b"#EXTM3U" in data2[:300]:
                next_url=urllib.parse.urljoin(next_url, next((x.strip() for x in data2.decode("utf-8","replace").splitlines() if x.strip() and not x.startswith("#")),""))
                status2,ctype2,data2,_=fetch(next_url)
            audio=bool(data2) and (data2[:1]==b"G" or data2[:2] in (b"\xff\xfb",b"\xff\xf3",b"\xff\xf1") or data2[:3]==b"ID3" or b"ftyp" in data2[:30] or (status2==200 and "video/mp2t" in ctype2.lower()))
            return {"station":name,"url":url,"ok":audio,"status":status2,"content_type":ctype2,"detail":str(data2[:12])}
        audio=bool(data) and (data[:3]==b"ID3" or data[:2] in (b"\xff\xfb",b"\xff\xf3",b"\xff\xf1",b"\xff\xf9") or data[:1]==b"\xff" or b"ftyp" in data[:30] or ctype.lower().startswith(("audio/","application/ogg")))
        return {"station":name,"url":url,"ok":audio,"status":status,"content_type":ctype,"detail":str(data[:12])}
    except Exception as e:
        return {"station":name,"url":url,"ok":False,"detail":str(e)[:200]}
tasks=[(name,url) for name,urls in GROUPS for url in urls]
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
    rows=list(pool.map(check,tasks))
rows.sort(key=lambda x:(not x["ok"],x["station"]))
print("RADIO_PROBE_START")
print(json.dumps({"checked":len(rows),"good":sum(r["ok"] for r in rows),"stations":len(GROUPS),"results":rows},ensure_ascii=False))
print("RADIO_PROBE_END")
