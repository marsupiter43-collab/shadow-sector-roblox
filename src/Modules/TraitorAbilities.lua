-- Shadow Sector Traitor Abilities System
-- Manages special traitor abilities and their effects

local Config = require(script.Parent.Parent.Shared:WaitForChild("Config"))
local Enums = require(script.Parent.Parent.Shared:WaitForChild("Enums"))

local TraitorAbilities = {}
TraitorAbilities.__index = TraitorAbilities

-- Initialize Traitor Abilities
function TraitorAbilities.new(traitorPlayer, role)
	local self = setmetatable({}, TraitorAbilities)
	
	self.TraitorPlayer = traitorPlayer
	self.TraitorRole = role
	self.AbilityState = Enums.AbilityState.Ready
	self.LastUsedTime = 0
	self.AbilityConfig = Config.TraitorRoles[role] or {}
	self.ActiveEffects = {}
	self.AffectedPlayers = {}
	
	return self
end

-- Use traitor ability
function TraitorAbilities:UseAbility(targetPlayerId, gameLoop)
	local currentTime = tick()
	
	-- Check if ability is ready
	if self.AbilityState == Enums.AbilityState.Cooldown then
		if currentTime - self.LastUsedTime < self.AbilityConfig.AbilityCooldown then
			return false, "Ability on cooldown"
		end
	end
	
	self.LastUsedTime = currentTime
	self.AbilityState = Enums.AbilityState.Active
	
	-- Execute role-specific ability
	if self.TraitorRole == "Saboteur" then
		self:UseSaboteur(targetPlayerId, gameLoop)
	elseif self.TraitorRole == "Hypnotizer" then
		self:UseHypnotizer(targetPlayerId, gameLoop)
	elseif self.TraitorRole == "Corrupted" then
		self:UseCorrupted(targetPlayerId, gameLoop)
	end
	
	return true
end

-- Saboteur Ability: Create false radar signals
function TraitorAbilities:UseSaboteur(targetPlayerId, gameLoop)
	print("[TraitorAbilities] Saboteur creating false signals for " .. tostring(targetPlayerId))
	
	local duration = self.AbilityConfig.AbilityDuration
	local startTime = tick()
	
	-- Create false radar signals that confuse survivors
	local falseSignals = {
		{Distance = math.random(30, 80), Direction = math.rad(math.random(0, 360))},
		{Distance = math.random(30, 80), Direction = math.rad(math.random(0, 360))},
		{Distance = math.random(30, 80), Direction = math.rad(math.random(0, 360))},
	}
	
	-- Send false radar updates to all survivors
	if gameLoop.RemoteEvents["RadarUpdate"] then
		for _, signal in ipairs(falseSignals) do
			local falseUpdate = {
				PlayerId = targetPlayerId,
				MonsterDistance = signal.Distance,
				MonsterDirection = signal.Direction,
				Accuracy = 0.3, -- Low accuracy indicates false signal
				IsFalseSignal = true,
				Timestamp = tick(),
			}
			gameLoop.RemoteEvents["RadarUpdate"]:FireAllClients(falseUpdate)
		end
	end
	
	-- Effect wears off after duration
	table.insert(self.ActiveEffects, {
		Type = "FalseSignals",
		StartTime = startTime,
		Duration = duration,
		Targets = {targetPlayerId},
	})
	
	-- Start cooldown
	self:StartCooldown()
end

-- Hypnotizer Ability: Distort target's vision
function TraitorAbilities:UseHypnotizer(targetPlayerId, gameLoop)
	print("[TraitorAbilities] Hypnotizer distorting vision for player " .. tostring(targetPlayerId))
	
	local duration = self.AbilityConfig.AbilityDuration
	local startTime = tick()
	
	-- Send distortion effect to target client
	if gameLoop.RemoteEvents["AbilityActivated"] then
		gameLoop.RemoteEvents["AbilityActivated"]:FireClient(
			gameLoop.GamePlayers[targetPlayerId].Player,
			{
				AbilityName = "Distortion",
				Duration = duration,
				Intensity = 0.8,
			}
		)
	end
	
	-- Track affected player
	table.insert(self.AffectedPlayers, targetPlayerId)
	
	-- Effect wears off after duration
	table.insert(self.ActiveEffects, {
		Type = "VisionDistortion",
		StartTime = startTime,
		Duration = duration,
		Targets = {targetPlayerId},
	})
	
	-- Start cooldown
	self:StartCooldown()
end

-- Corrupted Ability: Backstab nearby survivor
function TraitorAbilities:UseCorrupted(targetPlayerId, gameLoop)
	print("[TraitorAbilities] Corrupted backstabbing player " .. tostring(targetPlayerId))
	
	-- Deal heavy damage to target
	gameLoop:DamagePlayer(
		targetPlayerId,
		self.AbilityConfig.Damage,
		Enums.DamageType.Traitor,
		self.TraitorPlayer
	)
	
	-- Fire backstab animation to clients
	if gameLoop.RemoteEvents["AbilityActivated"] then
		gameLoop.RemoteEvents["AbilityActivated"]:FireAllClients({
			AbilityName = "Backstab",
			UserId = self.TraitorPlayer,
			TargetId = targetPlayerId,
			Damage = self.AbilityConfig.Damage,
		})
	end
	
	-- Start cooldown
	self:StartCooldown()
end

-- Sabotage generator
function TraitorAbilities:SabotageGenerator(generatorId, gameLoop)
	print("[TraitorAbilities] Sabotaging generator " .. tostring(generatorId))
	
	-- Disable generator for a short time
	if gameLoop.RemoteEvents["GeneratorActivated"] then
		gameLoop.RemoteEvents["GeneratorActivated"]:FireAllClients({
			GeneratorId = generatorId,
			Action = "Sabotaged",
			Duration = 15, -- seconds
		})
	end
end

-- Reveal location of survivor
function TraitorAbilities:RevealSurvivor(targetPlayerId, gameLoop)
	print("[TraitorAbilities] Revealing survivor location to traitor")
	
	-- Send survivor location to traitor
	if gameLoop.GamePlayers[targetPlayerId] then
		local targetData = gameLoop.GamePlayers[targetPlayerId]
		if gameLoop.RemoteEvents["RadarUpdate"] then
			gameLoop.RemoteEvents["RadarUpdate"]:FireClient(
				gameLoop.GamePlayers[self.TraitorPlayer].Player,
				{
					RevealedTarget = targetPlayerId,
					Position = targetData.Position,
					Name = targetData.Player.Name,
					Timestamp = tick(),
				}
			)
		end
	end
end

-- Start ability cooldown
function TraitorAbilities:StartCooldown()
	self.AbilityState = Enums.AbilityState.Cooldown
	
	-- Notify clients of cooldown
	if self.TraitorPlayer then
		print("[TraitorAbilities] Ability on cooldown for " .. self.AbilityConfig.AbilityCooldown .. " seconds")
	end
end

-- Update active effects
function TraitorAbilities:UpdateEffects(deltaTime)
	local currentTime = tick()
	local expiredEffects = {}
	
	for i, effect in ipairs(self.ActiveEffects) do
		local elapsed = currentTime - effect.StartTime
		
		if elapsed >= effect.Duration then
			-- Effect expired
			table.insert(expiredEffects, i)
		end
	end
	
	-- Remove expired effects (in reverse to preserve indices)
	for i = #expiredEffects, 1, -1 do
		table.remove(self.ActiveEffects, expiredEffects[i])
	end
	
	-- Check if cooldown is over
	if self.AbilityState == Enums.AbilityState.Cooldown then
		if currentTime - self.LastUsedTime >= self.AbilityConfig.AbilityCooldown then
			self.AbilityState = Enums.AbilityState.Ready
		end
	end
end

-- Get ability cooldown remaining time
function TraitorAbilities:GetCooldownRemaining()
	if self.AbilityState == Enums.AbilityState.Ready then
		return 0
	end
	
	local currentTime = tick()
	local elapsed = currentTime - self.LastUsedTime
	local remaining = math.max(0, self.AbilityConfig.AbilityCooldown - elapsed)
	
	return remaining
end

-- Can use ability
function TraitorAbilities:CanUseAbility()
	return self.AbilityState == Enums.AbilityState.Ready
end

-- Traitor sabotage passive ability
function TraitorAbilities:ApplySabotagePassive(itemData)
	if self.TraitorRole == "Saboteur" then
		-- Reduce effectiveness of survivor items
		if itemData.Type == Enums.ItemType.Radar then
			itemData.Accuracy = itemData.Accuracy * 0.7 -- 30% less accurate
		elseif itemData.Type == Enums.ItemType.Flashlight then
			itemData.Range = itemData.Range * 0.8 -- 20% shorter range
		end
	end
end

-- Corrupted passive: Gain strength near monster
function TraitorAbilities:ApplyCorruptedPassive(monsterDistance)
	if self.TraitorRole == "Corrupted" then
		-- Gain damage boost based on proximity to monster
		local damageMultiplier = 1.0
		
		if monsterDistance < 30 then
			damageMultiplier = 1.5 -- 50% damage increase
		elseif monsterDistance < 60 then
			damageMultiplier = 1.25 -- 25% damage increase
		elseif monsterDistance < 100 then
			damageMultiplier = 1.1 -- 10% damage increase
		end
		
		return damageMultiplier
	end
	
	return 1.0
end

-- Hypnotizer passive: See survivor auras
function TraitorAbilities:GetHypnotizerPassive(gamePlayers)
	if self.TraitorRole == "Hypnotizer" then
		local survivorAuras = {}
		
		for userId, playerData in pairs(gamePlayers) do
			if playerData.State == Enums.PlayerState.Alive and userId ~= self.TraitorPlayer then
				-- Hypnotizer can see aura of each survivor
				table.insert(survivorAuras, {
					UserId = userId,
					Position = playerData.Position,
					Health = playerData.Health,
				})
			end
		end
		
		return survivorAuras
	end
	
	return {}
end

-- Reset traitor abilities
function TraitorAbilities:Reset()
	self.AbilityState = Enums.AbilityState.Ready
	self.LastUsedTime = 0
	self.ActiveEffects = {}
	self.AffectedPlayers = {}
end

-- Get traitor ability info
function TraitorAbilities:GetAbilityInfo()
	return {
		Role = self.TraitorRole,
		AbilityName = self.AbilityConfig.Name or self.TraitorRole,
		Description = self.AbilityConfig.Description,
		State = self.AbilityState,
		Cooldown = self:GetCooldownRemaining(),
		CanUse = self:CanUseAbility(),
		ActiveEffects = #self.ActiveEffects,
	}
end

return TraitorAbilities
