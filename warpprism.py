import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3
from operator import itemgetter

'''
Warp Prism
-----------------
Load Range: 6
Sight: 10
Cargo Capacity: 8
Speed 4.13 (+1.23)
Attributes: Armored, Mechanical, Psionic

Watch over the assigned units, pick them up when shield is low and
release them back to fighting when shield is back to full strength.
'''
_debug = True
log = False

class WarpPrism:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.last_action = ''
		self.lastcommand = ''
		self.last_target = None
		self.label = 'Idle'
		self.retreating = False

	def make_decision(self, game, warpprism):
		self.game = game
		self.warpprism = warpprism
		self.pickup = False
		self.abilities = self.game.allAbilities.get(self.warpprism.tag)
		self.runList()
		
		#debugging info
		if _debug or self.warpprism.is_selected:
			if self.last_target:
				spos = Point3((self.warpprism.position3d.x, self.warpprism.position3d.y, (self.warpprism.position3d.z + 1)))
				self.game._client.debug_line_out(spos, self.last_target, (155, 255, 25))
			self.game._client.debug_text_3d(self.label, self.warpprism.position3d)
		
		
		
	def runList(self):
		#our main priority is to make sure we don't die with units on board.
		if self.executeOrder66():
			self.label = "Order 66"
			return #we are going down.
		
		#2 if we have space, and there is a unit in trouble, go pick them up
		if self.extractionNeeded():
			self.label = "Extracting"
			return #lets go get em!
		
		#3 if not extacting, make sure we are out of attack range.
		if self.keepRange():
			self.label = "Adjusting Range"
			return

		#3 priority is to make sure our unit is safe.
		if self.keepSafe():
			self.label = "Retreating"
			return #staying alive.

		#4 if there is a unit with full shields in our cargo, take them to battle.
		if self.battleDropOff():
			self.label = "Battle Drop"
			return #dropping off near the closest enemy.

		#move towards friendly units near enemy.
		if self.moveFriendlies():
			self.label = "Moving to Action"
			return #moving to friendly
		



		# 
		# 
		# #4 if there is a unit with full shields in our cargo, take them to battle.
		# if self.battleDropOff():
		# 	self.label = "Battle Drop"
		# 	return #dropping off near the closest enemy.
		# 	
		# #5 if cargo is full, go drop off our cargo in a safe zone.
		# if self.safeZoneDrop():
		# 	self.label = "Safe Zone Drop"
		# 	return #dropping off in a safe zone.
		# 
		# #6 if we have cargo space and none of the units are in need of help, just shadow the military and wait for backup.
		# if self.shadowUnits():
		# 	self.label = "Shadowing Units"
		# 	return
		# 
		# #7 else, might as well find a place to setup for warping units.
		# if self.warpSetUp():
		# 	self.label = "Warp Setup Moving"
		# 	return #moving to setup a warp spot.


	

	def battleDropOff(self):
		#check our passengers and see if any have a full shield.
		#print (self.abilities)
		if self.warpprism.cargo_used == 0:
			return False #nobody to drop off.
		
		for passenger in self.warpprism.passengers:
			if passenger.shield < 1:
				return False #everyone is not ready to go.
		#if we make it to here, then everyone wants to be dropped back into battle.
		#find the closest friendly to drop near.
		fUnits = self.game.units().not_flying.filter(lambda x: x.can_attack_ground)
		if self.game.known_enemy_units.exists and len(self.game.units().not_flying) > 0 and fUnits:
			closestFriendly = fUnits.closest_to(self.game.known_enemy_units.closest_to(self.warpprism))
		elif len(self.game.units().not_flying) > 0 and fUnits:
			closestFriendly = fUnits.closest_to(self.warpprism)
		if closestFriendly:
			if self.warpprism.distance_to(closestFriendly) > 3:
				if self.checkNewAction('move', closestFriendly.position[0], closestFriendly.position[1]):
					self.game.combinedActions.append(self.warpprism.move(closestFriendly))
				return True
			else:
				dropPos = self.game.findDropTarget(self.warpprism, closestFriendly, dis1=6, dis2=8)
				if dropPos:
					if AbilityId.UNLOADALLAT_WARPPRISM in self.abilities and self.game.can_afford(UNLOADALLAT_WARPPRISM):
						self.game.combinedActions.append(self.warpprism(AbilityId.UNLOADALLAT_WARPPRISM, self.warpprism.position))
						return True
		return False


	def executeOrder66(self):
		if (self.warpprism.health_percentage * 100) < 10:
			#drop all units we are going down.
			if self.warpprism.cargo_used > 0:
				dropPos = self.game.findDropTarget(self.warpprism, self.warpprism, dis1=2, dis2=4)
				if dropPos:
					if AbilityId.UNLOADALLAT_WARPPRISM in self.abilities and self.game.can_afford(UNLOADALLAT_WARPPRISM):
						self.game.combinedActions.append(self.warpprism(AbilityId.UNLOADALLAT_WARPPRISM, self.warpprism.position))
						return True
			#go to the enemy base and scout as much as possible before dying.
			searchPos = self.game.getSearchPos(self.warpprism)
			if self.checkNewAction('move', searchPos[0], searchPos[1]):
				self.game.combinedActions.append(self.warpprism.move(searchPos))
			return True
		return False
		
	
	def keepRange(self):
		(danger, closestEnemies) = self.game.inRange(self.warpprism)
		if danger:
			#move out of range.
			retreatPoint = self.game.findRangeRetreatTarget(self.warpprism, closestEnemies, inc_size=1)
			if retreatPoint:
				self.last_target = retreatPoint.position
				if self.checkNewAction('move', retreatPoint[0], retreatPoint[1]):
					self.game.combinedActions.append(self.warpprism.move(retreatPoint))
				return True
			
		
	def keepSafe(self):
		#find out if we are in danger, and if we are then retreat.
		(danger, closestEnemy) = self.game.inDanger(self.warpprism, True, friend_range=10, enemy_range=10)
		if danger:
			self.retreating = True
			retreatPoint = self.game.findAirRetreatTarget(self.warpprism, inc_size=3, enemy_radius=10)
			if retreatPoint:
				self.last_target = retreatPoint.position
				if self.checkNewAction('move', retreatPoint[0], retreatPoint[1]):
					self.game.combinedActions.append(self.warpprism.move(retreatPoint))
				return True

		self.retreating = False
		return False

	def extractionNeeded(self):
		#find units near us, and see if they are retreating.
		if self.warpprism.shield > 0:
			freeCargo = self.warpprism.cargo_max - self.warpprism.cargo_used
			friendlyClose = self.game.units().not_flying.not_structure.exclude_type([ADEPTPHASESHIFT]).closer_than(10, self.warpprism).filter(lambda x: x.cargo_size <= freeCargo).sorted(lambda x: x.distance_to(self.warpprism))
			for friend in friendlyClose:
				#find the unit object so we can check if retreating.
				#print (friend.name)
				unitObj = self.game.objectByTag(friend)
				if unitObj.retreating:
					#if we are close enough for pickup, do so.
					if self.warpprism.distance_to(friend.position) > 6: # + self.warpprism.radius + friend.radius:
						if self.checkNewAction('move', friend.position[0], friend.position[1]):
							self.game.combinedActions.append(self.warpprism.move(friend.position))
							return True
					else:
						if AbilityId.LOAD_WARPPRISM in self.abilities and self.game.can_afford(LOAD_WARPPRISM):
							self.game.combinedActions.append(self.warpprism(AbilityId.LOAD_WARPPRISM, friend))
							return True
		return False

	def moveFriendlies(self):
		#find the friendly unit that is closest to enemy and move towards it, or just move to the closest friendly if no enemies fround
		fUnits = self.game.units().not_flying.filter(lambda x: x.can_attack_ground)
		if self.game.known_enemy_units.exists and len(self.game.units().not_flying) > 0 and fUnits:
			closestFriendly = fUnits.closest_to(self.game.known_enemy_units.closest_to(self.warpprism))
		elif len(self.game.units().not_flying) > 0 and fUnits:
			closestFriendly = fUnits.closest_to(self.warpprism)
		if closestFriendly:
			#if we are not close to it, then our priority is to get there.
			if self.warpprism.distance_to(closestFriendly) > 2:
				if self.checkNewAction('move', closestFriendly.position.x, closestFriendly.position.y):
					self.game.combinedActions.append(self.warpprism.move(closestFriendly))
				self.last_target = Point3((closestFriendly.position3d.x, closestFriendly.position3d.y, (closestFriendly.position3d.z + 1)))
				return True
		return False

	def deliverUnits(self):
		#make sure we don't deliver them to danger
		(danger, junkEnemy) = self.game.inDanger(self.warpprism, False, friend_range=8, enemy_range=8)
		if self.game.time > self.nextdrop and not danger:
			if self.game.known_enemy_units.exclude_type([ADEPTPHASESHIFT]).exists:
				#see if there is enemy close enough for a dropoff.
				enemyTarget = self.game.findGroundTarget(self.warpprism, can_target_air=False, max_enemy_distance=8, target_hitpoints=True, target_buildings=False)
				if not enemyTarget:
					enemyTarget = self.game.findGroundTarget(self.warpprism, can_target_air=False, max_enemy_distance=8, target_hitpoints=True, target_buildings=True)
				if enemyTarget:
					#find a place on the ground near the enemyTarget.
					dropPos = self.game.findDropTarget(self.warpprism, enemyTarget, dis1=6, dis2=8)
					if dropPos:
						if AbilityId.UNLOADALLAT_WARPPRISM in self.abilities and self.game.can_afford(UNLOADALLAT_WARPPRISM):
							self.game.combinedActions.append(self.warpprism(AbilityId.UNLOADALLAT_WARPPRISM, self.warpprism.position))
							return True
				else:
					# move to nearest enemy ground unit/building because no enemy unit is closer than 5
					closestEnemy = self.game.known_enemy_units.not_flying.closest_to(self.warpprism)
					if self.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
						self.game.combinedActions.append(self.warpprism.move(closestEnemy))
					return True
		return False



	def checkNewAction(self, action, posx, posy):
		actionStr = (action + '-' + str(posx) + '-' + str(posy))		
		if actionStr == self.last_action:
			return False
		self.last_action = actionStr
		return True
		
	def funeral(self, game):
		print ('warp died')
	
	def updateAssigned(self):
		if len(self.assigned_units) > 0:
			objs = []
			for unit_tag in self.assigned_units:
				unit_obj = self.game.units(IMMORTAL).find_by_tag(unit_tag)
				unit_wrapper = self.game._im_objects.get(unit_tag)
				self.assigned_dict.update({unit_tag:[unit_wrapper, unit_obj]})
				objs.append(unit_obj)
			self.assigned_objects = objs
			
	def addAssignedUnit(self, unit_tag):
		self.assigned_units.append(unit_tag)
		self.updateAssigned()
		
	def removeAssignedUnit(self, unit_tag):
		self.assigned_units.remove(unit_tag)
		del self.assigned_dict[unit_tag]
		self.updateAssigned()
		
		
		
		
		
	