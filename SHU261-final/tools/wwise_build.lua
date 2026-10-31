-- Wwise 无界面构建 v5（最终）：参数设置 + Event/Action + SoundBank
-- 依据 WObjects.xml 的官方枚举：
--   RandomOrSequence: 1 = Random
--   3DPosition: 0 = Emitter(3D) / 1 = Emitter with Automation / 2 = Listener with Automation
--   3DSpatialization: 0 = None / 1 = Position
--   PlayMechanismStepOrContinuous: 1 = Step(单发) / 0 = Continuous
--   ActionType: 1 = Play

local LOG = {}
local function log(s) LOG[#LOG + 1] = s; print(s) end

local RET = { ["return"] = { "id", "name", "type", "path" } }

local function call(uri, args, options)
  local ok, r1 = pcall(wa_call, uri, args or {}, options or {})
  if not ok then
    local msg = type(r1) == "table" and r1.message or tostring(r1)
    local argname = (type(r1) == "table" and r1.details and r1.details.argumentName) or ""
    log("[FAIL] " .. uri .. " | " .. tostring(msg) .. " | arg=" .. tostring(argname))
    return nil
  end
  return r1
end

local function findObject(path)
  local r = call("ak.wwise.core.object.get", { waql = "\"" .. path .. "\"" }, RET)
  if r and r["return"] and r["return"][1] then return r["return"][1] end
  return nil
end

local function getProps(id, names)
  local r = call("ak.wwise.core.object.get", { from = { id = { id } } }, { ["return"] = names })
  if r and r["return"] and r["return"][1] then return r["return"][1] end
  return nil
end

local function setObj(objPath, props)
  local spec = { object = objPath }
  for k, v in pairs(props) do spec["@" .. k] = v end
  local r = call("ak.wwise.core.object.set", { objects = { spec } })
  return r ~= nil
end

-- 引用类属性（Attenuation / Target 等）在不同版本里接受 "GUID 字符串" 或 "{id=..}" 表，
-- 这里两种都试一次，返回成功的那种形态。
local function setRef(objPath, prop, guid)
  local attempts = { guid, { id = guid } }
  for _, v in ipairs(attempts) do
    local spec = { object = objPath }
    spec["@" .. prop] = v
    local ok, r = pcall(wa_call, "ak.wwise.core.object.set", { objects = { spec } }, {})
    if ok then
      log("   [引用] " .. prop .. " <- " .. type(v) .. " 形态成功")
      return true
    end
  end
  log("   [引用] " .. prop .. " 两种形态都失败")
  return false
end

---------------------------------------------------------------- 1. 定位
local ROOT = "\\Actor-Mixer Hierarchy\\Default Work Unit\\BedroomAmbience"
local base = findObject(ROOT .. "\\AMB_Bedroom_Base_Loop")
local container = findObject(ROOT .. "\\RND_Bedroom_Spot")
local att = findObject("\\Attenuations\\Default Work Unit\\ATT_Bedroom_Spot")
local evWU = findObject("\\Events\\Default Work Unit")
local sbWU = findObject("\\SoundBanks\\Default Work Unit")
log("base=" .. tostring(base and base.id))
log("container=" .. tostring(container and container.id))
log("attenuation=" .. tostring(att and att.id))
if not (base and container and att and evWU and sbWU) then return "abort" end

------------------------------------------ 2. 基底：无缝循环 + 音量
local ok = setObj(base.id, {
  IsLoopingEnabled = true,
  IsLoopingInfinite = true,
  Volume = -3.0,
})
log("[基底] 循环设置 " .. (ok and "OK" or "FAIL"))

------------------------------------------ 3. Random Container：随机 + 定位
ok = setObj(container.id, {
  RandomOrSequence = 1,              -- Random
  NormalOrShuffle = 1,               -- Standard
  RandomAvoidRepeating = true,
  RandomAvoidRepeatingCount = 3,
  PlayMechanismStepOrContinuous = 1, -- Step（单发）
  PlayMechanismLoop = false,
  PlayMechanismResetPlaylistEachPlay = true,
  ["3DPosition"] = 0,                -- Emitter (3D)
  ["3DSpatialization"] = 1,          -- Position
  EnableAttenuation = true,
  Volume = 0.0,
})
log("[容器] 随机/定位设置 " .. (ok and "OK" or "FAIL"))
setRef(container.id, "Attenuation", att.id)

------------------------------------------ 4. Attenuation 作用距离
ok = setObj(att.id, { RadiusMax = 25.0 })
log("[衰减] RadiusMax=25m " .. (ok and "OK" or "FAIL"))

------------------------------------------ 5. Event + Action
local evSet = call("ak.wwise.core.object.set", {
  objects = {
    {
      object = "\\Events\\Default Work Unit",
      onNameConflict = "merge",
      children = {
        {
          type = "Event", name = "PLAY_Bedroom_Ambience",
          children = {
            { type = "Action", name = "Play_Ambience", ["@ActionType"] = 1 },
          },
        },
        {
          type = "Event", name = "PLAY_Bedroom_Spot",
          children = {
            { type = "Action", name = "Play_Spot", ["@ActionType"] = 1 },
          },
        },
      },
    },
  },
  onNameConflict = "merge",
})
log("[事件] 创建 Event/Action " .. (evSet and "OK" or "FAIL"))

local evAmb = findObject("\\Events\\Default Work Unit\\PLAY_Bedroom_Ambience")
local evSpot = findObject("\\Events\\Default Work Unit\\PLAY_Bedroom_Spot")
log("   PLAY_Bedroom_Ambience=" .. tostring(evAmb and evAmb.id))
log("   PLAY_Bedroom_Spot=" .. tostring(evSpot and evSpot.id))

if evAmb then
  local actAmb = findObject("\\Events\\Default Work Unit\\PLAY_Bedroom_Ambience\\Play_Ambience")
  if actAmb then setRef(actAmb.id, "Target", base.id) end
end
if evSpot then
  local actSpot = findObject("\\Events\\Default Work Unit\\PLAY_Bedroom_Spot\\Play_Spot")
  if actSpot then setRef(actSpot.id, "Target", container.id) end
end

------------------------------------------ 6. SoundBank
local sb = findObject("\\SoundBanks\\Default Work Unit\\Main")
local sbID
if sb then
  sbID = sb.id
  log("[Bank] Main 已存在 " .. tostring(sbID))
else
  local r = call("ak.wwise.core.object.create", {
    parent = sbWU.id, type = "SoundBank", name = "Main",
  }, {})
  sbID = r and r.id
  log("[Bank] 新建 Main " .. tostring(sbID))
end

if sbID and evAmb and evSpot then
  local inc = call("ak.wwise.core.soundbank.setInclusions", {
    soundbank = sbID,
    operation = "replace",
    inclusions = {
      { object = evAmb.id, filter = { "events", "structures", "media" } },
      { object = evSpot.id, filter = { "events", "structures", "media" } },
    },
  })
  log("[Bank] 包含两个事件 " .. (inc and "OK" or "FAIL"))
end

------------------------------------------ 7. 收尾清理：删除空的导入暂存目录
local stagePath = ROOT .. "\\_Import_Stage"
local stage = findObject(stagePath)
if stage then
  local kids = call("ak.wwise.core.object.get", {
    from = { id = { stage.id } },
    transform = { { select = { "children" } } },
  }, RET)
  local n = (kids and kids["return"]) and #kids["return"] or 0
  if n == 0 then
    local del = call("ak.wwise.core.object.delete", { object = stage.id }, {})
    log("[清理] 空目录 _Import_Stage 已删除 " .. (del and "OK" or "FAIL"))
  else
    log("[清理] _Import_Stage 仍有 " .. n .. " 个子对象，保留")
  end
end

------------------------------------------ 8. 保存 + 回读校验
call("ak.wwise.core.project.save", {}, {})

log("--- 回读校验 ---")
local b = getProps(base.id, { "IsLoopingEnabled", "IsLoopingInfinite", "Volume" })
if b then
  log(string.format("  基底层  IsLoopingEnabled=%s  IsLoopingInfinite=%s  Volume=%.1f",
    tostring(b.IsLoopingEnabled), tostring(b.IsLoopingInfinite), b.Volume or 0))
end
local c = getProps(container.id, { "RandomOrSequence", "RandomAvoidRepeating", "3DPosition", "3DSpatialization", "EnableAttenuation", "PlayMechanismStepOrContinuous" })
if c then
  log(string.format("  随机容器 RandomOrSequence=%s AvoidRepeat=%s 3DPosition=%s 3DSpatialization=%s EnableAtten=%s Step/Cont=%s",
    tostring(c.RandomOrSequence), tostring(c.RandomAvoidRepeating), tostring(c["3DPosition"]),
    tostring(c["3DSpatialization"]), tostring(c.EnableAttenuation), tostring(c.PlayMechanismStepOrContinuous)))
end
local a = getProps(att.id, { "RadiusMax" })
if a then log(string.format("  衰减     RadiusMax=%.1f m", a.RadiusMax or 0)) end

local kids = call("ak.wwise.core.object.get", {
  from = { id = { container.id } },
  transform = { { select = { "children" } } },
}, RET)
if kids and kids["return"] then
  log(string.format("  容器子对象 %d 个", #kids["return"]))
end
local evKids = call("ak.wwise.core.object.get", {
  from = { id = { evSpot and evSpot.id or evAmb and evAmb.id } },
  transform = { { select = { "children" } } },
}, { ["return"] = { "id", "name", "type", "ActionType", "Target" } })
if evKids and evKids["return"] then
  for _, o in ipairs(evKids["return"]) do
    log(string.format("  事件子对象: %s | type=%s | ActionType=%s | Target=%s",
      tostring(o.name), tostring(o.type), tostring(o.ActionType),
      type(o.Target) == "table" and tostring(o.Target.name) or tostring(o.Target)))
  end
end

return "v5 done"
