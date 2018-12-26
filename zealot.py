import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3
# import datetime
# import time

'''
Zealot Info
----------------

Description: Ground Unit
Built From: Gateway
Cost:
	Minerals: 100
	Vespene: 0
	GameSpeed: 27
	Supply: 2
Attributes: Light, Biological
Attack 1:
	Targets:	Ground
	Damage:	 	8 (+1) (x2)
	DPS:	 	18.6 (+2.33)
	Cooldown: 	0.86
	Range:	 	0.1
Defence:
	Health: 100
	Shield: 50
	Armor: 1 (+1)
Sight: 9
Speed: 3.15, 4.13 (+4.62) with Charge
Cargo Size: 2
Strong against:
    Marauder
    Immortal
    Zergling
Weak against:
    Hellion
    Colossus
    Roach
'''
_debug = False

class Zealot:
	
	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'
		self.closestEnemies = None
		
	def make_decision(self, game, unit):
		self.game = game
		self.unit = unit
		self.saved_position = unit.position

		self.runList()
		
		#debugging info
		if _debug or self.unit.is_selected:
			if self.last_target:
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, self.last_target, (155, 255, 25))
			self.game._client.debug_text_3d(self.label, self.unit.position3d)


	def runList(self):
		#get all the enemies around us.
		self.closestEnemies = self.game.getUnitEnemies(self)
		#self.closestEnemies = self.closestEnemies.exclude_type([REAPER])
		if self.closestEnemies.amount > 0:
			#enemies around us mode.
			#attack if possible.
			if self.game.attack(self):
				self.label = 'Attacking'
				return #attacked already this step.

			#see if we are able to escape if needed.
			if self.game.keepSafe(self):
				self.label = 'Retreating Safe'
				return #staying alive

			#look around our range and find the highest target value and move towards it.
			if (not self.game.defend_only or self.game.under_attack) and self.game.moveNearEnemies(self):
				self.label = 'Moving Priority Target'
				return #moving towards a better target.

			#see if we are at the best target and just need to wait.
			if self.game.doNothing(self):
				self.label = 'Do Nothing'			
				return #waiting

		#if we are in defend mode and we aren't under attack, then go to the defend point.
		if self.game.defend_only and not self.game.under_attack:
			self.game.defend(self)
			self.label = 'Defending'			
			return #defending.

		#in attack mode.
		if self.game.moveToFriendlies(self):
			self.label = 'Moving Friend'
			return #moving to friend.					

		#move the closest known enemy.
		if self.game.moveToEnemies(self):
			self.label = 'Moving Enemy'			
			return #moving to next target.

		if self.game.searchEnemies(self):
			self.label = 'Search'			
			return #looking for targets
			
			
				
			
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
	


