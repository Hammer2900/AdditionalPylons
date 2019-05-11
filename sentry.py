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
		self.comeHome = False
		self.homeTarget = None
		self.enemy_target_bonuses = {
			'Medivac': 300,
			'SCV': 100,
			'SiegeTank': 300,
			'Battlecruiser': 350,
			'Infestor': 300,
			'BroodLord': 300,
			'WidowMine': 300,
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
				self.game._client.debug_line_out(spos, self.last_target, color=Point3((155, 255, 25)))
	
			self.game._client.debug_text_3d(self.label, self.unit.position3d)


	def runList(self):
		if not self.unit.is_ready:
			return #warping in
		self.shield_status()
		
		#check if we need to come home and defend.
		self.comeHome = self.game.checkHome(self)
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

		#hallucinate a phoenix to scout with.
		if self.makeScout():
			self.label = 'Creating Scout'
			return				
			
		#if we are in defend mode and we aren't under attack, then go to the defend point.
		if self.game.defend_only and not self.game.under_attack:
			self.game.defend(self)
			self.label = 'Defending'			
			return #defending.
		
		#move to rally point before attacking:
		if self.game.moveRally and not self.game.under_attack:
			self.game.rally(self)
			self.label = 'Rallying'
			return #moving to rally

		#move to friendly.
		#if self.game.moveToFriendlies(self):
		if self.move_friendlies():
			self.label = 'Moving Friend'
			return #moving to friend.
		
		#4 center ourselves among our friendlies.
		if self.center_friendlies():
			self.label = 'Center Friends'
			return #we are moving towards friends.		

		#7 find the enemy
		if self.game.searchEnemies(self):
			self.label = 'Search'
			return #looking for targets

		self.label = 'Idle'


	def runListAssault(self):
		if not self.unit.is_ready:
			return #warping in
		self.shield_status()

		#keep safe from effects
		if self.game.effectSafe(self):
			self.label = 'Dodging'
			return #dodging effects.				


		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
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
		
		#move to rally point before attacking:
		if self.game.moveRally and not self.game.under_attack:
			self.game.rally(self)
			self.label = 'Rallying'
			return #moving to rally
		
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



	def needShield(self):
		#if an enemy has us in range, then activate shield if possible.
		if self.closestEnemies.filter(lambda x: x.ground_range > 2 and not x.name in ['SCV', 'Probe', 'Drone', 'Broodling'] and x.distance_to(self.unit) < 6).amount >= 1:
			if self.game.unitList.shieldSafe(self):
				if self.activateShield():
					self.last_action = 'Shield'
					return True	

		if self.closestEnemies.filter(lambda x: x.is_flying and x.target_in_range(self.unit)).amount >= 1:
			if self.activateDecoy(AbilityId.HALLUCINATION_VOIDRAY):
				self.last_action = 'Hall'
				return True
			
		elif self.closestEnemies.filter(lambda x: not x.name in ['SCV', 'Probe', 'Drone', 'Broodling'] and x.target_in_range(self.unit)).amount >= 1:
			if self.activateDecoy(AbilityId.HALLUCINATION_IMMORTAL):
				self.last_action = 'Hall'
				return True
		#if there are many units that can attack the ground near us, fake immortal
		elif self.closestEnemies.filter(lambda x: (x.can_attack_air and x.can_attack_ground) and not x.is_flying and not x.name in ['SCV', 'Probe', 'Drone', 'Broodling'] and x.distance_to(self.unit) < 8).amount >= 4:
			if self.activateDecoy(AbilityId.HALLUCINATION_IMMORTAL):
				self.last_action = 'Hall'
				return True
		#check to see if it's a bunch of air units, if so fake voidray.
		elif self.closestEnemies.filter(lambda x: x.is_flying and x.distance_to(self.unit) < 8).amount >= 4:
			if self.activateDecoy(AbilityId.HALLUCINATION_VOIDRAY):
				self.last_action = 'Hall'
				return True		
		return False		

		

	def activateDecoy(self, ability=AbilityId.HALLUCINATION_COLOSSUS):
		if ability in self.abilities and self.game.can_afford(ability):
			self.game.combinedActions.append(self.unit(ability))
			self.last_action = 'Hall'
			return True
		return False			
		
	def makeScout(self):
		#check to see if a scout already exists
		if self.game.unitList.phoenixScouting():
			return False
		if (self.unit.energy > 150 or self.game.units(OBSERVER).ready.amount < 1 and self.game.defend_only) or self.game.time < 300:
			if AbilityId.HALLUCINATION_PHOENIX in self.abilities and self.game.can_afford(HALLUCINATION_PHOENIX):
				self.game.combinedActions.append(self.unit(AbilityId.HALLUCINATION_PHOENIX ))
				self.last_action = 'Hall'
				return True
		return False		
		
		
	def activateShield(self):
		if AbilityId.GUARDIANSHIELD_GUARDIANSHIELD in self.abilities and self.game.can_afford(GUARDIANSHIELD_GUARDIANSHIELD):
			self.game.combinedActions.append(self.unit(AbilityId.GUARDIANSHIELD_GUARDIANSHIELD ))
			self.shielded = True
			self.last_action = 'Shield'
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

	@property
	def isHallucination(self) -> bool:
		return False
	
	@property
	def sendHome(self) -> bool:
		return self.comeHome
		