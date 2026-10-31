# SHU261 基础实践 · 期末作业 —— 卧室/书房（电脑桌）环境声设计

> **学号**：24122099　**姓名**：唐清文
> **作业**：环境声设计（Scene Sound Design）—— 素材采集 → 剪辑导出 → Wwise 中间件集成
> **场景**：卧室兼书房（电脑桌）—— 一个学生最熟悉、也最容易被忽略的日常声音现场

---

## 一、这个作品做了什么

把"一个人坐在电脑桌前"的日常空间，拆成 **持续层 + 偶发层** 两层声音结构，
用手机实录采集 3 段原始素材，经自建管线剪辑导出 **13 个 48 kHz / 24 bit / stereo 声音资产**，
再在 Wwise 中搭成"无缝循环基底 + 随机触发点声"的可交互声音系统。

| 环节 | 成果 |
| --- | --- |
| 场景分析 | 三层声音结构（持续层 / 偶发层 / 人声层），见 [`docs/scene-analysis.md`](./docs/scene-analysis.md) |
| 素材采集 | 手机实录 3 段（风扇 61.64 s、键盘 32.28 s、椅子 18.88 s），见 [`docs/recording-log.md`](./docs/recording-log.md) |
| 剪辑导出 | 13 个资产，全部 48 kHz / 24 bit / stereo WAV，零削波 |
| Wwise 集成 | 无缝循环基底 ×1、Random Container ×1（12 个子对象）、Positioning + 25 m 衰减、2 个 Event、SoundBank 生成通过 |
| 自动化 | 剪辑管线与 Wwise 工程构建均为脚本化（Python + Wwise WAAPI），可复现 |

---

## 二、交付物清单

```
SHU261-final/
├─ README.md                        ← 本文件（总览与验收对照）
├─ docs/
│  ├─ scene-analysis.md             场景分析：空间描述、声音分层、素材需求清单
│  ├─ recording-log.md              录音日志：设备设置、原始素材、处理链路、资产测量数据
│  ├─ wwise-setup.md                Wwise 工程：层级结构、参数表、Event、SoundBank、试听步骤
│  └─ recording-guide.md            录音施工单（录音前的操作规范，可作附录）
├─ assets/
│  ├─ fig1-scene-layout.svg         场景平面示意图（声源与录制位置）
│  ├─ fig2-sound-layers.svg         声音分层结构图
│  └─ *.wav                         13 个声音资产（48 kHz / 24 bit / stereo）
├─ tools/                           自建处理与构建脚本（可复现）
│  ├─ make_assets.py                剪辑/导出管线（降噪、滤波、漂移压平、无缝循环化、24bit 导出）
│  ├─ split_onsets.py               冲击声自动切分（一次录一串动作 → 逐条资产）
│  ├─ inspect_wav.py                WAV 体检（格式/峰值/RMS/削波）
│  ├─ analyze_wav.py                内容分析（电平包络/分频段能量/声道相关性）
│  ├─ wwise_import.lua              Wwise 导入与层级整理（WAAPI）
│  └─ wwise_build.lua               Wwise 参数/Event/SoundBank 构建（WAAPI）
└─ wwise/
   └─ BedroomAmbience/              Wwise 工程（Wwise 2025.1.12.9287）
      ├─ BedroomAmbience.wproj
      ├─ Originals/SFX/             导入的音频源（与 assets/ 同名同内容）
      └─ *.wwu                      Actor-Mixer / Events / Attenuations / SoundBanks 工作单元
```

---

## 三、验收对照（逐条对题目要求）

| 题目要求 | 完成情况 | 证据 |
| --- | --- | --- |
| 确定场景 + 图片 + 文字说明 | ✅ | 场景图 [`assets/fig1-scene-layout.svg`](./assets/fig1-scene-layout.svg)、说明 [`docs/scene-analysis.md`](./docs/scene-analysis.md) |
| ≥2 种声音素材（持续基底 + 间断随机） | ✅ 3 类 | 持续层 1 类、偶发层 2 类（键盘、椅子） |
| 基底资产 **> 30 s** | ✅ **60.64 s** | `assets/AMB_Bedroom_Base_Loop.wav` |
| 随机声资产 **≥ 3 个** | ✅ **12 个** | `KEY_single_01..05`、`KEY_typing_01..03`、`CHR_move_01..04` |
| 格式 **48 kHz / 24 bit / stereo .wav** | ✅ 13/13 | `docs/recording-log.md` 测量表 |
| 新建 Wwise 工程，名称不含中文 | ✅ `BedroomAmbience` | `wwise/BedroomAmbience/BedroomAmbience.wproj` |
| 配置 .gitignore | ✅ | 仓库根 `.gitignore` + Wwise 工程自带规则 |
| 基底持续不断循环播放 | ✅ | `IsLoopingEnabled=true`、`IsLoopingInfinite=true` |
| 随机声用 Random Container | ✅ | `RND_Bedroom_Spot`：`RandomOrSequence=1`（Random）、Avoid Repeating ×3、Play Mode=Step |
| 随机声 Positioning 随距离变化 | ✅ | `3DPosition=Emitter`、`3DSpatialization=Position`、`Attenuation→ATT_Bedroom_Spot`（RadiusMax 25 m） |
| Soundcaster 预览测试 | ✅ 工程已就绪 | 操作步骤见 [`docs/wwise-setup.md`](./docs/wwise-setup.md) 第 7 节 |

---

## 四、三个技术要点（这个作品真正花功夫的地方）

### 1. 手机录音的"长时响度漂移"必须压平，否则循环会露馅

手机录音时人稍微一动、风扇转速一变，30 秒里的电平就会漂 5–6 dB。
直接剪成循环播放时，接缝处会出现"音量台阶"，一听就假。

管线里的 `flatten_level()` 按 0.25 s 窗计算短时 RMS，取中位电平为目标，
算出每窗的修正增益后做 2 s 平滑，再逐样本线性插值应用，且限制在 ±8 dB 内
（不改变动态内容本身，只修正缓慢的响度倾斜）。

实测：风扇素材漂移 **6.4 dB → 1.8 dB**。

### 2. 无缝循环 = 等功率交叉淡化 + 单段连续素材

不做"复制粘贴两遍"这种伪循环。做法是把素材尾部 1.0 s 等功率叠到头部 1.0 s，
再裁掉尾部那 1.0 s——循环点两侧是连续的同一段声学过程，接缝不可闻。

60.64 s 基底来自**一条 61.64 s 的连续录音**（不是拼接），因此循环周期足够长，
听不出重复感。

### 3. 一次录音切成 N 个资产：onset 自动切分

键盘那条 32 s 里有上百次敲击，手工切不现实。
`split_onsets.py` 用 5 ms 窗计算包络，取 20% 分位数作为噪声底，
阈值取"噪声底 + 10 dB"，再做最短间隔合并（30 ms）与最短长度过滤（15 ms）。

实测：32.28 s 键盘录音 → 检测出 **113 个敲击事件**；
18.88 s 椅子录音 → 检测出 **11 个动作事件**。
导出时每条自动做去直流、40 Hz 高通、淡入淡出、峰值归一化。

---

## 五、怎么听这个作品

**方式一：直接在 Wwise 里听（推荐）**

1. 用 Wwise Launcher 打开 `wwise/BedroomAmbience/BedroomAmbience.wproj`
2. Soundcaster Session 里拉入 `PLAY_Bedroom_Ambience` 与 `PLAY_Bedroom_Spot` 播放
   （详细步骤见 [`docs/wwise-setup.md`](./docs/wwise-setup.md) 第 7 节）
3. 想验证 Position 衰减：把 Game Object 拖远，音量与高频会随距离衰减（25 m 到零）

**方式二：直接听导出的 WAV**

`assets/AMB_Bedroom_Base_Loop.wav` 循环播放即为场景基底；
`KEY_*` / `CHR_*` 是随机叠上去的点声。

---

## 六、环境与版本说明

| 项目 | 版本 / 说明 |
| --- | --- |
| Wwise | **2025.1.12.9287**（题目要求 2025.1.11.9262；同一 2025.1 补丁线，工程格式与 WAAPI 完全一致，`project schema 133`） |
| Wwise 工程 | `BedroomAmbience`，平台 Windows |
| 录音设备 | 安卓手机，48 kHz / 24 bit / 立体声双麦 |
| 处理环境 | Python 3.13，纯标准库（无第三方依赖），Windows |
| Wwise 自动化 | `WwiseConsole execute-lua-script` + WAAPI（`wa_call`） |
| 原始录音 | 未入库（体积原因），仅保留剪辑后资产；原始文件与参数的对应关系见录音日志 |

---

## 七、可复现命令

```powershell
# 1. 体检任意录音
python tools/inspect_wav.py <file.wav>

# 2. 基底：压平漂移 + 无缝循环 + 导出 48k/24bit/stereo
python tools/make_assets.py base `
  --in raw_fan_60s.wav `
  --out assets/AMB_Bedroom_Base_Loop.wav `
  --rms -23 --xfade 1.0 --flatten --keep-stereo

# 3. 随机声：一次录音自动切成多条资产
python tools/split_onsets.py `
  --in raw_keyboard.wav --out-dir staging --prefix KEY `
  --min-gap 0.03 --thresh 10

# 4. Wwise：导入 + 整理层级，然后设置参数/事件/SoundBank
WwiseConsole execute-lua-script tools/wwise_import.lua --project <proj>
WwiseConsole execute-lua-script tools/wwise_build.lua  --project <proj>
WwiseConsole generate-soundbank <proj> --platform Windows
```

---

*本作品仅用于 SHU261 基础实践课程期末作业。所有声音素材均为本人实地录制。*
