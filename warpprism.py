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
_debug = False
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
		self.bonus_range = 9.5
		self.comeHome = False
		self.homeTarget = None

	def make_decision(self, game, unit):
		self.game = game
		self.unit = unit
		self.pickup = False
		self.abilities = self.game.allAbilities.get(self.unit.tag)
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
				
		
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			#our main priority is to make sure we don't die with units on board.
			if self.executeOrder66():
				self.label = "Order 66"
				return #we are going down.

			#3 priority is to keep our distance from enemies
			if self.KeepKiteRange():
				self.label = 'Kiting'
				return #kiting

		#go to either rally postition, defend position, or pylon position.
		move_position = None
		if self.game.defend_only:
			move_position = self.game.defensive_pos
		elif self.game.moveRally:
			move_position = self.game.rally_pos
		else:
			move_position = self.game.prism_pylon_pos
			
		#move to the position if we aren't near it.
		if self.moveMobilePosition(move_position):
			self.label = 'Moving to position'
			return
		
		if self.mobilePylon():
			self.label = "Mobile Pylon"
			return #pylon mode.		
		
		self.label = 'idle'

		
		
	def runListOld(self):
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			#our main priority is to make sure we don't die with units on board.
			if self.executeOrder66():
				self.label = "Order 66"
				return #we are going down.

			#3 priority is to keep our distance from enemies
			if self.KeepKiteRange():
				self.label = 'Kiting'
				return #kiting
	
		
			if self.mobilePylon():
				self.label = "Mobile Pylon"
				return #pylon mode.


		if self.clearPylonMode():
			self.label = 'Clearing Pylon'
			return

		#if we are in defend mode and we aren't under attack, then go to the defend point.
		if self.game.defend_only and not self.game.under_attack:
			self.game.defend(self)
			self.label = 'Defending'			
			return #defending.
		


		#move towards friendly units near enemy.
		if self.moveFriendlies():
			self.label = "Moving to Action"
			return #moving to friendly
		

	def moveMobilePosition(self, position):
		#if we are already in pylon position, don't move for small amounts.
		dist = 2
		if AbilityId.MORPH_WARPPRISMTRANSPORTMODE in self.abilities:
			dist = 10
		
		if position and self.unit.distance_to(position) > dist:
			#check to see if we need to get out of pylon position.
			if self.clearPylonMode():
				return True
			
			if self.checkNewAction('move', position.x, position.y):
				self.game.combinedActions.append(self.unit.move(position))
			return True
		return False		


	def clearPylonMode(self):
		#make sure there aren't any units warping in under us.
		#if not self.unit.is_ready:
		warping = self.game.units.filter(lambda x: not x.is_structure and not x.is_ready and x.distance_to(self.unit) < 4)
		if len(warping) > 0:
			return True
		
		if AbilityId.MORPH_WARPPRISMTRANSPORTMODE in self.abilities and self.game.can_afford(MORPH_WARPPRISMTRANSPORTMODE):
			self.game.combinedActions.append(self.unit(AbilityId.MORPH_WARPPRISMTRANSPORTMODE))
			return True
		return False
	
	def mobilePylon(self):
		if AbilityId.MORPH_WARPPRISMPHASINGMODE in self.abilities and self.game.can_afford(MORPH_WARPPRISMPHASINGMODE):
			self.game.combinedActions.append(self.unit(AbilityId.MORPH_WARPPRISMPHASINGMODE))
			self.last_target = None
			return True
		


	def mobilePylonOld(self):
		#if enemies are in range, but not close enough to damage us, then go into pylon mode.
		if len(self.closestEnemies) > 0:
			#not in ability is available, we aren't in pylon mode.
			if AbilityId.MORPH_WARPPRISMPHASINGMODE in self.abilities:
				#check to see if we want to be in pylon mode.
				if len(self.closestEnemies.closer_than(15, self.unit)) > 0 and len(self.closestEnemies.closer_than(9, self.unit)) == 0 and self.game.can_afford(MORPH_WARPPRISMPHASINGMODE):
					self.game.combinedActions.append(self.unit(AbilityId.MORPH_WARPPRISMPHASINGMODE))
					return True
			elif AbilityId.MORPH_WARPPRISMTRANSPORTMODE in self.abilities:
				#in pylon mode.  See if we should continue or leave.
				if (len(self.closestEnemies.closer_than(25, self.unit)) == 0 or len(self.closestEnemies.closer_than(9, self.unit)) > 0) and self.game.can_afford(MORPH_WARPPRISMTRANSPORTMODE):
					self.game.combinedActions.append(self.unit(AbilityId.MORPH_WARPPRISMTRANSPORTMODE))
				return True
		return False
				
			


	def KeepKiteRange(self):
		#kite if we can.	
		targetEnemy = self.findKiteTarget()
		if targetEnemy:
			kitePoint = self.findKiteBackTarget(targetEnemy)
			if kitePoint:
				if AbilityId.MORPH_WARPPRISMTRANSPORTMODE in self.abilities and self.game.can_afford(MORPH_WARPPRISMTRANSPORTMODE):
					self.game.combinedActions.append(self.unit(AbilityId.MORPH_WARPPRISMTRANSPORTMODE))
					return True

				if self.checkNewAction('move', kitePoint[0], kitePoint[1]):
					self.game.combinedActions.append(self.unit.move(kitePoint))
				if self.unit.is_selected or _debug:
					self.last_target = kitePoint.position
					self.game._client.debug_line_out(self.game.unitDebugPos(self.unit), self.game.p3AddZ(targetEnemy.position3d), color=Point3((0, 206, 3)))
					self.game._client.debug_line_out(self.game.unitDebugPos(self.unit), self.game.p2AddZ(kitePoint), color=Point3((212, 66, 244)))			
				return True
		return False

	def findKiteTarget(self):
		kitables = self.closestEnemies.filter(lambda x: not x.name in ['SCV', 'Probe', 'Drone'] and x.distance_to(self.unit) < self.bonus_range)
		if kitables:
			enemyThreats = kitables.sorted(lambda x: x.distance_to(self.unit))
			return enemyThreats[0]

	def findKiteBackTarget(self, enemy):
		dist = self.unit.distance_to(enemy) - (self.unit.radius + enemy.radius + self.bonus_range)
		#move away from the target that much.
		if self.unit.position != enemy.position:
			targetpoint = self.unit.position.towards(enemy.position, distance=dist)		
			return targetpoint
		
		
##LEGACY BELOW			
		

	def battleDropOff(self):
		#check our passengers and see if any have a full shield.
		#print (self.abilities)
		if self.unit.cargo_used == 0:
			return False #nobody to drop off.
		
		for passenger in self.unit.passengers:
			if passenger.shield < 1:
				return False #everyone is not ready to go.
		#if we make it to here, then everyone wants to be dropped back into battle.
		#find the closest friendly to drop near.
		fUnits = self.game.units().not_flying.filter(lambda x: x.can_attack_ground)
		if self.game.known_enemy_units.exists and len(self.game.units().not_flying) > 0 and fUnits:
			closestFriendly = fUnits.closest_to(self.game.known_enemy_units.closest_to(self.unit))
		elif len(self.game.units().not_flying) > 0 and fUnits:
			closestFriendly = fUnits.closest_to(self.unit)
		if closestFriendly:
			if self.unit.distance_to(closestFriendly) > 3:
				if self.checkNewAction('move', closestFriendly.position[0], closestFriendly.position[1]):
					self.game.combinedActions.append(self.unit.move(closestFriendly))
				return True
			else:
				dropPos = self.game.findDropTarget(self.unit, closestFriendly, dis1=6, dis2=8)
				if dropPos:
					if AbilityId.UNLOADALLAT_WARPPRISM in self.abilities and self.game.can_afford(UNLOADALLAT_WARPPRISM):
						self.game.combinedActions.append(self.unit(AbilityId.UNLOADALLAT_WARPPRISM, self.unit.position))
						return True
		return False


	def executeOrder66(self):
		if (self.unit.health_percentage * 100) < 10:
			#drop all units we are going down.
			if self.unit.cargo_used > 0:
				dropPos = self.game.findDropTarget(self.unit, self.unit, dis1=2, dis2=4)
				if dropPos:
					if AbilityId.UNLOADALLAT_WARPPRISM in self.abilities and self.game.can_afford(UNLOADALLAT_WARPPRISM):
						self.game.combinedActions.append(self.unit(AbilityId.UNLOADALLAT_WARPPRISM, self.unit.position))
						return True
			#go to the enemy base and scout as much as possible before dying.
			searchPos = self.game.getSearchPos(self.unit)
			if self.checkNewAction('move', searchPos[0], searchPos[1]):
				self.game.combinedActions.append(self.unit.move(searchPos))
			return True
		return False
		
	
	def keepRange(self):
		(danger, closestEnemies) = self.game.inRange(self.unit)
		if danger:
			#move out of range.
			retreatPoint = self.game.findRangeRetreatTarget(self.unit, closestEnemies, inc_size=1)
			if retreatPoint:
				self.last_target = retreatPoint.position
				if self.checkNewAction('move', retreatPoint[0], retreatPoint[1]):
					self.game.combinedActions.append(self.unit.move(retreatPoint))
				return True
			
		
	def keepSafe(self):
		#find out if we are in danger, and if we are then retreat.
		#(danger, closestEnemy) = self.game.inDanger(self.unit, True, friend_range=10, enemy_range=10)
		(danger, closestEnemy) = self.game.inDanger(self)
		if danger:
			self.retreating = True
			retreatPoint = self.game.findAirRetreatTarget(self.unit, inc_size=3, enemy_radius=10)
			if retreatPoint:
				self.last_target = retreatPoint.position
				if self.checkNewAction('move', retreatPoint[0], retreatPoint[1]):
					self.game.combinedActions.append(self.unit.move(retreatPoint))
				return True

		self.retreating = False
		return False

	def extractionNeeded(self):
		#find units near us, and see if they are retreating.
		if self.unit.shield > 0:
			freeCargo = self.unit.cargo_max - self.unit.cargo_used
			friendlyClose = self.game.units().not_flying.not_structure.exclude_type([ADEPTPHASESHIFT]).closer_than(10, self.unit).filter(lambda x: x.cargo_size <= freeCargo).sorted(lambda x: x.distance_to(self.unit))
			for friend in friendlyClose:
				#find the unit object so we can check if retreating.
				#print (friend.name)
				unitObj =  self.game.unitList.objectByTag(friend)
				if unitObj.retreating:
					#if we are close enough for pickup, do so.
					if self.unit.distance_to(friend.position) > 6: # + self.unit.radius + friend.radius:
						if self.checkNewAction('move', friend.position[0], friend.position[1]):
							self.game.combinedActions.append(self.unit.move(friend.position))
							return True
					else:
						if AbilityId.LOAD_WARPPRISM in self.abilities and self.game.can_afford(LOAD_WARPPRISM):
							self.game.combinedActions.append(self.unit(AbilityId.LOAD_WARPPRISM, friend))
							return True
		return False

	def moveFriendlies(self):
		#find the friendly unit that is closest to enemy and move towards it, or just move to the closest friendly if no enemies fround
		closestFriendly = None
		fUnits = self.game.units().not_flying.filter(lambda x: x.can_attack_ground)
		if self.game.known_enemy_units.exists and len(self.game.units().not_flying) > 0 and fUnits:
			closestFriendly = fUnits.closest_to(self.game.known_enemy_units.closest_to(self.unit))
		elif len(self.game.units().not_flying) > 0 and fUnits:
			closestFriendly = fUnits.closest_to(self.unit)
		if closestFriendly:
			#if we are not close to it, then our priority is to get there.
			if self.unit.distance_to(closestFriendly) > 2:
				if self.checkNewAction('move', closestFriendly.position.x, closestFriendly.position.y):
					self.game.combinedActions.append(self.unit.move(closestFriendly))
				self.last_target = Point3((closestFriendly.position3d.x, closestFriendly.position3d.y, (closestFriendly.position3d.z + 1)))
				return True
		return False

	def deliverUnits(self):
		#make sure we don't deliver them to danger
		(danger, junkEnemy) = self.game.inDanger(self.unit, False, friend_range=8, enemy_range=8)
		if self.game.time > self.nextdrop and not danger:
			if self.game.known_enemy_units.exclude_type([ADEPTPHASESHIFT]).exists:
				#see if there is enemy close enough for a dropoff.
				enemyTarget = self.game.findGroundTarget(self.unit, can_target_air=False, max_enemy_distance=8, target_hitpoints=True, target_buildings=False)
				if not enemyTarget:
					enemyTarget = self.game.findGroundTarget(self.unit, can_target_air=False, max_enemy_distance=8, target_hitpoints=True, target_buildings=True)
				if enemyTarget:
					#find a place on the ground near the enemyTarget.
					dropPos = self.game.findDropTarget(self.unit, enemyTarget, dis1=6, dis2=8)
					if dropPos:
						if AbilityId.UNLOADALLAT_WARPPRISM in self.abilities and self.game.can_afford(UNLOADALLAT_WARPPRISM):
							self.game.combinedActions.append(self.unit(AbilityId.UNLOADALLAT_WARPPRISM, self.unit.position))
							return True
				else:
					# move to nearest enemy ground unit/building because no enemy unit is closer than 5
					closestEnemy = self.game.known_enemy_units.not_flying.closest_to(self.unit)
					if self.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
						self.game.combinedActions.append(self.unit.move(closestEnemy))
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
		
	@property
	def isHallucination(self) -> bool:
		return False

	@property
	def sendHome(self) -> bool:
		return self.comeHome				
		
		
		
	