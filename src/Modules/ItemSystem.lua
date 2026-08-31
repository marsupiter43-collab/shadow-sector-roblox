-- Shadow Sector Item System
-- Manages all survivor and traitor items, inventory, and item effects

local Config = require(script.Parent.Parent.Shared:WaitForChild("Config"))
local Enums = require(script.Parent.Parent.Shared:WaitForChild("Enums"))

local ItemSystem = {}
ItemSystem.__index = ItemSystem

-- Initialize Item System
function ItemSystem.new()
	local self = setmetatable({}, ItemSystem)
	
	self.ItemDatabase = {}
	self.PlayerInventories = {}
	self.ActiveItems = {}
	self.ItemEffects = {}
	
	self:InitializeItemDatabase()
	
	return self
end

-- Initialize item database with all available items
function ItemSystem:InitializeItemDatabase()
	self.ItemDatabase = {
		-- Survivor Items
		[Enums.ItemType.Radar] = {
			Name = "Radar Scanner",
			Type = Enums.ItemType.Radar,
			Rarity = Enums.Rarity.Uncommon,
			MaxRange = 100,
			Accuracy = 0.9,
			CooldownTime = 5,
			Description = "Detects the monster's location within range",
			EffectType = "Detection",
			ConsumableCharges = math.huge, -- Reusable
		},
		[Enums.ItemType.Flashlight] = {
			Name = "Flashlight",
			Type = Enums.ItemType.Flashlight,
			Rarity = Enums.Rarity.Common,
			Range = 40,
			Brightness = 1.0,
			Duration = 30,
			Description = "Illuminate dark areas and stun the monster",
			EffectType = "Stun",
			ConsumableCharges = 3,
		},
		[Enums.ItemType.Medkit] = {
			Name = "Medical Kit",
			Type = Enums.ItemType.Medkit,
			Rarity = Enums.Rarity.Common,
			HealAmount = 50,
			Duration = 5,
			Description = "Restore health to yourself or teammates",
			EffectType = "Heal",
			ConsumableCharges = 2,
		},
		[Enums.ItemType.RepairKit] = {
			Name = "Repair Kit",
			Type = Enums.ItemType.RepairKit,
			Rarity = Enums.Rarity.Uncommon,
			RepairSpeed = 1.5,
			Duration = 20,
			Description = "Speed up generator repairs",
			EffectType = "RepairBoost",
			ConsumableCharges = 1,
		},
		[Enums.ItemType.Adrenaline] = {
			Name = "Adrenaline Shot",
			Type = Enums.ItemType.Adrenaline,
			Rarity = Enums.Rarity.Rare,
			SpeedBoost = 1.4,
			Duration = 15,
			Description = "Temporary speed boost to escape danger",
			EffectType = "SpeedBoost",
			ConsumableCharges = 1,
		},
		[Enums.ItemType.Camouflage] = {
			Name = "Camouflage Cloak",
			Type = Enums.ItemType.Camouflage,
			Rarity = Enums.Rarity.Rare,
			Invisibility = 0.7,
			Duration = 20,
			Description = "Become nearly invisible to the monster",
			EffectType = "Invisibility",
			ConsumableCharges = 1,
		},
		[Enums.ItemType.Beacon] = {
			Name = "Distress Beacon",
			Type = Enums.ItemType.Beacon,
			Rarity = Enums.Rarity.Uncommon,
			Range = 150,
			Duration = 30,
			Description = "Call for teammate help in nearby areas",
			EffectType = "Teleport",
			ConsumableCharges = 1,
		},
		[Enums.ItemType.Scanner] = {
			Name = "Advanced Scanner",
			Type = Enums.ItemType.Scanner,
			Rarity = Enums.Rarity.Epic,
			MaxRange = 200,
			Accuracy = 1.0,
			CooldownTime = 3,
			Description = "Ultra-precise monster detection system",
			EffectType = "PreciseDetection",
			ConsumableCharges = math.huge,
		},
		
		-- Traitor Items
		[Enums.ItemType.Poison] = {
			Name = "Poison Vial",
			Type = Enums.ItemType.Poison,
			Rarity = Enums.Rarity.Rare,
			Damage = 30,
			Duration = 10,
			Description = "Poison a survivor's item or drink",
			EffectType = "Poison",
			ConsumableCharges = 1,
		},
		[Enums.ItemType.Mimic] = {
			Name = "Mimic Device",
			Type = Enums.ItemType.Mimic,
			Rarity = Enums.Rarity.Epic,
			Accuracy = 0.8,
			Duration = 15,
			Description = "Impersonate another survivor",
			EffectType = "Disguise",
			ConsumableCharges = 1,
		},
		[Enums.ItemType.Sabotage] = {
			Name = "Sabotage Kit",
			Type = Enums.ItemType.Sabotage,
			Rarity = Enums.Rarity.Uncommon,
			DisableDuration = 20,
			Description = "Temporarily disable survivor equipment",
			EffectType = "EMP",
			ConsumableCharges = 2,
		},
		[Enums.ItemType.Decoy] = {
			Name = "Decoy Grenade",
			Type = Enums.ItemType.Decoy,
			Rarity = Enums.Rarity.Uncommon,
			Duration = 30,
			Description = "Create false radar signals to confuse survivors",
			EffectType = "FalseSignal",
			ConsumableCharges = 2,
		},
	}
end

-- Create player inventory
function ItemSystem:CreateInventory(playerId, maxSlots)
	maxSlots = maxSlots or 5
	
	self.PlayerInventories[playerId] = {
		PlayerId = playerId,
		MaxSlots = maxSlots,
		Items = {},
		CurrentSlots = 0,
		EquippedItem = nil,
	}
	
	return self.PlayerInventories[playerId]
end

-- Add item to player inventory
function ItemSystem:AddItemToInventory(playerId, itemType, quantity)
	quantity = quantity or 1
	
	if not self.PlayerInventories[playerId] then
		self:CreateInventory(playerId)
	end
	
	local inventory = self.PlayerInventories[playerId]
	local itemData = self.ItemDatabase[itemType]
	
	if not itemData then
		return false, "Item type not found"
	end
	
	-- Check if inventory is full
	if inventory.CurrentSlots >= inventory.MaxSlots then
		return false, "Inventory is full"
	end
	
	-- Add item to inventory
	table.insert(inventory.Items, {
		Type = itemType,
		Name = itemData.Name,
		Rarity = itemData.Rarity,
		Data = itemData,
		Charges = itemData.ConsumableCharges,
		AddedTime = tick(),
	})
	
	inventory.CurrentSlots = inventory.CurrentSlots + 1
	
	return true, "Item added successfully"
end

-- Remove item from inventory
function ItemSystem:RemoveItemFromInventory(playerId, itemIndex)
	if not self.PlayerInventories[playerId] then
		return false, "Player inventory not found"
	end
	
	local inventory = self.PlayerInventories[playerId]
	
	if itemIndex < 1 or itemIndex > #inventory.Items then
		return false, "Invalid item index"
	end
	
	table.remove(inventory.Items, itemIndex)
	inventory.CurrentSlots = math.max(0, inventory.CurrentSlots - 1)
	
	if inventory.EquippedItem == itemIndex then
		inventory.EquippedItem = nil
	end
	
	return true, "Item removed successfully"
end

-- Use item from inventory
function ItemSystem:UseItem(playerId, itemIndex, targetPlayerId, gameLoop)
	if not self.PlayerInventories[playerId] then
		return false, "Player inventory not found"
	end
	
	local inventory = self.PlayerInventories[playerId]
	local item = inventory.Items[itemIndex]
	
	if not item then
		return false, "Item not found in inventory"
	end
	
	-- Check if item has charges
	if item.Charges <= 0 then
		return false, "Item has no charges remaining"
	end
	
	-- Execute item effect
	local success = self:ExecuteItemEffect(playerId, item, targetPlayerId, gameLoop)
	
	if success then
		-- Decrease charges
		item.Charges = item.Charges - 1
		
		-- Remove item if out of charges
		if item.Charges <= 0 then
			self:RemoveItemFromInventory(playerId, itemIndex)
		end
		
		return true, "Item used successfully"
	end
	
	return false, "Failed to use item"
end

-- Execute item effect based on type
function ItemSystem:ExecuteItemEffect(playerId, item, targetPlayerId, gameLoop)
	local effectType = item.Data.EffectType
	
	print("[ItemSystem] Executing effect: " .. tostring(effectType) .. " for item: " .. item.Name)
	
	if effectType == "Detection" then
		return self:ApplyDetectionEffect(playerId, item, gameLoop)
	elseif effectType == "Stun" then
		return self:ApplyStunEffect(playerId, item, targetPlayerId, gameLoop)
	elseif effectType == "Heal" then
		return self:ApplyHealEffect(playerId, item, targetPlayerId, gameLoop)
	elseif effectType == "RepairBoost" then
		return self:ApplyRepairBoostEffect(playerId, item, gameLoop)
	elseif effectType == "SpeedBoost" then
		return self:ApplySpeedBoostEffect(playerId, item, gameLoop)
	elseif effectType == "Invisibility" then
		return self:ApplyInvisibilityEffect(playerId, item, gameLoop)
	elseif effectType == "Poison" then
		return self:ApplyPoisonEffect(playerId, item, targetPlayerId, gameLoop)
	elseif effectType == "Disguise" then
		return self:ApplyDisguiseEffect(playerId, item, gameLoop)
	elseif effectType == "EMP" then
		return self:ApplyEMPEffect(playerId, item, targetPlayerId, gameLoop)
	elseif effectType == "FalseSignal" then
		return self:ApplyFalseSignalEffect(playerId, item, gameLoop)
	else
		return false
	end
end

-- Detection effect - reveal monster location
function ItemSystem:ApplyDetectionEffect(playerId, item, gameLoop)
	print("[ItemSystem] Applying Detection effect")
	
	-- Send radar update to player
	if gameLoop.RemoteEvents["RadarUpdate"] then
		gameLoop.RemoteEvents["RadarUpdate"]:FireClient(
			gameLoop.GamePlayers[playerId].Player,
			{
				MonsterDistance = math.random(20, 100),
				MonsterDirection = math.rad(math.random(0, 360)),
				Accuracy = item.Data.Accuracy,
				Timestamp = tick(),
			}
		)
	end
	
	return true
end

-- Stun effect - temporarily stun monster
function ItemSystem:ApplyStunEffect(playerId, item, targetPlayerId, gameLoop)
	print("[ItemSystem] Applying Stun effect")
	
	-- Stun the monster
	if gameLoop.RemoteEvents["MonsterStunned"] then
		gameLoop.RemoteEvents["MonsterStunned"]:FireAllClients({
			Duration = item.Data.Duration,
			Source = playerId,
			Timestamp = tick(),
		})
	end
	
	-- Add stun effect to active effects
	table.insert(self.ItemEffects, {
		Type = "Stun",
		PlayerId = playerId,
		Duration = item.Data.Duration,
		StartTime = tick(),
	})
	
	return true
end

-- Heal effect - restore player health
function ItemSystem:ApplyHealEffect(playerId, item, targetPlayerId, gameLoop)
	print("[ItemSystem] Applying Heal effect")
	
	local target = targetPlayerId or playerId
	
	if gameLoop.GamePlayers[target] then
		gameLoop:HealPlayer(target, item.Data.HealAmount)
		
		if gameLoop.RemoteEvents["PlayerHealed"] then
			gameLoop.RemoteEvents["PlayerHealed"]:FireAllClients({
				PlayerId = target,
				HealAmount = item.Data.HealAmount,
				HealedBy = playerId,
				Timestamp = tick(),
			})
		end
	end
	
	return true
end

-- Repair boost effect - speed up generator repairs
function ItemSystem:ApplyRepairBoostEffect(playerId, item, gameLoop)
	print("[ItemSystem] Applying Repair Boost effect")
	
	table.insert(self.ItemEffects, {
		Type = "RepairBoost",
		PlayerId = playerId,
		Multiplier = item.Data.RepairSpeed,
		Duration = item.Data.Duration,
		StartTime = tick(),
	})
	
	return true
end

-- Speed boost effect - temporary speed increase
function ItemSystem:ApplySpeedBoostEffect(playerId, item, gameLoop)
	print("[ItemSystem] Applying Speed Boost effect")
	
	table.insert(self.ItemEffects, {
		Type = "SpeedBoost",
		PlayerId = playerId,
		Multiplier = item.Data.SpeedBoost,
		Duration = item.Data.Duration,
		StartTime = tick(),
	})
	
	if gameLoop.RemoteEvents["SpeedBoostActive"] then
		gameLoop.RemoteEvents["SpeedBoostActive"]:FireClient(
			gameLoop.GamePlayers[playerId].Player,
			{
				Duration = item.Data.Duration,
				Multiplier = item.Data.SpeedBoost,
			}
		)
	end
	
	return true
end

-- Invisibility effect - make player nearly invisible
function ItemSystem:ApplyInvisibilityEffect(playerId, item, gameLoop)
	print("[ItemSystem] Applying Invisibility effect")
	
	table.insert(self.ItemEffects, {
		Type = "Invisibility",
		PlayerId = playerId,
		Opacity = item.Data.Invisibility,
		Duration = item.Data.Duration,
		StartTime = tick(),
	})
	
	if gameLoop.RemoteEvents["InvisibilityActive"] then
		gameLoop.RemoteEvents["InvisibilityActive"]:FireAllClients({
			PlayerId = playerId,
			Duration = item.Data.Duration,
			Opacity = item.Data.Invisibility,
		})
	end
	
	return true
end

-- Poison effect - traitor ability
function ItemSystem:ApplyPoisonEffect(playerId, item, targetPlayerId, gameLoop)
	print("[ItemSystem] Applying Poison effect to player " .. tostring(targetPlayerId))
	
	table.insert(self.ItemEffects, {
		Type = "Poison",
		PlayerId = targetPlayerId,
		Damage = item.Data.Damage,
		Duration = item.Data.Duration,
		StartTime = tick(),
		SourceTraitor = playerId,
	})
	
	return true
end

-- Disguise effect - traitor ability
function ItemSystem:ApplyDisguiseEffect(playerId, item, gameLoop)
	print("[ItemSystem] Applying Disguise effect")
	
	table.insert(self.ItemEffects, {
		Type = "Disguise",
		PlayerId = playerId,
		Duration = item.Data.Duration,
		StartTime = tick(),
	})
	
	return true
end

-- EMP effect - disable survivor items
function ItemSystem:ApplyEMPEffect(playerId, item, targetPlayerId, gameLoop)
	print("[ItemSystem] Applying EMP effect")
	
	table.insert(self.ItemEffects, {
		Type = "EMP",
		PlayerId = targetPlayerId,
		Duration = item.Data.DisableDuration,
		StartTime = tick(),
		SourceTraitor = playerId,
	})
	
	return true
end

-- False signal effect - traitor ability
function ItemSystem:ApplyFalseSignalEffect(playerId, item, gameLoop)
	print("[ItemSystem] Applying False Signal effect")
	
	-- Create multiple false signals
	for i = 1, 3 do
		if gameLoop.RemoteEvents["RadarUpdate"] then
			gameLoop.RemoteEvents["RadarUpdate"]:FireAllClients({
				MonsterDistance = math.random(30, 150),
				MonsterDirection = math.rad(math.random(0, 360)),
				Accuracy = 0.4, -- Low accuracy
				IsFalseSignal = true,
				Timestamp = tick(),
			})
		end
	end
	
	return true
end

-- Get player inventory
function ItemSystem:GetPlayerInventory(playerId)
	return self.PlayerInventories[playerId]
end

-- Get item info
function ItemSystem:GetItemInfo(itemType)
	return self.ItemDatabase[itemType]
end

-- Check if player has item type
function ItemSystem:HasItemType(playerId, itemType)
	if not self.PlayerInventories[playerId] then
		return false
	end
	
	for _, item in ipairs(self.PlayerInventories[playerId].Items) do
		if item.Type == itemType then
			return true
		end
	end
	
	return false
end

-- Count item charges in inventory
function ItemSystem:CountItemCharges(playerId, itemType)
	if not self.PlayerInventories[playerId] then
		return 0
	end
	
	local totalCharges = 0
	
	for _, item in ipairs(self.PlayerInventories[playerId].Items) do
		if item.Type == itemType then
			totalCharges = totalCharges + item.Charges
		end
	end
	
	return totalCharges
end

-- Update active item effects
function ItemSystem:UpdateEffects(deltaTime)
	local currentTime = tick()
	local expiredEffects = {}
	
	for i, effect in ipairs(self.ItemEffects) do
		local elapsed = currentTime - effect.StartTime
		
		if elapsed >= effect.Duration then
			table.insert(expiredEffects, i)
		end
	end
	
	-- Remove expired effects
	for i = #expiredEffects, 1, -1 do
		table.remove(self.ItemEffects, expiredEffects[i])
	end
end

-- Clear player inventory
function ItemSystem:ClearInventory(playerId)
	if self.PlayerInventories[playerId] then
		self.PlayerInventories[playerId].Items = {}
		self.PlayerInventories[playerId].CurrentSlots = 0
		self.PlayerInventories[playerId].EquippedItem = nil
	end
end

return ItemSystem
