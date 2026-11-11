#!/usr/bin/env python3
"""Kindle 7 WP63GW: 600x800 grayscale dashboard, with three Charizard sprites."""
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"site"
ASSETS=ROOT/"assets"
MODE=os.environ.get("OUTPUT_MODE","1")
TZ=ZoneInfo("Asia/Shanghai")
CITY=os.environ.get("CITY","深圳")
FONT_PATHS=["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/System/Library/Fonts/PingFang.ttc"]
WEATHER={0:"晴",1:"晴",2:"多云",3:"阴",45:"雾",48:"雾",51:"小雨",53:"毛毛雨",
         55:"毛毛雨",61:"小雨",63:"中雨",65:"大雨",71:"小雪",73:"中雪",
         75:"大雪",80:"阵雨",81:"阵雨",82:"强阵雨",95:"雷雨",96:"雷雨",99:"雷雨"}
SAYINGS=["把时间留给重要的事。","慢一点，也是在向前走。","今天，做好眼前的一件事。",
         "读书，是给自己更多选择。","保持好奇，保持行动。",
         "热爱生活，也热爱平凡。","让日子成为值得回忆的故事。"]

def choose_form(hour):
    if 6<=hour<12:
        return "normal","早上 · 喷火龙"
    if 12<=hour<18:
        return "mega_x","中午 · 喷火龙 X"
    return "mega_y","晚上 · 喷火龙 Y"

def fetch_weather():
    query=urlencode({"latitude":os.environ.get("LATITUDE","22.5431"),
       "longitude":os.environ.get("LONGITUDE","114.0579"),
       "current":"temperature_2m,relative_humidity_2m,weather_code",
       "daily":"temperature_2m_max,temperature_2m_min",
       "forecast_days":1,"timezone":"Asia/Shanghai"})
    try:
        req=Request("https://api.open-meteo.com/v1/forecast?"+query,
            headers={"User-Agent":"KindleDashboard/1.0"})
        with urlopen(req,timeout=18) as response:
            payload=json.load(response)
        c=payload["current"]
        d=payload["daily"]
        return {"ok":True, "temp":str(round(c["temperature_2m"]))+"°",
            "desc":WEATHER.get(c["weather_code"],"天气变化"),
            "range":"%s° ~ %s°" % (round(d["temperature_2m_min"][0]),
                                   round(d["temperature_2m_max"][0])),
            "humidity":"湿度 %s%%" % c["relative_humidity_2m"]}
    except Exception as error:
        print("Weather unavailable:",error)
        return {"ok":False,"temp":"--°","desc":"天气暂不可用",
                "range":"--","humidity":"--"}

def font(size):
    choices=[os.environ.get("FONT_PATH","")]+FONT_PATHS
    path=next((p for p in choices if p and Path(p).is_file()),None)
    if not path:
        raise RuntimeError("Please install fonts-noto-cjk")
    return ImageFont.truetype(path,size)

def sprite_on(canvas,form):
    with Image.open(ASSETS/(form+".png")) as source:
        sp=source.convert("RGBA")
    bbox=sp.getbbox()
    if bbox is None:
        raise ValueError("Empty sprite: "+form)
    sp=sp.crop(bbox)
    maxw,maxh=205,191
    factor=min(maxw//sp.width,maxh//sp.height)
    if factor>=1:
        sp=sp.resize((sp.width*factor,sp.height*factor),Image.Resampling.NEAREST)
    else:
        sp.thumbnail((maxw,maxh),Image.Resampling.NEAREST)
    x=350+(maxw-sp.width)//2
    y=99+(maxh-sp.height)//2
    canvas.paste(sp.convert("RGB"),(x,y),sp.getchannel("A"))

def render():
    now=datetime.now(TZ)
    if "PREVIEW_HOUR" in os.environ:
        hour=int(os.environ["PREVIEW_HOUR"])
        if not 0<=hour<=23:
            raise ValueError("PREVIEW_HOUR must be 0..23")
        now=now.replace(hour=hour)
    form,title=choose_form(now.hour)
    weather=fetch_weather()
    canvas=Image.new("RGB",(600,800),"white")
    sprite_on(canvas,form)
    d=ImageDraw.Draw(canvas)
    def txt(x,y,s,size):
        d.text((x,y),str(s),font=font(size),fill="black")
    def line(y,size=2):
        d.line((42,y,558,y),fill="black",width=size)
    week=["星期一","星期二","星期三","星期四","星期五","星期六","星期日"]
    txt(42,30,"KINDLE · 每日信息",19)
    line(82,3)
    txt(40,101,now.strftime("%H:%M"),86)
    txt(42,231,now.strftime("%Y年%m月%d日"),27)
    txt(42,279,week[now.weekday()],26)
    txt(350,302,title,17)
    line(338)
    txt(42,357,CITY+" · 天气",23)
    txt(42,398,weather["temp"],68)
    txt(268,424,weather["desc"],25)
    txt(42,507,"今日气温 "+weather["range"],24)
    txt(42,549,weather["humidity"],21)
    line(609)
    txt(42,632,"今日一句",21)
    txt(42,681,SAYINGS[now.toordinal()%len(SAYINGS)],24)
    line(739)
    txt(42,755,"更新于 "+now.strftime("%H:%M")+" · Open-Meteo",14)
    gray=canvas.convert("L")
    if MODE=="1":
        img=gray.convert("1",dither=Image.Dither.NONE)
    elif MODE=="L":
        img=gray.point(lambda v:min(255,round(v/17)*17))
    else:
        raise ValueError("OUTPUT_MODE must be 1 or L")
    OUT.mkdir(parents=True,exist_ok=True)
    img.save(OUT/"screen.png",optimize=True)
    (OUT/"status.json").write_text(json.dumps({
       "generated_at":now.isoformat(),"width":600,"height":800,
       "city":CITY,"weather_ok":weather["ok"],"form":form,
       "title":title,"mode":MODE},ensure_ascii=False,indent=2),encoding="utf-8")
    print("Generated",form,str(OUT/"screen.png"))

if __name__=="__main__":
    render()
