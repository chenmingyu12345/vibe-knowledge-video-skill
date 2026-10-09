# 程序动画与渲染

优先复用本地工程。HyperFrames + GSAP 可制作可重复渲染的 HTML 动画；FFmpeg/FFprobe 用于音轨与成片检查。使用项目本地依赖和 lockfile，具体命令以安装版本的 `--help` 为准，不固定用户目录或浏览器版本。

新工程可安装 `hyperframes gsap ffmpeg-static ffprobe-static`。检查真实可执行文件：npm 可能禁止包安装脚本，目录存在不代表 FFmpeg 已下载。设置 `HYPERFRAMES_BROWSER_PATH` 时查找实际可用 Chromium；调用子进程时将 FFmpeg/FFprobe 目录加入 PATH。

在工程目录调用 `node node_modules/hyperframes/bin/hyperframes.mjs --help`，确认 lint、snapshot、render 的参数后执行。渲染前 lint，渲染后对 MP4 解码检查。旧版本 HTML 放工程外存档，根目录只留一个根合成，避免 multiple_root_compositions。

根合成声明 `data-composition-id`、`data-start`、`data-duration`、`data-width`、`data-height`、`data-fps`。注册暂停 GSAP 时间线到 `window.__timelines[compositionId]`。镜头与音频的 clip 时间、轨道属性按当前版本核对。

常见问题：

- 初始状态立即用 `gsap.set`，不要只在时间线零秒设置，避免首帧闪现。
- 框架控制 clip 的显隐；动画内部元素的 opacity 和 transform。
- 位移用 x/y，避免持续动画 left/top 和 letterSpacing 引发布局抖动。
- SVG 组旋转明确设置 svgOrigin，错误中心会导致绕远处运动与裁切。
- 随机粒子固定种子；减少逐粒子 blur 和复杂叠加滤镜，黑帧时隔离滤镜。
- 字体必须实际加载，离线工程可用 @font-face 和可用本地字体，检查中文回退。
- 时间边界浮点提示结合实际帧核查，不忽略真实重叠。

音乐：用户指定本地参考原配乐时提取原音轨，写 `配乐来源.md` 记录源文件、区间、声道和使用位置。曲名没识别就写未识别。直接提取不去除人声；有真人说话声时不能直接当纯音乐使用。长度不足时处理循环并试听。默认不新增任何说话声，字幕讲解保留。

全片完成后重新检查所有镜头、总时长和末帧，不能用十秒样片检查代替全片验收。交付 MP4、源码、分镜和状态；skill 包不包含 node_modules、参考作者的整套视频或音乐素材。
