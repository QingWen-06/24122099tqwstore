-- Wwise 脚手架：在全新工程里建立目录、Random Container、Attenuation，并导入整理全部资产
-- 幂等：已存在的对象直接复用，已在容器内的声音不重复移动。
-- 用法：
--   WwiseConsole execute-lua-script wwise_scaffold.lua --project X.wproj --no-color
-- 之后执行 wwise_build.lua 设置参数/Event/SoundBank。

local function log(s) print(s) end

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

local function ensureFolder(parentID, name, fullPath)
  local e = findObject(fullPath)
  if e then
    log("[存在] " .. fullPath)
    return e.id
  end
  local r = call("ak.wwise.core.object.create",
    { parent = parentID, type = "Folder", name = name, onNameConflict = "merge" }, {})
  if r then
    log("[新建] " .. fullPath .. " " .. tostring(r.id))
    return r.id
  end
  return nil
end

local function childrenOf(id)
  local r = call("ak.wwise.core.object.get", {
    from = { id = { id } },
    transform = { { select = { "children" } } },
  }, RET)
  return (r and r["return"]) or {}
end

---------------------------------------------------------------- 1. 工作单元
local amWU = findObject("\\Actor-Mixer Hierarchy\\Default Work Unit")
local atWU = findObject("\\Attenuations\\Default Work Unit")
if not (amWU and atWU) then
  return "abort: work unit 找不到"
end
log("AM=" .. amWU.id .. "  AT=" .. atWU.id)

------------------------------------------------------------ 2. 目录
local ROOT = "\\Actor-Mixer Hierarchy\\Default Work Unit\\BedroomAmbience"
local STAGE = ROOT .. "\\_Import_Stage"
local rootID = ensureFolder(amWU.id, "BedroomAmbience", ROOT)
local stageID = ensureFolder(rootID, "_Import_Stage", STAGE)
if not (rootID and stageID) then return "abort: 目录" end

------------------------------------------------ 3. Random Container
local rndPath = ROOT .. "\\RND_Bedroom_Spot"
local rnd = findObject(rndPath)
local rndID
if rnd then
  rndID = rnd.id
  log("[存在] RND_Bedroom_Spot " .. rndID)
else
  local r = call("ak.wwise.core.object.create",
    { parent = rootID, type = "RandomSequenceContainer", name = "RND_Bedroom_Spot" }, {})
  rndID = r and r.id
  log("[新建] RND_Bedroom_Spot " .. tostring(rndID))
end
if not rndID then return "abort: 容器" end

--------------------------------------------------- 4. Attenuation
local attPath = "\\Attenuations\\Default Work Unit\\ATT_Bedroom_Spot"
local att = findObject(attPath)
local attID
if att then
  attID = att.id
  log("[存在] ATT_Bedroom_Spot " .. attID)
else
  local r = call("ak.wwise.core.object.create",
    { parent = atWU.id, type = "Attenuation", name = "ATT_Bedroom_Spot" }, {})
  attID = r and r.id
  log("[新建] ATT_Bedroom_Spot " .. tostring(attID))
end

------------------------------------------------------------ 5. 导入
local ASSETS = "E:\\dpsk\\build\\assets\\"
local BASE = "AMB_Bedroom_Base_Loop"
local SPOT = {
  "KEY_single_01", "KEY_single_02", "KEY_single_03", "KEY_single_04", "KEY_single_05",
  "KEY_typing_01", "KEY_typing_02", "KEY_typing_03",
  "CHR_move_01", "CHR_move_02", "CHR_move_03", "CHR_move_04",
}

-- 基底导入到 ROOT
if not findObject(ROOT .. "\\" .. BASE) and not findObject(STAGE .. "\\" .. BASE) then
  local r = call("ak.wwise.core.audio.import", {
    importOperation = "useExisting",
    ["default"] = { importLanguage = "SFX", importLocation = ROOT },
    imports = { { audioFile = ASSETS .. BASE .. ".wav", objectPath = BASE, objectType = "Sound SFX" } },
  }, RET)
  log("[导入基底] " .. tostring(r and #(r.files or {}) or 0) .. " 个文件")
else
  log("[导入基底] 已存在，跳过")
end

-- 随机声导入到 STAGE
local imports = {}
for _, name in ipairs(SPOT) do
  if not findObject(STAGE .. "\\" .. name) and not findObject(rndPath .. "\\" .. name) then
    imports[#imports + 1] = {
      audioFile = ASSETS .. name .. ".wav", objectPath = name, objectType = "Sound SFX",
    }
  end
end
if #imports > 0 then
  local r = call("ak.wwise.core.audio.import", {
    importOperation = "useExisting",
    ["default"] = { importLanguage = "SFX", importLocation = STAGE },
    imports = imports,
  }, RET)
  log("[导入随机声] " .. tostring(r and #(r.files or {}) or 0) .. " 个文件")
else
  log("[导入随机声] 无需导入")
end

-------------------------------------------------- 6. 整理：把 STAGE 里的声音搬进容器
local moved = 0
for _, o in ipairs(childrenOf(stageID)) do
  if o.type == "Sound" and not findObject(rndPath .. "\\" .. o.name) then
    local mv = call("ak.wwise.core.object.move",
      { object = o.id, parent = rndID, onNameConflict = "rename" }, {})
    if mv then
      moved = moved + 1
      log("   [移入] " .. tostring(mv.name))
    end
  end
end
log("[整理] 移入 " .. moved .. " 个")

-------------------------------------------------- 7. 报告
log("--- BedroomAmbience 子对象 ---")
for _, o in ipairs(childrenOf(rootID)) do
  log("   " .. tostring(o.type) .. " | " .. tostring(o.name))
end
local kids = childrenOf(rndID)
log("--- RND_Bedroom_Spot 子对象: " .. #kids .. " 个 ---")
for _, o in ipairs(kids) do
  log("   " .. tostring(o.name))
end

call("ak.wwise.core.project.save", {}, {})
return "scaffold done"
