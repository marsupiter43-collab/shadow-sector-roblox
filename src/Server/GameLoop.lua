-- Shadow Sector Main Game Loop
-- Server-side core game logic and state management

local Config = require(script.Parent.Parent.Shared:WaitForChild("Config"))
local Enums = require(script.Parent.Parent.Shared:WaitForChild("Enums"))
local NetworkProtocol = require(script.Parent.Parent.Shared:WaitForChild("NetworkProtocol"))

local GameLoop = {}
GameLoop.__index = GameLoop

-- Initialize Game Loop
function GameLoop.new()
	local self = setmetatable({}, GameLoop)
	
	self.GameState = Enums.GameState.Lobby
	self.Players = {}
	self.GamePlayers = {} -- Players in current game
	self.TraitorPlayer = nil
	self.MonsterAI = nil
	self.ActiveItems = {}
	self.GameEvents = {}
	self.ElapsedTime = 0
	self.MatchStartTime = 0
	self.GeneratorsActivated = 0
	self.EscapedPlayers = {}
	self.DeadPlayers = {}
	self.WinCondition = nil
	
	-- Network connections
	self.RemoteEvents = {}
	self.RemoteFunctions = {}
	
	self:InitializeNetworking()
	
	return self
end

-- Initialize networking infrastructure
function GameLoop:InitializeNetworking()
	local ReplicatedStorage = game:GetService("ReplicatedStorage")
	
	-- Create or get RemoteEvent folder
	local RemoteEventsFolder = ReplicatedStorage:FindFirstChild("RemoteEvents")
	if not RemoteEventsFolder then
		RemoteEventsFolder = Instance.new("Folder")
		RemoteEventsFolder.Name = "RemoteEvents"
		RemoteEventsFolder.Parent = ReplicatedStorage
	end
	
	-- Create RemoteEvents for different game events
	local eventNames = {
		"PlayerJoined",
		"PlayerLeft",
		"GameStarted",
		"GameStateChanged",
		"PlayerUpdate",
		"MonsterUpdate",
		"DamageEvent",
		"ItemSync",
		"AbilityActivated",
		"RadarUpdate",
		"HealthUpdate",
		"ChatMessage",
		"GameEnded",
	}
	
	for _, eventName in ipairs(eventNames) do
		if not RemoteEventsFolder:FindFirstChild(eventName) then
			local remoteEvent = Instance.new("RemoteEvent")
			remoteEvent.Name = eventName
			remoteEvent.Parent = RemoteEventsFolder
			self.RemoteEvents[eventName] = remoteEvent
		else
			self.RemoteEvents[eventName] = RemoteEventsFolder:FindFirstChild(eventName)
		end
	end
	
	-- Setup event listeners
	self:SetupEventListeners()
end

-- Setup event listeners
function GameLoop:SetupEventListeners()
	local Players = game:GetService("Players")
	
	-- Player joined
	Players.PlayerAdded:Connect(function(player)
		self:OnPlayerJoined(player)
	end)
	
	-- Player leaving
	Players.PlayerRemoving:Connect(function(player)
		self:OnPlayerLeft(player)
	end)
end

-- Called when a player joins
function GameLoop:OnPlayerJoined(player)
	print("[GameLoop] Player joined: " .. player.Name)
	
	self.Players[player.UserId] = {
		Player = player,
		State = Enums.PlayerState.Alive,
		Health = Config.Survivor.Health,
		Stamina = Config.Survivor.StaminaMax,
		Inventory = {},
		Role = Enums.TraitorRole.None,
		JoinTime = tick(),
	}
	
	-- Fire joined event
	if self.RemoteEvents["PlayerJoined"] then
		self.RemoteEvents["PlayerJoined"]:FireClient(player, player.UserId, player.Name)
	end
	
	-- Check if we can start matchmaking
	self:CheckMatchmakingConditions()
end

-- Called when a player leaves
function GameLoop:OnPlayerLeft(player)
	print("[GameLoop] Player left: " .. player.Name)
	
	-- Remove from players list
	if self.Players[player.UserId] then
		self.Players[player.UserId] = nil
	end
	
	-- If in active game, handle elimination
	if self.GameState == Enums.GameState.InProgress then
		if self.GamePlayers[player.UserId] then
			self:EliminatePlayer(player.UserId, "Left the game")
		end
	end
	
	-- Fire left event
	if self.RemoteEvents["PlayerLeft"] then
		self.RemoteEvents["PlayerLeft"]:FireAllClients(player.UserId, player.Name)
	end
	
	-- Check if game should end
	self:CheckGameEndConditions()
end

-- Check if matchmaking can start
function GameLoop:CheckMatchmakingConditions()
	local playerCount = 0
	for _, _ in pairs(self.Players) do
		playerCount = playerCount + 1
	end
	
	if self.GameState == Enums.GameState.Lobby and playerCount >= Config.GameSettings.MinPlayers then
		print("[GameLoop] Starting matchmaking with " .. playerCount .. " players")
		self:StartMatchmaking()
	end
end

-- Start matchmaking process
function GameLoop:StartMatchmaking()
	self.GameState = Enums.GameState.Loading
	
	-- Fire game state change
	if self.RemoteEvents["GameStateChanged"] then
		self.RemoteEvents["GameStateChanged"]:FireAllClients(self.GameState)
	end
	
	-- Wait a bit for loading
	wait(2)
	
	-- Assign players to game
	self:AssignGamePlayers()
	
	-- Assign roles
	self:AssignRoles()
	
	-- Start game
	self:StartGame()
end

-- Assign players to game
function GameLoop:AssignGamePlayers()
	local assignedCount = 0
	local maxPlayers = Config.GameSettings.MaxPlayers
	
	for userId, playerData in pairs(self.Players) do
		if assignedCount < maxPlayers then
			self.GamePlayers[userId] = playerData
			assignedCount = assignedCount + 1
		end
	end
	
	print("[GameLoop] Assigned " .. assignedCount .. " players to game")
end

-- Assign traitor role
function GameLoop:AssignRoles()
	local playerList = {}
	for userId, playerData in pairs(self.GamePlayers) do
		table.insert(playerList, {UserId = userId, PlayerData = playerData})
	end
	
	-- Randomly select traitor
	if #playerList > 0 then
		local traitorIndex = math.random(1, #playerList)
		local traitorUserId = playerList[traitorIndex].UserId
		self.TraitorPlayer = traitorUserId
		
		-- Assign traitor role
		local roles = {"Saboteur", "Hypnotizer", "Corrupted"}
		local selectedRole = roles[math.random(1, #roles)]
		self.GamePlayers[traitorUserId].Role = selectedRole
		
		print("[GameLoop] Assigned traitor role '" .. selectedRole .. "' to player " .. traitorUserId)
		
		-- Notify traitor privately
		local traitorPlayer = self.GamePlayers[traitorUserId].Player
		if self.RemoteEvents["TraitorAssigned"] then
			self.RemoteEvents["TraitorAssigned"]:FireClient(traitorPlayer, selectedRole)
		end
	end
end

-- Start the actual game
function GameLoop:StartGame()
	self.GameState = Enums.GameState.InProgress
	self.MatchStartTime = tick()
	self.ElapsedTime = 0
	self.GeneratorsActivated = 0
	
	print("[GameLoop] Game started with " .. self:GetPlayerCount() .. " players")
	
	-- Fire game started event
	if self.RemoteEvents["GameStarted"] then
		self.RemoteEvents["GameStarted"]:FireAllClients(self.MatchStartTime)
	end
	
	-- Start game loop
	self:RunGameLoop()
end

-- Main game loop
function GameLoop:RunGameLoop()
	while self.GameState == Enums.GameState.InProgress do
		local deltaTime = wait(0.1) -- 100ms tick rate
		
		self.ElapsedTime = tick() - self.MatchStartTime
		
		-- Update game logic
		self:UpdatePlayers(deltaTime)
		self:UpdateMonster(deltaTime)
		self:UpdateItems(deltaTime)
		
		-- Check win conditions
		self:CheckGameEndConditions()
		
		-- Broadcast updates to clients
		self:SyncGameState()
	end
end

-- Update player states
function GameLoop:UpdatePlayers(deltaTime)
	for userId, playerData in pairs(self.GamePlayers) do
		if playerData.State == Enums.PlayerState.Alive then
			-- Regenerate stamina
			if playerData.Stamina < Config.Survivor.StaminaMax then
				playerData.Stamina = math.min(playerData.Stamina + Config.Survivor.StaminaRegenRate * deltaTime, Config.Survivor.StaminaMax)
			end
			
			-- Regenerate health slowly
			if playerData.Health < Config.Survivor.Health then
				playerData.Health = math.min(playerData.Health + 2 * deltaTime, Config.Survivor.Health)
			end
		end
	end
end

-- Update monster AI
function GameLoop:UpdateMonster(deltaTime)
	if not self.MonsterAI then
		return
	end
	
	-- Monster AI logic would be implemented in MonsterAI.lua
	-- This is a placeholder for state synchronization
	self.MonsterAI:Update(deltaTime, self.GamePlayers)
end

-- Update active items
function GameLoop:UpdateItems(deltaTime)
	for itemId, itemData in pairs(self.ActiveItems) do
		-- Update item states (battery drain, etc.)
		if itemData.Type == Enums.ItemType.Flashlight then
			itemData.Battery = math.max(0, itemData.Battery - Config.Flashlight.BatteryDrainRate * deltaTime)
		elseif itemData.Type == Enums.ItemType.Radar then
			itemData.Battery = math.max(0, itemData.Battery - Config.Radar.BatteryDrainRate * deltaTime)
		end
	end
end

-- Sync game state to clients
function GameLoop:SyncGameState()
	local gameStatePacket = NetworkProtocol.CreateGameStateSyncPacket(
		self.GameState,
		self.GamePlayers,
		self.MonsterAI
	)
	
	if self.RemoteEvents["GameStateChanged"] then
		self.RemoteEvents["GameStateChanged"]:FireAllClients(gameStatePacket)
	end
end

-- Handle player damage
function GameLoop:DamagePlayer(playerId, damageAmount, damageType, sourceId)
	local playerData = self.GamePlayers[playerId]
	if not playerData then return end
	
	if playerData.State ~= Enums.PlayerState.Alive then return end
	
	playerData.Health = math.max(0, playerData.Health - damageAmount)
	
	-- Fire damage event
	local damagePacket = NetworkProtocol.CreateDamageEventPacket(playerId, damageAmount, damageType, sourceId)
	if self.RemoteEvents["DamageEvent"] then
		self.RemoteEvents["DamageEvent"]:FireAllClients(damagePacket)
	end
	
	-- Check if player died
	if playerData.Health <= 0 then
		self:KillPlayer(playerId, damageType, sourceId)
	end
end

-- Kill player
function GameLoop:KillPlayer(playerId, deathType, sourceId)
	local playerData = self.GamePlayers[playerId]
	if not playerData then return end
	
	playerData.State = Enums.PlayerState.Dead
	table.insert(self.DeadPlayers, {UserId = playerId, DeathType = deathType, SourceId = sourceId, Time = tick()})
	
	print("[GameLoop] Player " .. playerId .. " killed by " .. tostring(deathType))
	
	-- Fire kill event
	if self.RemoteEvents["DamageEvent"] then
		self.RemoteEvents["DamageEvent"]:FireAllClients({
			MessageType = Enums.NetworkEvent.PlayerDied,
			PlayerId = playerId,
			DeathType = deathType,
		})
	end
end

-- Eliminate player (left game, disconnected, etc.)
function GameLoop:EliminatePlayer(playerId, reason)
	local playerData = self.GamePlayers[playerId]
	if not playerData then return end
	
	playerData.State = Enums.PlayerState.Eliminated
	print("[GameLoop] Player " .. playerId .. " eliminated: " .. reason)
end

-- Activate generator
function GameLoop:ActivateGenerator()
	self.GeneratorsActivated = self.GeneratorsActivated + 1
	
	print("[GameLoop] Generator activated! (" .. self.GeneratorsActivated .. "/" .. Config.Generator.RequiredGenerators .. ")")
	
	-- Fire event
	if self.RemoteEvents["GeneratorActivated"] then
		self.RemoteEvents["GeneratorActivated"]:FireAllClients(self.GeneratorsActivated)
	end
	
	-- Check if all generators activated
	if self.GeneratorsActivated >= Config.Generator.RequiredGenerators then
		self:AllGeneratorsActivated()
	end
end

-- Called when all generators are activated
function GameLoop:AllGeneratorsActivated()
	print("[GameLoop] All generators activated! Escape now available!")
end

-- Player escaped
function GameLoop:PlayerEscaped(playerId)
	local playerData = self.GamePlayers[playerId]
	if not playerData then return end
	
	playerData.State = Enums.PlayerState.Escaped
	table.insert(self.EscapedPlayers, playerId)
	
	print("[GameLoop] Player " .. playerId .. " escaped!")
	
	-- Fire escape event
	if self.RemoteEvents["DamageEvent"] then
		self.RemoteEvents["DamageEvent"]:FireAllClients({
			MessageType = Enums.GameEvent.PlayerEscaped,
			PlayerId = playerId,
		})
	end
end

-- Check game end conditions
function GameLoop:CheckGameEndConditions()
	local aliveCount = 0
	local escapedCount = 0
	
	for _, playerData in pairs(self.GamePlayers) do
		if playerData.State == Enums.PlayerState.Alive then
			aliveCount = aliveCount + 1
		elseif playerData.State == Enums.PlayerState.Escaped then
			escapedCount = escapedCount + 1
		end
	end
	
	-- All survivors dead or escaped
	if aliveCount == 0 and escapedCount >= 0 then
		self:EndGame()
	end
	
	-- Time expired
	if self.ElapsedTime > Config.GameSettings.GameDuration then
		self:EndGame()
	end
end

-- End the game
function GameLoop:EndGame()
	if self.GameState == Enums.GameState.Finished then
		return
	end
	
	self.GameState = Enums.GameState.Finished
	
	-- Determine winner
	local survivors = {}
	local traitorWon = false
	
	for userId, playerData in pairs(self.GamePlayers) do
		if playerData.State == Enums.PlayerState.Escaped then
			table.insert(survivors, userId)
		end
	end
	
	print("[GameLoop] Game ended! Survivors: " .. #survivors)
	
	-- Fire game ended event
	if self.RemoteEvents["GameEnded"] then
		self.RemoteEvents["GameEnded"]:FireAllClients({
			Survivors = survivors,
			TraitorId = self.TraitorPlayer,
			ElapsedTime = self.ElapsedTime,
		})
	end
	
	-- Reset for next game
	self:ResetGame()
end

-- Reset game for next round
function GameLoop:ResetGame()
	wait(5) -- Wait for clients to show results
	
	self.GameState = Enums.GameState.Lobby
	self.GamePlayers = {}
	self.TraitorPlayer = nil
	self.ElapsedTime = 0
	self.GeneratorsActivated = 0
	self.EscapedPlayers = {}
	self.DeadPlayers = {}
	
	self:CheckMatchmakingConditions()
end

-- Get current player count
function GameLoop:GetPlayerCount()
	local count = 0
	for _, _ in pairs(self.GamePlayers) do
		count = count + 1
	end
	return count
end

return GameLoop
