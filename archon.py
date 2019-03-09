import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

'''
Archon Info
-----------------
Description: Ground Unit
Cost: varies varies 9 4
Attributes: Psionic, Massive
Attack 1:
	Targets:	Ground / Air
	Damage:	 	25 (+3) (Splash)
	DPS:	 	20 (+2.4)
	Cooldown:	1.25
	Bonus:	 	+10 (+1) vs Biological
	Bonus DPS:	+8 (+0.8) vs Biological
	Range:	 	3
Defence:
	Health: 10
	Shield: 350
	Armor: 0 (+1)
Speed: 3.94
Cargo Size: 4
Strong against:
    Mutalisk

Weak against:
    Thor
    Ultralisk
    Immortal
'''

_debug = False

class Archon:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'

	def make_decision(self, game, unit):
		self.saved_position = unit.position #first line always.
		self.game = game
		self.unit = unit
		self.bonus_range = 0

			
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

			#keep safe from effects
			if self.game.effectSafe(self):
				self.label = 'Dodging'
				return #dodging effects.			
			
			#1 priority is always attack first if we can
			if self.game.attack(self, self.bonus_range):
				self.label = 'Attacking'
				return #we attacked this step.
	
			#2 keep safe again.
			if self.game.keepSafe(self):
				self.label = 'Retreating Death'
				return #staying alive
	
			#3 priority is to keep our distance from enemies
			if self.game.KeepKiteRange(self, self.bonus_range):
				self.label = 'Kiting'
				return #kiting
			
			#look around our range and find the highest target value and move towards it.
			if (not self.game.defend_only or self.game.under_attack) and self.game.moveNearEnemies(self):
				self.label = 'Moving Priority Target'
				return #moving towards a better target.			

		#if we are in defend mode and we aren't under attack, then go to the defend point.
		if self.game.defend_only and not self.game.under_attack:
			self.game.defend(self)
			self.label = 'Defending'			
			return #defending.

		#move to friendly.
		if self.game.moveToFriendlies(self):
			self.label = 'Moving Friend'
			return #moving to friend.
					
		#6 move the closest known enemy.
		if self.game.moveToEnemies(self):
			self.label = 'Moving Enemy'
			return #moving to next target.
					
		#8 find the enemy
		if self.game.searchEnemies(self):
			self.label = 'Searching'
			return #looking for targets

		self.label = 'Idle'


	
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
		return self.retreating

	
		

		
		
		
		
	