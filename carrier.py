import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

'''
Carrier Info
-----------------
Description: Large Air Unit
Built From: Stargate
Requirements: Fleet Beacon
Cost:
	Minerals: 350 (+15 / Interceptor)
	Vaspene: 250
	Gamespeed: 86
	Supply: 6
Attributes: Armored, Massive, Mechanical
Attack 1:
	Targets:	 	Ground / Air
	Damage:	 	5 (+1) (x2) (x8 Interceptors)
	DPS:	 	37.4 (+7.5) (w/ 8 Interceptors)
	Cooldown:	 	2.14 (Interceptor attack cooldown)
		0.36 (Interceptor launch)
		0.09 (Interceptor launch w/ Graviton Catapult, first 4)
		0.18 (Interceptor launch w/ Graviton Catapult, last 4)
	Range:	 	8 to 14 (See Description)
	Defence:
		Health: 250
		Shield: 150
		Armor: 2 (+1)
Sight: 12
Speed: 2.62
Strong against:
    Thor
    Mutalisk
    Phoenix
Weak against:
    Viking
    Corruptor
    Tempest
'''
_debug = False

class Carrier:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'
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
		#get all the enemies around us.
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			#see if we are able to escape if needed.
			#2 keep safe again.
			# if self.game.keepSafe(self):
			# 	self.label = 'Retreating Death'
			# 	return #staying alive

			#3 priority is to keep our distance from enemies
			if self.KeepKiteRange():
			 	self.label = 'Kiting'
			 	return #kiting
			
			#1 priority is always attack first if we can
			if self.attack():
			 	self.label = 'Attacking'
			 	return #we attacked this step.



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
		self.label = 'Idle'


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
		dist = self.unit.distance_to(enemy) - 8
		#move away from the target that much.
		if self.unit.position != enemy.position:
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
		enemyThreats = self.closestEnemies.closer_than(10, self.unit).filter(lambda x: x.can_attack_air).sorted(lambda x: x.distance_to(self.unit))
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
	

	
