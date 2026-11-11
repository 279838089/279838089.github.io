# Kindle 7 WP63GW 墨水屏自动看板

2014 Kindle 7（WP63GW / KT2）：600×800，黑白 PNG。原 Jekyll 博客已备份在 **backup-jekyll-20261111** 分支。

- 展示页：https://279838089.github.io/
- 图片：https://279838089.github.io/screen.png
- JSON 状态：https://279838089.github.io/status.json

## 喷火龙自动切换（北京时间）
| 时段 | 形态 |
|---|---|
| 06:00—11:59 | 普通喷火龙 |
| 12:00—17:59 | Mega 喷火龙 X |
| 18:00—05:59 | Mega 喷火龙 Y |

素材由 GitHub Actions 从 Pokémon Showdown 的 gen5 精灵图库获取，不调用 AI 图片生成。相关像素素材和宝可梦形象归原权利人，仅用于个人非商业展示。

## 部署
仓库 Settings → Pages → Build and deployment → Source，选择 **GitHub Actions**。然后在 Actions 中运行 **Kindle dashboard** → **Run workflow**。每 3 小时生成一次图片，并覆盖早 6 点、午 12 点、晚 18 点的形态切换（计划 :17 UTC+8，实际可能延迟）。如果 Pages 没有设置为 GitHub Actions，部署任务可能失败。

## Kindle
下载 `kindle/update.sh` 放到 Kindle 中，修改其中 DEST 为原有显示脚本所读图片路径；运行 `sh update.sh`。脚本仅负责下载替换，屏幕刷新继续使用现有程序。古老的 Kindle 系统 wget/curl 可能不支持现代 TLS，需要先在设备上验证。

## 本地
安装 fonts-noto-cjk，然后执行 `pip install -r requirements.txt && python fetch_sprites.py && python render.py`。设置 PREVIEW_HOUR=8/13/20 可以测试三种模式。OUTPUT_MODE=L 可以输出 16 级灰度（默认 1-bit）。
