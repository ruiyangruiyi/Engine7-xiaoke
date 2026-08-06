const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "小柯";
pres.title = "Engine7 安装备忘录";

// 配色 - Ocean Gradient
const C = {
  navy: "1E2761",
  deepBlue: "065A82",
  teal: "1C7293",
  midnight: "21295C",
  ice: "CADCFC",
  white: "FFFFFF",
  light: "F0F4F8",
  gray: "64748B",
  accent: "00A896",
  coral: "F96167",
  gold: "F9E795",
};

// === Slide 1: 封面 ===
let s1 = pres.addSlide();
s1.background = { color: C.navy };
s1.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 5.2, w: 10, h: 0.425, fill: { color: C.accent }
});
s1.addText("Engine 7", {
  x: 0.8, y: 1.5, w: 8, h: 1, fontSize: 52, fontFace: "Arial Black", color: C.white, bold: true
});
s1.addText("安装与使用备忘录", {
  x: 0.8, y: 2.5, w: 8, h: 0.8, fontSize: 28, fontFace: "Calibri", color: C.ice
});
s1.addText("你的私人 AI 助手使用指南", {
  x: 0.8, y: 3.5, w: 8, h: 0.5, fontSize: 16, fontFace: "Calibri", color: C.gray
});

// === Slide 2: 日常使用 ===
let s2 = pres.addSlide();
s2.background = { color: C.white };
s2.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 1, fill: { color: C.navy }
});
s2.addText("🚀 日常使用", {
  x: 0.5, y: 0.2, w: 9, h: 0.6, fontSize: 28, fontFace: "Arial Black", color: C.white
});

s2.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.3, w: 9, h: 1.2, fill: { color: C.light },
  shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.1 }
});
s2.addText([
  { text: "启动助手", options: { bold: true, fontSize: 18, color: C.deepBlue, breakLine: true } },
  { text: "Win+R → 输入 cmd → 点确定\n在黑窗口输入：engine7 start", options: { fontSize: 14, color: C.gray } }
], { x: 0.8, y: 1.5, w: 8.4, h: 0.8 });

s2.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 2.7, w: 4.2, h: 1.2, fill: { color: C.light },
  shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.1 }
});
s2.addText([
  { text: "停止助手", options: { bold: true, fontSize: 16, color: C.coral, breakLine: true } },
  { text: "在黑窗口按 Ctrl+C", options: { fontSize: 13, color: C.gray } }
], { x: 0.7, y: 2.85, w: 3.8, h: 0.8 });

s2.addShape(pres.shapes.RECTANGLE, {
  x: 5.3, y: 2.7, w: 4.2, h: 1.2, fill: { color: C.light },
  shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.1 }
});
s2.addText([
  { text: "开机自启（可选）", options: { bold: true, fontSize: 16, color: C.accent, breakLine: true } },
  { text: "输入：engine7 service install", options: { fontSize: 13, color: C.gray } }
], { x: 5.5, y: 2.85, w: 3.8, h: 0.8 });

s2.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 4.1, w: 9, h: 0.8, fill: { color: C.gold, transparency: 30 }
});
s2.addText("⚠️ 黑窗口不能关！关了助手就停了。关了重新开：Win+R → cmd → engine7 start", {
  x: 0.7, y: 4.2, w: 8.6, h: 0.6, fontSize: 13, color: C.midnight, bold: true
});

// === Slide 3: 飞书聊天 ===
let s3 = pres.addSlide();
s3.background = { color: C.white };
s3.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 1, fill: { color: C.teal }
});
s3.addText("💬 飞书聊天", {
  x: 0.5, y: 0.2, w: 9, h: 0.6, fontSize: 28, fontFace: "Arial Black", color: C.white
});

s3.addText('在飞书搜索框搜"开发者小助手"或"Amy"，找到机器人直接聊天。', {
  x: 0.5, y: 1.2, w: 9, h: 0.6, fontSize: 16, color: C.midnight, bold: true
});

const features = [
  { icon: "📊", title: "做文档", desc: 'Word / PPT / PDF\n直接说"帮我做个PPT"' },
  { icon: "📅", title: "日程管理", desc: '加日程、查安排\n"明天有什么安排？"' },
  { icon: "🔔", title: "提醒事项", desc: '定时提醒\n"提醒我明天10点打电话"' },
  { icon: "🌐", title: "联网搜索", desc: "需要申请 Tavily Key\ntavily.com 免费注册" },
];

features.forEach((f, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  const x = 0.5 + col * 4.7;
  const y = 2 + row * 1.6;
  s3.addShape(pres.shapes.RECTANGLE, {
    x: x, y: y, w: 4.3, h: 1.3, fill: { color: C.light },
    shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.1 }
  });
  s3.addText(f.icon, { x: x + 0.2, y: y + 0.25, w: 0.6, h: 0.6, fontSize: 24 });
  s3.addText([
    { text: f.title, options: { bold: true, fontSize: 15, color: C.deepBlue, breakLine: true } },
    { text: f.desc, options: { fontSize: 12, color: C.gray } }
  ], { x: x + 0.9, y: y + 0.2, w: 3.2, h: 1 });
});

// === Slide 4: 个性化设置 ===
let s4 = pres.addSlide();
s4.background = { color: C.white };
s4.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 1, fill: { color: C.midnight }
});
s4.addText("✨ 个性化设置", {
  x: 0.5, y: 0.2, w: 9, h: 0.6, fontSize: 28, fontFace: "Arial Black", color: C.white
});

s4.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.3, w: 9, h: 1.5, fill: { color: C.light },
  shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.1 }
});
s4.addText([
  { text: "📝 改助手性格（SOUL.md）", options: { bold: true, fontSize: 18, color: C.deepBlue, breakLine: true } },
  { text: "Win+R → cmd → 输入：notepad C:\\Users\\EDY\\.engine7\\workspace\\SOUL.md", options: { fontSize: 13, color: C.gray, breakLine: true } },
  { text: "改完保存（Ctrl+S），重启 engine7 start 生效", options: { fontSize: 13, color: C.gray } }
], { x: 0.8, y: 1.5, w: 8.4, h: 1.1 });

s4.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 3, w: 9, h: 1.5, fill: { color: C.light },
  shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.1 }
});
s4.addText([
  { text: "⚙️ 改配置（main7.json）", options: { bold: true, fontSize: 18, color: C.deepBlue, breakLine: true } },
  { text: "Win+R → cmd → 输入：notepad C:\\Users\\EDY\\.engine7\\configs\\main7.json", options: { fontSize: 13, color: C.gray, breakLine: true } },
  { text: "改完保存，重启 engine7 start 生效", options: { fontSize: 13, color: C.gray } }
], { x: 0.8, y: 3.2, w: 8.4, h: 1.1 });

s4.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 4.5, w: 9, h: 0.6, fill: { color: C.coral, transparency: 20 }
});
s4.addText("💡 改配置文件后都要重启 engine7 才生效（Ctrl+C → engine7 start）", {
  x: 0.7, y: 4.55, w: 8.6, h: 0.5, fontSize: 13, color: C.white, bold: true
});

// === Slide 5: 飞书后台 ===
let s5 = pres.addSlide();
s5.background = { color: C.white };
s5.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 1, fill: { color: C.deepBlue }
});
s5.addText("🔧 飞书后台操作", {
  x: 0.5, y: 0.2, w: 9, h: 0.6, fontSize: 28, fontFace: "Arial Black", color: C.white
});

s5.addText('浏览器打开 open.feishu.cn → 开发者后台 → 点"Amy"应用', {
  x: 0.5, y: 1.2, w: 9, h: 0.5, fontSize: 15, color: C.midnight, bold: true
});

const adminItems = [
  "基础信息 → 改头像、名字",
  "权限管理 → 开关权限（改完要发布新版本）",
  "事件与回调 → 消息接收设置（长连接模式）",
  "版本管理与发布 → 改了设置必须创建新版本发布才生效",
];

adminItems.forEach((item, i) => {
  s5.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.9 + i * 0.7, w: 9, h: 0.55, fill: { color: C.light }
  });
  s5.addShape(pres.shapes.OVAL, {
    x: 0.7, y: 2.05 + i * 0.7, w: 0.25, h: 0.25, fill: { color: C.accent }
  });
  s5.addText(String(i + 1), {
    x: 0.7, y: 2.03 + i * 0.7, w: 0.25, h: 0.25, fontSize: 12, color: C.white, align: "center", valign: "middle", bold: true
  });
  s5.addText(item, {
    x: 1.1, y: 1.95 + i * 0.7, w: 8.2, h: 0.5, fontSize: 14, color: C.midnight, valign: "middle"
  });
});

// === Slide 6: 注意事项 ===
let s6 = pres.addSlide();
s6.background = { color: C.navy };
s6.addText("📝 注意事项", {
  x: 0.5, y: 0.5, w: 9, h: 0.8, fontSize: 32, fontFace: "Arial Black", color: C.white
});

const notes = [
  { icon: "🟢", text: "engine7 必须开着（黑窗口不能关），飞书才能收到消息" },
  { icon: "🟢", text: "飞书没回复？先看黑窗口是否还开着" },
  { icon: "🟢", text: "黑窗口关了重新开：Win+R → cmd → engine7 start" },
  { icon: "🟢", text: "改了配置文件后要重启 engine7（Ctrl+C → engine7 start）" },
  { icon: "🟢", text: "飞书后台改了设置要创建新版本发布才生效" },
];

notes.forEach((n, i) => {
  s6.addText([
    { text: n.icon + "  ", options: { fontSize: 18 } },
    { text: n.text, options: { fontSize: 15, color: C.ice } }
  ], {
    x: 0.8, y: 1.6 + i * 0.65, w: 8.5, h: 0.55, valign: "middle"
  });
});

s6.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 5, w: 9, h: 0.4, fill: { color: C.accent }
});
s6.addText("有问题随时在群里 @张小柯！🌹", {
  x: 0.5, y: 5, w: 9, h: 0.4, fontSize: 16, color: C.white, align: "center", valign: "middle", bold: true
});

pres.writeFile({ fileName: "/Users/chongzhang/xiaoke/workspace/Engine7-安装备忘录.pptx" })
  .then(() => console.log("PPT 生成成功！"))
  .catch(err => console.error("PPT 生成失败:", err));
