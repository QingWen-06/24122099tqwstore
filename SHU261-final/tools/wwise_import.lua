-- Wwise 无界面导入：把 build/assets 里的随机声导入并整理进 Random Container
-- 用法：
--   WwiseConsole execute-lua-script wwise_import.lua --project X.wproj --no-color
-- 幂等：已存在的同名声音不会重复导入，已在容器里的不会重复移动。

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

local ROOT = "\\Actor-Mixer Hierarchy\\Default Work Unit\\BedroomAmbience"
local STAGE = ROOT .. "\\_Import_Stage"
local ASSETS = "E:\\dpsk\\build\\assets\\"

-- 需要作为"随机间断声"进 Random Container 的资产
local SPOT = {
  "KEY_single_01", "KEY_single_02", "KEY_single_03", "KEY_single_04", "KEY_single_05",
  "KEY_typing_01", "KEY_typing_02", "KEY_typing_03",
  "CHR_move_01", "CHR_move_02", "CHR_move_03", "CHR_move_04",
}

local root = findObject(ROOT)
local stage = findObject(STAGE)
local container = findObject(ROOT .. "\\RND_Bedroom_Spot")
if not (root and stage and container) then
  log("abort: 缺少目录或容器（root=" .. tostring(root) .. " stage=" .. tostring(stage) ..
      " container=" .. tostring(container) .. "）")
  return "abort"
end

-- 1) 逐个导入尚未存在的资产（audio.import 的 useExisting 会复用同名 Originals）
local imports = {}
for _, name in ipairs(SPOT) do
  if not findObject(STAGE .. "\\" .. name) and not findObject(ROOT .. "\\" .. name)
     and not findObject(ROOT .. "\\RND_Bedroom_Spot\\" .. name) then
    imports[#imports + 1] = {
      audioFile = ASSETS .. name .. ".wav",
      objectPath = name,
      objectType = "Sound SFX",
    }
  end
end

if #imports > 0 then
  local r = call("ak.wwise.core.audio.import", {
    importOperation = "useExisting",
    ["default"] = { importLanguage = "SFX", importLocation = STAGE },
    imports = imports,
  }, RET)
  log("[导入] " .. tostring(r and #(r.files or {}) or 0) .. " 个新文件")
else
  log("[导入] 无需导入，全部已存在")
end

-- 2) 把暂存区里的 Sound 全部搬进容器
local r = call("ak.wwise.core.object.get", {
  from = { id = { stage.id } },
  transform = { { select = { "children" } } },
}, RET)

local moved, kept = 0, 0
if r and r["return"] then
  for _, o in ipairs(r["return"]) do
    if o.type == "Sound" then
      if findObject(ROOT .. "\\RND_Bedroom_Spot\\" .. o.name) then
        kept = kept + 1
      else
        local mv = call("ak.wwise.core.object.move",
          { object = o.id, parent = container.id, onNameConflict = "rename" }, {})
        if mv then
          moved = moved + 1
          log("   [移入] " .. tostring(mv.name))
        end
      end
    end
  end
end
log(string.format("[整理] 移入 %d 个，已在容器内 %d 个", moved, kept))

-- 3) 报告容器当前内容
local kids = call("ak.wwise.core.object.get", {
  from = { id = { container.id } },
  transform = { { select = { "children" } } },
}, { ["return"] = { "id", "name", "type" } })
if kids and kids["return"] then
  log("[容器] RND_Bedroom_Spot 现有 " .. #kids["return"] .. " 个子对象:")
  for _, o in ipairs(kids["return"]) do
    log("   " .. tostring(o.type) .. " | " .. tostring(o.name))
  end
end

call("ak.wwise.core.project.save", {}, {})
return "import done"
