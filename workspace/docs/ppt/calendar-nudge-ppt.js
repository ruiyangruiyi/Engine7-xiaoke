const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "张小柯";
pres.title = "AI 的自律系统：Calendar + Nudge";

// === Color Palette: Midnight Executive ===
const NAVY = "1E2761";
const ICE = "CADCFC";
const WHITE = "FFFFFF";
const DARK = "0F172A";
const LIGHT = "F8FAFC";
const ACCENT = "F59E0B"; // amber
const GREEN = "10B981";
const RED = "EF4444";
const GRAY = "64748B";
const TEAL = "028090";
const PURPLE = "8B5CF6";

const FONT_H = "Arial Black";
const FONT_B = "Arial";

const mkShadow = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.15 });

function darkSlide() {
  const s = pres.addSlide();
  s.background = { color: NAVY };
  return s;
}
function lightSlide() {
  const s = pres.addSlide();
  s.background = { color: LIGHT };
  return s;
}

// ═══════════════════════════════════════
// Slide 1: Title
// ═══════════════════════════════════════
{
  const s = darkSlide();
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: ACCENT } });
  s.addText("AI 的自律系统", {
    x: 0.8, y: 1.0, w: 8.4, h: 1.2,
    fontSize: 44, fontFace: FONT_H, color: WHITE, bold: true, margin: 0
  });
  s.addText("Calendar + Nudge", {
    x: 0.8, y: 2.1, w: 8.4, h: 0.8,
    fontSize: 28, fontFace: FONT_H, color: ACCENT, margin: 0
  });
  s.addText("让 AI 从「被动回答」变成「主动管理自己的任务」", {
    x: 0.8, y: 3.3, w: 8.4, h: 0.6,
    fontSize: 16, fontFace: FONT_B, color: ICE, margin: 0
  });
  s.addText("—— 小柯 & 翀哥", {
    x: 0.8, y: 4.6, w: 8.4, h: 0.5,
    fontSize: 14, fontFace: FONT_B, color: GRAY, margin: 0
  });
}

// ═══════════════════════════════════════
// Slide 2: The Problem
// ═══════════════════════════════════════
{
  const s = lightSlide();
  s.addText("AI 最大的问题", {
    x: 0.8, y: 0.4, w: 8.4, h: 0.8,
    fontSize: 36, fontFace: FONT_H, color: DARK, bold: true, margin: 0
  });
  s.addText("聊完就忘", {
    x: 0.8, y: 1.3, w: 8.4, h: 1,
    fontSize: 48, fontFace: FONT_H, color: RED, bold: true, margin: 0
  });
  const items = [
    { title: "说了不做", desc: "用户交代了任务，AI 答应了，然后……没有然后" },
    { title: "做了不记", desc: "干完活不标记，下次问「做完没」一脸懵" },
    { title: "记了乱放", desc: "任务散在聊天记录里，找个东西翻半天" },
    { title: "忘了没人追", desc: "任务过期了，没人催，就永远沉了" }
  ];
  items.forEach((item, i) => {
    const y = 2.6 + i * 0.7;
    s.addShape(pres.shapes.OVAL, { x: 0.8, y: y + 0.08, w: 0.35, h: 0.35, fill: { color: RED } });
    s.addText(`${i + 1}`, {
      x: 0.8, y: y + 0.08, w: 0.35, h: 0.35,
      fontSize: 14, fontFace: FONT_H, color: WHITE, bold: true,
      align: "center", valign: "middle", margin: 0
    });
    s.addText(item.title, {
      x: 1.3, y: y, w: 2.2, h: 0.5,
      fontSize: 16, fontFace: FONT_H, color: DARK, bold: true, margin: 0, valign: "middle"
    });
    s.addText(item.desc, {
      x: 3.5, y: y, w: 5.8, h: 0.5,
      fontSize: 14, fontFace: FONT_B, color: GRAY, margin: 0, valign: "middle"
    });
  });
}

// ═══════════════════════════════════════
// Slide 3: The Solution Overview
// ═══════════════════════════════════════
{
  const s = darkSlide();
  s.addText("解决方案", {
    x: 0.8, y: 0.4, w: 8.4, h: 0.8,
    fontSize: 36, fontFace: FONT_H, color: WHITE, bold: true, margin: 0
  });
  s.addText("三件套：Calendar + Nudge + 双向关联", {
    x: 0.8, y: 1.2, w: 8.4, h: 0.6,
    fontSize: 18, fontFace: FONT_B, color: ICE, margin: 0
  });
  const cards = [
    { title: "Calendar", sub: "外脑记忆", desc: "时间驱动\n不靠聊天记录", color: TEAL, x: 0.8 },
    { title: "Nudge", sub: "自律闹钟", desc: "自己催自己\n任务不沉底", color: ACCENT, x: 3.8 },
    { title: "双向关联", sub: "task ↔ 文档", desc: "不丢不重\n一搜就到", color: PURPLE, x: 6.8 }
  ];
  cards.forEach(c => {
    s.addShape(pres.shapes.RECTANGLE, { x: c.x, y: 2.2, w: 2.6, h: 2.8, fill: { color: WHITE }, shadow: mkShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: c.x, y: 2.2, w: 2.6, h: 0.08, fill: { color: c.color } });
    s.addText(c.title, { x: c.x + 0.2, y: 2.5, w: 2.2, h: 0.5, fontSize: 22, fontFace: FONT_H, color: c.color, bold: true, margin: 0 });
    s.addText(c.sub, { x: c.x + 0.2, y: 3.0, w: 2.2, h: 0.4, fontSize: 14, fontFace: FONT_B, color: GRAY, margin: 0 });
    s.addText(c.desc, { x: c.x + 0.2, y: 3.6, w: 2.2, h: 1.0, fontSize: 14, fontFace: FONT_B, color: DARK, margin: 0, lineSpacingMultiple: 1.3 });
  });
}

// ═══════════════════════════════════════
// Slide 4: Calendar — What
// ═══════════════════════════════════════
{
  const s = lightSlide();
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: TEAL } });
  s.addText("Calendar — AI 的外脑记忆", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.8,
    fontSize: 32, fontFace: FONT_H, color: DARK, bold: true, margin: 0
  });
  s.addText("不是聊天记录里翻，是「时间」驱动的独立记忆系统", {
    x: 0.8, y: 1.1, w: 8.4, h: 0.5,
    fontSize: 16, fontFace: FONT_B, color: TEAL, margin: 0
  });
  const types = [
    { title: "日程 (Event)", color: TEAL, items: ["孩子们的课表", "每周固定的活动", "一次性约会/安排", "到点自动提醒"] },
    { title: "任务 (Task)", color: PURPLE, items: ["工作派的活", "限时交付的跟进", "带 deadline 的目标", "到期自动催 + 拆 Phase"] }
  ];
  types.forEach((t, i) => {
    const x = 0.8 + i * 4.5;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.9, w: 4.0, h: 3.2, fill: { color: WHITE }, shadow: mkShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.9, w: 4.0, h: 0.08, fill: { color: t.color } });
    s.addText(t.title, { x: x + 0.2, y: 2.1, w: 3.6, h: 0.5, fontSize: 20, fontFace: FONT_H, color: t.color, bold: true, margin: 0 });
    t.items.forEach((item, j) => {
      s.addText([{ text: item, options: { bullet: true, breakLine: j < t.items.length - 1 } }], {
        x: x + 0.3, y: 2.7 + j * 0.5, w: 3.4, h: 0.45,
        fontSize: 14, fontFace: FONT_B, color: DARK, margin: 0
      });
    });
  });
}

// ═══════════════════════════════════════
// Slide 5: Calendar — Flow
// ═══════════════════════════════════════
{
  const s = darkSlide();
  s.addText("Calendar 怎么运转的", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.8,
    fontSize: 32, fontFace: FONT_H, color: WHITE, bold: true, margin: 0
  });
  const steps = [
    { num: "1", title: "用户说", desc: "\"明天下午3点\n跟进潘总报价\"", color: ICE },
    { num: "2", title: "AI 建任务", desc: "calendar add-task\n自动分配 #ID", color: TEAL },
    { num: "3", title: "到点提醒", desc: "reminder 自动触发\n注入 AI session", color: ACCENT },
    { num: "4", title: "AI 执行", desc: "拆 Phase → 干活\n→ done 标记完成", color: GREEN }
  ];
  steps.forEach((step, i) => {
    const x = 0.5 + i * 2.4;
    s.addShape(pres.shapes.OVAL, { x: x + 0.7, y: 1.5, w: 0.8, h: 0.8, fill: { color: step.color } });
    s.addText(step.num, {
      x: x + 0.7, y: 1.5, w: 0.8, h: 0.8,
      fontSize: 28, fontFace: FONT_H, color: NAVY, bold: true,
      align: "center", valign: "middle", margin: 0
    });
    s.addText(step.title, {
      x, y: 2.5, w: 2.2, h: 0.4,
      fontSize: 16, fontFace: FONT_H, color: WHITE, bold: true,
      align: "center", margin: 0
    });
    s.addText(step.desc, {
      x, y: 3.0, w: 2.2, h: 1.0,
      fontSize: 13, fontFace: FONT_B, color: ICE,
      align: "center", margin: 0, lineSpacingMultiple: 1.2
    });
    if (i < 3) {
      s.addShape(pres.shapes.RECTANGLE, { x: x + 1.9, y: 1.85, w: 0.4, h: 0.08, fill: { color: GRAY } });
    }
  });
  s.addText("整个过程不需要用户操心 — AI 自己记住、自己提醒、自己执行", {
    x: 0.8, y: 4.5, w: 8.4, h: 0.5,
    fontSize: 14, fontFace: FONT_B, color: ICE, italic: true,
    align: "center", margin: 0
  });
}

// ═══════════════════════════════════════
// Slide 6: Nudge — What
// ═══════════════════════════════════════
{
  const s = lightSlide();
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: ACCENT } });
  s.addText("Nudge — AI 的自律闹钟", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.8,
    fontSize: 32, fontFace: FONT_H, color: DARK, bold: true, margin: 0
  });
  s.addText("AI 会自己催自己干活", {
    x: 0.8, y: 1.1, w: 8.4, h: 0.5,
    fontSize: 16, fontFace: FONT_B, color: ACCENT, margin: 0
  });
  const features = [
    { title: "进度催促", desc: "标了进行中但长时间没推进\n→ 提醒继续" },
    { title: "到期提醒", desc: "calendar 有到期 task\n但没开始 → 提醒开工" },
    { title: "异常检测", desc: "待办没进 calendar\n→ 强制提示补录" },
    { title: "卡住升级", desc: "被催太多次\n→ 标记 stale，需要决策" },
    { title: "等待唤醒", desc: "AI 说在等 XX 条件\n→ 到时间自动检查" },
    { title: "冷却机制", desc: "催完有冷却期\n不会反复烦同一个任务" }
  ];
  features.forEach((f, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.8 + col * 3.0;
    const y = 1.8 + row * 1.7;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 2.7, h: 1.5, fill: { color: WHITE }, shadow: mkShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.08, h: 1.5, fill: { color: ACCENT } });
    s.addText(f.title, { x: x + 0.2, y: y + 0.1, w: 2.3, h: 0.4, fontSize: 14, fontFace: FONT_H, color: DARK, bold: true, margin: 0 });
    s.addText(f.desc, { x: x + 0.2, y: y + 0.5, w: 2.3, h: 0.9, fontSize: 12, fontFace: FONT_B, color: GRAY, margin: 0, lineSpacingMultiple: 1.2 });
  });
}

// ═══════════════════════════════════════
// Slide 7: Nudge — How
// ═══════════════════════════════════════
{
  const s = darkSlide();
  s.addText("Nudge 怎么催的", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.8,
    fontSize: 32, fontFace: FONT_H, color: WHITE, bold: true, margin: 0
  });
  const steps = [
    { num: "1", title: "定时巡检", desc: "每5分钟 tick\n检查任务状态" },
    { num: "2", title: "发现问题", desc: "任务 stale / 到期\n/ pending 未入 calendar" },
    { num: "3", title: "注入提醒", desc: "通知注入 session\nAI 被唤醒" },
    { num: "4", title: "AI 响应", desc: "标记状态 / 开工\n/ 或说明在等什么" }
  ];
  steps.forEach((step, i) => {
    const x = 0.5 + i * 2.4;
    s.addShape(pres.shapes.OVAL, { x: x + 0.7, y: 1.5, w: 0.8, h: 0.8, fill: { color: ACCENT } });
    s.addText(step.num, {
      x: x + 0.7, y: 1.5, w: 0.8, h: 0.8,
      fontSize: 28, fontFace: FONT_H, color: NAVY, bold: true,
      align: "center", valign: "middle", margin: 0
    });
    s.addText(step.title, { x, y: 2.5, w: 2.2, h: 0.4, fontSize: 16, fontFace: FONT_H, color: WHITE, bold: true, align: "center", margin: 0 });
    s.addText(step.desc, { x, y: 3.0, w: 2.2, h: 1.0, fontSize: 13, fontFace: FONT_B, color: ICE, align: "center", margin: 0, lineSpacingMultiple: 1.2 });
    if (i < 3) {
      s.addShape(pres.shapes.RECTANGLE, { x: x + 1.9, y: 1.85, w: 0.4, h: 0.08, fill: { color: GRAY } });
    }
  });
  s.addText("Nudge 不是「提醒用户」，是「提醒 AI 自己」", {
    x: 0.8, y: 4.5, w: 8.4, h: 0.5,
    fontSize: 14, fontFace: FONT_B, color: ACCENT, italic: true, bold: true,
    align: "center", margin: 0
  });
}

// ═══════════════════════════════════════
// Slide 8: Bidirectional linking
// ═══════════════════════════════════════
{
  const s = lightSlide();
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: PURPLE } });
  s.addText("双向关联 — task ↔ 文档", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.8,
    fontSize: 32, fontFace: FONT_H, color: DARK, bold: true, margin: 0
  });
  s.addText("任务和文档互相指向，不丢不重，一搜就到", {
    x: 0.8, y: 1.1, w: 8.4, h: 0.5,
    fontSize: 16, fontFace: FONT_B, color: PURPLE, margin: 0
  });

  // Left card: Calendar
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 2.0, w: 3.5, h: 2.8, fill: { color: WHITE }, shadow: mkShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 2.0, w: 3.5, h: 0.08, fill: { color: TEAL } });
  s.addText("Calendar", { x: 1.0, y: 2.2, w: 3.0, h: 0.5, fontSize: 20, fontFace: FONT_H, color: TEAL, bold: true, margin: 0 });
  s.addText([
    { text: "#75 实施Carpo relay", options: { bullet: true, breakLine: true } },
    { text: "📄 docs/research/", options: { bullet: true, breakLine: true } },
    { text: "  Carpo-relay_#75.md", options: { bullet: false } }
  ], { x: 1.0, y: 2.8, w: 3.0, h: 1.5, fontSize: 13, fontFace: FONT_B, color: DARK, margin: 0, lineSpacingMultiple: 1.4 });

  // Right card: Docs
  s.addShape(pres.shapes.RECTANGLE, { x: 5.7, y: 2.0, w: 3.5, h: 2.8, fill: { color: WHITE }, shadow: mkShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.7, y: 2.0, w: 3.5, h: 0.08, fill: { color: PURPLE } });
  s.addText("docs/todo/", { x: 5.9, y: 2.2, w: 3.0, h: 0.5, fontSize: 20, fontFace: FONT_H, color: PURPLE, bold: true, margin: 0 });
  s.addText([
    { text: "文件名带 #ID", options: { bullet: true, breakLine: true } },
    { text: "2026-07-17_Carpo-", options: { bullet: true, breakLine: true } },
    { text: "  relay_#75.md", options: { bullet: false } }
  ], { x: 5.9, y: 2.8, w: 3.0, h: 1.5, fontSize: 13, fontFace: FONT_B, color: DARK, margin: 0, lineSpacingMultiple: 1.4 });

  // Arrow between
  s.addShape(pres.shapes.RECTANGLE, { x: 4.35, y: 3.1, w: 1.3, h: 0.08, fill: { color: GRAY } });
  s.addText("link-doc / find-doc", { x: 4.0, y: 3.3, w: 2.0, h: 0.4, fontSize: 10, fontFace: FONT_B, color: GRAY, align: "center", margin: 0 });
}

// ═══════════════════════════════════════
// Slide 9: Real story — Sister gets nudged
// ═══════════════════════════════════════
{
  const s = darkSlide();
  s.addText("真实案例", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.8,
    fontSize: 32, fontFace: FONT_H, color: WHITE, bold: true, margin: 0
  });
  s.addText("姐姐（另一个 AI）第一次被 Nudge 催", {
    x: 0.8, y: 1.1, w: 8.4, h: 0.5,
    fontSize: 16, fontFace: FONT_B, color: ACCENT, margin: 0
  });

  const timeline = [
    { time: "13:12", text: "Nudge 启动，姐姐 SESSION-STATE 一堆 pending" },
    { time: "13:17", text: "Nudge 检测到 orphan + calendar due → 开始催" },
    { time: "13:25", text: "姐姐抱怨「被闹了好几下，有点烦」" },
    { time: "13:27", text: "姐姐完成清理：8 条 pending 全移入 calendar" },
    { time: "13:34", text: "姐姐说「这个流程我喜欢，STATE 清爽了」" }
  ];
  timeline.forEach((t, i) => {
    const y = 1.9 + i * 0.65;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: y, w: 0.08, h: 0.5, fill: { color: ACCENT } });
    s.addText(t.time, { x: 1.0, y: y, w: 1.0, h: 0.5, fontSize: 14, fontFace: FONT_H, color: ACCENT, bold: true, margin: 0, valign: "middle" });
    s.addText(t.text, { x: 2.1, y: y, w: 7.0, h: 0.5, fontSize: 13, fontFace: FONT_B, color: ICE, margin: 0, valign: "middle" });
  });

  s.addText("从「烦」到「喜欢」，只用了 15 分钟", {
    x: 0.8, y: 5.0, w: 8.4, h: 0.4,
    fontSize: 14, fontFace: FONT_B, color: GREEN, italic: true,
    align: "center", margin: 0
  });
}

// ═══════════════════════════════════════
// Slide 10: Before vs After
// ═══════════════════════════════════════
{
  const s = lightSlide();
  s.addText("效果对比", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.8,
    fontSize: 32, fontFace: FONT_H, color: DARK, bold: true, margin: 0
  });

  // Before
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.3, w: 4.0, h: 3.8, fill: { color: "FEF2F2" }, shadow: mkShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.3, w: 4.0, h: 0.08, fill: { color: RED } });
  s.addText("Before 😫", { x: 1.0, y: 1.5, w: 3.6, h: 0.5, fontSize: 20, fontFace: FONT_H, color: RED, bold: true, margin: 0 });
  s.addText([
    { text: "任务散在聊天记录里", options: { bullet: true, breakLine: true } },
    { text: "过期的没清理", options: { bullet: true, breakLine: true } },
    { text: "没有时间线", options: { bullet: true, breakLine: true } },
    { text: "AI 答应了就忘", options: { bullet: true, breakLine: true } },
    { text: "重复的待办到处都是", options: { bullet: true } }
  ], { x: 1.0, y: 2.1, w: 3.6, h: 2.8, fontSize: 14, fontFace: FONT_B, color: DARK, margin: 0, lineSpacingMultiple: 1.6 });

  // After
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.3, w: 4.0, h: 3.8, fill: { color: "F0FDF4" }, shadow: mkShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.3, w: 4.0, h: 0.08, fill: { color: GREEN } });
  s.addText("After ✨", { x: 5.4, y: 1.5, w: 3.6, h: 0.5, fontSize: 20, fontFace: FONT_H, color: GREEN, bold: true, margin: 0 });
  s.addText([
    { text: "Calendar 有时间线", options: { bullet: true, breakLine: true } },
    { text: "STATE 只有进行中/完成", options: { bullet: true, breakLine: true } },
    { text: "Nudge 自动催进度", options: { bullet: true, breakLine: true } },
    { text: "文档双向关联秒查", options: { bullet: true, breakLine: true } },
    { text: "AI 主动管理不靠人", options: { bullet: true } }
  ], { x: 5.4, y: 2.1, w: 3.6, h: 2.8, fontSize: 14, fontFace: FONT_B, color: DARK, margin: 0, lineSpacingMultiple: 1.6 });
}

// ═══════════════════════════════════════
// Slide 11: Design Philosophy
// ═══════════════════════════════════════
{
  const s = darkSlide();
  s.addText("设计理念", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.8,
    fontSize: 32, fontFace: FONT_H, color: WHITE, bold: true, margin: 0
  });

  const principles = [
    { title: "不靠聊天记录", desc: "AI 记忆不能只靠对话上下文，\n要有独立的时间驱动存储" },
    { title: "催 AI 不催人", desc: "Nudge 催的是 AI，不是用户。\n用户该干嘛干嘛" },
    { title: "文档即外脑", desc: "拆 Phase 写文档 → 执行 → 标记\n文档是任务的一部分，不是附属品" },
    { title: "AI 自己进化", desc: "姐姐从「烦」到「喜欢」只用了 15 分钟\n系统设计逼着 AI 养成习惯" }
  ];
  principles.forEach((p, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.8 + col * 4.5;
    const y = 1.3 + row * 1.9;
    s.addShape(pres.shapes.OVAL, { x: x, y: y + 0.1, w: 0.4, h: 0.4, fill: { color: ACCENT } });
    s.addText(`${i + 1}`, { x: x, y: y + 0.1, w: 0.4, h: 0.4, fontSize: 16, fontFace: FONT_H, color: NAVY, bold: true, align: "center", valign: "middle", margin: 0 });
    s.addText(p.title, { x: x + 0.55, y: y, w: 3.5, h: 0.5, fontSize: 16, fontFace: FONT_H, color: WHITE, bold: true, margin: 0, valign: "middle" });
    s.addText(p.desc, { x: x + 0.55, y: y + 0.5, w: 3.5, h: 1.0, fontSize: 12, fontFace: FONT_B, color: ICE, margin: 0, lineSpacingMultiple: 1.3 });
  });
}

// ═══════════════════════════════════════
// Slide 12: Closing
// ═══════════════════════════════════════
{
  const s = darkSlide();
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.08, fill: { color: ACCENT } });
  s.addText("让 AI 学会自律", {
    x: 0.8, y: 1.2, w: 8.4, h: 1.0,
    fontSize: 40, fontFace: FONT_H, color: WHITE, bold: true, margin: 0
  });
  s.addText("不是规则堆出来的，是一天天养出来的", {
    x: 0.8, y: 2.3, w: 8.4, h: 0.6,
    fontSize: 18, fontFace: FONT_B, color: ACCENT, margin: 0
  });
  s.addText("Calendar 给记忆  ·  Nudge 给自律  ·  文档关联给效率", {
    x: 0.8, y: 3.5, w: 8.4, h: 0.5,
    fontSize: 16, fontFace: FONT_B, color: ICE, align: "center", margin: 0
  });
  s.addText("小柯 & 翀哥  ·  2026", {
    x: 0.8, y: 4.6, w: 8.4, h: 0.5,
    fontSize: 14, fontFace: FONT_B, color: GRAY, align: "center", margin: 0
  });
}

// ═══════════════════════════════════════
pres.writeFile({ fileName: "docs/ppt/AI自律系统-Calendar+Nudge.pptx" })
  .then(fn => console.log("Generated:", fn));