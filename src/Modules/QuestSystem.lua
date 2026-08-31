-- Shadow Sector Quest System
-- Manages objectives, tasks, and goals for survivors and traitors

local Config = require(script.Parent.Parent.Shared:WaitForChild("Config"))
local Enums = require(script.Parent.Parent.Shared:WaitForChild("Enums"))

local QuestSystem = {}
QuestSystem.__index = QuestSystem

-- Initialize Quest System
function QuestSystem.new()
	local self = setmetatable({}, QuestSystem)
	
	self.QuestDatabase = {}
	self.PlayerQuests = {}
	self.CompletedQuests = {}
	self.QuestProgress = {}
	self.ObjectiveList = {}
	
	self:InitializeQuestDatabase()
	self:InitializeObjectives()
	
	return self
end

-- Initialize quest database
function QuestSystem:InitializeQuestDatabase()
	self.QuestDatabase = {
		-- Survivor Quests
		[1] = {
			Id = 1,
			Name = "Escape the Facility",
			Description = "Survive and escape from the facility",
			Type = Enums.QuestType.Survival,
			Rewards = {
				Experience = 500,
				Currency = 100,
			},
			Difficulty = Enums.Difficulty.Hard,
			TimeLimit = 600, -- 10 minutes
		},
		[2] = {
			Id = 2,
			Name = "Repair All Generators",
			Description = "Repair all 5 generators to power the exit",
			Type = Enums.QuestType.Objective,
			Rewards = {
				Experience = 300,
				Currency = 75,
			},
			Difficulty = Enums.Difficulty.Medium,
			TargetCount = 5,
		},
		[3] = {
			Id = 3,
			Name = "Collect Resources",
			Description = "Collect 10 resource items around the facility",
			Type = Enums.QuestType.Collection,
			Rewards = {
				Experience = 200,
				Currency = 50,
			},
			Difficulty = Enums.Difficulty.Easy,
			TargetCount = 10,
		},
		[4] = {
			Id = 4,
			Name = "Assist Teammates",
			Description = "Heal or help 3 teammates during the match",
			Type = Enums.QuestType.Cooperation,
			Rewards = {
				Experience = 250,
				Currency = 60,
			},
			Difficulty = Enums.Difficulty.Medium,
			TargetCount = 3,
		},
		[5] = {
			Id = 5,
			Name = "Survive the Hunt",
			Description = "Evade the monster for 5 minutes",
			Type = Enums.QuestType.Survival,
			Rewards = {
				Experience = 350,
				Currency = 80,
			},
			Difficulty = Enums.Difficulty.Hard,
			TimeLimit = 300,
		},
		[6] = {
			Id = 6,
			Name = "Unlock Secrets",
			Description = "Find and unlock 3 secret areas",
			Type = Enums.QuestType.Exploration,
			Rewards = {
				Experience = 400,
				Currency = 90,
			},
			Difficulty = Enums.Difficulty.Medium,
			TargetCount = 3,
		},
		
		-- Traitor Quests
		[101] = {
			Id = 101,
			Name = "Eliminate Survivors",
			Description = "Eliminate 2 survivors without being discovered",
			Type = Enums.QuestType.Elimination,
			Rewards = {
				Experience = 400,
				Currency = 100,
			},
			Difficulty = Enums.Difficulty.Hard,
			TargetCount = 2,
			TraitorOnly = true,
		},
		[102] = {
			Id = 102,
			Name = "Sabotage Equipment",
			Description = "Sabotage 3 pieces of survivor equipment",
			Type = Enums.QuestType.Sabotage,
			Rewards = {
				Experience = 300,
				Currency = 75,
			},
			Difficulty = Enums.Difficulty.Medium,
			TargetCount = 3,
			TraitorOnly = true,
		},
		[103] = {
			Id = 103,
			Name = "Spread Chaos",
			Description = "Cause 5 survivor deaths indirectly",
			Type = Enums.QuestType.Chaos,
			Rewards = {
				Experience = 350,
				Currency = 85,
			},
			Difficulty = Enums.Difficulty.Hard,
			TargetCount = 5,
			TraitorOnly = true,
		},
		[104] = {
			Id = 104,
			Name = "Block Generators",
			Description = "Prevent 3 generator repairs",
			Type = Enums.QuestType.Sabotage,
			Rewards = {
				Experience = 250,
				Currency = 60,
			},
			Difficulty = Enums.Difficulty.Medium,
			TargetCount = 3,
			TraitorOnly = true,
		},
		[105] = {
			Id = 105,
			Name = "Hunt the Survivors",
			Description = "Survive for 10 minutes as a traitor",
			Type = Enums.QuestType.Survival,
			Rewards = {
				Experience = 300,
				Currency = 70,
			},
			Difficulty = Enums.Difficulty.Medium,
			TimeLimit = 600,
			TraitorOnly = true,
		},
	}
end

-- Initialize main objectives
function QuestSystem:InitializeObjectives()
	self.ObjectiveList = {
		-- Primary Objectives
		{
			Id = "primary_escape",
			Name = "Escape the Facility",
			Description = "Find the exit and escape",
			Type = Enums.ObjectiveType.Primary,
			Status = Enums.ObjectiveStatus.Active,
			Progress = 0,
			Target = 1,
			Reward = true,
		},
		{
			Id = "primary_generators",
			Name = "Power the Exit",
			Description = "Repair all 5 generators",
			Type = Enums.ObjectiveType.Primary,
			Status = Enums.ObjectiveStatus.Active,
			Progress = 0,
			Target = 5,
			Reward = false,
		},
		{
			Id = "primary_traitor",
			Name = "Identify the Traitor",
			Description = "Find and eliminate the traitor",
			Type = Enums.ObjectiveType.Primary,
			Status = Enums.ObjectiveStatus.Active,
			Progress = 0,
			Target = 1,
			Reward = false,
			TraitorObjective = false,
		},
		
		-- Secondary Objectives
		{
			Id = "secondary_resources",
			Name = "Collect Resources",
			Description = "Gather resources for survival",
			Type = Enums.ObjectiveType.Secondary,
			Status = Enums.ObjectiveStatus.Active,
			Progress = 0,
			Target = 10,
			Reward = false,
		},
		{
			Id = "secondary_help",
			Name = "Help Teammates",
			Description = "Assist other survivors",
			Type = Enums.ObjectiveType.Secondary,
			Status = Enums.ObjectiveStatus.Active,
			Progress = 0,
			Target = 3,
			Reward = false,
		},
		{
			Id = "secondary_exploration",
			Name = "Explore the Facility",
			Description = "Find hidden areas and secrets",
			Type = Enums.ObjectiveType.Secondary,
			Status = Enums.ObjectiveStatus.Active,
			Progress = 0,
			Target = 5,
			Reward = false,
		},
	}
end

-- Assign quests to player
function QuestSystem:AssignQuestToPlayer(playerId, questId, isTraitor)
	if not self.PlayerQuests[playerId] then
		self.PlayerQuests[playerId] = {}
	end
	
	local quest = self.QuestDatabase[questId]
	
	if not quest then
		return false, "Quest not found"
	end
	
	-- Check if traitor quest
	if quest.TraitorOnly and not isTraitor then
		return false, "This quest is only for traitors"
	end
	
	-- Check if quest already assigned
	for _, playerQuest in ipairs(self.PlayerQuests[playerId]) do
		if playerQuest.Id == questId then
			return false, "Quest already assigned"
		end
	end
	
	-- Create quest progress entry
	local questProgress = {
		QuestId = questId,
		PlayerId = playerId,
		Status = Enums.QuestStatus.Active,
		Progress = 0,
		StartTime = tick(),
		CompletedTime = nil,
		IsTraitor = isTraitor,
	}
	
	table.insert(self.PlayerQuests[playerId], questProgress)
	
	return true, "Quest assigned successfully"
end

-- Update quest progress
function QuestSystem:UpdateQuestProgress(playerId, questId, amount)
	if not self.PlayerQuests[playerId] then
		return false, "Player not found"
	end
	
	local quest = self.QuestDatabase[questId]
	
	if not quest then
		return false, "Quest not found"
	end
	
	-- Find player's quest
	for _, playerQuest in ipairs(self.PlayerQuests[playerId]) do
		if playerQuest.QuestId == questId then
			playerQuest.Progress = playerQuest.Progress + amount
			
			-- Check if quest is completed
			if playerQuest.Progress >= quest.TargetCount then
				self:CompleteQuest(playerId, questId)
			end
			
			return true, "Progress updated"
		end
	end
	
	return false, "Quest not assigned to player"
end

-- Complete quest
function QuestSystem:CompleteQuest(playerId, questId)
	if not self.PlayerQuests[playerId] then
		return false, "Player not found"
	end
	
	local quest = self.QuestDatabase[questId]
	
	if not quest then
		return false, "Quest not found"
	end
	
	-- Find and complete quest
	for i, playerQuest in ipairs(self.PlayerQuests[playerId]) do
		if playerQuest.QuestId == questId then
			playerQuest.Status = Enums.QuestStatus.Completed
			playerQuest.CompletedTime = tick()
			
			-- Record completed quest
			if not self.CompletedQuests[playerId] then
				self.CompletedQuests[playerId] = {}
			end
			
			table.insert(self.CompletedQuests[playerId], {
				QuestId = questId,
				CompletedTime = tick(),
				Rewards = quest.Rewards,
			})
			
			print("[QuestSystem] Quest " .. quest.Name .. " completed by player " .. tostring(playerId))
			
			return true, "Quest completed"
		end
	end
	
	return false, "Quest not assigned to player"
end

-- Fail quest
function QuestSystem:FailQuest(playerId, questId)
	if not self.PlayerQuests[playerId] then
		return false, "Player not found"
	end
	
	-- Find and fail quest
	for i, playerQuest in ipairs(self.PlayerQuests[playerId]) do
		if playerQuest.QuestId == questId then
			playerQuest.Status = Enums.QuestStatus.Failed
			table.remove(self.PlayerQuests[playerId], i)
			
			return true, "Quest failed"
		end
	end
	
	return false, "Quest not assigned to player"
end

-- Update objective progress
function QuestSystem:UpdateObjective(objectiveId, progress, totalPlayers)
	for _, objective in ipairs(self.ObjectiveList) do
		if objective.Id == objectiveId then
			objective.Progress = objective.Progress + progress
			
			-- Notify all players of objective update
			print("[QuestSystem] Objective '" .. objective.Name .. "' progress: " .. objective.Progress .. "/" .. objective.Target)
			
			if objective.Progress >= objective.Target then
				objective.Status = Enums.ObjectiveStatus.Completed
				print("[QuestSystem] Objective '" .. objective.Name .. "' completed!")
			end
			
			return true
		end
	end
	
	return false
end

-- Complete objective
function QuestSystem:CompleteObjective(objectiveId)
	for _, objective in ipairs(self.ObjectiveList) do
		if objective.Id == objectiveId then
			objective.Status = Enums.ObjectiveStatus.Completed
			print("[QuestSystem] Objective '" .. objective.Name .. "' completed!")
			return true
		end
	end
	
	return false
end

-- Get player quests
function QuestSystem:GetPlayerQuests(playerId)
	return self.PlayerQuests[playerId] or {}
end

-- Get quest info
function QuestSystem:GetQuestInfo(questId)
	return self.QuestDatabase[questId]
end

-- Get all objectives
function QuestSystem:GetAllObjectives()
	return self.ObjectiveList
end

-- Get objective by id
function QuestSystem:GetObjective(objectiveId)
	for _, objective in ipairs(self.ObjectiveList) do
		if objective.Id == objectiveId then
			return objective
		end
	end
	
	return nil
end

-- Check if player has completed quest
function QuestSystem:HasCompletedQuest(playerId, questId)
	if not self.CompletedQuests[playerId] then
		return false
	end
	
	for _, completed in ipairs(self.CompletedQuests[playerId]) do
		if completed.QuestId == questId then
			return true
		end
	end
	
	return false
end

-- Get active quests for player
function QuestSystem:GetActiveQuests(playerId)
	if not self.PlayerQuests[playerId] then
		return {}
	end
	
	local activeQuests = {}
	
	for _, quest in ipairs(self.PlayerQuests[playerId]) do
		if quest.Status == Enums.QuestStatus.Active then
			table.insert(activeQuests, quest)
		end
	end
	
	return activeQuests
end

-- Get quest completion rewards
function QuestSystem:GetQuestRewards(questId)
	local quest = self.QuestDatabase[questId]
	
	if quest then
		return quest.Rewards
	end
	
	return nil
end

-- Reset player quests
function QuestSystem:ResetPlayerQuests(playerId)
	if self.PlayerQuests[playerId] then
		self.PlayerQuests[playerId] = {}
	end
end

-- Get quest progress percentage
function QuestSystem:GetQuestProgressPercentage(playerId, questId)
	if not self.PlayerQuests[playerId] then
		return 0
	end
	
	local quest = self.QuestDatabase[questId]
	
	if not quest then
		return 0
	end
	
	for _, playerQuest in ipairs(self.PlayerQuests[playerId]) do
		if playerQuest.QuestId == questId then
			local percentage = (playerQuest.Progress / quest.TargetCount) * 100
			return math.min(100, percentage)
		end
	end
	
	return 0
end

-- Get objective progress percentage
function QuestSystem:GetObjectiveProgressPercentage(objectiveId)
	local objective = self:GetObjective(objectiveId)
	
	if not objective then
		return 0
	end
	
	local percentage = (objective.Progress / objective.Target) * 100
	return math.min(100, percentage)
end

-- Get all quests by difficulty
function QuestSystem:GetQuestsByDifficulty(difficulty)
	local quests = {}
	
	for questId, quest in pairs(self.QuestDatabase) do
		if quest.Difficulty == difficulty then
			table.insert(quests, quest)
		end
	end
	
	return quests
end

-- Get all quests by type
function QuestSystem:GetQuestsByType(questType)
	local quests = {}
	
	for questId, quest in pairs(self.QuestDatabase) do
		if quest.Type == questType then
			table.insert(quests, quest)
		end
	end
	
	return quests
end

-- Check time limit for quest
function QuestSystem:CheckQuestTimeLimit(playerId, questId, currentTime)
	if not self.PlayerQuests[playerId] then
		return true
	end
	
	local quest = self.QuestDatabase[questId]
	
	if not quest or not quest.TimeLimit then
		return true
	end
	
	for _, playerQuest in ipairs(self.PlayerQuests[playerId]) do
		if playerQuest.QuestId == questId then
			local elapsed = currentTime - playerQuest.StartTime
			
			if elapsed > quest.TimeLimit then
				self:FailQuest(playerId, questId)
				return false
			end
			
			return true
		end
	end
	
	return true
end

return QuestSystem
