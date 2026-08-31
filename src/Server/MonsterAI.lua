-- Shadow Sector Monster AI System
-- Handles monster behavior, pathfinding, and hunting logic

local Config = require(script.Parent.Parent.Shared:WaitForChild("Config"))
local Enums = require(script.Parent.Parent.Shared:WaitForChild("Enums"))

local MonsterAI = {}
MonsterAI.__index = MonsterAI

-- Initialize Monster AI
function MonsterAI.new(monsterModel, gameLoop)
	local self = setmetatable({}, MonsterAI)
	
	self.Model = monsterModel
	self.GameLoop = gameLoop
	self.Position = monsterModel.PrimaryPart.Position
	self.Velocity = Vector3.new(0, 0, 0)
	self.CurrentState = Enums.MonsterState.Idle
	self.TargetPlayer = nil
	self.Health = Config.Monster.Health
	self.LastAttackTime = 0
	self.AlertLevel = 0 -- 0-1, how alerted the monster is
	self.PatrolPath = {}
	self.SensoryData = {
		LastSeenTarget = nil,
		LastHeardSound = nil,
		DetectedLights = {},
	}
	
	self:InitializePatrolPath()
	
	return self
end

-- Initialize patrol path for the monster
function MonsterAI:InitializePatrolPath()
	-- This would be populated from the map design
	-- For now, random patrol points
	self.PatrolPath = {
		Vector3.new(0, 5, 0),
		Vector3.new(50, 5, 50),
		Vector3.new(-50, 5, 50),
		Vector3.new(-50, 5, -50),
		Vector3.new(50, 5, -50),
	}
	self.CurrentPatrolIndex = 1
end

-- Main update loop
function MonsterAI:Update(deltaTime, gamePlayers)
	-- Gather sensory information
	self:ScanEnvironment(gamePlayers)
	
	-- Update AI state
	self:UpdateAIState(deltaTime, gamePlayers)
	
	-- Execute current behavior
	self:ExecuteBehavior(deltaTime, gamePlayers)
	
	-- Update position and velocity
	self:UpdatePhysics(deltaTime)
	
	-- Sync to clients
	self:SyncToClients()
end

-- Scan environment for threats, light, and sound
function MonsterAI:ScanEnvironment(gamePlayers)
	self.SensoryData.DetectedLights = {}
	local closestPlayer = nil
	local closestDistance = math.huge
	
	for userId, playerData in pairs(gamePlayers) do
		if playerData.State == Enums.PlayerState.Alive then
			local playerPosition = playerData.Position or Vector3.new(0, 0, 0)
			local distance = (playerPosition - self.Position).Magnitude
			
			-- Check if player is in detection range
			if distance < Config.Monster.DetectionRange then
				-- Check line of sight (basic implementation)
				if self:HasLineOfSight(playerPosition) then
					self.SensoryData.LastSeenTarget = userId
					
					if distance < closestDistance then
						closestDistance = distance
						closestPlayer = userId
					end
				end
			end
			
			-- Detect light sources
			if playerData.Inventory then
				for _, item in ipairs(playerData.Inventory) do
					if item.Type == Enums.ItemType.Flashlight and item.Active then
						local lightDistance = (playerPosition - self.Position).Magnitude
						if lightDistance < Config.Flashlight.MonsterAttractRadius then
							table.insert(self.SensoryData.DetectedLights, {
								PlayerId = userId,
								Distance = lightDistance,
								Brightness = item.Brightness or 1,
							})
						end
					end
				end
			end
		end
	end
	
	-- Update alert level based on sensory input
	self:UpdateAlertLevel()
end

-- Check if there's line of sight to target
function MonsterAI:HasLineOfSight(targetPosition)
	local rayOrigin = self.Position + Vector3.new(0, 2, 0)
	local rayDirection = (targetPosition - rayOrigin).Unit * Config.Monster.DetectionRange
	
	local raycastParams = RaycastParams.new()
	raycastParams.FilterType = Enum.RaycastFilterType.Exclude
	raycastParams.FilterDescendantsInstances = {self.Model}
	
	local result = workspace:Raycast(rayOrigin, rayDirection, raycastParams)
	
	-- If no obstacle, we have line of sight
	return result == nil
end

-- Update alert level based on sensory data
function MonsterAI:UpdateAlertLevel()
	local baseAlertLevel = 0
	
	-- Light detection increases alert
	if #self.SensoryData.DetectedLights > 0 then
		local totalLightBrightness = 0
		for _, light in ipairs(self.SensoryData.DetectedLights) do
			totalLightBrightness = totalLightBrightness + light.Brightness
		end
		baseAlertLevel = math.min(1, totalLightBrightness * Config.Monster.LightSensitivity)
	end
	
	-- Last seen target increases alert
	if self.SensoryData.LastSeenTarget then
		baseAlertLevel = math.max(baseAlertLevel, 0.8)
	end
	
	-- Smoothly transition alert level
	self.AlertLevel = self.AlertLevel * 0.9 + baseAlertLevel * 0.1
end

-- Update monster AI state based on alert level and situation
function MonsterAI:UpdateAIState(deltaTime, gamePlayers)
	local previousState = self.CurrentState
	
	if self.CurrentState == Enums.MonsterState.Idle then
		-- Transition to investigating if high alert
		if self.AlertLevel > 0.5 then
			self.CurrentState = Enums.MonsterState.Investigating
		end
	
	elseif self.CurrentState == Enums.MonsterState.Investigating then
		-- Transition to hunting if target seen
		if self.SensoryData.LastSeenTarget then
			self.TargetPlayer = self.SensoryData.LastSeenTarget
			self.CurrentState = Enums.MonsterState.Hunting
		elseif self.AlertLevel < 0.3 then
			-- Return to idle if alert subsides
			self.CurrentState = Enums.MonsterState.Idle
		end
	
	elseif self.CurrentState == Enums.MonsterState.Hunting then
		-- Check if target is still alive and in range
		if self.TargetPlayer then
			local targetData = gamePlayers[self.TargetPlayer]
			if targetData and targetData.State == Enums.PlayerState.Alive then
				local distance = (targetData.Position - self.Position).Magnitude
				if distance > Config.Monster.DetectionRange * 1.5 then
					-- Lost target
					self.TargetPlayer = nil
					self.CurrentState = Enums.MonsterState.Investigating
				end
			else
				-- Target dead or gone
				self.TargetPlayer = nil
				self.CurrentState = Enums.MonsterState.Investigating
			end
		end
	
	elseif self.CurrentState == Enums.MonsterState.Attacking then
		-- Attack state is brief, return to hunting after
		self.CurrentState = Enums.MonsterState.Hunting
	end
	
	-- Log state change
	if previousState ~= self.CurrentState then
		print("[MonsterAI] State changed: " .. previousState .. " -> " .. self.CurrentState)
	end
end

-- Execute behavior based on current state
function MonsterAI:ExecuteBehavior(deltaTime, gamePlayers)
	if self.CurrentState == Enums.MonsterState.Idle then
		self:PatrolBehavior(deltaTime)
	
	elseif self.CurrentState == Enums.MonsterState.Investigating then
		self:InvestigateBehavior(deltaTime)
	
	elseif self.CurrentState == Enums.MonsterState.Hunting then
		self:HuntingBehavior(deltaTime, gamePlayers)
	
	elseif self.CurrentState == Enums.MonsterState.Attacking then
		self:AttackBehavior(deltaTime, gamePlayers)
	end
end

-- Patrol behavior (idle state)
function MonsterAI:PatrolBehavior(deltaTime)
	-- Move towards next patrol point
	local targetPoint = self.PatrolPath[self.CurrentPatrolIndex]
	local direction = (targetPoint - self.Position).Unit
	
	self.Velocity = direction * Config.Monster.WalkSpeed
	
	-- Check if reached patrol point
	if (self.Position - targetPoint).Magnitude < 5 then
		self.CurrentPatrolIndex = self.CurrentPatrolIndex + 1
		if self.CurrentPatrolIndex > #self.PatrolPath then
			self.CurrentPatrolIndex = 1
		end
	end
end

-- Investigate behavior (increased alert state)
function MonsterAI:InvestigateBehavior(deltaTime)
	-- Move towards last known position of sound/light
	if self.SensoryData.DetectedLights and #self.SensoryData.DetectedLights > 0 then
		local targetLight = self.SensoryData.DetectedLights[1]
		local direction = (targetLight - self.Position).Unit
		self.Velocity = direction * Config.Monster.WalkSpeed * 1.2
	elseif self.SensoryData.LastSeenTarget then
		-- Move towards last seen target position
		self.Velocity = self.Velocity * 0.9 -- Slow down
	else
		-- Return to patrol if nothing found
		self:PatrolBehavior(deltaTime)
	end
end

-- Hunting behavior (target acquired)
function MonsterAI:HuntingBehavior(deltaTime, gamePlayers)
	if not self.TargetPlayer then
		return
	end
	
	local targetData = gamePlayers[self.TargetPlayer]
	if not targetData then
		return
	end
	
	local targetPosition = targetData.Position or self.Position
	local distance = (targetPosition - self.Position).Magnitude
	
	-- Check if in attack range
	if distance < 5 then
		self.CurrentState = Enums.MonsterState.Attacking
		self:AttackBehavior(deltaTime, gamePlayers)
		return
	end
	
	-- Sprint towards target
	local direction = (targetPosition - self.Position).Unit
	self.Velocity = direction * Config.Monster.SprintSpeed
end

-- Attack behavior
function MonsterAI:AttackBehavior(deltaTime, gamePlayers)
	local currentTime = tick()
	
	-- Check attack cooldown
	if currentTime - self.LastAttackTime < Config.Monster.AttackCooldown then
		return
	end
	
	if not self.TargetPlayer then
		return
	end
	
	local targetData = gamePlayers[self.TargetPlayer]
	if not targetData then
		return
	end
	
	-- Deal damage to target
	self.GameLoop:DamagePlayer(
		self.TargetPlayer,
		Config.Monster.Damage,
		Enums.DamageType.Monster,
		"Monster"
	)
	
	self.LastAttackTime = currentTime
	print("[MonsterAI] Attacked player " .. self.TargetPlayer)
end

-- Update physics (position based on velocity)
function MonsterAI:UpdatePhysics(deltaTime)
	-- Apply gravity
	self.Velocity = self.Velocity + Vector3.new(0, -20 * deltaTime, 0)
	
	-- Update position
	self.Position = self.Position + self.Velocity * deltaTime
	
	-- Ground collision (basic)
	if self.Position.Y < 5 then
		self.Position = Vector3.new(self.Position.X, 5, self.Position.Z)
		self.Velocity = Vector3.new(self.Velocity.X, 0, self.Velocity.Z)
	end
	
	-- Update model
	if self.Model and self.Model.PrimaryPart then
		self.Model:SetPrimaryPartCFrame(CFrame.new(self.Position))
	end
end

-- Take damage
function MonsterAI:TakeDamage(damageAmount)
	self.Health = math.max(0, self.Health - damageAmount)
	
	if self.Health <= 0 then
		self:Die()
	end
end

-- Monster dies
function MonsterAI:Die()
	self.CurrentState = Enums.MonsterState.Dead
	print("[MonsterAI] Monster died!")
	
	-- Disable monster
	if self.Model then
		self.Model:Destroy()
	end
end

-- Sync monster state to clients
function MonsterAI:SyncToClients()
	if self.GameLoop.RemoteEvents["MonsterUpdate"] then
		local monsterUpdatePacket = {
			Position = self.Position,
			Velocity = self.Velocity,
			State = self.CurrentState,
			TargetId = self.TargetPlayer,
			Health = self.Health,
			AlertLevel = self.AlertLevel,
			Timestamp = tick(),
		}
		self.GameLoop.RemoteEvents["MonsterUpdate"]:FireAllClients(monsterUpdatePacket)
	end
end

-- Get monster data for debugging
function MonsterAI:GetDebugInfo()
	return {
		Position = self.Position,
		State = self.CurrentState,
		AlertLevel = self.AlertLevel,
		TargetPlayer = self.TargetPlayer,
		Health = self.Health,
		LastSeenTarget = self.SensoryData.LastSeenTarget,
		DetectedLights = #self.SensoryData.DetectedLights,
	}
end

return MonsterAI
