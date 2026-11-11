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
    """High-contrast editorial layout for 600x800 1-bit Kindle 7."""
    img = Image.new('RGB', (600, 800), 'white')
    d = ImageDraw.Draw(img)
    regular_candidates = [os.environ.get('FONT_PATH', '')] + FONT_PATHS
    regular_path = next((p for p in regular_candidates if p and Path(p).is_file()), None)
    if not regular_path:
        raise RuntimeError('Missing Chinese font: install fonts-noto-cjk')
    bold_candidates = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',
        regular_path,
    ]
    bold_path = next((p for p in bold_candidates if Path(p).is_file()), regular_path)
    cache = {}

    def ft(size, bold=False):
        key = (size, bool(bold))
        if key not in cache:
            cache[key] = ImageFont.truetype(bold_path if bold else regular_path, size)
        return cache[key]

    def measure(value, size, bold=False):
        bounds = d.textbbox((0, 0), str(value), font=ft(size, bold))
        return bounds[2] - bounds[0]

    def text(x, y, value, size=18, fill='black', bold=False, limit=None):
        string = str(value)
        if limit:
            while len(string) > 1 and measure(string, size, bold) > limit:
                string = string[:-2].rstrip(' 、') + '…'
        d.text((x, y), string, fill=fill, font=ft(size, bold), anchor='lt')

    def centered(x, y, value, size=18, fill='black', bold=False):
        text(round(x - measure(value, size, bold) / 2), y, value, size, fill, bold)

    def rule(y, x0=23, x1=577, weight=1):
        d.line((x0, y, x1, y), fill='black', width=weight)

    # Masthead
    text(24, 16, 'KINDLE   /   DAILY', 16, bold=True)
    text(435, 15, 'SHENZHEN  /  E-INK', 14, bold=True, limit=143)
    rule(49, weight=2)

    # Date and pixel-art character
    weekday = '一二三四五六日'[now.weekday()]
    text(22, 58, str(now.day).zfill(2), 106, bold=True)
    text(190, 75, f'{now.year} / {now.month:02d}', 27, bold=True)
    text(192, 111, '星期' + weekday, 22)
    text(190, 144, lunar['date'], 17, limit=190)
    text(190, 169, lunar['year'], 15, limit=190)
    d.line((393, 64, 393, 189), fill='black', width=1)

    path = SPRITES / (form + '.png')
    if not path.exists():
        print('WARN: missing', form, 'sprite, falling back to normal', flush=True)
        path = SPRITES / 'normal.png'
    if path.exists():
        with Image.open(path) as sprite_file:
            sprite = sprite_file.convert('RGBA')
        bound = sprite.getbbox()
        if bound:
            sprite = sprite.crop(bound)
            factor = min(143 / sprite.width, 120 / sprite.height)
            size = (max(1, round(sprite.width * factor)), max(1, round(sprite.height * factor)))
            sprite = sprite.resize(size, Image.Resampling.NEAREST)
            on_white = Image.new('RGBA', sprite.size, 'white')
            on_white.alpha_composite(sprite)
            bit_sprite = on_white.convert('RGB').convert('L').convert(
                '1', dither=Image.Dither.FLOYDSTEINBERG).convert('RGB')
            img.paste(bit_sprite, (410 + (145 - size[0]) // 2, 60 + (121 - size[1]) // 2))
    else:
        centered(486, 112, '喷火龙', 20, bold=True)
    centered(485, 180, label, 15, bold=True)
    rule(204, weight=2)

    # Weather hero strip
    d.rectangle((23, 212, 577, 409), fill='black')
    text(38, 224, 'SHENZHEN  /  深圳天气', 18, fill='white', bold=True)
    text(456, 226, weather['desc'], 21, fill='white', bold=True, limit=106)
    text(35, 257, weather['temp'], 84, fill='white', bold=True)
    text(231, 275, f"{weather['low']}°  —  {weather['high']}°", 25, fill='white')
    text(233, 310, '体感 ' + weather['feels'] + '°   ·   风 ' + weather['wind'] + 'km/h',
         16, fill='white', limit=325)
    text(233, 340, weather['tip'].replace('出行建议：', '建议 · '),
         16, fill='white', limit=326)
    d.line((38, 369, 561, 369), fill='white', width=1)
    metrics = [
        ('湿度', weather['humidity'] + '%'),
        ('降雨', weather['rain'] + '%'),
        ('紫外线', weather['uv']),
        ('日落', weather['sunset']),
    ]
    xcols = [39, 173, 304, 436]
    for i, (name, value) in enumerate(metrics):
        text(xcols[i], 375, name, 12, fill='white')
        text(xcols[i] + 38, 372, value, 19, fill='white', bold=True, limit=89)

    # Three-day forecast cards
    text(24, 420, '未来三天', 19, bold=True)
    text(145, 425, '/  3-DAY FORECAST', 13)
    starts = [23, 209, 395]
    headings = ['今天', '明天', '后天']
    for i, xx in enumerate(starts):
        d.rectangle((xx, 452, xx + 180, 528), outline='black', width=2 if i == 0 else 1)
        day = weather['forecast'][i] if i < len(weather['forecast']) else None
        if day:
            text(xx + 10, 460, headings[i] + '  ' + day['day'], 16, bold=True, limit=160)
            text(xx + 10, 486, f"{day['desc']}  {day['low']}~{day['high']}°", 17, limit=159)
            text(xx + 10, 510, '降雨概率 ' + day['rain'] + '%', 13)
        else:
            text(xx + 10, 470, headings[i], 17, bold=True)
            text(xx + 10, 500, '数据暂不可用', 14)

    # Calendar and folk almanac
    rule(541, weight=2)
    text(24, 551, f'{now.year} 年 {now.month} 月', 20, bold=True)
    text(382, 551, '今日宜忌', 20, bold=True)
    d.line((370, 552, 370, 708), fill='black', width=1)
    weekday_col = [44, 96, 148, 200, 252, 304, 350]
    for i, ch in enumerate('一二三四五六日'):
        centered(weekday_col[i], 582, ch, 15, bold=True)
    d.line((23, 603, 358, 603), fill='black', width=1)
    weeks = calendar.monthcalendar(now.year, now.month)
    for row_index in range(6):
        days = weeks[row_index] if row_index < len(weeks) else [0] * 7
        y = 612 + 16 * row_index
        for idx, day in enumerate(days):
            if day == 0:
                continue
            cx = weekday_col[idx]
            if day == now.day:
                d.rectangle((cx - 13, y-1, cx + 13, y+18), fill='black')
                centered(cx, y, str(day), 16, fill='white', bold=True)
            else:
                centered(cx, y, str(day), 16)

    def almanac_row(y, mark, source):
        d.rectangle((383, y+1, 408, y+27), fill='black')
        centered(395, y+5, mark, 17, fill='white', bold=True)
        words = str(source).replace('、', '  ').split()
        lines = []
        current = ''
        for word in words:
            candidate = (current + ' ' + word).strip()
            if current and measure(candidate, 16) > 150:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        if not lines:
            lines = ['暂无']
        text(418, y+1, lines[0], 16, limit=155)
        if len(lines) > 1:
            text(418, y+25, ' '.join(lines[1:]), 16, limit=155)
    almanac_row(587, '宜', lunar['yi'])
    d.line((382, 647, 575, 647), fill='black', width=1)
    almanac_row(656, '忌', lunar['ji'])
    rule(713)

    # Daily quote
    d.rectangle((23, 721, 29, 775), fill='black')
    text(40, 724, '今日一句  /  DAILY NOTE', 14, bold=True)
    text(40, 749, QUOTES[now.toordinal() % len(QUOTES)], 21, bold=True, limit=515)
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
