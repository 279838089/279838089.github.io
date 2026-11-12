# 慢调 FM · Radio PWA

复古风格、面向 iPhone 的在线 FM 收音机。部署在 https://279838089.github.io/radio/ 。

## 使用方法
1. iPhone 用 Safari 打开网页，点击共享 → 添加到主屏幕。第一次播放需手动点击播放（iOS 音频播放策略）。
2. 拖动 87.5–108.0 MHz 刻度或从精选频道选台。调频只是网络音频模拟，不接收手机硬件 FM 信号。
3. 「探索全球」通过 Radio Browser 搜索网络电台，右上角爱心收藏。
4. 右上角「+」可以添加 HTTPS 直播源，或者粘贴标准 M3U 文本批量导入。
5. 状态、收藏、音量、自定义电台保存在当前设备浏览器 localStorage，不同步到云端。

## 技术
- 零框架 HTML / CSS / JavaScript，刻度更新通过 requestAnimationFrame + transform 实现。
- iOS Safari 原生播放 HLS；其他兼容浏览器仅在需要时加载 hls.js。
- 电台来源：公开索引、Radio Browser API、用户自定义网络直播流；个别源可能失效、限制地区或不支持跨域。
- 单个 Audio 元素复用，备用源自动切换；播放状态由媒体事件驱动。
- 支持 Media Session 控件（是否出现在锁屏取决于 iOS 版本），睡眠定时、PWA 离线外壳。
- iOS Safari 的网页音量由系统控制，页面音量滑块不一定能改变设备播放音量。
- PWA 离线缓存仅包含界面，收听直播仍需网络。

## 部署
这个项目放在 `site/radio/`。仓库现有 Kindle dashboard Actions 使用 `site/` 作为 Pages artifact 根目录，因此不需改动发布流程，更不会覆盖 Kindle 看板。

项目仅供个人学习使用；电台音频内容的权利属于各电台和版权方。公开分发前，请确认直播流的使用授权。
