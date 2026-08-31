-- Shadow Sector Network Protocol
-- Defines all network communication structures and validation

local Enums = require(script.Parent:WaitForChild("Enums"))
local Config = require(script.Parent:WaitForChild("Config"))

local NetworkProtocol = {}

-- Message Types
NetworkProtocol.MessageType = {
	PlayerUpdate = "PlayerUpdate",
	MonsterUpdate = "MonsterUpdate",
	ItemSync = "ItemSync",
	AbilityUse = "AbilityUse",
	GameStateSync = "GameStateSync",
	DamageEvent = "DamageEvent",
	ChatMessage = "ChatMessage",
}

-- Player Update Packet Structure
function NetworkProtocol.CreatePlayerUpdatePacket(player, position, velocity, state)
	return {
		MessageType = NetworkProtocol.MessageType.PlayerUpdate,
		PlayerId = player.UserId,
		Position = position,
		Velocity = velocity,
		State = state,
		Timestamp = tick(),
	}
end

-- Validate Player Update
function NetworkProtocol.ValidatePlayerUpdate(packet, lastPosition)
	if not packet.PlayerId or not packet.Position or not packet.Timestamp then
		return false, "Missing required fields"
	end
	
	-- Anti-cheat: Check speed
	if lastPosition then
		local distance = (packet.Position - lastPosition).Magnitude
		local deltaTime = math.max(0.01, packet.Timestamp - (packet.LastTimestamp or tick()))
		local speed = distance / deltaTime
		
		if speed > Config.AntiCheat.MaxSpeed then
			return false, "Speed exceeding maximum: " .. tostring(speed)
		end
	end
	
	return true
end

-- Monster Update Packet Structure
function NetworkProtocol.CreateMonsterUpdatePacket(monster)
	return {
		MessageType = NetworkProtocol.MessageType.MonsterUpdate,
		Position = monster.Position,
		Velocity = monster.Velocity,
		State = monster.CurrentState,
		TargetId = monster.TargetPlayer and monster.TargetPlayer.UserId or nil,
		Health = monster.Health,
		Timestamp = tick(),
	}
end

-- Item Sync Packet Structure
function NetworkProtocol.CreateItemSyncPacket(item, action, playerId)
	return {
		MessageType = NetworkProtocol.MessageType.ItemSync,
		ItemId = item.Id,
		ItemType = item.Type,
		Action = action, -- "picked", "dropped", "used"
		PlayerId = playerId,
		Position = item.Position,
		Timestamp = tick(),
	}
end

-- Ability Use Packet Structure
function NetworkProtocol.CreateAbilityUsePacket(playerId, abilityName, targetPlayerId)
	return {
		MessageType = NetworkProtocol.MessageType.AbilityUse,
		UserId = playerId,
		AbilityName = abilityName,
		TargetId = targetPlayerId,
		Timestamp = tick(),
	}
end

-- Validate Ability Use
function NetworkProtocol.ValidateAbilityUse(packet, player)
	if packet.UserId ~= player.UserId then
		return false, "User ID mismatch"
	end
	
	if not packet.AbilityName then
		return false, "Missing ability name"
	end
	
	return true
end

-- Game State Sync Packet Structure
function NetworkProtocol.CreateGameStateSyncPacket(gameState, players, monster)
	return {
		MessageType = NetworkProtocol.MessageType.GameStateSync,
		GameState = gameState,
		PlayerCount = #players,
		PlayerStates = {}, -- Populated with player data
		MonsterHealth = monster.Health,
		ElapsedTime = gameState.ElapsedTime,
		Timestamp = tick(),
	}
end

-- Damage Event Packet Structure
function NetworkProtocol.CreateDamageEventPacket(victimId, damageAmount, damageType, sourceId)
	return {
		MessageType = NetworkProtocol.MessageType.DamageEvent,
		VictimId = victimId,
		DamageAmount = damageAmount,
		DamageType = damageType, -- Monster, Traitor, Environment, Fall
		SourceId = sourceId,
		Timestamp = tick(),
	}
end

-- Validate Damage Event
function NetworkProtocol.ValidateDamageEvent(packet)
	if not packet.VictimId or not packet.DamageAmount or not packet.DamageType then
		return false, "Missing required damage fields"
	end
	
	if packet.DamageAmount < 0 or packet.DamageAmount > 100 then
		return false, "Invalid damage amount"
	end
	
	return true
end

-- Chat Message Packet Structure
function NetworkProtocol.CreateChatMessagePacket(playerId, playerName, message)
	return {
		MessageType = NetworkProtocol.MessageType.ChatMessage,
		PlayerId = playerId,
		PlayerName = playerName,
		Message = message,
		Timestamp = tick(),
	}
end

-- Validate Chat Message
function NetworkProtocol.ValidateChatMessage(packet)
	if not packet.PlayerId or not packet.Message then
		return false, "Missing required fields"
	end
	
	if #packet.Message > 500 then
		return false, "Message too long"
	end
	
	-- Filter bad words (basic implementation)
	if NetworkProtocol.ContainsBadWords(packet.Message) then
		return false, "Message contains inappropriate content"
	end
	
	return true
end

-- Bad Words Filter (basic)
function NetworkProtocol.ContainsBadWords(message)
	local badWords = {"badword1", "badword2"} -- Add actual filter words
	local lowerMessage = string.lower(message)
	
	for _, word in ipairs(badWords) do
		if string.find(lowerMessage, word) then
			return true
		end
	end
	
	return false
end

-- Radar Update Packet Structure
function NetworkProtocol.CreateRadarUpdatePacket(playerId, monsterDistance, monsterDirection, accuracy)
	return {
		MessageType = Enums.NetworkEvent.RadarUpdate,
		PlayerId = playerId,
		MonsterDistance = monsterDistance,
		MonsterDirection = monsterDirection, -- Angle or Vector
		Accuracy = accuracy or 1.0, -- 0-1, how accurate the reading is
		Timestamp = tick(),
	}
end

-- Health Update Packet Structure
function NetworkProtocol.CreateHealthUpdatePacket(playerId, health, maxHealth)
	return {
		MessageType = Enums.NetworkEvent.HealthUpdate,
		PlayerId = playerId,
		Health = health,
		MaxHealth = maxHealth,
		Timestamp = tick(),
	}
end

-- Stamina Update Packet Structure
function NetworkProtocol.CreateStaminaUpdatePacket(playerId, stamina, maxStamina)
	return {
		MessageType = Enums.NetworkEvent.StaminaUpdate,
		PlayerId = playerId,
		Stamina = stamina,
		MaxStamina = maxStamina,
		Timestamp = tick(),
	}
end

-- Anti-Cheat Validation Suite
function NetworkProtocol.ValidatePacket(packet, context)
	if not packet or not packet.MessageType then
		return false, "Invalid packet structure"
	end
	
	-- Timestamp validation (packet shouldn't be too old)
	local timeDiff = tick() - packet.Timestamp
	if timeDiff > 5 then -- 5 second threshold
		return false, "Packet too old"
	end
	
	-- Type-specific validation
	if packet.MessageType == NetworkProtocol.MessageType.PlayerUpdate then
		return NetworkProtocol.ValidatePlayerUpdate(packet, context.lastPosition)
	elseif packet.MessageType == NetworkProtocol.MessageType.AbilityUse then
		return NetworkProtocol.ValidateAbilityUse(packet, context.player)
	elseif packet.MessageType == NetworkProtocol.MessageType.DamageEvent then
		return NetworkProtocol.ValidateDamageEvent(packet)
	elseif packet.MessageType == NetworkProtocol.MessageType.ChatMessage then
		return NetworkProtocol.ValidateChatMessage(packet)
	end
	
	return true
end

-- Compression for large packets (basic)
function NetworkProtocol.CompressPacket(packet)
	-- TODO: Implement packet compression for bandwidth optimization
	return packet
end

-- Decompression
function NetworkProtocol.DecompressPacket(compressedData)
	-- TODO: Implement packet decompression
	return compressedData
end

return NetworkProtocol
