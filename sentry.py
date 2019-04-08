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
		self.shielded = False
		self.shield_time = None
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
		if not self.unit.is_ready:
			return #warping in
		self.shield_status()
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			#keep safe from effects
			if self.game.effectSafe(self):
				self.label = 'Dodging'
				return #dodging effects.				

			#see if we need to shield our friends.
			if self.needShield():
				self.label = 'Shield Activated'
				return
			
			#see if we are able to escape if needed.
			if self.game.canEscape(self) and self.game.keepSafe(self):
				self.label = 'Retreating Safe'
				return #staying alive

			#always attack if we can.
			if self.game.attack(self):
				self.label = 'Attacking'
				return #attacked already this step.

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
	
		#hallucinate a phoenix to scout with.
		if self.makeScout():
			self.label = 'Creating Scout'
			return				
			
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


	def runListSupport(self):
		#if shield status
		self.shield_status()
		
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			#keep safe from effects
			if self.game.effectSafe(self):
				self.label = 'Dodging'
				return #dodging effects.
			
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
				#put up a dummy to get attacked/scare off.
				if self.activateDecoy():
					self.label = 'Decoy Sent'
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



	def needShield(self):
		#if 2 enemies are ranged units and we have friendlies near us, then shield.
		if self.closestEnemies.filter(lambda x: x.ground_range > 2 and x.target_in_range(self.unit)).amount >= 1:
			if self.game.unitList.shieldSafe(self):
				if self.activateShield():
					return True
		return False
			
			

	def activateDecoy(self):
		# if AbilityId.HALLUCINATION_COLOSSUS in self.abilities and self.game.can_afford(HALLUCINATION_COLOSSUS):
		# 	self.game.combinedActions.append(self.unit(AbilityId.HALLUCINATION_COLOSSUS))
		# 	return True
		return False			
		

	def makeScout(self):
		if (self.unit.energy > 150 or self.game.units(OBSERVER).ready.amount < 1 and self.game.defend_only) or self.game.time < 300:
			if AbilityId.HALLUCINATION_PHOENIX in self.abilities and self.game.can_afford(HALLUCINATION_PHOENIX):
				self.game.combinedActions.append(self.unit(AbilityId.HALLUCINATION_PHOENIX ))
				return True
		return False		
		
		
	def activateShield(self):
		if AbilityId.GUARDIANSHIELD_GUARDIANSHIELD in self.abilities and self.game.can_afford(GUARDIANSHIELD_GUARDIANSHIELD):
			self.game.combinedActions.append(self.unit(AbilityId.GUARDIANSHIELD_GUARDIANSHIELD ))
			self.shielded = True
			self.shield_time = self.game.time
			return True
		return False


	def shield_status(self):
		if self.shielded and self.shield_time >= self.game.time + 11:
			self.shielded = False

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
	def shieldActive(self) -> bool:
		return self.shielded


	@property
	def position(self) -> Point2:
		return self.saved_position
	
	@property
	def isRetreating(self) -> bool:
		return self.retreating

