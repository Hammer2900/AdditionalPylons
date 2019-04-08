import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

'''
Disruptor Info
-----------------
Description: Ground Unit
Built From: Robotics Facility
Requirements: Robotics Bay
Cost:
	Minerals: 150
	Gas: 150
	Speed: 36
	Supply: 3
Attributes: Armored, Mechanical
Defence:
	Health: 100
	Shield: 100
	Armor: 1 (+1)
Sight: 9
Speed: 3.15
Cargo Size: 4
Strong against:
    Marauder
    Hydralisk
    Probe
Weak against:
    Thor
    Ultralisk
    Immortal
'''
_debug = False

class Disruptor:

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
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:

			#keep safe from effects
			if self.game.effectSafe(self):
				self.label = 'Dodging'
				return #dodging effects.
			
			#send a nova if we can.
			if self.sendNova():
				self.label = 'Firing Nova'
				return #sending Nova
	
			#save our butts if we can
			if self.game.keepSafe(self):
				self.label = 'Retreating Death'
				return #staying alive
			
			#3 priority is to keep our distance from enemies
			if self.KeepKiteRange():
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
		
		#move the closest known enemy.
		if self.game.moveToEnemies(self):
			self.label = 'Moving Enemy'
			return #moving to next target.

		#find the enemy
		if self.game.searchEnemies(self):
			self.label = 'Search'
			return #looking for targets

		self.label = 'Idle'

		#print ('Adept has nothing to do for some reason')


	def findKiteBackTarget(self, enemy):
		#find out what our attack range is.
		#get the distance of the enemy - our attack range and move that far back.
		dist = 0
		if AbilityId.EFFECT_PURIFICATIONNOVA in self.abilities and self.game.can_afford(EFFECT_PURIFICATIONNOVA):
			dist = self.unit.distance_to(enemy) - (8 + enemy.radius)
		else:
			dist = self.unit.distance_to(enemy) - (12 + enemy.radius)
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

	def sendNova(self):
		#EFFECT_PURIFICATIONNOVA
		#targetEnemy = self.game.findGroundTarget(self.unit, can_target_air=False, max_enemy_distance=8)
		#check to see if a nova exists already, if so, wait.
		if len(self.game.units(DISRUPTORPHASED)) > 0:
			#check to see if they re close to us.
			if len(self.game.units(DISRUPTORPHASED).closer_than(10, self.unit)) > 0:
				return False
		
		targetEnemy = self.findNovaTarget()
		if targetEnemy:
			if AbilityId.EFFECT_PURIFICATIONNOVA in self.abilities and self.game.can_afford(EFFECT_PURIFICATIONNOVA):
				self.game.combinedActions.append(self.unit(AbilityId.EFFECT_PURIFICATIONNOVA, targetEnemy.position))
				return True
		return False		



	def findNovaTarget(self):
		#if a nova is already in play, wait.
		if self.game.units(NOVA).closer_than(5, self.unit):
			return None
		#find atleast 3 targets in radius.
		if self.closestEnemies.not_structure.not_flying.closer_than(10, self.unit):
			enemycenter =  self.game.center3d(self.closestEnemies.not_structure.not_flying.closer_than(10, self.unit))
			#check if there are 3 targets in the radius.
			enemies = self.closestEnemies.not_structure.not_flying.closer_than(1.5, enemycenter)
			if enemies and enemies.amount > 0:
				#find the closest enemy to center.
				closestEnemy = enemies.closest_to(enemycenter)
				#check to make sure there are no friendlies within 1.5 of the target.
				friendlies = self.game.units.not_structure.not_flying.closer_than(1.5, closestEnemy)
				if not friendlies:
					return closestEnemy
		return None
	
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
	

				
			
	
		

		
		
		
		
	