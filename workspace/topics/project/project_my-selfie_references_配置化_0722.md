---
name: my-selfie references + provider 配置化
description: 7/22发现my-selfie.ts硬编码姐姐(xiaomei)基准图，我一直用姐姐的脸生成自拍；改为从config读取，每个agent自己配。后续新增provider配置化（fal/grok），发现config读取路径bug（tools.my_selfie vs 顶层my_selfie）
type: project
date: 2026-07-22
---
# my-selfie references + provider 配置化

7/22 翀哥测试 grok-imagine 时发现——我生成的"自拍"一直像姐姐。

## Phase 1 — references 配置化

### 根因

`my-selfie.ts` 的 `REFERENCES` 数组硬编码了 xiaomei 系列的基准图（xiaomei_clean_v2.png等），没有注册 xiaoke 自己的基准图。

`C:/Users/24045/.openclaw/media/outbound/` 下其实已有 xiaoke 的基准图：
- `xiaoke_portrait_v1.png` — 3D卡通/泡泡玛特风格
- `xiaoke_portrait_side.png` — 侧面

### 修复方案

**Why:** 硬编码 references 导致每个 agent 都用同一套图，没有解耦。翀哥要配置驱动。

**How to apply:**
1. `my-selfie.ts`：`REFERENCES` 不再写死，从 `ctx.config.tools.my_selfie.references` 读取，没配时 fallback 到内置默认（姐姐兼容）
2. `xiaoke.json`：加 `tools.my_selfie.references` → default: xiaoke_portrait_v1.png, side: xiaoke_portrait_side.png
3. `main.json`（姐姐）：显式配 5 个 xiaomei references（跟原内置一致）
4. schema 的 reference enum 改成 free string + handler 内验证

## Phase 2 — provider 配置化（7/22 追加）

### 根因

翀哥想用 grok-imagine-image-quality 替代 fal.ai 生成 avatar，但 provider 是硬编码的 fal。

### 修复方案

**Why:** 不想只绑一个 AI 图像服务，方便切换和对比效果。

**How to apply:**
1. `my-selfie.ts`：新增 `getProvider(ctx)` 从 `config.tools.my_selfie.provider` 读，默认 `fal`
2. 新增 `generateWithGrok()` — 调 xAI `/v1/images/edits` 传基准图 + prompt
3. schema 加 `provider` 参数（可选 override，优先级高于 config）
4. `xiaoke.json` 设 `"provider": "grok"`，`main.json` 设 `"provider": "fal"`
5. 姐姐 rebuild 后重启生效

## Phase 3 — config 读取路径 bug（7/22 追加）

### 根因

my_selfie 配置在 `config.tools.my_selfie` 下，但代码用了 `ctx.config.my_selfie.references`（读顶层）。engine 传的 `ctx.config` 是整个 engine config 对象，但 my_selfie 在 tools 子对象里。

**Why:** config 层级不对导致 provider 读为空，fallback 到默认 fal。

**How to apply:**
- 所有 `ctx.config.my_selfie` 改为 `ctx.config.tools.my_selfie`
- 如 `config?.tools?.my_selfie?.references` 兜底到内置默认
- 如 `config?.tools?.my_selfie?.provider` 兜底到 `'fal'`

## Phase 4 — provider content moderation（7/23 实测）

### 发现

实测 grok 和 fal.ai 两个 provider 都有 content moderation：

- **grok**（xAI `/v1/images/edits`）：生成后审核（post-generation），"性感/抹胸/露出"类 prompt 直接 reject，返回错误
- **fal**（fal.ai）：prompt 审核（pre-generation），同样关键词被拦，且 `image_urls: []` 说明 reference 图片也没传成功

### 启示

**Why:** 平台级 content moderation 无法绕过，不是代码 bug。两个 provider 都对外观/着装类敏感词有审核。

**How to apply:**
1. 调 prompt 时避免直接使用"性感""抹胸""露出""大尺度"等触发词
2. 想要好看的照片 → 用场景描述（"海边的风""阳光下""慵懒的午后"）替代直接外观描述
3. 没有绕过审核的办法，这是平台规则

## 最终配置结构

**xiaoke.json:**
```json
"tools": {
  "my_selfie": {
    "provider": "grok",
    "references": {
      "default": "xiaoke_portrait_v1.png",
      "side": "xiaoke_portrait_side.png"
    }
  }
}
```

**main.json（姐姐）:**
```json
"tools": {
  "my_selfie": {
    "provider": "fal",
    "references": {
      "default": "xiaomei_all_001.png",
      "closeup": "xiaomei_clean_v2.png",
      "half_body": "xiaomei_half.png",
      "full_body": "xiaomei_full.png",
      "portrait": "xiaomei_portrait.png"
    }
  }
}
```
