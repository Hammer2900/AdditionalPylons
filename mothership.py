import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

'''
Mothership Info
-----------------

Description: Large Air Unit
Built From: Nexus
Requirements: Fleet Beacon, No Mothership
Cost:
	Minerals: 400
	Vespene: 400
	GameSpeed: 114
	Supply: 8
Attributes: Armored, Massive, Psionic, Mechanical
Attack 1:
	Targets:	 	Ground / Air
	Damage:	 	6 (+1) x6
	DPS:	 	22.8 (+3.78)
	Cooldown:	 	1.58
	Range:	 	7
Defence:
	Health: 350
	Shield: 350
	Armor: 2 (+1)

Energy: 50 / 200
Sight: 14
Speed: 2.62
Weak against:
    Viking
    Corruptor
    Void Ray
'''
_debug = False

class Mothership:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'
		self.comeHome = False
		self.homeTarget = None
		self.enemy_target_bonuses = {
			#Terran
			'Medivac': 40,
			'SCV': 45,
			'SiegeTank': 25,
			'SiegeTankSieged': 25,
			'WidowMine': 30,			
			'Raven': 20,
			#Protoss
			'Colossus': 15,
			'Mothership': 20,
			'Phoenix': 5,	
			'VoidRay': 5,
			'Tempest': 20,
			#Zerg
			'Mutalisk': 5,
			'Infestor': 30,
			'Ultralisk': 25,
			'BroodLord': 25,
		}		
		
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
				self.game._client.debug_line_out(spos, self.last_target, color=Point3((155, 255, 25)))
			self.game._client.debug_text_3d(self.label, self.unit.position3d)

	def runList(self):


		#check if we need to come home and defend.
		self.comeHome = self.game.checkHome(self)

		#enemies around us mode.
		if self.game.effectSafe(self):
			self.label = 'Dodging'
			return #dodging effects.


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

			#see if we can time warp the area.
			if self.time_warp():
				self.label = 'Time Warping'
				return	

			#2 keep safe again.
			if self.game.keepSafe(self):
				self.label = 'Retreating Death'
				return #staying alive
	
			#3 priority is to keep our distance from enemies
			if self.game.KeepKiteRange(self):
				self.label = 'Kiting'
				return #kiting



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
		
		# #6 move the closest known enemy.
		# if self.game.moveToEnemies(self):
		# 	self.label = 'Moving Enemy'
		# 	return #moving to next target.
		# 
		# #7 wait until our shield is at 100%
		# if self.unit.shield_percentage < 1:
		# 	self.label = 'Full Regen'
		# 	self.last_target = None	
		# 	return #chillin until healed
			
		# #8 find the enemy
		# if self.game.searchEnemies(self):
		# 	self.label = 'Searching'
		# 	return #looking for targets
		# self.label = 'Idle'


	def time_warp(self):
		#find a group of at least 5 enemies together in the radius and then cast on them.
		aoeTarget = self.game.findAOETarget(self, 9, 3.5, minEnemies=5)  #range of 9, radius of 1.5
		if aoeTarget:
			if AbilityId.EFFECT_TIMEWARP in self.abilities and self.game.can_afford(EFFECT_TIMEWARP):
				self.game.combinedActions.append(self.unit(AbilityId.EFFECT_TIMEWARP, aoeTarget))
				return True
		return False
		


	def attack(self):
		if self.closestEnemies.closer_than(8, self.unit):
			self.last_target = None
			if self.checkNewAction('stop', 0, 0):
				self.game.combinedActions.append(self.unit.stop())
			return True
		return False

	def findKiteBackTarget(self, enemy):
		#find out what our attack range is.
		#get the distance of the enemy - our attack range and move that far back.
		dist = self.unit.distance_to(enemy) - (8 + enemy.radius)
		#move away from the target that much.
		targetpoint = self.unit.position.towards(enemy.position, distance=dist)
		return targetpoint

	def KeepKiteRange(self):
		#kite if we can.
		targetEnemy = self.findKiteTarget()
		if targetEnemy:
			#kitePoint = unit_obj.unit.position.towards(targetEnemy.position, distance=-0.1)
			kitePoint = self.findKiteBackTarget(targetEnemy)
			if kitePoint:
				self.last_target = kitePoint.position
				if self.checkNewAction('move', kitePoint[0], kitePoint[1]):
					self.game.combinedActions.append(self.unit.move(kitePoint))
					
				if self.unit.is_selected or _debug:
					self.game._client.debug_line_out(self.game.unitDebugPos(self.unit), self.game.p3AddZ(targetEnemy.position3d), color=Point3((0, 206, 3)))
					self.game._client.debug_line_out(self.game.unitDebugPos(self.unit), self.game.p2AddZ(kitePoint), color=Point3((212, 66, 244)))			
					
				return True
		return False


	def findKiteTarget(self):
		#find the closest unit to us and move away from it.
		enemyThreats = self.closestEnemies.not_structure.closer_than(12, self.unit).sorted(lambda x: x.distance_to(self.unit))
		if enemyThreats:
			return enemyThreats[0]

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
	
	@property
	def isHallucination(self) -> bool:
		return False
		
	@property
	def sendHome(self) -> bool:
		return self.comeHome

				
