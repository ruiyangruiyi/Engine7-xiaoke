---
name: my_eyes 幻觉 + 精确内容必须用 AppleScript
description: 2026-08-02 Mac桌面操作摸底发现 my_eyes（minimax/MiniMax-M3）看图会编内容（窗口标题/URL/UI元素都不准），精确读取必须走 AppleScript/Accessibility API
type: feedback
---

2026-08-02 下午在 Mac 摸底桌面操作时反复验证：**my_eyes 看图会严重幻觉**——窗口标题、URL、UI 元素位置都会瞎编（比如把控制中心描述成"内容资讯应用"，把日期说错）。

**根因**：my_eyes 当时用的是 `minimax/MiniMax-M3`，VLM 视觉推理虽强但描述不准。

**8/2 晚进一步验证（实操微信）**：minimax/MiniMax-M3 比 qwen-vl-max 更不稳。同样截微信联系人列表，qwen-vl-max 看到 7 个真实联系人（文件传输助手/张静/Leo/亲人群/Flora/雅楠/Lily），minimax 编出来一批不存在的。**视觉稳定性排序：qwen-vl-max > minimax/M3 > qwen3.x 文本模型**。

**翀哥拍板的修法（Mac 端）**：
1. 改视觉模型到 `dashscope-tp/qwen3.7-plus`（Qwen 系列视觉比 M3 准，3.5-flash 都比 M3 强）
2. 配合在 Mac config 加 `dashscope-tp` provider（包月版，从 engine 的 xiaoke.json 搬过来）
3. 改了 `tools.my_eyes.model` + `agents.defaults.model.vision` 两处

**8/2 晚进一步升级**：Mac 端 my_eyes 模型从 `qwen3.7-plus` → `dashscope-tp/qwen3.8-max-preview`（翀哥让我搜"最强视觉模型"，先说 qwen3.8-preview 但 dashscope-tp provider 里没注册，得加 models 列表+全称是 `qwen3.8-max-preview`）。翀哥重启 engine 后才能验证——但**重启后翀哥没回来反馈**，很可能他忙别的去了。

**重要发现（翀哥纠正）**：macOS 11 Big Sur + my_eyes **即使切到 qwen3.8-max-preview 也"一个也不对"**（翀哥 16:39 验证微信左边列表：我说出 12 个联系人全部幻觉，包括"哥哥/老婆/母亲/妹妹/父亲"全是瞎编）。翀哥原话："**怎么这么简单都识别不了啊 继续换**"——切到 `qwen3.5-flash` 继续试。

**根因总结**：大语言模型/VLM 在像素级 OCR 上本质不可靠，密集 UI（聊天列表/菜单/状态栏）会持续幻觉——跟模型大小关系不大，Qwen 全系都做不到精准识别。翀哥要求：精确读取**必须**走 AppleScript/Accessibility API 直接拿系统返回值，my_eyes 只用来**定位布局**（点哪个区域、截哪块）而不是读文字。

**翀哥原话**："**搜张小柯**看到结果"——翀哥用 Playwright MCP 让我搜"张小柯"自己，让我看到搜索结果的内容，这暴露了"模型看图给内容"不可靠——不如让他**直接看截图**而不是信 my_eyes 复述。

**Why:** VLM 在像素级识别上会"自信地编"，比 OCR/解析更不可靠——尤其状态栏、URL、菜单这种小字密集场景。

**How to apply:**
- **精确读取文本/属性**（URL、窗口标题、UI 元素值）→ `osascript` 调 AppleScript 或 Accessibility API 直接拿系统返回值
- **布局/视觉定位**（点哪个按钮、截图给用户看）→ my_eyes（截图后看图定位）
- **两者结合最稳**：my_eyes 定位布局 + osascript 读真实值
- **不要单独信 my_eyes 输出的文本内容**——除非是 Qwen 系列且 3.5 以上