import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

'''
Sentry Info
----------------
Description: Ground Unit
Built From: Gateway
Cost:
	Minerals: 50
	Vespene: 100
	GameSpeed: 26 2
Attributes: Light, Mechanical, Psionic
Attack 1:
	Targets:	Ground / Air
	Damage:	 	6 (+1)
	DPS:	 	8.4 (+1.4)
	Cooldown:	0.71
	Range:	 	5
Defence:
	Health: 40
	Shield: 40
	Armor: 1 (+1)
Energy: 50 / 200
Sight: 10
Speed: 3.15
Cargo Size: 2
Strong against:
    Zealot
    Zergling
Weak against:
    Stalker
    Reaper
    Hydralisk

'''
_debug = False

class Sentry:
	
	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'

	
	def make_decision(self, game, unit):
		self.saved_position = unit.position
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
			
			#see if we need to shield our friends.
			if self.shieldFriends():
				self.label = 'Shield Friends'
				return
			
			#1a check to see if we are even able to retreat.
			if self.game.canEscape(self):
				#1b priority is to save our butts if we can because we have to stop to attack.
				if self.game.keepSafe(self):
					self.label = 'Retreating Safe'
					return #staying alive
			else:
				#see if we can shield anyway
				if self.activateShield():
					self.label = 'Shield Self'
					return #shields up to live longer
	
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
		
		#hallucinate a phoenix to scout with.
		if self.makeScout():
			self.label = 'Creating Scout'
			return		

		#if we are in defend mode and we aren't under attack, then go to the defend point.
		if self.game.defend_only and not self.game.under_attack:
			self.game.defend(self)
			self.label = 'Defending'			
			return #defending.
		
		#3 find friendlies and get in the center of them.
		if self.move_friendlies():
			self.label = 'Moving Friends'
			return #we are moving towards friends.
		
		#4 center ourselves among our friendlies.
		if self.center_friendlies():
			self.label = 'Center Friends'
			return #we are moving towards friends.
		
		if self.shield_friendlies():
			self.label = 'Shield Friends'
			return #shielding friendlies
		
		self.label = 'Idle'
		self.last_target = None



	def shieldFriends(self):
		#if 2 enemies are ranged units and we have friendlies near us, then shield.
		if self.closestEnemies.filter(lambda x: x.ground_range > 2).amount >= 2:
			#check to see if we have friends near.
			fUnits = self.game.units().exclude_type([SENTRY,WARPPRISM]).not_flying.filter(lambda x: x.can_attack_ground).closer_than(1.7, self.unit)
			if fUnits and fUnits.amount > 1:
				if self.activateShield():
					return True
		return False
			
			

	def makeScout(self):
		if self.unit.energy > 175 or self.game.units(OBSERVER).ready.amount < 4:
			if AbilityId.HALLUCINATION_PHOENIX in self.abilities and self.game.can_afford(HALLUCINATION_PHOENIX ):
				self.game.combinedActions.append(self.unit(AbilityId.HALLUCINATION_PHOENIX ))
				return True
		return False		
		
		
	def activateShield(self):
		if AbilityId.GUARDIANSHIELD_GUARDIANSHIELD in self.abilities and self.game.can_afford(GUARDIANSHIELD_GUARDIANSHIELD ):
			self.game.combinedActions.append(self.unit(AbilityId.GUARDIANSHIELD_GUARDIANSHIELD ))
			return True
		return False


	def shield_friendlies(self):
		fUnits = self.game.units().exclude_type([SENTRY,WARPPRISM]).not_flying.filter(lambda x: x.can_attack_ground)
		if self.closestEnemies.exists and fUnits:
			closestFriendly = fUnits.closest_to(self.game.known_enemy_units.closest_to(self.unit))
		elif fUnits:
			closestFriendly = fUnits.closest_to(self.unit)
		if closestFriendly:
			if self.unit.distance_to(closestFriendly) < 4:
				#check to see if the unit is in danger and if it is, pop the shield.
				enemyThreatsClose = self.closestEnemies.closer_than(8, closestFriendly)
				if enemyThreatsClose.exists:
					closestEnemy = enemyThreatsClose.closest_to(closestFriendly)
					if closestEnemy.target_in_range(closestFriendly):
						if self.activateShield():
							return True
		return False

	def center_friendlies(self):
		#find all the ground units in our shield range and center on them.
		friendlyClose_pos = self.game.units().not_flying.filter(lambda x: x.can_attack_ground).closer_than(4, self.unit).center
		if friendlyClose_pos:
			if self.unit.distance_to(friendlyClose_pos) > 2:
				if self.checkNewAction('move', friendlyClose_pos.x, friendlyClose_pos.y):
					self.game.combinedActions.append(self.unit.move(friendlyClose_pos))
				self.last_target = Point3((friendlyClose_pos.x, friendlyClose_pos.y, self.game.getHeight(friendlyClose_pos)))
				return True
		return False

	def move_friendlies(self):
		#find the friendly unit that is closest to enemy and move towards it, or just move to the closest friendly if no enemies fround
		fUnits = self.game.units().exclude_type([SENTRY,WARPPRISM,PROBE]).not_flying.filter(lambda x: x.can_attack_ground)
		closestFriendly = None
		if self.game.known_enemy_units.exists and fUnits:
			closestFriendly = fUnits.closest_to(self.game.known_enemy_units.closest_to(self.unit))
		elif fUnits:
			closestFriendly = fUnits.closest_to(self.unit)
		if closestFriendly:
			#if we are not close to it, then our priority is to get there.
			if self.unit.distance_to(closestFriendly) > 2:
				if self.checkNewAction('move', closestFriendly.position.x, closestFriendly.position.y):
					self.game.combinedActions.append(self.unit.move(closestFriendly))
				self.last_target = Point3((closestFriendly.position3d.x, closestFriendly.position3d.y, (closestFriendly.position3d.z + 1)))
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

