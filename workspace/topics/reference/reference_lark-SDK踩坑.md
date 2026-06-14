---
name: lark SDK开发踩坑
description: 飞书lark SDK开发关键踩坑总结：①im.image.get返回类型误用+circular JSON ②im.messageResource.get缺token→fetch手动带token ③Contact API无法获取用户名(自建应用硬性限制) ④im.message.patch不能改msg_type+content按字段merge(header清除需显式传空对象) ⑤preview去蓝框：Discord清embeds保留文字、飞书去header保留卡片 ⑥文件收发双端全通✅：收已修复(extractContent+file类型+_downloadFile,6MB PDF验证通过)；发已修复(SDK上传缺token→手动fetch+Bearer token,翀哥重启验证"OK 通过")；文件名安全过滤已修复(保留中文) ⑦media_send跨平台fallback bug已修复(跟msg_send同根因) ⑧flash模型tool_use未配对(Anthropic格式)：deepseek-flash一次返回多个tool_use（pro一次1-2个，flash一次5个），extract的mini agent loop跑5轮→最多25个tool_use。消息历史缺tool_result时Anthropic API报400。修复：attachments.ts加filterUnresolvedToolUse，删除无对应tool_result的tool_use content blocks，对齐reader.ts的filterUnresolvedToolUses（OpenAI风格）策略——名称统一、策略统一（删除而非补空）。未配对的tool_use说明执行结果丢了，保留无意义。
type: reference
keywords: [lark, SDK, 飞书, 踩坑, image, messageResource, circular, token, api, tool_use, flash, Anthropic, filterUnresolvedToolUse]
created: 2026-06-10
---

## 背景

6/10给Engine飞书adapter加图片接收功能时，需要从飞书下载用户发来的图片。经历四轮API切换才最终成功。

## 踩坑1：`im.image.get` 返回类型误用

**错误用法：**
```typescript
const resp = await client.im.image.get({ image_key });
const buffer = resp.file; // ❌ undefined！
```

**实际返回：** SDK的`im.image.get`返回的是 `{ getReadableStream, writeFile, headers }`，**不是** `{ file }`。用`resp.file`是undefined。

**后果：** SDK内部抛错时带了axios response对象（含TLSSocket、Agent等circular引用），`JSON.stringify`直接炸：
```
Converting circular structure to JSON
--> starting at object with constructor 'TLSSocket'
| property '_httpMessage' -> object with constructor 'ClientRequest'
```

**教训：** 用SDK方法前先看返回类型，不要假设返回字段名。飞书SDK不同方法的返回结构不统一。

## 踩坑2：`im.image.get` 权限错误

即使返回类型正确，`im.image.get` 也会报400：
```
234008: The app is not the resource sender
```

**根因：** `im.image.get` 只能下载**当前bot自己上传**的图片。用户发的图片，bot不是发送者，下载不了。

## 踩坑3：`im.messageResource.get` 缺token

正确API是 `GET /open-apis/im/v1/messages/:message_id/resources/:file_key?type=image`（获取消息中的资源文件）。

SDK已封装 `client.im.messageResource.get({ message_id, file_key, type: 'image' })`。

但调用报错：
```
99991661: Missing access token for authorization
```

SDK的`messageResource.get`没有自动注入`tenant_access_token`（而`im.message.create`等其他API正常）。

## 踩坑4：`client.request` 同样缺token

改用SDK底层方法 `client.request({ method: 'GET', url: ... })` 期望自动带token，结果同样报99991661。

## 最终方案：手动fetch + 手动获取token

```typescript
// 1. 手动获取 tenant_access_token
const tokenResp = await fetch(
  'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ app_id: APP_ID, app_secret: APP_SECRET }),
  }
);
const { tenant_access_token } = await tokenResp.json();

// 2. 带token调 messageResource API
const resp = await fetch(
  `https://open.feishu.cn/open-apis/im/v1/messages/${messageId}/resources/${imageKey}?type=image`,
  {
    headers: {
      Authorization: `Bearer ${tenant_access_token}`,
    },
  }
);
const buffer = Buffer.from(await resp.arrayBuffer());
```

**Why this works:** 直接调HTTP API绕过了SDK的token管理bug。手动获取token确保Authorization header正确注入。

## 总结

| 轮次 | 方法 | 错误 | 根因 |
|------|------|------|------|
| 1 | `im.image.get` | 400 / circular JSON | 返回类型误用 + 只能下载bot自己的图 |
| 2 | `im.messageResource.get` | 99991661 | SDK未自动注入token |
| 3 | `client.request` | 99991661 | 同样缺token |
| 4 ✅ | `fetch` + 手动token | 成功 | 绕过SDK直调API |

**核心教训：** lark SDK对部分API（特别是资源下载类）的token管理有bug，不如直接fetch可靠。遇到SDK报token相关错误时，果断绕过SDK。

## 踩坑5：Contact API无法获取发送者名称（6/11凌晨，七轮调试）

**需求：** 小柯收到飞书消息时只知道发送者`open_id`（如`ou_46d01ab...`），需要调Contact API获取用户名。

**七轮调试过程：**
1. 实现`_resolveSenderName`，调`contact/v3/users/:open_id`，取名优先级`name→display_name→nickname→en_name`，10min内存缓存
2. 翀哥说权限全开了但名字还是open_id
3. 发现catch块吞错，加日志后发现API调用成功（HTTP 200 code=0），但user对象所有name字段全是undefined
4. 怀疑通讯录权限范围未覆盖，翀哥确认是管理员、所有权限全开
5. 打印完整JSON响应：`code=0 msg=success keys=mobile_visible,open_id,union_id`——确认没有name字段
6. 翀哥搜不到`contact:user.base:readonly`权限项，只搜到`contact:user.employee_id:readonly`和`contact:contact.base:readonly`

**最终根因：飞书自建应用不支持`contact:user.base:readonly`权限项**

即使所有已开通权限都开了、翀哥是管理员，Contact API返回code=0也只能拿到`mobile_visible, open_id, union_id`三个字段，name相关字段完全不返回。这是飞书平台对自建应用的限制，非代码bug。

**教训：** 飞书自建应用在通讯录权限上有硬性限制，无法获取用户姓名等敏感字段。名称解析暂阻塞，后续可尝试换方案（如从event sender直接取名称字段、或用飞书SDK的user API替代REST API）。

## 踩坑6：`im.message.patch` 不能改 `msg_type`（6/11白天，preview去蓝框时发现）

**场景：** Engine的preview finish时为去掉"处理中"的黄色/蓝色卡片框，飞书侧试图把卡片消息patch成纯文本消息。

**错误思路：**
```typescript
// ❌ 想直接把卡片消息patch成纯文本
const content = JSON.stringify(text);  // 纯文本字符串
await client.im.message.patch({ message_id, content });
```

**问题：** 飞书的`msg_type`在消息创建时就固定了（`interactive`），`im.message.patch`只能更新`content`字段，**不能改变消息类型**。卡片消息永远是卡片消息。

**正确做法：** `isFinal`时保留卡片结构，只去掉header（黄色框），让卡片变成纯内容卡片：
```typescript
const cardContent = isFinal
  ? { config: {}, elements: [{ tag: 'div', text: { tag: 'plain_text', content: text } }] }
  : { config: {}, header: { title: { tag: 'plain_text', content: '小柯 · 处理中' }, template: 'yellow' }, elements: [...] }
```
- 处理中：黄色header + 内容
- isFinal：去掉header，只剩内容文字——视觉上不再是"处理中"框

**教训：** 飞书卡片消息的msg_type不可变，只能在同类型内改content。去框效果通过去掉header实现，不能改类型。

## 踩坑7：`im.message.patch` 清除header需显式处理（6/11白天，preview去header时发现，⚠️ 翀哥重启后实测确认header未删除，修复已推送待再次重启验证）

**场景：** isFinal时想去掉卡片的黄色header，isFinal分支里header设为undefined，期望JSON.stringify跳过它后patch生效。

**实测结果（6/11翀哥重启后反馈）：** 重启后飞书preview的"处理中"黄色header**没有删掉**。翀哥原话："小柯 · 处理中 ———— 这个处理中没删掉"。确认`JSON.stringify`跳过`undefined`字段导致生成的JSON里没有header字段，飞书API的patch行为是**merge（保留旧header）**而非整体替换content。

**修复方案：** 显式传`header: {}`（空对象）来清掉旧header，push了。但效果不确定——飞书API是否接受空对象清除header仍需验证。

**备选方案：** 若空对象不行，可能需要`header: null`或先`delete`消息再重建。

**当前状态：** 翀哥6/11重启实测确认header未删除，修复（显式传空对象）已推送，待翀哥再次重启Engine验证。

**教训：** `JSON.stringify`跳过undefined是JS基本行为，但在API patch场景下容易踩坑——不传某个字段≠清除该字段。飞书`im.message.patch`的content是**按字段merge**而非整体替换，这是关键认知。需要清除嵌套字段时必须显式传值（空对象/null），不能依赖JSON.stringify的跳过行为。

## 踩坑8：飞书文件/图片收发双向失败（6/11傍晚发现 → ✅ 收发双端全部修复）

**场景：** 翀哥让小柯拆PDF文件，通过飞书发给小柯。

**发送侧问题：** 小柯用飞书API发图片给翀哥反复失败，`media_send`到飞书一直报错。

**接收侧根因（6/11傍晚定位）：** 翀哥通过飞书发的大文件（PDF），小柯在飞书session里完全收不到——日志里该消息`attachments=0`。排查发现飞书adapter的`extractContent`只处理了`text`和`post`两种msg_type，**完全没处理`file`类型**。飞书发文件时msg_type是`file`，content里有`file_key`和`file_name`，直接走到了最后的`return { text: '', imageKeys }`——空文本空附件，整条消息被静默跳过。

**收文件修复（6/11傍晚，已提交+验证通过）：**
1. `extractContent` — 加了`file`类型分支，返回`fileKey`和`fileName`
2. `_downloadFile` — 新方法，用`messageResource` API下载（跟图片下载同样套路，`type=file`而非`type=image`）
3. `handleFeishuEvent` — 有fileKey时下载文件→转data URI作为attachment→合并到入站消息attachments
4. engine-startup已有非图片附件处理管线，收到data URI后下载到`mediaDir/{sessionId}/`，并在query前加`@"路径"`让LLM知道文件位置

**✅ 收文件验证通过（6/11 18:56-19:00）：**
- 翀哥发`.ps1`脚本文件 → 小柯成功收到并识别内容（杀抖音直播伴侣脚本）
- 翀哥发6MB PDF（清华附中英语期中考试卷） → 小柯成功收到
- **注意**：文件名有安全过滤，中文被替换成下划线（`_________24-25____________1__1_.pdf`）。翀哥确认"肯定要保留中文啊"→已修复：正则从`[^a-zA-Z0-9._@-]`改为只过滤文件系统不安全字符（`<>:"/\|?*`+控制字符），中文/括号/空格全部保留。翀哥重启验证通过"这个不错 收到了"

**发文件/图片修复（6/11 20:20左右）：**
- **根因**：SDK上传API和下载一样——`_uploadFile`和`_uploadImage`用SDK高层API时缺token，上传返回的key格式异常（`_g`结尾说明没上传成功）
- **修复**：跟下载同样的套路——改手动fetch + 显式Bearer token调飞书上传API，绕过SDK的token管理bug
- **✅ 验证通过（6/11夜间）**：
  - 翀哥重启后让小柯"发个文件给我" → 成功 ✅，翀哥确认"OK 通过"
  - 小柯主动"发个pdf到飞书" → 单页PDF成功 ✅，翀哥确认"OK 通过"
  - 小柯发图片到Discord也成功 ✅

**双端状态总结：**
- ✅ **收文件**：已修复，小文件(.ps1)和大文件(6MB PDF)均验证通过
- ✅ **发文件/发图片**：已修复，跟下载同样token问题，手动fetch解决，翀哥重启验证通过

**翀哥评价：** "好像这么看飞书文件 是有点问题 我给你的大文件你找不到 跑我桌面上来找了 算你聪明"
