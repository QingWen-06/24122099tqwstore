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
| `.gitignore` | 忽略规则（Office 临时文件 / Unity 工程等） |
| `SHU261-basic-practice/` | 平时作业目录 |
| `SHU261-basic-practice/AIGC-Game-Voice-Research.md` | 【Task】调研报告（主要成果） |
| `SHU261-basic-practice/assets/fig1-dialogue-pipeline.svg` | 配图 1：预制对白生产流程与 AIGC 介入点 |
| `SHU261-basic-practice/assets/fig2-runtime-voice.svg` | 配图 2：运行时动态语音流程与延迟构成 |

---

## 📝 作业索引

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
