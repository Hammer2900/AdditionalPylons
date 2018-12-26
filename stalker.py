import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

'''
Stalker Info
---------------------
Description: Ground Unit
Built From: Gateway
Cost:
	Minerals: 125
	Vaspene: 50
	GameSpeed: 30
	Supply: 2
Attributes: Armored, Mechanical
Attack 1:
	Targets:	Ground / Air
	Damage:	 	13 (+1)
	DPS:	 	9.7 (+0.75)
	Cooldown:	1.34
	Bonus:	 	+5 (+1) vs Armored
	Bonus DPS:	+3.7 (+0.75) vs Armored
	Range:	 	6
Defence:
	Health: 80
	Sheild: 80
	Armor: 1 (+1)
Sight: 10
Speed: 4.13
Cargo Size: 2
Strong against:
    Reaper
    Void Ray
    Mutalisk
Weak against:
    Marauder
    Immortal
    Zergling

'''
_debug = False

class Stalker:
	
	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'
		
		
	def make_decision(self, game, unit):
		self.game = game
		self.stalker = unit
		self.unit = unit
		self.saved_position = self.unit.position
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
			#1 priority is always attack first if we can
			if self.game.attack(self):
				self.label = 'Attacking'
				return #we attacked this step.			
			
			#1a check to see if we are even able to retreat.
			if self.game.canEscape(self):
				#1b priority is to save our butts if we can because we have to stop to attack.
				if self.game.keepSafe(self):
					self.label = 'Retreating Safe'
					return #staying alive
			else:
				#see if we can blink out of it.
				if self.blinkRetreat():
					self.label = 'Blinking'
					return #trying to blink away.

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
						
		#8 find the enemy
		if self.game.searchEnemies(self):
			self.label = 'Searching'
			return #looking for targets




	def blinkRetreat(self):
		self.retreating = True
		if AbilityId.EFFECT_BLINK_STALKER in self.abilities and self.game.can_afford(EFFECT_BLINK_STALKER):
			retreatPoint = self.game.findGroundRetreatTarget(self.unit, inc_size=6, enemy_radius=10)
			if retreatPoint:
				if self.checkNewAction('blink', retreatPoint[0], retreatPoint[1]):
					self.game.combinedActions.append(self.unit(AbilityId.EFFECT_BLINK_STALKER, retreatPoint))
				self.last_target = retreatPoint.position
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

			
