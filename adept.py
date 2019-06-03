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
		self.shadeOrder = None
		self.comeHome = False
		self.homeTarget = None
		self.last_health = 0
		self.damaged = False
		self.chasePosition = None
		self.last_health_update = 0
		self.enemy_target_bonuses = {
			#gets bonus vs light units.
			#Terran
			'Marine': 5,
			'Reaper': 5,
			'Hellion': 5,
			'SCV': 40,
			'WidowMine': 30,		
			'WidowMineBurrowed': 50,	
			'SiegeTank': 25,
			'SiegeTankSieged': 25,
			#Protoss
			'Zealot': 5,
			'Adept': 10,
			'Sentry': 10,
			'HighTemplar': 15,
			'DarkTemplar': 20,
			#Zerg
			'Zergling': 5,
			'Hydralisk': 10,
			'Infestor': 30,
		}

	def make_decision(self, game, unit):
		self.saved_position = unit.position #first line always.
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)	
		self.trackHealth()	
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

		self.shadeOrder = 'Search'
		#1a priority is to send shade towards enemy if we can.
		if self.psionicTransfer():
			self.label = 'Go Go Shade'
			return #sending Psionic Transfer scout
		
		#keep safe from effects
		if self.game.effectSafe(self):
			self.label = 'Dodging'
			return #dodging effects.	
		
		#check if we need to come home and defend.
		self.comeHome = self.game.checkHome(self)			
		


		self.closestEnemies = self.game.getUnitEnemies(self)
		#get the order for our shade
		self.ownerOrder()		
		
		if self.closestEnemies.amount > 0:
			
			#check if we are surrounded
			if self.game.checkSurrounded(self):
				self.shadeOrder = 'Surrounded'

			#see if we are able to escape if needed.
			# if self.game.canEscape(self) and self.game.keepSafe(self):
			# 	self.label = 'Retreating Safe'
			# 	return #staying alive

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

		#print ('Adept has nothing to do for some reason')

	def trackHealth(self):
		if (self.unit.health + self.unit.shield) < self.last_health:
			self.damaged = True
			self.last_health_update = self.game.time
		elif self.damaged:
			if self.last_health_update <= (self.game.time - 2):
				self.damaged = False
		self.last_health = self.unit.health + self.unit.shield
		



	def psionicTransfer(self):
		#see if we need to cast a shade at the enemy.
		if AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT in self.abilities and self.game.can_afford(ADEPTPHASESHIFT_ADEPTPHASESHIFT):
			self.game.combinedActions.append(self.unit(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, self.unit.position))
			return True
		return False
	
	def psionicTransferReal(self):
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


	def workerSearch(self) -> bool:
		if self.game.defend_only or self.game.under_attack:
			return False
		townhalls = self.closestEnemies.filter(lambda x: x.type_id in {NEXUS,HATCHERY,COMMANDCENTER,ORBITALCOMMAND} and x.distance_to(self.unit) > 7)
		if len(townhalls) > 0:
			return True
		return False

		
		

	def ownerOrder(self):
		#list of things we could tell our shade to do.
		#if surrounded by enemies, shade should find a safe place to move too.
		if len(self.closestEnemies) > 0 and self.game.checkSurrounded(self):
			self.shadeOrder = 'Surrounded'
		#if we are being told to come home, then shade should head towards the defensive point.
		elif self.comeHome:
			self.shadeOrder = 'ComeHome'
		#if we are near an enemy base, try to get near workers to kill them.
		elif self.workerSearch():
			self.shadeOrder = 'WorkerSearch'
		#check general retreat.
		elif self.game.defend_only and not self.game.under_attack and self.unit.distance_to(self.game.defensive_pos) > 3:
			self.shadeOrder = 'GoDefensivePoint'
		#if we are in battle, shade should go behind the lines and try to pick off soft targets like infestors.
		elif len(self.closestEnemies) > 0 and self.findPriorityTargets():
			self.shadeOrder = 'PriorityTarget'
		#if we are in battle, have shade go behind us like a blink.
		elif len(self.closestEnemies) > 0:
			self.shadeOrder = 'Battle'
		elif self.game.moveRally and not self.game.under_attack and self.unit.distance_to(self.game.rally_pos) > 3:
			self.shadeOrder = 'MoveRally'
		#if we are scouting, have the shade go into the base and search around.
		else:
			self.shadeOrder = 'None'


	def checkChasing(self, targetEnemy):
		if self.shadeOrder == 'Battle':
			enemy_distance = self.unit.distance_to(targetEnemy)
			if enemy_distance > 6:
				lead_position = self.game.leadTarget(targetEnemy, self)
				overall = self.unit.distance_to(lead_position) - enemy_distance
				if overall > 0:
					self.shadeOrder = 'Chase'
					self.chasePosition = lead_position


	def findPriorityTargets(self):
		if len(self.closestEnemies) > 0:
			targets = self.closestEnemies.filter(lambda x: x.type_id in {SIEGETANKSIEGED,INFESTOR,INFESTORBURROWED} and x.distance_to(self.unit) > 4)
			if len(targets) > 0:
				return True


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
	def wasDamaged(self) -> bool:
		return self.damaged

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
