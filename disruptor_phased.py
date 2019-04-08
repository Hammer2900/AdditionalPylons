import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

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
		self.enemy_target_bonuses = {
			'Medivac': 300,
			'SCV': 100,
			'SiegeTank': 300,
			'Battlecruiser': 350,
			'Carrier': 350,
			'Infestor': 300,
			'BroodLord': 300,
			'WidowMine': 300,
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

		self.life_left = 2 - (self.game.time - self.life_start)
			

		self.runList()
	
		#debugging info
		if _debug or self.unit.is_selected:
			if self.last_target:
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, self.last_target, (155, 255, 25))
			self.game._client.debug_text_3d(self.label, self.unit.position3d)	
	
	
	def runList(self):
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:

			#find the closest ground enemy.
			if self.moveToEnemies():
				self.label = 'Moving to Enemies'
				return #moving to enemies.
			
		self.label = 'Nothing to do'
		
		
	def clearMines(self):
		#self.saved_position
		tags = []
		if len(self.game.burrowed_mines) > 0:
			for tag, position in self.game.burrowed_mines.items():
				dist = self.unit.distance_to(position)
				if dist < 2.5:
					#remove widowmine
					tags.append(tag)
		for tag in tags:
			self.game.removeWidowmine(tag)
			self.game._strat_manager.remove_intel(tag)


		
	def moveToEnemies(self):
		#change our range based on time left.
		if self.life_left == 2:
			mRange = 8
		elif self.life_left == 1:
			mRange = 4
		else:
			mRange = 2
		
		#find target
		#check to see if there is a burrowed widowmine near us, if so lets kill it.
		closestDistance = 10000
		closestDodge = None
		our_target = None
		if len(self.game.burrowed_mines) > 0:
			for tag, position in self.game.burrowed_mines.items():
				dist = self.unit.distance_to(position)
				if dist < closestDistance:
					closestDodge = position
					closestDistance = dist
			if closestDistance < 5.5:
				our_target = closestDodge
		if not our_target:
			our_target = self.game.findAOETarget(self, mRange, 1.5)
		#if we have a target, then move to it.
		if our_target:
			if _debug:
				self.last_target = Point3((our_target.position3d.x, our_target.position3d.y, (our_target.position3d.z + 1)))
			if self.checkNewAction('move', our_target.position[0], our_target.position[1]):
				self.game.combinedActions.append(self.unit.move(our_target))
			return True
		
		#no target, plan B.
		if self.game.known_enemy_units.not_structure.not_flying.exclude_type([ADEPTPHASESHIFT]).exists:
			closestEnemy = self.game.known_enemy_units.not_structure.not_flying.exclude_type([ADEPTPHASESHIFT]).closest_to(self.unit)
			self.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
			if self.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
				self.game.combinedActions.append(self.unit.move(closestEnemy))
			return True
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
	def position(self) -> Point2:
		return self.saved_position
	
	@property
	def isRetreating(self) -> bool:
		return False