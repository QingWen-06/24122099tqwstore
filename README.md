# 24122099tqwstore

上海大学 **SHU261 基础实践** 课程作业仓库。

- **学号**：24122099
- **姓名**：唐清文
- **仓库用途**：存放平时作业与期末作业（文档、素材、工程文件）
- **仓库属性**：公开（Public）

---

## 📁 目录结构

```
24122099tqwstore/
├── README.md                     ← 本文件（仓库总览与作业索引）
├── .gitignore                    ← 忽略规则（Office 临时文件 / Unity 工程等）
└── SHU261-basic-practice/        ← 平时作业
    ├── AIGC-Game-Audio-Research.md   ← 【Task】调研报告（主交付物）
    └── assets/
        ├── fig1-pipeline.svg         ← 配图 1：AIGC 游戏音频生产管线总览
        └── fig2-matrix.svg           ← 配图 2：生成模式 × 音频方向 交叉矩阵
```

---

## 📝 作业索引

### Task 01 — 当下 AIGC 在游戏音频设计中的应用（调研）

| 项目 | 内容 |
| --- | --- |
| 交付物 | [`SHU261-basic-practice/AIGC-Game-Audio-Research.md`](./SHU261-basic-practice/AIGC-Game-Audio-Research.md) |
| 配图 | [`fig1-pipeline.svg`](./SHU261-basic-practice/assets/fig1-pipeline.svg)、[`fig2-matrix.svg`](./SHU261-basic-practice/assets/fig2-matrix.svg) |
| 调研角度 | ① Voice / Music / SFX 三个方向　② Text-to-Audio、Video-to-Audio 等生成模式 |
| 核心结论 | AIGC 在游戏音频中最成熟的落点是**变体生产与初稿**，而非最终成品；分轨能力与元数据台账比单次生成质量更决定工程可用性 |

**报告覆盖范围**

1. 技术底座：神经音频编解码器 + 自回归 / 扩散生成器
2. Voice 方向：临时配音、多语言本地化、NPC 语气变体、声音身份资产管理
3. Music 方向：循环 bed、分轨、垂直重混与水平重排等自适应音乐技术
4. SFX 方向：Video-to-Audio 拟音替代、变体爆炸、结构化提示词模板
5. 十类生成模式的交叉对比（TTS / TTA / TTM / V2A / A2A / TTV）
6. 从 Prompt 到 Wwise 事件的完整工作流与工程规范
7. 版权、声音人格权、《人工智能生成合成内容标识办法》（GB 45438—2025）、平台披露等合规风险

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
