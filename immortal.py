import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3
import datetime
import time

'''
Immortal Info
-----------------
Attributes: Armored, Mechanical
Attack 1:
	Targets: 	Ground
	Damage:	 	20 (+2)
	DPS:	 	19.2 (+1.92)
	Cooldown:	1.04
	Bonus:	 	+30 (+3) vs Armored
	Bonus DPS:	+28.9 (+2.9) vs Armored
	Range:	 	6
Defence:
	Health: 200
	Shield: 100
	Armor: 1 (+1)
Sight: 9
Speed: 3.15
Cargo Size: 4
Strong against:
    Siege Tank
    Stalker
    Roach
Weak against:
    Marine
    Zealot
    Zergling
'''

_debug = False

class Immortal:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'
		self.is_hallucination = None
		self.comeHome = False
		self.homeTarget = None
		self.enemy_target_bonuses = {
			#gets bonus vs armored units.
			#Terran
			'Marauder': 5,
			'Thor': 5,
			'SiegeTank': 25,
			'SiegeTankSieged': 25,			
			'SCV': 40,
			'Viking': 5,
			'VikingFighter': 5,
			'Cyclone': 5,
			'WidowMine': 30,	
			'WidowMineBurrowed': 50,		
			#Protoss
			'Stalker': 5,
			'Immortal': 5,
			'Disruptor': 5,
			#Zerg
			'Roach': 5,
			'Infestor': 30,
			'Ultralisk': 5,
		}		

	def make_decision(self, game, unit):
		self.saved_position = unit.position #first line always.
		self.game = game
		self.unit = unit

		if self.is_hallucination is None:
			self.check_hallucination()
		
		if self.is_hallucination:
			self.runHallList()
		else:
			self.runList()
		

		#debugging info
		if _debug or self.unit.is_selected:
			if self.last_target:
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, self.last_target, color=Point3((155, 255, 25)))
			self.game._client.debug_text_3d(self.label, self.unit.position3d)
			
			
			
	def runList(self):
		
		#keep safe from effects
		if self.game.effectSafe(self):
			self.label = 'Dodging'
			return #dodging effects.	
		
		#check if we need to come home and defend.
		self.comeHome = self.game.checkHome(self)
				
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:

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
		
		#move to rally point before attacking:
		if self.game.moveRally and not self.game.under_attack:
			self.game.rally(self)
			self.label = 'Rallying'
			return #moving to rally
		
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

		self.label = 'Idle'


	def runHallList(self):
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			#look around our range and find the highest target value and move towards it.
			if self.moveNearEnemies(self):
				self.label = 'Hall Moving Priority Target'
				return #moving towards a better target.			
			return #moving to friend.
					
		#6 move the closest known enemy.
		if self.game.moveToEnemies(self):
			self.label = 'Hall Moving Enemy'
			return #moving to next target.
					
		#8 find the enemy
		if self.game.searchEnemies(self):
			self.label = 'Hall Searching'
			return #looking for targets
		
		self.label = 'Idle'		

	def check_hallucination(self):
		#if a robo is near us, then likely not a hallucination.
		if len(self.game.units(ROBOTICSFACILITY)) == 0:
			self.is_hallucination = True
			return
		#robo exist in game, see if it's closer than 4 distance away.
		if self.game.units(ROBOTICSFACILITY).closer_than(4, self.unit):
			self.is_hallucination = False
			return
		else:
			self.is_hallucination = True
			return
		self.is_hallucination = False

	def moveNearEnemies(self, unit_obj):
		if not self.closestEnemies:
			return False  # no enemies to move to
		
		#find the center of enemies and move to it to draw fire.
		#targetPoint = self.game.findAOETarget(self, 25, 6, minEnemies=1)
		targetPoint = self.game.findDrawFireTarget(self, 10)
		if targetPoint:
			if self.checkNewAction('move', targetPoint.position.x, targetPoint.position.y):
				self.game.combinedActions.append(self.unit.move(targetPoint.position))
			return True
		return False

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
		if self.is_hallucination:
			return True
		return False
	
	@property
	def sendHome(self) -> bool:
		return self.comeHome	
		
		
		
		
		
	