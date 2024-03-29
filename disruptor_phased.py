import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3
from sc2.unit import Unit

'''
Disruptor Phase AOE Ball
-----------------
unit.name = DisruptorPhased

Searches for the most enemies to damage.
'''

_debug = False

class DisruptorPhased:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.saved_position = None
		self.last_action = ''
		self.life_start = None
		self.last_target = None
		self.targetPosition = None
		self.comeHome = False
		self.homeTarget = None
		self.cancelRequested = False
		self.enemy_target_bonuses = {
			'Medivac': 300,
			'SCV': 100,
			'SiegeTank': 300,
			'Battlecruiser': 350,
			'Carrier': 350,
			'Infestor': 400,
			'BroodLord': 300,
			'WidowMine': 300,
			'WidowMineBurrowed': 350,
			'Mothership': 600,
			'Viking': 300,
			'VikingFighter': 300,		
		}		

		
	def make_decision(self, game, unit):
		self.saved_position = unit.position #first line always.
		self.game = game
		self.unit = unit
		if not self.life_start:
			self.life_start = self.game.time
			self.owner = self.find_owner()
			
		self.life_left = 2.1 - (self.game.time - self.life_start)
			

		self.runList()
	
		#debugging info
		if _debug or self.unit.is_selected:
			if self.last_target:
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, self.last_target, color=Point3((155, 255, 25)))
				self.game._client.debug_sphere_out(self.game.turn3d(self.last_target), 1.5, Point3((155, 255, 25)))
				self.game._client.debug_text_3d('TARGET LOC', self.game.turn3d(self.last_target))
			self.game._client.debug_text_3d(self.label, self.unit.position3d)	
	
	
	def runList(self):
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:

			#find the closest ground enemy.
			if self.moveToEnemies():
				self.label = 'Moving to Enemies'
				return #moving to enemies.
			
		self.label = 'Nothing to do'
		self.cancelRequested = True

	def find_owner(self):
		if len(self.game.units(DISRUPTOR)) > 0:
			owner = self.game.units(DISRUPTOR).closest_to(self.unit)
			return owner
		return None
		

	
	def clearLurkers(self):
		#self.saved_position
		tags = []
		if len(self.game.burrowed_lurkers) > 0:
			for tag, position in self.game.burrowed_lurkers.items():
				dist = self.unit.distance_to(position)
				if dist < 2.5:
					#remove widowmine
					tags.append(tag)
		for tag in tags:
			self.game.removeLurker(tag)
			self.game._strat_manager.remove_intel(tag)
			
	def clearMines(self):
		#self.saved_position
		tags = []
		if len(self.game.burrowed_mines) > 0:
			for tag, [position, lastseen] in self.game.burrowed_mines.items():
				dist = self.unit.distance_to(position)
				if dist < 2.5:
					#remove widowmine
					tags.append(tag)
		for tag in tags:
			self.game.removeWidowmine(tag)
			self.game._strat_manager.remove_intel(tag)


	def moveToEnemies(self):
		mRange = ((self.unit.movement_speed * 2) * self.life_left) #1.5 is radius of explosion
		#print (self.life_left, mRange)
		#find target
		#check to see if there is a burrowed widowmine near us, if so lets kill it.
		closestDistance = 10000
		closestDodge = None
		our_target = None
		#check for widow mines.
		if len(self.game.burrowed_mines) > 0:
			for tag, [position, lastseen] in self.game.burrowed_mines.items():
				dist = self.unit.distance_to(position)
				if dist < closestDistance:
					closestDodge = position
					closestDistance = dist
			if closestDistance < mRange:
				our_target = closestDodge
		#check for burrowed lurkers.
		if len(self.game.burrowed_lurkers) > 0:
			for tag, position in self.game.burrowed_lurkers.items():
				dist = self.unit.distance_to(position)
				if dist < closestDistance:
					closestDodge = position
					closestDistance = dist
			if closestDistance < mRange:
				our_target = closestDodge
		#check for priority targets.
		if not our_target:
			if len(self.closestEnemies.of_type([INFESTOR,SIEGETANKSIEGED,SIEGETANK,GHOST]).closer_than(mRange, self.unit)) > 0:
				our_target = self.closestEnemies.of_type([INFESTOR,SIEGETANKSIEGED,SIEGETANK,GHOST]).closest_to(self.unit)
	
		#find an AOE target if we don't have one yet.
		if not our_target:
			our_target = self.game.findAOETarget(self, mRange, 1.5)

		if not our_target:
			#no target, plan B.
			if self.closestEnemies.not_structure.not_flying.exclude_type([ADEPTPHASESHIFT]).exists:
				closestEnemy = self.closestEnemies.not_structure.not_flying.exclude_type([ADEPTPHASESHIFT]).closest_to(self.unit)
				our_target = closestEnemy

		if not our_target:
			#if no target still, just move away from friendlies.
			closestFriendly = self.game.units.not_flying.exclude_type([ADEPTPHASESHIFT]).closest_to(self.unit)
			if closestFriendly and self.unit.distance_to(closestFriendly) < 2:
				#move away from the friendly.
				our_target = self.unit.position.towards(closestFriendly.position, distance=-2)
			#self.cancelRequested = True
		# 
		# if self.life_left <= 0.2:
		# 	#check for friendlies and cancel if they are in danger.
		# 	friends = self.game.units.filter(lambda x: not x.is_flying and not x.type_id in {ADEPTPHASESHIFT,DISRUPTOR,DISRUPTORPHASED} and x.distance_to(self.unit) <= (1.5 + x.radius))
		# 	if len(friends) > 0:
		# 		#check to see if it's a priority target, if so, ignore it.
		# 		enemies = self.closestEnemies.filter(lambda x: x.type_id in {SIEGETANKSIEGED,INFESTOR,INFESTORBURROWED,GHOST} and x.distance_to(self.unit) <= (1.5 + x.radius))
		# 		if len(enemies) == 0:
		# 			self.cancelRequested = True


		#if we have a target, then move to it.
		if our_target:
			self.targetPosition = our_target.position
			if _debug:
				self.last_target = our_target
				
			# 	self.last_target = Point3((our_target.position3d.x, our_target.position3d.y, (our_target.position3d.z + 1)))
			if self.checkNewAction('move', our_target.position[0], our_target.position[1]):
				self.game.combinedActions.append(self.unit.move(our_target))
			return True
		else:
			self.targetPosition = self.unit.position
		return False

		
	def getTargetBonus(self, targetName):
		if self.enemy_target_bonuses.get(targetName):
			return self.enemy_target_bonuses.get(targetName)
		else:
			return 0
		
	def checkNewAction(self, action, posx, posy):
		actionStr = (action + '-' + str(posx) + '-' + str(posy))		
		if actionStr == self.last_action:
			return False
		self.last_action = actionStr
		return True
	

	@property
	def requestCancel(self) -> bool:
		if self.cancelRequested:
			return True
		return False

	@property
	def ownerTag(self):
		if self.owner:
			return self.owner.tag
		
	@property
	def currentTarget(self) -> Point2:
		if self.targetPosition:
			return self.targetPosition
	
	@property
	def position(self) -> Point2:
		return self.saved_position
	
	@property
	def isRetreating(self) -> bool:
		return False
	
	@property
	def isHallucination(self) -> bool:
		return False

	@property
	def sendHome(self) -> bool:
		return self.comeHome
		

