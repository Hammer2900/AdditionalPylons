import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

'''
Adept Info
-----------------
Description: Ground Unit
Built From: Gateway
Cost:
	Minerals: 100
	Vespene: 25
	GameSpeed: 27
	Supply: 2
Attributes: Light, Biological
Attack 1:
	Targets:	Ground
	Damage:	 	10 (+1)
	DPS:	 	6.2 (+0.62)
				9 (+0.9) Resonating Glaives
	Cooldown:	1.61 (-0.5)
	Bonus:	 	+12 (+1) vs Light
	Bonus DPS:	+7.45 (+0.62) vs Light
	Range:	 	4
Defence:
	Health: 70
	Shield: 70
	Armor: 1 (+1)
Sight: 9 (4 as a Shade)
Speed: 3.5
Cargo Size: 2
Strong against:
    Zergling
    Zealot
    Marine

Weak against:
    Roach
    Stalker
    Marauder
'''
_debug = False

class Adept:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.shade_range = 6
		self.last_target = None
		self.label = 'Idle'		

	def make_decision(self, game, unit):
		self.saved_position = unit.position #first line always.
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)	
	
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
			
			#see if we are able to escape if needed.
			if self.game.canEscape(self) and self.game.keepSafe(self):
				self.label = 'Retreating Safe'
				return #staying alive

			#always attack if we can.
			if self.game.attack(self):
				self.label = 'Attacking'
				return #attacked already this step.
		
			#1a priority is to send shade towards enemy if we can.
			if self.psionicTransfer():
				self.label = 'Go Go Shade'
				return #sending Psionic Transfer scout

			#save our butts if we can
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

		#5 move the closest known enemy.
		if self.game.moveToEnemies(self):
			self.label = 'Moving Enemy'
			return #moving to next target.
	
		#7 find the enemy
		if self.game.searchEnemies(self):
			self.label = 'Search'
			return #looking for targets

		self.label = 'Idle'

		#print ('Adept has nothing to do for some reason')


	def psionicTransfer(self):
		#see if we need to cast a shade at the enemy.
		if not self.game.units(ADEPTPHASESHIFT).closer_than(6, self.unit):
			#targetEnemy = self.game.findGroundTarget(self.unit, can_target_air=False, max_enemy_distance=self.shade_range)
			targetEnemy = self.closestEnemies.closer_than(6, self.unit)
			if targetEnemy:
				closestEnemy = targetEnemy.closest_to(self.unit)
				#scoutPoint = self.game.findRetreatTarget(closestEnemy, self.unit, False, inc_size=6)
				#if scoutPoint:
				if AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT in self.abilities and self.game.can_afford(ADEPTPHASESHIFT_ADEPTPHASESHIFT):
					self.game.combinedActions.append(self.unit(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, closestEnemy.position))
					return True
		return False


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
	

				
			
	
		

		
		
		
		
	