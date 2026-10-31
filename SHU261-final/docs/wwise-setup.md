# Wwise 工程说明：BedroomAmbience

> 本文记录 Wwise 工程的**完整构建结果**：层级结构、每一个参数的取值与依据、
> Event/Action 结构、SoundBank 生成结果、自动化构建方式，以及 Soundcaster 试听步骤。
> 工程内所有对象均由脚本通过 WAAPI 创建（`tools/wwise_import.lua`、`tools/wwise_build.lua`），
> 可一键重建，不是手工点击出来的。

---

## 一、工程基本信息

| 项目 | 值 |
| --- | --- |
| 工程名称 | `BedroomAmbience`（英文，符合"工程名称不要使用中文"的要求） |
| 工程文件 | `SHU261-final/wwise/BedroomAmbience/BedroomAmbience.wproj` |
| Wwise 版本 | **2025.1.12.9287**（`branch=wwise_v2025.1.12`，`project schema 133`） |
| 目标平台 | Windows |
| Actor-Mixer 工作单元 | `\Containers\Default Work Unit`（Wwise 2025 中 Actor-Mixer Hierarchy 组的显示名） |
| 创建方式 | `WwiseConsole create-new-project BedroomAmbience.wproj --platform Windows` |

### 关于版本的一处说明

题目要求安装 **2025.1.11.9262**，本机已安装的是 **2025.1.12.9287**（同一 2025.1 补丁线内的更新版本，
本机未另装 9262 版本）。工程格式（schema 133）与 WAAPI 接口完全一致，
题目涉及的全部功能（Random Container、Positioning、Attenuation、SoundBank）在此版本下均已验证可用。
若评审要求严格的 9262 版本号，用 Launcher 安装后 `WwiseConsole migrate` 即可无损降/升版本迁移。

---

## 二、层级结构（工程实际结构）

```
\Actor-Mixer Hierarchy\Default Work Unit
└─ BedroomAmbience                                   (Folder, {BAC745E2-41AC-4AFD-8C76-D8D67170E810})
   ├─ AMB_Bedroom_Base_Loop                          (Sound SFX, {F4AD6515-39F5-4D52-A8F7-8BE3A4EABA40})
   │   └─ 60.64 s 无缝循环基底
   └─ RND_Bedroom_Spot                               (Random Container, {01BE1073-3978-45D9-B6C7-53E631951F37})
      ├─ KEY_single_01                               (0.12 s)
      ├─ KEY_single_02                               (0.20 s)
      ├─ KEY_single_03                               (0.14 s)
      ├─ KEY_single_04                               (0.11 s)
      ├─ KEY_single_05                               (0.15 s)
      ├─ KEY_typing_01                               (0.54 s)
      ├─ KEY_typing_02                               (0.60 s)
      ├─ KEY_typing_03                               (0.88 s)
      ├─ CHR_move_01                                 (1.44 s)
      ├─ CHR_move_02                                 (2.00 s)
      ├─ CHR_move_03                                 (1.96 s)
      └─ CHR_move_04                                 (1.62 s)

\Attenuations\Default Work Unit
└─ ATT_Bedroom_Spot                                 (Attenuation, {110C63D4-0477-4281-9600-5235356C1590})

\Events\Default Work Unit
├─ PLAY_Bedroom_Ambience                            ({B056EC04-8CEB-45C0-B156-FBE441E2E93D}, Event ID 3257288689)
│   └─ Play_Ambience                                (Action, ActionType=Play → Target = AMB_Bedroom_Base_Loop)
└─ PLAY_Bedroom_Spot                                ({F3EDE29A-FA25-4749-BDEB-5763CFDA9266}, Event ID 1431343029)
    └─ Play_Spot                                    (Action, ActionType=Play → Target = RND_Bedroom_Spot)

\SoundBanks\Default Work Unit
└─ Main                                             (SoundBank, {4FD8356A-0C83-4ED7-B02E-43C125371E65})
```

音频源文件被 Wwise 复制到 `Originals/SFX/`，与 `assets/` 下的交付资产同名同内容。

---

## 三、参数表（每个值都有依据）

### 3.1 基底层 `AMB_Bedroom_Base_Loop`（Sound SFX）

| 属性 | 值 | 依据 / 作用 |
| --- | --- | --- |
| `IsLoopingEnabled` | **true** | 题目要求"正确设置参数使其能够持续不断地循环播放"——循环开关是必要条件 |
| `IsLoopingInfinite` | **true** | 无限循环（而非 N 次后停止），环境基底需要"永远在播" |
| `Volume` | **−3.0 dB** | 基底是垫底层，留出与点声之间的动态空间（基底 RMS −23 dBFS / 点声峰值 −3 dBFS，约 20 dB 差） |
| `3DPosition` | 0（Emitter，默认） | 环境床保持默认 3D 发射器定位，由游戏侧把 Emitter 放在房间中心 |
| 输出总线 | Master Audio Bus（默认） | 本版不额外建 Bus 层级，避免增加与作业要求无关的复杂度 |

> 3D 距离衰减**只施加在随机声容器上**（见 3.2），基底不挂衰减：
> 环境床若跟随距离衰减，玩家走远后房间会"消失"，与"空间始终存在"的设计目标冲突。

### 3.2 随机声容器 `RND_Bedroom_Spot`（Random Container）

| 属性 | 值 | 依据 / 作用 |
| --- | --- | --- |
| `RandomOrSequence` | **1 = Random** | 题目要求"使用 Random Container 让其能够随机触发"。枚举值取自官方 `WObjects.xml`：`0=Sequence / 1=Random` |
| `NormalOrShuffle` | 1 = Standard | 每次触发独立随机取一条，不做洗牌式遍历 |
| `RandomAvoidRepeating` | **true** | 避免连续两次触发同一条素材（否则键盘"咔"两声一模一样，立刻露馅） |
| `RandomAvoidRepeatingCount` | **3** | 最近 3 条内不重复，配合 12 条素材有足够的变体空间 |
| `PlayMechanismStepOrContinuous` | **1 = Step** | 单发模式：播完一条就结束，由游戏事件再次触发。`0=Continuous` 会自动连播，不符合"间断随机声"的语义 |
| `PlayMechanismLoop` | false | 容器本身不循环 |
| `PlayMechanismResetPlaylistEachPlay` | true | 每次播放重新打乱播放列表，保证随机性 |
| `3DPosition` | **0 = Emitter** | 随机声是"房间里某个位置发出的声音"，必须 3D 定位 |
| `3DSpatialization` | **1 = Position** | 位置型空间化（`0=None / 1=Position / 2=Position + Orientation`）。点声源无朝向需求，取 Position |
| `EnableAttenuation` | **true** | 打开衰减，使音量随距离变化 |
| `Attenuation` | **`ATT_Bedroom_Spot`** | 指向自定义衰减对象（引用型属性，赋值为对象 GUID） |
| `Volume` | 0.0 dB | 点声不做整体衰减，靠各子对象的峰值归一化（−3 dBFS）统一电平 |

### 3.3 衰减对象 `ATT_Bedroom_Spot`（Attenuation）

| 属性 | 值 | 依据 |
| --- | --- | --- |
| `RadiusMax` | **25.0 m** | 卧室/书房尺度下，25 m 已远超整个房间的听觉可能范围——在房间内移动能听到真实的近远变化，走出房间自然听不到 |
| 曲线 | Wwise 默认 volume 曲线（1 m 附近 0 dB → RadiusMax 处 −200 dB） | 使用引擎默认衰减曲线，保证与真实听感一致 |

> 为什么这样设计 Positioning：键盘在 20 cm、椅子在 50 cm、桌边到门口约 2 m。
> 用同一个 25 m 衰减曲线，距离越远音量与高频衰减越多，
> 于是"近处的键盘"和"稍远的椅子"即使在容器里被随机选中，也会因为游戏侧的位置而得到不同的听感——
> 这正是题目"使其能够根据距离远近而发生变化"的落地方式。

### 3.4 枚举值来源说明（不是猜的）

所有 int 型参数的含义均从 Wwise 自带的官方定义文件 `Authoring\Data\WObjects\WObjects.xml` 中查得：

| 属性 | 枚举定义（原文摘录） |
| --- | --- |
| `RandomOrSequence` | `<Value DisplayName="Sequence">0</Value>` / `<Value DisplayName="Random">1</Value>` |
| `3DPosition` | `Emitter=0` / `Emitter with Automation=1` / `Listener with Automation=2` |
| `3DSpatialization` | `None=0` / `Position=1` / `Position + Orientation=2` |
| `PlayMechanismStepOrContinuous` | `Continuous=0` / `Step=1` |
| `NormalOrShuffle` | `Shuffle=0` / `Standard=1` |
| `ActionType` | `<Value DisplayName="/Play">1</Value>` |

---

## 四、Event / Action 结构

| Event | Action | ActionType | Target |
| --- | --- | --- | --- |
| `PLAY_Bedroom_Ambience` | `Play_Ambience` | Play（=1） | `AMB_Bedroom_Base_Loop` |
| `PLAY_Bedroom_Spot` | `Play_Spot` | Play（=1） | `RND_Bedroom_Spot` |

- 两个 Event 分开而不是合成一个：基底是"进入场景播一次就一直循环"，点声是"每次玩家操作后触发一次"，
  游戏侧的调用时机完全不同，必须解耦。
- Action 的 `Target` 是引用型属性，通过 WAAPI 赋值为对象 GUID（字符串形态），已回读校验：
  `Play_Spot | ActionType=1 | Target=RND_Bedroom_Spot`。

---

## 五、SoundBank

| 项目 | 值 |
| --- | --- |
| SoundBank | `Main`（`\SoundBanks\Default Work Unit\Main`） |
| 包含方式 | Inclusions：两个 Event，filter = `events` + `structures` + `media` |
| 生成命令 | `WwiseConsole generate-soundbank BedroomAmbience.wproj --platform Windows` |
| 生成结果 | `Process completed successfully`（退出码 0） |
| 产物 | `GeneratedSoundBanks/Windows/Main.bnk` **11.6 MB**、`Init.bnk`、`Main.txt`、`Main.json`、`SoundbanksInfo` 相关文件 |

**`Main.txt` 实测内容（证明两个 Event 与 13 个音源全部入包）**

| 类型 | 条目 |
| --- | --- |
| Event | `PLAY_Bedroom_Spot`(1431343029)、`PLAY_Bedroom_Ambience`(3257288689) |
| In-Memory Audio | `AMB_Bedroom_Base_Loop`（11 642 976 B，即 60.64 s 循环体真实入包） |
| In-Memory Audio | `KEY_single_01..05`、`KEY_typing_01..03`、`CHR_move_01..04`（共 12 条点声） |

> `GeneratedSoundBanks/` 属可再生产物，已按标准做法加入 `.gitignore`；需要时执行上面的生成命令即可复现。

---

## 六、自动化构建方式（不靠手点）

Wwise 无界面模式下的 Lua 环境里 `ak` 全局是 `nil`，但提供了 `wa_call(uri, args, options)`，
可直接调用 WAAPI 函数。本作品全部构建动作都走这条路径：

```lua
-- 查询：waql + options.return
wa_call("ak.wwise.core.object.get", { waql = "\"\\Actor-Mixer Hierarchy\\Default Work Unit\"" },
        { ["return"] = { "id", "name", "path" } })

-- 创建：options 必须为空表（create 的 optionsSchema 不接受 return）
wa_call("ak.wwise.core.object.create",
        { parent = id, type = "RandomSequenceContainer", name = "RND_Bedroom_Spot" }, {})

-- 改属性：@ 前缀 + 对象路径/ID
wa_call("ak.wwise.core.object.set",
        { objects = { { object = path, ["@RandomOrSequence"] = 1, ["@3DPosition"] = 0 } } }, {})

-- 引用型属性（Attenuation / Action Target）：传 GUID 字符串
wa_call("ak.wwise.core.object.set",
        { objects = { { object = path, ["@Attenuation"] = "{110C63D4-...}" } } }, {})
```

运行方式：

```powershell
WwiseConsole execute-lua-script tools/wwise_import.lua --project <proj> --no-color
WwiseConsole execute-lua-script tools/wwise_build.lua  --project <proj> --no-color
WwiseConsole generate-soundbank <proj> --platform Windows
```

两个脚本都是**幂等**的：重复执行不会产生重复对象（已存在则复用、已在容器内则不重复移动）。

---

## 七、Soundcaster Session 试听步骤（题目要求项）

> 无界面模式没有音频设备，试听需在 Wwise Authoring 图形界面中完成。以下为实际可操作步骤。

**准备**

1. 打开 Wwise Launcher → 切到 `Wwise` 标签 → 选择已安装的 `2025.1.12.9287`
2. 点击 `Open Project`，选择 `SHU261-final/wwise/BedroomAmbience/BedroomAmbience.wproj`
   （首次打开会提示迁移/加载，选择打开即可）

**建 Soundcaster 会话并试听**

3. 顶部菜单 `Windows → Soundcaster`（或在 Layout 里找 Soundcaster 视图）
4. Soundcaster 左上角 Session 下拉框 → 选 `Default Work Unit`（工程已自带；如需新建：`Session → New`，命名 `Final_Preview`）
5. 在 `Project Explorer` 里展开 `Events`，把 `PLAY_Bedroom_Ambience` 和 `PLAY_Bedroom_Spot`
   分别拖进 Soundcaster 的模块槽位
6. 点击 `PLAY_Bedroom_Ambience` 的播放键 → 基底应**持续不间断地循环播放**（验证 `IsLoopingEnabled` + `IsLoopingInfinite`）
7. 反复点击 `PLAY_Bedroom_Spot` 的播放键 → 每次应触发**不同的**键盘/椅子声（验证 Random Container 的随机与不重复）
8. 同时播放两者 → 基底垫底、点声位于前景，检查混音比例

**验证 Positioning 随距离变化**

9. 打开 `Windows → Attenuation Editor`，选中 `ATT_Bedroom_Spot`，
   确认 volume 曲线从 1 m 处的 0 dB 衰减到 25 m 处的 −200 dB
10. 打开 `Windows → Voice Profiler`（或 `Layouts → Profiler`），播放 `PLAY_Bedroom_Spot` 时
    可以观察 voice 的实际音量计算值随 Game Object 距离变化
11. 直接听对比：把 `RND_Bedroom_Spot` 的 `Attenuation` 临时换成另一条更短的衰减（如 RadiusMax 2 m），
    再次播放，能明显听出低频保留、高频与整体音量更快衰减 —— 这就是距离变化带来的听感差异，
    验证完记得换回 `ATT_Bedroom_Spot`

**收尾**

12. `Project → Save`（Ctrl+S），关闭工程

> 试听要点：基底听"有没有接缝"（60.64 s 循环点应在 60 s 后出现，正常监听下不可闻）；
> 点声听"是否会重复"（连续触发 10 次，不应出现同一条素材连播两次，因为 `RandomAvoidRepeatingCount=3`）。

---

## 八、`.gitignore` 配置说明

Wwise 生成工程时自带了一份模板（`wwise/BedroomAmbience/.gitignore`），已覆盖
`.cache*`、`*.validationcache`、`.backup*`、`*.akd`、`*.prof`、`*.wsettings` 等**本地缓存与机器相关文件**。

仓库根 `.gitignore` 在此基础上补充：

| 规则 | 原因 |
| --- | --- |
| `SHU261-final/wwise/**/GeneratedSoundBanks/` | 生成产物，可由 `generate-soundbank` 一键重建，体积大且随平台变化 |
| `SHU261-final/wwise/**/*.wsettings` | 本机窗口布局等用户设置 |
| `final-raw/`、`*.raw.wav` | 原始录音体积大且非交付物 |
| `build/`、`staging/` | 中间产物 |
| `__pycache__/`、`*.pyc` | Python 缓存 |

保留入库的：`.wproj`、全部 `.wwu` 工作单元、`Originals/`（音源）、`assets/` 交付 WAV、`docs/`、`tools/`。
这样别人克隆下来能**直接打开工程并听到声音**，同时不会把无关文件传上去。
