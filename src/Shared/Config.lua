-- Shadow Sector Shared Configuration
-- Centralized game settings for server and client

local Config = {}

-- Game Settings
Config.GameSettings = {
	GameDuration = 600, -- 10 minutes in seconds
	MinPlayers = 4,
	MaxPlayers = 8,
	
	-- Traitor probability
	TraitorCount = 1, -- 1 traitor per game
	
	-- Spawn settings
	SpawnProtectionTime = 5, -- seconds of invulnerability after spawn
	RespawnTime = 15, -- seconds to respawn after death
}

-- Monster Settings
Config.Monster = {
	WalkSpeed = 25,
	SprintSpeed = 45,
	DetectionRange = 100,
	LightSensitivity = 0.8, -- 0-1, higher = more sensitive to light
	NoiseSensitivity = 0.7, -- 0-1, higher = more sensitive to sound
	Health = 100,
	Damage = 35,
	AttackCooldown = 2, -- seconds between attacks
}

-- Survivor Settings
Config.Survivor = {
	WalkSpeed = 16,
	SprintSpeed = 25,
	StaminaMax = 100,
	StaminaDrain = 15, -- per second while sprinting
	StaminaRegenRate = 8, -- per second while resting
	Health = 50,
}

-- Radar Settings
Config.Radar = {
	Range = 120, -- units
	UpdateRate = 0.5, -- seconds between updates
	BatteryLife = 300, -- seconds
	BatteryDrainRate = 1, -- per second
	Accuracy = 0.85, -- 0-1, chance of accurate reading
}

-- Flashlight Settings
Config.Flashlight = {
	BatteryLife = 180, -- seconds
	BatteryDrainRate = 1.5, -- per second
	Range = 40,
	Brightness = 2,
	MonsterAttractRadius = 60, -- How far the monster can detect light
	LightAlertValue = 0.7, -- 0-1, how much the monster is alerted by light
}

-- First Aid Kit Settings
Config.FirstAidKit = {
	Uses = 2,
	HealAmount = 30,
	UseTime = 3, -- seconds to use
	ReviveChance = 0.6, -- 60% chance to revive dead teammate
}

-- Generator Settings
Config.Generator = {
	ActivationTime = 10, -- seconds to activate
	RequiredGenerators = 2, -- number needed to escape
	PowerRestoreTime = 5, -- seconds for area to light up after generator
}

-- Traitor Roles
Config.TraitorRoles = {
	Saboteur = {
		Name = "Saboteur",
		Ability = "FalseSignal",
		AbilityCooldown = 15,
		AbilityDuration = 8,
		Description = "Create false radar signals to confuse survivors",
	},
	Hypnotizer = {
		Name = "Hypnotizer",
		Ability = "DistortVision",
		AbilityCooldown = 20,
		AbilityDuration = 6,
		Description = "Distort a survivor's vision for 6 seconds",
	},
	Corrupted = {
		Name = "Corrupted",
		Ability = "BackStab",
		AbilityCooldown = 25,
		AbilityDuration = 1,
		Damage = 40,
		Description = "Backstab nearby survivor for heavy damage",
	},
}

-- UI Settings
Config.UI = {
	GuiScale = 1,
	ResponsiveScale = true, -- Auto-scale for mobile
	MinimumScale = 0.8, -- Minimum UI scale for low-res devices
	MaximumScale = 1.2, -- Maximum UI scale for high-res devices
	CornerRadius = 8,
	AnimationSpeed = 0.3,
}

-- Network Settings
Config.Network = {
	PlayerUpdateRate = 0.1, -- seconds between position syncs
	MonsterUpdateRate = 0.05, -- faster updates for monster
	MaxPacketSize = 1024, -- bytes
	ReplicationDistance = 200, -- only replicate players within this distance
}

-- Anti-Cheat Settings
Config.AntiCheat = {
	MaxSpeed = 60, -- units per second
	SpeedCheckInterval = 0.5, -- seconds
	TeleportThreshold = 100, -- units, flag if player teleports this far
	DetectionSensitivity = 0.9, -- 0-1, higher = stricter
}

-- Economy Settings
Config.Economy = {
	EscapeReward = 500, -- currency units
	SurvivalBonus = 50, -- per 60 seconds survived
	TraitorBonus = 300, -- for successful traitor win
	CosmeticMultiplier = 1.5, -- event bonus multiplier
}

-- Progression Settings
Config.Progression = {
	MaxLevel = 100,
	XpPerEscape = 100,
	XpPerKill = 50,
	XpPerObjective = 75,
	LevelUpCurve = 2, -- exponential growth (xp needed = level ^ curve)
}

-- Cosmetics/Customization
Config.Cosmetics = {
	MaxFlashlightSkins = 15,
	MaxRadarSkins = 12,
	MaxCharacterSkins = 30,
	MaxEmotes = 20,
	DefaultSkin = "Default",
}

-- Map Settings
Config.Maps = {
	{
		Name = "Abandoned Facility",
		Size = Vector3.new(500, 300, 500),
		Difficulty = 1.0,
	},
	{
		Name = "Midnight Forest",
		Size = Vector3.new(600, 400, 600),
		Difficulty = 1.2,
	},
	{
		Name = "Underground Complex",
		Size = Vector3.new(400, 250, 400),
		Difficulty = 1.1,
	},
}

return Config
