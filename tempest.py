import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

'''
Tempest Info
-----------------
Description: Air Unit
Built From: Stargate
Cost:
	Minerals: 300
	Vespene: 200
	GameSpeed: 43
	Supply: 6
Attributes: Armored, Mechanical, Massive
Attack 1:
	Targets:	 	Ground
	Damage:	 	40 (+4)
	DPS:	 	16.97 (+1.697)
	Cooldown:	 	2.36
	Range:	 	10
Attack 2:
	Targets:	 	Air
	Damage:	 	30 (+3)
	DPS:	 	12.73 (+1.273)
	Cooldown:	 	2.36
	Bonus:	 	+22 (+2) vs Massive
	Bonus DPS:	 	+9.32 (+0.847) vs Massive
	Range:	 	15
Defence:
	Health: 300
	Shield: 150
	Armor: 2 (+1)
Sight: 12
Speed: 2.62
Strong against:
    Liberator
    Brood lord
    Colossus
Weak against:
    Viking
    Corruptor
    Void Ray
'''

_debug = False

class Tempest:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'
		self.enemy_target_bonuses = {
			'Medivac': 3000,
			'SCV': 1000,
			'SiegeTank': 3250,
			'Battlecruiser': 3500,
			'Carrier': 3500,
			'Infestor': 3000,
			'BroodLord': 3000,
			'WidowMine': 3000,
			'Mothership': 6000,
			'Viking': 3000,
			'VikingFighter': 3000,		
			'Phoenix': 3000,	
			'VoidRay': 3000,
			'Raven': 2500,
			'Banshee': 2000,
			'Tempest': 3500,
		}
		
		
		
	def make_decision(self, game, unit):
		self.saved_position = unit.position #first line always.
		self.game = game
		self.unit = unit
		
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
		if self.closestEnemies.amount > 0:
			#see if we are able to escape if needed.
			if self.game.canEscape(self) and self.game.keepSafe(self):
				self.label = 'Retreating Safe'
				return #staying alive

			#1 priority is always attack first if we can
			if self.game.attack(self):
				self.label = 'Attacking'
				return #we attacked this step.
	
			#2 keep safe again.
			if self.game.keepSafe(self):
				self.label = 'Retreating Death'
				return #staying alive
	
			#3 priority is to keep our distance from enemies
			if self.game.KeepKiteRange(self):
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
		
		#7 wait until our shield is at 100%
		if self.unit.shield_percentage < 1:
			self.label = 'Full Regen'
			self.last_target = None	
			return #chillin until healed
			
		#8 find the enemy
		if self.game.searchEnemies(self):
			self.label = 'Searching'
			return #looking for targets


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
		return self.retreating



		
		
		
		
	