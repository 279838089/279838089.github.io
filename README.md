# Kindle 7 WP63GW · 深圳墨水屏看板

600×800、1-bit 黑白 PNG，适配 2014 年入门 Kindle 7 (WP63GW / KT2)。

- 展示页面：https://279838089.github.io/
- 图片直链：https://279838089.github.io/screen.png
- 构建状态：https://279838089.github.io/status.json

## 新版版面（屏幕从上到下）

1. 北京时间、星期、农历、干支年
2. 深圳当前天气、大号温度、体感温度、湿度、风速、降雨概率、UV、日落时间
3. 早中晚喷火龙：06:00–11:59 普通喷火龙；12:00–17:59 Mega X；18:00–05:59 Mega Y
4. 今天、明天、后天三天天气：天气现象、温度范围、降雨概率
5. 当月 7 列完整月历，黑底白字标注今天
6. 传统黄历宜忌（由 lunar_python 离线计算；民俗参考，非科学建议）
7. 每日语录、构建更新时间

天气由 Open-Meteo API 获取；如果天气 API 临时不可用，看板仍可生成，天气位置显示“暂无数据”。农历/黄历由 lunar_python 本地生成，不调用黄历收费 API。

喷火龙像素素材来自 Pokémon Showdown 原有素材，并非 AI 生成；Pokémon 相关形象版权归原权利人，仅用于个人非商业展示。

## 发布

GitHub Pages 设置为 **GitHub Actions**。工作流在 master 推送时触发，且大约每 3 小时定时更新一次（实际调度可能延迟）。输出 site/screen.png 与 site/status.json；图片直链不变。

## Kindle 下载

原有 Kindle 脚本继续从 https://279838089.github.io/screen.png 下载，然后交给现有显示脚本。老设备无法握手现代 TLS 时，需要兼容代理或 TLS 客户端。

## 本地运行

安装 Noto CJK 字体后执行：
    pip install -r requirements.txt
    python fetch_sprites.py
    PREVIEW_HOUR=13 python render.py

PREVIEW_HOUR 可为 8、13、20，分别测试三种喷火龙。OUTPUT_MODE=L 输出 8-bit 灰阶 PNG；默认 OUTPUT_MODE=1 为老 Kindle 更兼容的 1-bit PNG。

旧版 Jekyll 博客仍保存在 backup-jekyll-20261111 分支。
