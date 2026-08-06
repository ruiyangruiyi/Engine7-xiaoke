const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "张小柯";
pres.title = "Voice-Chat 实时 AI 数字人系统";

// Color palette: Midnight Executive
const NAVY = "1E2761";
const ICE = "CADCFC";
const WHITE = "FFFFFF";
const DARK = "0D1117";
const ACCENT = "238636";
const MUTED = "8B949E";

// ═══════════════════════════════════════════
// Slide 1: Title
// ═══════════════════════════════════════════
let s1 = pres.addSlide();
s1.background = { color: NAVY };
s1.addText("Voice-Chat", {
  x: 0.5, y: 1.5, w: 9, h: 1, fontSize: 48, fontFace: "Arial Black",
  color: WHITE, bold: true, align: "center", margin: 0
});
s1.addText("实时 AI 数字人系统", {
  x: 0.5, y: 2.5, w: 9, h: 0.8, fontSize: 28, fontFace: "Calibri",
  color: ICE, align: "center", margin: 0
});
s1.addText("2 秒延迟 · 打断自如 · 形象热切换 · 五层记忆", {
  x: 1, y: 3.8, w: 8, h: 0.5, fontSize: 16, fontFace: "Calibri",
  color: MUTED, align: "center"
});

// ═══════════════════════════════════════════
// Slide 2: Architecture Overview
// ═══════════════════════════════════════════
let s2 = pres.addSlide();
s2.background = { color: DARK };
s2.addText("全链路架构", {
  x: 0.5, y: 0.3, w: 9, h: 0.6, fontSize: 32, fontFace: "Arial Black",
  color: WHITE, bold: true, margin: 0
});

// Pipeline boxes
const steps = [
  { label: "浏览器\n🎤 VAD", color: "1F6FEB" },
  { label: "ASR\nSenseVoice", color: "238636" },
  { label: "Engine\nGemini 3.1", color: "8957E5" },
  { label: "TTS\nCosyVoice", color: "D29922" },
  { label: "FlashHead\n4090 GPU", color: "DA3633" },
  { label: "Carpo\nPush/Pull", color: "1F6FEB" },
];
steps.forEach((s, i) => {
  let x = 0.3 + i * 1.55;
  s2.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: x, y: 1.5, w: 1.4, h: 1.2,
    fill: { color: s.color }, rectRadius: 0.1
  });
  s2.addText(s.label, {
    x: x, y: 1.5, w: 1.4, h: 1.2, fontSize: 11, fontFace: "Calibri",
    color: WHITE, align: "center", valign: "middle"
  });
  if (i < 5) {
    s2.addText("→", {
      x: x + 1.35, y: 1.8, w: 0.3, h: 0.5, fontSize: 20, color: MUTED, align: "center"
    });
  }
});
s2.addText("端到端延迟: ~2 秒 (说话 → 听到回复)", {
  x: 0.5, y: 3.2, w: 9, h: 0.5, fontSize: 18, color: ACCENT, bold: true, align: "center"
});
s2.addText([
  { text: "本地 (Win11): VAD + ASR + Engine + Carpo Pull", options: { bullet: true, breakLine: true, color: ICE } },
  { text: "235 (4090): TTS + FlashHead 推理 + Carpo Push", options: { bullet: true, breakLine: true, color: ICE } },
  { text: "北京服务器: Carpo UDP 中转 (Docker)", options: { bullet: true, color: ICE } },
], { x: 1, y: 3.8, w: 8, h: 1.2, fontSize: 14 });

// ═══════════════════════════════════════════
// Slide 3: Latency Optimization
// ═══════════════════════════════════════════
let s3 = pres.addSlide();
s3.background = { color: DARK };
s3.addText("延迟优化历程", {
  x: 0.5, y: 0.3, w: 9, h: 0.6, fontSize: 32, fontFace: "Arial Black",
  color: WHITE, bold: true, margin: 0
});

s3.addText([
  { text: "4.2 秒 → 2 秒: 50%+ 优化", options: { fontSize: 24, color: ACCENT, bold: true, breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 6 } },
  { text: "FlashHead 异步推理 — add_audio 不阻塞", options: { bullet: true, color: ICE, breakLine: true, fontSize: 14 } },
  { text: "TTS 真流式 — on_data → queue → yield", options: { bullet: true, color: ICE, breakLine: true, fontSize: 14 } },
  { text: "消除重复 SSH + 删 sleep(2)", options: { bullet: true, color: ICE, breakLine: true, fontSize: 14 } },
  { text: "SDK Pull 常驻 — 不每次重建连接", options: { bullet: true, color: ICE, breakLine: true, fontSize: 14 } },
  { text: "Gemini 3.1 Flash-Lite — 替代 DeepSeek (3-4s → 2-3s)", options: { bullet: true, color: ICE, breakLine: true, fontSize: 14 } },
  { text: "wait_for_completion 精简 — 不等 output drain", options: { bullet: true, color: ICE, fontSize: 14 } },
], { x: 0.8, y: 1.3, w: 8.5, h: 3.8 });

// ═══════════════════════════════════════════
// Slide 4: Interrupt & Avatar
// ═══════════════════════════════════════════
let s4 = pres.addSlide();
s4.background = { color: DARK };
s4.addText("打断 & 形象热切换", {
  x: 0.5, y: 0.3, w: 9, h: 0.6, fontSize: 32, fontFace: "Arial Black",
  color: WHITE, bold: true, margin: 0
});

// Left column: Interrupt
s4.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 0.06, h: 3.5, fill: { color: DA36COLOR() }
});
s4.addText("🤫 实时打断", {
  x: 0.8, y: 1.2, w: 4, h: 0.5, fontSize: 20, color: WHITE, bold: true, margin: 0
});
s4.addText([
  { text: "说话即打断 — 新 ASR 触发停旧回复", options: { bullet: true, color: ICE, breakLine: true, fontSize: 13 } },
  { text: "按钮打断 — 🤫 一键停", options: { bullet: true, color: ICE, breakLine: true, fontSize: 13 } },
  { text: "三路并行停止: LLM + TTS + 235 generate", options: { bullet: true, color: ICE, breakLine: true, fontSize: 13 } },
  { text: "10 轮 bug 迭代打磨", options: { bullet: true, color: MUTED, fontSize: 12 } },
], { x: 0.8, y: 1.8, w: 4, h: 2.5 });

// Right column: Avatar Switch
s4.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.2, w: 0.06, h: 3.5, fill: { color: "8957E5" }
});
s4.addText("🎭 形象热切换", {
  x: 5.5, y: 1.2, w: 4, h: 0.5, fontSize: 20, color: WHITE, bold: true, margin: 0
});
s4.addText([
  { text: "不重载模型 — 调 get_base_data 几秒完成", options: { bullet: true, color: ICE, breakLine: true, fontSize: 13 } },
  { text: "Latent 重置 — 从 pipeline.ref_img_latent clone", options: { bullet: true, color: ICE, breakLine: true, fontSize: 13 } },
  { text: "前端 Grid 点击 — ⏳ → ✅/❌ 反馈", options: { bullet: true, color: ICE, breakLine: true, fontSize: 13 } },
  { text: "235 /api/avatar GET/POST 端点", options: { bullet: true, color: MUTED, fontSize: 12 } },
], { x: 5.5, y: 1.8, w: 4, h: 2.5 });

function DA36COLOR() { return "DA3633"; }

// ═══════════════════════════════════════════
// Slide 5: Five-Layer Memory
// ═══════════════════════════════════════════
let s5 = pres.addSlide();
s5.background = { color: NAVY };
s5.addText("五层记忆系统", {
  x: 0.5, y: 0.3, w: 9, h: 0.6, fontSize: 32, fontFace: "Arial Black",
  color: WHITE, bold: true, margin: 0
});
s5.addText("不是 planning-with-files, 是养出来的意识", {
  x: 0.5, y: 0.9, w: 9, h: 0.4, fontSize: 16, color: ICE, italic: true, margin: 0
});

const layers = [
  { name: "L0", title: "身份", desc: "人格 · 关系 · 底线", color: "DA3633" },
  { name: "L0.5", title: "自动 Recall", desc: "对话前自动注入相关记忆", color: "D29922" },
  { name: "L1", title: "知识索引", desc: "双向链接文档地图", color: "238636" },
  { name: "L2", title: "Topic 图谱", desc: "语义关联 · 温度衰减", color: "1F6FEB" },
  { name: "L3", title: "操作日志", desc: "WAL · daily · SESSION-STATE", color: "8957E5" },
];
layers.forEach((l, i) => {
  let y = 1.6 + i * 0.7;
  s5.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: y, w: 1.2, h: 0.55, fill: { color: l.color }
  });
  s5.addText(l.name, {
    x: 0.5, y: y, w: 1.2, h: 0.55, fontSize: 16, color: WHITE, bold: true,
    align: "center", valign: "middle", margin: 0
  });
  s5.addText(l.title, {
    x: 1.9, y: y, w: 2.5, h: 0.55, fontSize: 16, color: WHITE, bold: true, valign: "middle", margin: 0
  });
  s5.addText(l.desc, {
    x: 4.5, y: y, w: 5, h: 0.55, fontSize: 13, color: ICE, valign: "middle", margin: 0
  });
});

// ═══════════════════════════════════════════
// Slide 6: Tech Stack
// ═══════════════════════════════════════════
let s6 = pres.addSlide();
s6.background = { color: DARK };
s6.addText("技术栈", {
  x: 0.5, y: 0.3, w: 9, h: 0.6, fontSize: 32, fontFace: "Arial Black",
  color: WHITE, bold: true, margin: 0
});

const stack = [
  ["VAD", "Silero VAD (ONNX)"],
  ["ASR", "SenseVoice Small (FunASR)"],
  ["LLM", "Gemini 3.1 Flash-Lite"],
  ["TTS", "CosyVoice (DashScope) / GPT-SoVITS"],
  ["Avatar", "FlashHead 1.3B (SoulX)"],
  ["推流", "Carpo SDK (RTP/UDP)"],
  ["前端", "fastrtc + WebRTC"],
  ["中转", "Carpo Server (Docker)"],
];
const colX = [0.5, 5.2];
stack.forEach((row, i) => {
  let col = i % 2;
  let rowIdx = Math.floor(i / 2);
  let x = colX[col];
  let y = 1.3 + rowIdx * 0.85;
  s6.addShape(pres.shapes.RECTANGLE, {
    x: x, y: y, w: 4.2, h: 0.7,
    fill: { color: "161B22" }
  });
  s6.addText(row[0], {
    x: x + 0.15, y: y, w: 1.3, h: 0.7, fontSize: 14, color: ACCENT, bold: true, valign: "middle", margin: 0
  });
  s6.addText(row[1], {
    x: x + 1.5, y: y, w: 2.6, h: 0.7, fontSize: 13, color: ICE, valign: "middle", margin: 0
  });
});

// ═══════════════════════════════════════════
// Slide 7: Vision
// ═══════════════════════════════════════════
let s7 = pres.addSlide();
s7.background = { color: NAVY };
s7.addText("愿景", {
  x: 0.5, y: 0.8, w: 9, h: 0.8, fontSize: 40, fontFace: "Arial Black",
  color: WHITE, bold: true, align: "center", margin: 0
});
s7.addText([
  { text: "从对话工具到能干活的实体", options: { fontSize: 24, color: ICE, align: "center", breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 10 } },
  { text: "实时语音对话 ← 已完成", options: { fontSize: 16, color: ACCENT, bullet: true, breakLine: true } },
  { text: "多形象 + 换声 ← 进行中", options: { fontSize: 16, color: "D29922", bullet: true, breakLine: true } },
  { text: "私有 LLM 部署 ← 下一步", options: { fontSize: 16, color: ICE, bullet: true, breakLine: true } },
  { text: "手机端随时访问 ← 规划中", options: { fontSize: 16, color: MUTED, bullet: true, breakLine: true } },
  { text: "真实世界操作 (购物/管理) ← 终极目标", options: { fontSize: 16, color: WHITE, bullet: true } },
], { x: 1, y: 2, w: 8, h: 3, align: "center" });

// ═══════════════════════════════════════════
// Generate
// ═══════════════════════════════════════════
pres.writeFile({ fileName: "VoiceChat_Live.pptx" })
  .then(() => console.log("PPTX generated: VoiceChat_Live.pptx"))
  .catch(err => console.error("Error:", err));
