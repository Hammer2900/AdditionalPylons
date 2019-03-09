import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3
from sc2 import Race

'''
Observer Info
-----------------
Attributes: Light, Mechanical, Detector
Defence:
	Health: 40
	Sheild: 20
	Armor: 0 (+1)
Sight: 11 (+2.75)
Speed: 2.62 (+1.32)
Strong against:
    Dark Templar
    Banshee
    Roach
Weak against:
    Photon Cannon
    Missile Turret
    Spore Crawler
'''
_debug = False

class Observer:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'
		self.expansionScout = False

	def make_decision(self, game, unit):
		self.saved_position = unit.position #first line always.
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)

		if self.expansionScout and self.game.enemy_race == Race.Zerg:
			self.expansionList()
		else:
			self.runList()

		#debugging info
		if _debug or self.unit.is_selected:
			if self.last_target:
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, self.last_target, (155, 255, 25))
			self.game._client.debug_text_3d(self.label, self.unit.position3d)



	def expansionList(self):
		self.closestEnemies = self.game.getUnitEnemies(self)
		self.closestEnemies = self.closestEnemies.exclude_type([DRONE,PROBE,SCV])
		if self.closestEnemies.amount > 0:		
			if self.keepSafe():
				self.label = 'Retreating'
				return #trying to stay alive.
		
		if self.checkExpansion():
			self.label = 'Expansion Check'
			return #making sure the next expansion slot is available.		


	def runListExp(self):
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			if self.keepSafe():
				self.label = 'Spotter Retreating'
				return #trying to stay alive.

		#find the friendly closest to the enemy that doesn't
		if self.findFriendly():
			self.label = 'Spotting for Friendly'
			return #found a place to spot.
	
		#keep distance from other observers.
		if self.keepDistance():
			self.label = 'Keeping Distance'
			return #moving away.

		#6 move the closest known enemy.
		if self.game.moveToEnemies(self):
			self.label = 'Spotter Moving Enemy'
			return #moving to next target.
		
		#7 wait until our shield is at 100%
		if self.unit.shield_percentage < 1:
			self.label = 'Spotter Full Regen'
			self.last_target = None	
			return #chillin until healed
			
		#8 find the enemy
		if self.game.searchEnemies(self):
			self.label = 'Spotter Searching'
			return #looking for targets	
		
		#if it's all taken, go scout the enemy.
		if self.scoutEnemy():
			self.label = 'Scout Enemy'
			return #moving towards enemy.




	def runList(self):
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:		
			if self.keepSafe():
				self.label = 'Spotter Retreating'
				return #trying to stay alive.

		#keep distance from other observers.
		if self.keepDistance():
			self.label = 'Keeping Distance'
			return #moving away.

		#6 move the closest known enemy.
		if self.game.moveToEnemies(self):
			self.label = 'Spotter Moving Enemy'
			return #moving to next target.
		
		#7 wait until our shield is at 100%
		if self.unit.shield_percentage < 1:
			self.label = 'Spotter Full Regen'
			self.last_target = None	
			return #chillin until healed
			
		#8 find the enemy
		if self.game.searchEnemies(self):
			self.label = 'Spotter Searching'
			return #looking for targets
	
		if self.scoutEnemy():
			self.label = 'Scout Enemy'
			return #moving towards enemy.			
		
		self.label = 'Idle'
		self.last_target = None



	def keepDistance(self):
		#find other observers that are closer than 11 distance away from us, and get the closest.
		if self.game.units(OBSERVER).tags_not_in([self.unit.tag]).closer_than(11, self.unit).exists:
			#move away from the closest.
			nearest = self.game.units(OBSERVER).tags_not_in([self.unit.tag]).closest_to(self.unit)
			retreatPoint = self.game.findSimpleRetreatPoint(self.unit, nearest)
			if retreatPoint:
				#self.last_target = retreatPoint.position
				if self.checkNewAction('move', retreatPoint[0], retreatPoint[1]):
					self.game.combinedActions.append(self.unit.move(retreatPoint))
				return True
		return False
	
	
	def surveillanceMode(self):
		if AbilityId.MORPH_SURVEILLANCEMODE in self.abilities and self.game.can_afford(MORPH_SURVEILLANCEMODE):
			self.game.combinedActions.append(self.unit(AbilityId.MORPH_SURVEILLANCEMODE))
			return True
		return False
	
	def observerMode(self):
		if AbilityId.MORPH_OBSERVERMODE in self.abilities and self.game.can_afford(MORPH_OBSERVERMODE):
			self.game.combinedActions.append(self.unit(AbilityId.MORPH_OBSERVERMODE))
			return True
		return False
	
	def enemyIntel(self):
		#if we have enemies around us and there isn't another obsever within 12 distance, go into scout mode.
		if self.game.units(OBSERVER).closer_than(12, self.unit).amount == 1 and self.game.known_enemy_units.amount > 0:
			#found enemies, need to use our ability here if possible.
			if self.checkNewAction('stop', 0, 0):
				self.game.combinedActions.append(self.unit.stop())
				self.last_target = None
			return True
		
		return False
	
	def scoutEnemy(self):
		#go to enemy base or to a random expansion.
		if self.unit.is_moving:
			return True #moving somewhere already
		searchPos = self.game.getSearchPos(self.unit)
		if self.checkNewAction('move', searchPos[0], searchPos[1]):
			self.game.combinedActions.append(self.unit.move(searchPos))
			self.last_target = Point3((searchPos.position.x, searchPos.position.y, self.game.getHeight(searchPos.position)))			
			return True
		return False
			
	def checkExpansion(self):
		#check to see if a unit is already there, if not, move to it.
		self.game.expPos
		
		if self.game.units(OBSERVER).closer_than(2, self.game.expPos).amount == 1 and self.unit.distance_to(self.game.expPos) > 3:
			return False #someone already there.
			
		if self.unit.is_moving:
			return True #moving somewhere already

		#check if we are already there, if not move to it.
		searchPos = self.game.expPos
		if self.unit.distance_to(searchPos) > 3:
			if self.checkNewAction('move', searchPos[0], searchPos[1]):
				self.game.combinedActions.append(self.unit.move(searchPos))
				self.last_target = Point3((searchPos.position.x, searchPos.position.y, self.game.getHeight(searchPos.position)))			
				return True
		else:
			#we are already there, detect enemies in our range and if it's clear, move on.
			#print (self.game.units(OBSERVER).closer_than(12, self.unit).amount)
			if self.game.units(OBSERVER).closer_than(12, self.unit).amount == 1:
				#found enemies, need to use our ability here if possible.
				if self.checkNewAction('stop', searchPos[0], searchPos[1]):
					self.game.combinedActions.append(self.unit.stop())
					self.last_target = None
				# else :
				# 	self.surveillanceMode()
				return True
		return False

	def keepSafe(self):
		#find out if detector units are near.
		detector = self.game.findDetectors(self.unit, 11)
		if detector:
			self.retreating = True
			#retreatPoint = self.game.findRetreatTarget(self.unit, closestEnemy, True)
			retreatPoint = self.game.findAirRetreatTarget(self.unit, inc_size=3, enemy_radius=10)
			if retreatPoint:
				if self.checkNewAction('move', retreatPoint[0], retreatPoint[1]):
					self.game.combinedActions.append(self.unit.move(retreatPoint))
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
	
	@property
	def isSolo(self) -> bool:
		return self.solo
		
	