-- Shadow Sector Shared Constants and Enums
-- Type definitions and constant values

local Enums = {}

-- Game States
Enums.GameState = {
	Lobby = "Lobby",
	Loading = "Loading",
	InProgress = "InProgress",
	Finished = "Finished",
	ResultScreen = "ResultScreen",
}

-- Player States
Enums.PlayerState = {
	Alive = "Alive",
	Injured = "Injured",
	Dead = "Dead",
	Escaped = "Escaped",
	Eliminated = "Eliminated",
}

-- Traitor Roles
Enums.TraitorRole = {
	None = "None",
	Saboteur = "Saboteur",
	Hypnotizer = "Hypnotizer",
	Corrupted = "Corrupted",
}

-- Item Types
Enums.ItemType = {
	Radar = "Radar",
	Flashlight = "Flashlight",
	FirstAidKit = "FirstAidKit",
	Generator = "Generator",
	Battery = "Battery",
}

-- Ability States
Enums.AbilityState = {
	Ready = "Ready",
	Active = "Active",
	Cooldown = "Cooldown",
	Disabled = "Disabled",
}

-- Monster States
Enums.MonsterState = {
	Idle = "Idle",
	Investigating = "Investigating",
	Hunting = "Hunting",
	Attacking = "Attacking",
	Dead = "Dead",
}

-- Game Events
Enums.GameEvent = {
	PlayerJoined = "PlayerJoined",
	PlayerLeft = "PlayerLeft",
	GameStarted = "GameStarted",
	GeneratorActivated = "GeneratorActivated",
	PlayerKilled = "PlayerKilled",
	PlayerEscaped = "PlayerEscaped",
	TraitorRevealed = "TraitorRevealed",
	GameEnded = "GameEnded",
	RadarUpdate = "RadarUpdate",
	MonsterAlert = "MonsterAlert",
}

-- Win Conditions
Enums.WinCondition = {
	SurvivorsEscaped = "SurvivorsEscaped",
	TraitorWon = "TraitorWon",
	MonsterWon = "MonsterWon",
	TimeExpired = "TimeExpired",
}

-- Chat Commands
Enums.ChatCommand = {
	Help = "/help",
	Stats = "/stats",
	Report = "/report",
	Trade = "/trade",
}

-- UI Screens
Enums.UIScreen = {
	MainMenu = "MainMenu",
	Matchmaking = "Matchmaking",
	InGame = "InGame",
	Inventory = "Inventory",
	Trading = "Trading",
	Settings = "Settings",
	Leaderboard = "Leaderboard",
}

-- Network Events (for RemoteEvents/RemoteFunctions)
Enums.NetworkEvent = {
	-- Player Events
	PlayerSpawned = "PlayerSpawned",
	PlayerMoved = "PlayerMoved",
	PlayerDied = "PlayerDied",
	PlayerRevived = "PlayerRevived",
	
	-- Item Events
	ItemPickedUp = "ItemPickedUp",
	ItemDropped = "ItemDropped",
	ItemUsed = "ItemUsed",
	
	-- Ability Events
	AbilityActivated = "AbilityActivated",
	AbilityCooldown = "AbilityCooldown",
	
	-- Monster Events
	MonsterAlert = "MonsterAlert",
	MonsterAttack = "MonsterAttack",
	MonsterMoved = "MonsterMoved",
	
	-- Game Events
	GeneratorActivated = "GeneratorActivated",
	GameStateChanged = "GameStateChanged",
	TraitorAssigned = "TraitorAssigned",
	
	-- UI Events
	RadarUpdate = "RadarUpdate",
	HealthUpdate = "HealthUpdate",
	StaminaUpdate = "StaminaUpdate",
	
	-- Chat Events
	ChatMessage = "ChatMessage",
	SystemMessage = "SystemMessage",
}

-- Error Codes
Enums.ErrorCode = {
	OK = 0,
	InvalidPlayer = 1,
	NotEnoughPlayers = 2,
	GameAlreadyRunning = 3,
	PlayerNotInGame = 4,
	InsufficientPermissions = 5,
	ItemNotFound = 6,
	AbilityNotReady = 7,
	InvalidMove = 8,
	NetworkError = 9,
	DataStoreError = 10,
}

-- Rarity Levels
Enums.Rarity = {
	Common = 1,
	Uncommon = 2,
	Rare = 3,
	Epic = 4,
	Legendary = 5,
}

-- Rarity Colors
Enums.RarityColor = {
	[1] = Color3.fromRGB(200, 200, 200), -- Common (Gray)
	[2] = Color3.fromRGB(0, 200, 0), -- Uncommon (Green)
	[3] = Color3.fromRGB(0, 150, 255), -- Rare (Blue)
	[4] = Color3.fromRGB(200, 0, 255), -- Epic (Purple)
	[5] = Color3.fromRGB(255, 200, 0), -- Legendary (Gold)
}

-- Damage Types
Enums.DamageType = {
	Monster = "Monster",
	Traitor = "Traitor",
	Environment = "Environment",
	Fall = "Fall",
}

-- Audio Event Types
Enums.AudioEvent = {
	PlayerFootstep = "PlayerFootstep",
	FlashlightOn = "FlashlightOn",
	FlashlightOff = "FlashlightOff",
	RadarBeep = "RadarBeep",
	GeneratorStart = "GeneratorStart",
	MonsterGrowl = "MonsterGrowl",
	MonsterAttack = "MonsterAttack",
	PlayerHurt = "PlayerHurt",
	PlayerDeath = "PlayerDeath",
	Escape = "Escape",
}

return Enums
