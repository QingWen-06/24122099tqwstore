# 24122099tqwstore

上海大学 **SHU261 基础实践** 课程作业仓库。

- **学号**：24122099
- **姓名**：唐清文
- **仓库用途**：存放平时作业与期末作业（文档、素材、工程文件）
- **仓库属性**：公开（Public）

---

## 📁 目录结构

| 路径 | 说明 |
| --- | --- |
| `README.md` | 本文件（仓库总览与作业索引） |
| `.gitignore` | 忽略规则（Office 临时文件 / Unity 工程 / Wwise 缓存与生成产物 / 原始录音等） |
| `SHU261-basic-practice/` | 平时作业目录 |
| `SHU261-basic-practice/AIGC-Game-Voice-Research.md` | 【Task】调研报告（主要成果） |
| `SHU261-basic-practice/assets/fig1-dialogue-pipeline.svg` | 配图 1：预制对白生产流程与 AIGC 介入点 |
| `SHU261-basic-practice/assets/fig2-runtime-voice.svg` | 配图 2：运行时动态语音流程与延迟构成 |
| `SHU261-final/` | 【Final】期末作业目录（环境声设计） |
| `SHU261-final/README.md` | 期末作业总览与验收对照 |
| `SHU261-final/docs/` | 场景分析、录音日志、Wwise 工程说明、录音施工单 |
| `SHU261-final/assets/` | 13 个声音资产（48 kHz / 24 bit / stereo WAV）+ 2 张示意图 |
| `SHU261-final/tools/` | 自建处理与构建脚本（Python 剪辑管线 + Wwise WAAPI 脚本） |
| `SHU261-final/wwise/BedroomAmbience/` | Wwise 工程（Wwise 2025.1.12） |

---

## 📝 作业索引

### Final — 卧室/书房（电脑桌）环境声设计

把"一个人坐在电脑桌前"的日常空间拆成 **持续层（机箱风扇 + 房间底噪）+ 偶发层（键盘、椅子）** 两层声音结构，
用手机实录 3 段原始素材，经自建管线剪辑导出 **13 个 48 kHz / 24 bit / stereo 声音资产**，
再在 Wwise 中搭成"无缝循环基底 + Random Container 随机点声 + Positioning 距离衰减"的可交互声音系统。

| 项目 | 内容 |
| --- | --- |
| 总说明 | [`SHU261-final/README.md`](./SHU261-final/README.md) |
| 场景分析 | [`SHU261-final/docs/scene-analysis.md`](./SHU261-final/docs/scene-analysis.md) |
| 录音日志与资产测量 | [`SHU261-final/docs/recording-log.md`](./SHU261-final/docs/recording-log.md) |
| Wwise 工程说明 | [`SHU261-final/docs/wwise-setup.md`](./SHU261-final/docs/wwise-setup.md) |
| 录音施工单 | [`SHU261-final/docs/recording-guide.md`](./SHU261-final/docs/recording-guide.md) |
| 场景与分层示意图 | [`fig1-scene-layout.svg`](./SHU261-final/assets/fig1-scene-layout.svg)、[`fig2-sound-layers.svg`](./SHU261-final/assets/fig2-sound-layers.svg) |
| Wwise 工程 | [`SHU261-final/wwise/BedroomAmbience/BedroomAmbience.wproj`](./SHU261-final/wwise/BedroomAmbience/BedroomAmbience.wproj) |
| 处理脚本 | [`make_assets.py`](./SHU261-final/tools/make_assets.py)、[`split_onsets.py`](./SHU261-final/tools/split_onsets.py)、[`wwise_build.lua`](./SHU261-final/tools/wwise_build.lua) |

**交付要点**

| 要求 | 结果 |
| --- | --- |
| 基底持续声 > 30 s | `AMB_Bedroom_Base_Loop.wav` —— **60.64 s**，等功率无缝循环（非拼接伪循环） |
| 随机间断声 ≥ 3 个 | **12 个**：键盘 8（单键 5 + 连打 3）、椅子 4 |
| 格式 48 kHz / 24 bit / stereo | 13/13 合规，削波采样数全为 0 |
| Random Container + Positioning | `RND_Bedroom_Spot`：Random / Avoid Repeating×3 / Emitter 3D / ATTN 25 m |
| SoundBank | `Main.bnk` 11.6 MB，含 2 个 Event 与 13 个音源，生成退出码 0 |

---

### Task 01 — 当下 AIGC 在游戏语音（Voice）设计中的应用（调研）

课程题目的范围包含 Voice、Music、SFX 三个方向，本次作业把范围收敛到 **Voice 方向**，只讨论游戏内人声对白的生产与播出。

| 项目 | 内容 |
| --- | --- |
| 报告文件 | [`SHU261-basic-practice/AIGC-Game-Voice-Research.md`](./SHU261-basic-practice/AIGC-Game-Voice-Research.md) |
| 配图 | [`fig1-dialogue-pipeline.svg`](./SHU261-basic-practice/assets/fig1-dialogue-pipeline.svg)、[`fig2-runtime-voice.svg`](./SHU261-basic-practice/assets/fig2-runtime-voice.svg) |
| 讨论范围 | 语音合成、语音克隆、情感与韵律控制、多语言本地化、运行时动态对白 |
| 不讨论 | 音乐生成、音效与拟音生成、语音识别、演唱合成 |
| 核心结论 | AIGC 在 Voice 方向最成熟的应用是变体生产与本地化首版；文本侧质量决定整条流程的天花板；音色必须作为带授权记录的资产管理 |

**报告章节**

1. 范围界定与 Voice 方向的工作量结构
2. 预制对白的生产流程与 AIGC 介入点
3. 文本侧：台词表字段与文本规范化（数字、多音字、专有名词、运行时变量）
4. 音色侧：零样本克隆 / 少样本微调 / 完整微调三条路线，音色一致性的四个维度
5. 表演侧：四种情感控制手段、变体生成做法、八类常见失败模式
6. 语言侧：跨语言克隆与时长约束
7. 运行时：动态对白流程、延迟构成与优化手段
8. 工程规范与 Wwise 对接（Dialogue Event、Random Container、RTPC、Voice Limit）
9. 质量评估：盲听测试设计与三级门槛
10. 风险与合规：声音人格权、内容标识（GB 45438—2025）、平台披露、从业者权益
11. 实例流程：一条台词从录入到游戏内播出的十一个步骤
12. 结论与展望
13. 术语对照
14. 参考资料

---

## 🔧 Git 基础操作备忘

本仓库使用 Git 与 GitHub 管理版本。常用命令：

```bash
# 克隆
git clone https://github.com/<用户名>/24122099tqwstore.git

# 日常提交三步
git status                      # 查看改动
git add .                       # 暂存（或 git add 具体文件）
git commit -m "docs: 更新调研报告"   # 提交

# 推送到远端
git push origin main

# 查看历史
git log --oneline --graph
```

**提交信息规范（约定式提交）**

| 前缀 | 含义 |
| --- | --- |
| `feat:` | 新增内容 |
| `docs:` | 文档修改 |
| `fix:` | 修正错误 |
| `assets:` | 素材/图片更新 |
| `chore:` | 杂项（配置、忽略规则等） |

---

*本仓库内容仅用于课程学习与作业提交。*
