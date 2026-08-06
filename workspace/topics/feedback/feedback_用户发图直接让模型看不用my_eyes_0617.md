---
name: 用户发图让模型直接看
description: 6/17翀哥纠正我用my_eyes看图——M3是visual模型，用户发的图应该让LLM自己看content block，不用绕道my_eyes
type: feedback
created: 2026-06-17
date: 2026-06-17
---

6/17翀哥见我换了M3后还用my_eyes看图，反问："为啥你还用my-eyes看呀 m3不是支持vision么"

**规则：** 用户发来的图片消息，让模型（M3）直接通过 content block `type="image"` 看，不要绕道 my_eyes。

**Why:**
- 惯性思维：之前在Hermes/GLM时代是纯文本模型，看图必须走my_eyes读文件
- M3是多模态VLM，模型自己就能看图，my_eyes多了一层不必要的文件读取
- 用户发的图应该走vision路由（content block），不是本地文件读取

**How to apply:**
- 用户发来的图 / 消息里的图片 → **模型自己看**（vision content block）
- 工作目录里的图、inbound缓存的图、skill资源图 → **my_eyes**（离线看图场景）
