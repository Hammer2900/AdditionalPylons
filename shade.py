import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

'''
Phase Info
-----------------
Description: Ground Unit
Sight: 4
Speed: 3.5

		#CANCEL_ADEPTSHADEPHASESHIFT
		#CANCEL_ADEPTPHASESHIFT
		#ADEPTPHASESHIFT_ADEPTPHASESHIFT
		#AdeptPhaseShift
'''


class Shade:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.saved_position = None
		self.last_action = ''
		self.tried_positions = []
		self.outs = 0
		self.shade_start = None
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
		
		
	def make_decision(self, game, shade):
		self.saved_position = shade.position #first line always.
		self.game = game
		self.shade = shade
		self.abilities = self.game.allAbilities.get(self.shade.tag)
		if not self.shade_start:
			self.shade_start = self.game.time
			
		if self.psionicCancel():
			return # canceled shade.
		
		#5 priority is to move towards enemies not in range.
		if self.moveToEnemies():
			return #moving to enemy
		
		if self.searchEnemies():
			return #search enemies.

	def psionicCancel(self):
		if self.shade_start:
			#see if it's time to cancel the shift.
			if (self.shade_start + 5.5) < self.game.time:
				#cancel the shift.
				if AbilityId.CANCEL_ADEPTSHADEPHASESHIFT in self.abilities and self.game.can_afford(CANCEL_ADEPTSHADEPHASESHIFT):
					self.game.combinedActions.append(self.shade(AbilityId.CANCEL_ADEPTSHADEPHASESHIFT))
					self.shade_start = None
					return True
		return False
		
		
	def searchEnemies(self):
		#search for enemies
		if self.shade.is_moving:
			return True #moving somewhere already
		searchPos = self.game.getSearchPos(self.shade)
		if self.checkNewAction('move', searchPos[0], searchPos[1]):
			self.game.combinedActions.append(self.shade.move(searchPos))
			return True
		return False
		
	def moveToEnemies(self):
		# move to nearest enemy ground unit/building because no enemy unit is closer than 5
		if self.game.known_enemy_units.exclude_type([ADEPTPHASESHIFT]).not_flying.exists:
			closestEnemy = self.game.known_enemy_units.exclude_type([ADEPTPHASESHIFT]).not_flying.furthest_to(self.shade)
			if self.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
				self.game.combinedActions.append(self.shade.move(closestEnemy))
			return True
		return False


	def getTargetBonus(self, targetName):
		if self.enemy_target_bonuses.get(targetName):
			return self.enemy_target_bonuses.get(targetName)
		else:
			return 0
	
	def checkNewAction(self, action, posx, posy):
		#actionStr = (action + '-' + str(int(posx)) + '-' + str(int(posy)))
		actionStr = (action + '-' + str(posx) + '-' + str(posy))		
		#print (actionStr, self.last_action)
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
	
	@property
	def isSolo(self) -> bool:
		return self.solo

				
			
	
		

		
		
		
		
	