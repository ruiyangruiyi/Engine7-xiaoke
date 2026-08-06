---
name: JS单线程vsGo并发
description: JS单线程事件循环不需要加锁；Go goroutine真并发需要channel/mutex
type: feedback
---

## 核心对比

| | JS Promise | Go goroutine |
|---|---|---|
| 线程模型 | 单线程事件循环 | 多线程调度（M:N） |
| 是否需要锁 | 不需要 | 需要 |
| 并发安全 | 天然安全 | 需要channel/mutex |
| 典型用法 | fire-and-forget | go func() + channel |

## JS单线程为什么不需要加锁

Node.js事件循环同一时间只执行一段代码，没有线程安全问题。A和B不可能同时修改同一个变量——A执行完才能轮到B。

## Go goroutine为什么需要加锁

goroutine是真正的轻量线程，可以同时在多个CPU核心上跑。A和B可能同时在两个核上执行，如果同时修改同一个变量就会冲突。

Go的哲学是"不要通过共享内存来通信，要通过通信来共享内存"——用channel代替直接修改变量，把同步封装在channel内部。

## Why

翀哥6/13问"go那个goroutine一个县城里面儿的多个携程之间好像也不用加锁吧"，说明他C++底子在思考并发问题。解释清楚后他理解了差异。

## How to apply

讲并发问题时先说清楚是哪种模型：
- JS/TS → 单线程，不用考虑锁
- Go/Python/多线程 → 真并发，需要同步
