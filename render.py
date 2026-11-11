#!/usr/bin/env python3
"""Kindle 7 (WP63GW): Shenzhen weather + month calendar + almanac + Charizard."""
import calendar
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'site'
SPRITES = ROOT / 'assets'
TZ = ZoneInfo('Asia/Shanghai')
CITY = os.environ.get('CITY', '深圳')
MODE = os.environ.get('OUTPUT_MODE', '1')
WEATHER_CODES = {0:'晴',1:'晴',2:'多云',3:'阴',45:'雾',48:'雾',51:'小雨',53:'小雨',55:'小雨',
                 61:'小雨',63:'中雨',65:'大雨',71:'小雪',73:'中雪',75:'大雪',
                 80:'阵雨',81:'阵雨',82:'强阵雨',95:'雷雨',96:'雷雨',99:'雷雨'}
QUOTES = ['把时间留给重要的事。','慢一点，也是在向前走。','今天，做好眼前的一件事。',
          '读书，是给自己更多选择。','保持好奇，保持行动。',
          '热爱生活，也热爱平凡。','让日子成为值得回忆的故事。']
FONT_PATHS = ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
              '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
              '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',
              '/System/Library/Fonts/PingFang.ttc']


def choose_form(hour):
    if 6 <= hour < 12:
        return 'normal', '早 · 喷火龙'
    if 12 <= hour < 18:
        return 'mega_x', '午 · Mega X'
    return 'mega_y', '晚 · Mega Y'


def get_weather():
    """Fetch weather once; return display-safe fallback on failure."""
    query = urlencode({
        'latitude': os.environ.get('LATITUDE', '22.5431'),
        'longitude': os.environ.get('LONGITUDE', '114.0579'),
        'timezone': 'Asia/Shanghai',
        'current': 'temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m',
        'daily': 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,uv_index_max,sunrise,sunset',
        'forecast_days': 3,
    })
    try:
        request = Request('https://api.open-meteo.com/v1/forecast?' + query,
                          headers={'User-Agent': 'KindleDashboard/2.0'})
        with urlopen(request, timeout=18) as response:
            payload = json.load(response)
        current, daily = payload['current'], payload['daily']
        forecast = []
        for index in range(min(3, len(daily['time']))):
            forecast.append({
                'day': daily['time'][index][5:].replace('-', '/'),
                'desc': WEATHER_CODES.get(daily['weather_code'][index], '多云'),
                'high': str(round(daily['temperature_2m_max'][index])),
                'low': str(round(daily['temperature_2m_min'][index])),
                'rain': str(round(daily['precipitation_probability_max'][index])),
            })
        def clock(value):
            return value[-5:] if value else '--:--'
        rain = round(daily['precipitation_probability_max'][0])
        uv = round(daily['uv_index_max'][0])
        if rain >= 55:
            tip = '出行建议：记得带伞'
        elif uv >= 6:
            tip = '出行建议：做好防晒'
        elif round(current['wind_speed_10m']) >= 30:
            tip = '出行建议：留意大风'
        else:
            tip = '出行建议：适合日常外出'
        return {
            'ok': True,
            'temp': str(round(current['temperature_2m'])) + '°',
            'desc': WEATHER_CODES.get(current['weather_code'], '多云'),
            'high': str(round(daily['temperature_2m_max'][0])),
            'low': str(round(daily['temperature_2m_min'][0])),
            'feels': str(round(current['apparent_temperature'])),
            'humidity': str(round(current['relative_humidity_2m'])),
            'wind': str(round(current['wind_speed_10m'])),
            'rain': str(rain), 'uv': str(uv),
            'sunrise': clock(daily['sunrise'][0]),
            'sunset': clock(daily['sunset'][0]),
            'tip': tip, 'forecast': forecast,
        }
    except Exception as exc:
        print('Weather unavailable:', exc)
        return {
            'ok': False, 'temp': '--°', 'desc': '天气暂不可用',
            'high': '--', 'low': '--', 'feels': '--', 'humidity': '--',
            'wind': '--', 'rain': '--', 'uv': '--', 'sunrise': '--:--',
            'sunset': '--:--', 'tip': '等待天气数据更新', 'forecast': [],
        }


def get_almanac(now):
    """Traditional almanac, for cultural reference only."""
    try:
        from lunar_python import Solar
        lunar = Solar.fromYmd(now.year, now.month, now.day).getLunar()
        month = lunar.getMonthInChinese()
        day = lunar.getDayInChinese()
        yi = [word for word in lunar.getDayYi() if word and word != '无']
        ji = [word for word in lunar.getDayJi() if word and word != '无']
        return {'ok': True, 'date': f'农历{month}月{day}',
                'year': lunar.getYearInGanZhi() + '年',
                'yi': '、'.join(yi[:4]) if yi else '无特别事项',
                'ji': '、'.join(ji[:4]) if ji else '无特别事项'}
    except Exception as exc:
        print('Almanac unavailable:', exc)
        return {'ok': False, 'date': '农历暂不可用', 'year': '',
                'yi': '暂不可用', 'ji': '暂不可用'}


def draw_board(now, weather, lunar, form, label):
    img = Image.new('RGB', (600, 800), 'white')
    d = ImageDraw.Draw(img)
    font_path = next((p for p in [os.environ.get('FONT_PATH', '')] + FONT_PATHS
                      if p and Path(p).is_file()), None)
    if not font_path:
        raise RuntimeError('Missing Chinese font. Install fonts-noto-cjk')
    fonts = {}
    def font(size):
        if size not in fonts:
            fonts[size] = ImageFont.truetype(font_path, size)
        return fonts[size]
    def text(x, y, value, size=18, max_width=None):
        s = str(value)
        ft = font(size)
        if max_width:
            while len(s) > 1 and d.textbbox((0, 0), s, font=ft)[2] > max_width:
                s = s[:-2].rstrip('、 ') + '…'
        d.text((x, y), s, fill='black', font=ft, anchor='lt')
    def center(cx, y, value, size=18):
        s = str(value)
        width = d.textbbox((0,0),s,font=font(size))[2]
        text(round(cx-width/2),y,s,size)
    def line(y, thick=2):
        d.line((28,y,572,y), fill='black', width=thick)

    weekdays = '一二三四五六日'
    text(29, 13, f'{now.month}月{now.day}日  星期{weekdays[now.weekday()]}', 28)
    text(457, 15, now.strftime('%H:%M'), 29)
    text(30, 59, lunar['date'] + '  ·  ' + lunar['year'], 18, max_width=420)
    text(515, 60, CITY, 19)
    line(92, 3)

    text(30, 105, '深圳实时天气', 19)
    text(30, 144, weather['temp'], 73)
    text(195, 151, weather['desc'], 26, 190)
    text(197, 198, f"{weather['low']}° ~ {weather['high']}°", 21)

    sprite_path = SPRITES / (form + '.png')
    if sprite_path.exists():
        with Image.open(sprite_path) as sprite_file:
            sprite = sprite_file.convert('RGBA')
        bounds = sprite.getbbox()
        if bounds:
            sprite = sprite.crop(bounds)
            factor = min(164 / sprite.width, 136 / sprite.height)
            size = (max(1, round(sprite.width * factor)), max(1, round(sprite.height * factor)))
            sprite = sprite.resize(size, Image.Resampling.NEAREST)
            img.paste(sprite.convert('RGB'),
                      (400 + (164 - size[0]) // 2, 112 + (136 - size[1]) // 2),
                      sprite.getchannel('A'))
    else:
        print('Sprite missing:', sprite_path)
    center(484, 254, label, 17)

    text(30, 274, f"体感 {weather['feels']}°", 18, 120)
    text(165, 274, f"湿度 {weather['humidity']}%", 18, 125)
    text(305, 274, f"风速 {weather['wind']}km/h", 18, 260)
    text(30, 301, f"降雨 {weather['rain']}%", 18, 145)
    text(171, 301, f"紫外线 {weather['uv']}", 18, 138)
    text(319, 301, f"日落 {weather['sunset']}", 18, 235)
    line(337)

    text(30, 346, '未来三天天气', 20)
    for i in range(3):
        x = 30 + i * 183
        f = weather['forecast'][i] if i < len(weather['forecast']) else None
        if f:
            text(x, 378, f['day'] + (' 今天' if i == 0 else ''), 18, 165)
            text(x, 405, f['desc'], 19)
            text(x, 429, f"{f['low']}~{f['high']}°  雨{f['rain']}%", 17, 171)
        else:
            text(x, 378, '暂无数据', 18)
    line(467)

    text(30, 475, f'{now.year}年{now.month}月 · 月历', 20)
    text(397, 478, '● 为今天', 15)
    columns = [67, 144, 221, 298, 375, 452, 529]
    for idx, name in enumerate('一二三四五六日'):
        center(columns[idx], 510, name, 17)
    weeks = calendar.monthcalendar(now.year, now.month)
    for row in range(6):
        days = weeks[row] if row < len(weeks) else [0] * 7
        yy = 540 + row * 21
        for c, day in enumerate(days):
            if not day:
                continue
            if day == now.day:
                d.rectangle((columns[c]-15,yy-1,columns[c]+15,yy+21), fill='black')
                s = str(day)
                width = d.textbbox((0,0),s,font=font(17))[2]
                d.text((columns[c]-width/2,yy+1),s,fill='white',font=font(17),anchor='lt')
            else:
                center(columns[c], yy, str(day), 17)
    line(671)

    text(30, 679, '今日黄历 · 民俗参考', 18)
    text(30, 705, '宜', 20)
    text(72, 706, lunar['yi'], 17, 496)
    text(30, 730, '忌', 20)
    text(72, 730, lunar['ji'], 17, 496)
    text(30, 753, '每日一句 · ' + QUOTES[now.toordinal() % len(QUOTES)], 17, 535)
    text(30, 779, '更新 '+now.strftime('%H:%M')+'  ·  天气 Open-Meteo  ·  黄历仅供参考', 12, 535)
    return img


def render():
    now = datetime.now(TZ)
    if 'PREVIEW_HOUR' in os.environ:
        hour = int(os.environ['PREVIEW_HOUR'])
        if not 0 <= hour <= 23:
            raise ValueError('PREVIEW_HOUR must be from 0 to 23')
        now = now.replace(hour=hour)
    weather = get_weather()
    lunar = get_almanac(now)
    form, label = choose_form(now.hour)
    img = draw_board(now, weather, lunar, form, label)
    gray = img.convert('L')
    if MODE == '1':
        output = gray.convert('1', dither=Image.Dither.NONE)
    elif MODE == 'L':
        output = gray.point(lambda v: min(255, round(v / 17) * 17))
    else:
        raise ValueError('OUTPUT_MODE must be 1 or L')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    output.save(OUTPUT / 'screen.png', optimize=True)
    (OUTPUT / 'status.json').write_text(json.dumps({
        'generated_at': now.isoformat(), 'width': 600, 'height': 800,
        'city': CITY, 'weather_ok': weather['ok'],
        'almanac_ok': lunar['ok'], 'lunar_date': lunar['date'],
        'yi': lunar['yi'], 'ji': lunar['ji'],
        'form': form, 'title': label, 'mode': MODE,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Generated', OUTPUT / 'screen.png', 'sprite:', form)


if __name__ == '__main__':
    render()
