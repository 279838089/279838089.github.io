# Kindle 7 WP63GW · 深圳墨水屏看板

600×800、1-bit 黑白 PNG，适配 2014 年入门 Kindle 7 (WP63GW / KT2)。

- 展示页面：https://279838089.github.io/
- 图片直链：https://279838089.github.io/screen.png
- 构建状态：https://279838089.github.io/status.json

## Kindle 黑白报纸式新版布局（屏幕从上到下）

1. 顶部报头：特大日期、农历与干支年；右上角展示喷火龙像素精灵；不放可能误导的静态时钟
2. 中间高对比度纯黑天气卡片：白色超大温度、体感温度、湿度、风速、降雨概率、UV、日落时间和出行建议
3. 三张并列的未来三天天气卡片：天气状况、温度范围和降雨概率
4. 双栏月历与黄历：左侧完整七列月历（今天反白），右侧今日宜、忌
5. 底部独立每日语录区：黑色竖线点缀，字体放大
6. 喷火龙早中晚切换：06:00–11:59 普通喷火龙；12:00–17:59 Mega X；18:00–05:59 Mega Y。底部不显示生成时间、数据源或提示文字；更新时间仍可在 `status.json` 查看。

所有元素按 600×800 固定画布设计，纯黑白线条和大字号，针对 Kindle 7 的 1-bit 显示优化。黄历由 lunar_python 离线计算，仅作民俗参考。

天气由 Open-Meteo API 获取；如果天气 API 临时不可用，看板仍可生成，天气位置显示“暂无数据”。农历/黄历由 lunar_python 本地生成，不调用黄历收费 API。

喷火龙像素素材来自 Pokémon Showdown 原有素材，并非 AI 生成；Pokémon 相关形象版权归原权利人，仅用于个人非商业展示。

**素材预存机制：** 首次成功运行的 GitHub Actions 会下载普通喷火龙、Mega X、Mega Y 的像素 PNG，并通过 `github-actions[bot]` 提交到 `assets/`。之后每次构建首先检查仓库中的 PNG，存在则完全跳过素材联网下载；缺失时才重试。`fetch_sprites.py` 只用于初次填充和后续手动补全。首次自动提交是否成功，可在仓库 `assets/normal.png`、`assets/mega_x.png`、`assets/mega_y.png` 中确认。

## 发布

GitHub Pages 设置为 **GitHub Actions**。工作流在 master 推送时触发，且每 3 小时计划更新一次（非每 6 小时，实际调度可能延迟；北京时间约 00:17、03:17、06:17、09:17、12:17、15:17、18:17、21:17）。输出 site/screen.png 与 site/status.json；图片直链不变。

## Kindle 下载

原有 Kindle 脚本继续从 https://279838089.github.io/screen.png 下载，然后交给现有显示脚本。老设备无法握手现代 TLS 时，需要兼容代理或 TLS 客户端。

## 本地运行

安装 Noto CJK 字体后执行：
    pip install -r requirements.txt
    python fetch_sprites.py
    PREVIEW_HOUR=13 python render.py

PREVIEW_HOUR 可为 8、13、20，分别测试三种喷火龙。OUTPUT_MODE=L 输出 8-bit 灰阶 PNG；默认 OUTPUT_MODE=1 为老 Kindle 更兼容的 1-bit PNG。

旧版 Jekyll 博客仍保存在 backup-jekyll-20261111 分支。
