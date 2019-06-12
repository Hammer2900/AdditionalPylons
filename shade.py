import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3
from sc2.units import Units


_debug = False

'''
Phase Info
-----------------
Description: Ground Unit
Sight: 4
Speed: 3.5

		#CANCEL_ADEPTSHADEPHASESHIFT
		#CANCEL_ADEPTPHASESHIFT
		#ADEPTPHASESHIFT_ADEPTPHASESHIFT
		#AdeptPhaseShift
'''


class Shade:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.saved_position = None
		self.last_action = ''
		self.shade_start = None
		self.owner = None
		self.ownerOrder = None
		self.comeHome = False
		self.homeTarget = None
		self.cachedTarget = None
		self.emptyTarget = None
		self.enemy_target_bonuses = {
			'WidowMine': 300,
		}
		
		
	def make_decision(self, game, unit):
		self.saved_position = unit.position #first line always.
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)
		self.label = 'Idle'
		if not self.shade_start:
			self.shade_start = self.game.time
			#find our owner adept.
			self.owner = self.find_owner()
			self.emptyTarget = self.findEmptyExpansion()
	
		self.getOwnerOrder()
		self.runList()

		#debugging info
		if _debug or self.unit.is_selected:
			if self.owner:
				opos = Point3((self.owner.position3d.x, self.owner.position3d.y, (self.owner.position3d.z + 1)))
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, opos, color=Point3((155, 255, 25)))
			lb = "{} ||| {}".format(str(self.ownerOrder), self.label)
			self.game._client.debug_text_3d(lb, self.unit.position3d)


	def runList(self):
		self.closestEnemies = self.game.getUnitEnemies(self)

		if self.psionicCancel():
			return # canceled shade.
		
		if self.ownerOrders():
			self.label = 'Owners Order'
			return #doing orders
		
		if self.moveToExpansion():
			self.label = 'Moving to Expansion'
			return
		
		#priority is to move towards enemies not in range.
		if self.moveToEnemies():
			self.label = 'Moving to Enemies'
			return #moving to enemy
		
		if self.searchEnemies():
			self.label = 'Searching for Enemies'
			return #search enemies.
				


	def findEmptyExpansion(self):
		#loop each expansion, if it's owned by a friendly, then don't add it.
		locations = []
		for possible in self.game.expansion_locations:
			if not self.game.units().closer_than(6, possible).exists:
				locations.append(possible)
		if len(locations) > 0:
			#choose a location randomly.
			return random.choice(locations)
		return None

	def mineralLineTarget(self, townhall):
		if self.cachedTarget:
			return self.cachedTarget
		self.cachedTarget = townhall
		if self.game.state.mineral_field.closer_than(15, townhall):
			mins = self.game.state.mineral_field.closer_than(15, townhall)
			vasp = self.game.state.vespene_geyser.closer_than(15, townhall)
			mf = Units((mins + vasp))
			f_distance = 0
			mineral_1 = None
			mineral_2 = None
			if mf:
				for mineral in mf:
					#loop other minerals and find the 2 minerals that are furthest apart.
					for n_mineral in mf:
						#make sure it's not the same mineral.
						if mineral.position == n_mineral.position:
							continue
						#get the distance between the 2.
						t_dist = mineral.position3d.distance_to(n_mineral.position3d)
						if t_dist > f_distance:
							mineral_1 = mineral
							mineral_2 = n_mineral
							f_distance = t_dist
			nf = [mineral_1, mineral_2]
			if len(nf) == 0:
				return townhall
			center_pos = Point2((sum([item.position.x for item in nf]) / len(nf), \
					sum([item.position.y for item in nf]) / len(nf)))
			position = townhall.position.towards(center_pos, 7)
			self.cachedTarget = position
			return position
		
		return townhall
		


	def ownerOrders(self):
		if not self.owner:
			return False
		owner_pos = self.game.unitList.unitPosition(self.owner)
		if self.ownerOrder == 'GoDefensivePoint':
			if self.checkNewAction('move', self.game.defensive_pos.position[0], self.game.defensive_pos.position[1]):
				self.game.combinedActions.append(self.unit.move(self.game.defensive_pos))
			return True
		elif self.ownerOrder == 'ComeHome':
			homeTarget = self.game.unitList.unitHomeTarget(self.owner)
			if self.checkNewAction('move', homeTarget.position[0], homeTarget.position[1]):
				self.game.combinedActions.append(self.unit.move(homeTarget))
			return True
		elif self.ownerOrder == 'WorkerSearch':
			townhalls = self.closestEnemies.filter(lambda x: x.type_id in {NEXUS,HATCHERY,COMMANDCENTER,ORBITALCOMMAND} and x.distance_to(owner_pos) > 7)
			if len(townhalls) > 0:
				#move to the mineral line of the closest one.
				target = self.mineralLineTarget(townhalls.closest_to(self.unit))
				if self.checkNewAction('move', target.position[0], target.position[1]):
					self.game.combinedActions.append(self.unit.move(target))
				return True
		elif self.ownerOrder == 'PriorityTarget' and len(self.closestEnemies) > 0:
			#find a priority target, and move to it and 2.5 distance away from the bulk of the enemies.
			center_enemies = self.closestEnemies.center
			targets = self.closestEnemies.filter(lambda x: x.type_id in {SIEGETANKSIEGED,INFESTOR,INFESTORBURROWED}
												 and x.distance_to(owner_pos) > 4).sorted(lambda x: x.distance_to(center_enemies), reverse=True)
			if targets:
				target_pos = targets.first.position.towards(center_enemies, -2.5)
				if target_pos:
					if self.checkNewAction('move', target_pos.position[0], target_pos.position[1]):
						self.game.combinedActions.append(self.unit.move(target_pos))
					return True
		elif self.ownerOrder in {'Battle', 'Surrounded'} and len(self.closestEnemies) > 0:
			#find the center of the enemies around the nearest.
			#targets = self.closestEnemies.filter(lambda x: x.can_attack_ground and x.distance_to(self.owner) < 9)
			targets = self.closestEnemies.filter(lambda x: x.can_attack_ground)
			if targets:
				center_enemies = targets.center
				#get our owners position.
				#owner_pos = self.game.unitList.unitPosition(self.owner)
				target_pos = owner_pos.towards(center_enemies, -5)

				if self.checkNewAction('move', target_pos.position[0], target_pos.position[1]):
					self.game.combinedActions.append(self.unit.move(target_pos))
				return True
		elif self.ownerOrder == 'Chase':
			#get the target of the owner.
			chaseTarget = self.game.unitList.adeptChaseTarget(self.owner)
			if chaseTarget:
				if self.checkNewAction('move', chaseTarget.position[0], chaseTarget.position[1]):
					self.game.combinedActions.append(self.unit.move(chaseTarget))
				return True
		elif self.ownerOrder == 'MoveRally':
			if self.checkNewAction('move', self.game.rally_pos.position[0], self.game.rally_pos.position[1]):
				self.game.combinedActions.append(self.unit.move(self.game.rally_pos))
			return True			
		#print ('no order able', self.ownerOrder)
		return False	
		

	def getOwnerOrder(self):
		#use the owner tag to get the object, then get it's order.
		if not self.owner:
			self.ownerOrder = 'NoOwner'
		else:
			self.ownerOrder = self.game.unitList.adeptOrder(self.owner)

	def find_owner(self):
		if len(self.game.units(ADEPT)) > 0:
			owner = self.game.units(ADEPT).closest_to(self.unit)
			return owner
		return None
		

	def psionicCancel(self):
		#leave if it's not time to cancel yet.
		if (self.shade_start + 6.5) >= self.game.time:
			return False
		
		owner_pos = self.game.unitList.unitPosition(self.owner)
		
		#if the owner order is that we are surrounded, do not cancel unless we are also surrounded.
		if self.ownerOrder == 'Surrounded':
			if not self.game.checkSurrounded(self):
				return False
		elif self.ownerOrder == 'WorkerSearch':
			#check the area and see if their are workers that aren't defended.
			enemies = self.closestEnemies.filter(lambda x: not x.type_id in {PROBE,SCV,DRONE} and x.can_attack_ground and x.distance_to(self.unit) < 8)
			if len(enemies) > 0:
				workers = self.closestEnemies.filter(lambda x: x.type_id in {PROBE,SCV,DRONE} and x.distance_to(self.unit) < 6)
				if len(workers) > 0:
					return False
		elif self.ownerOrder == 'ComeHome':
			homeTarget = self.game.unitList.unitHomeTarget(self.owner)
			if homeTarget and owner_pos.distance_to(homeTarget) > self.unit.distance_to(homeTarget) and not self.game.checkSurrounded(self):
				return False
		elif self.ownerOrder == 'GoDefensivePoint':
			#check to make sure we are closer to the point than our owner.
			if owner_pos.distance_to(self.game.defensive_pos) > self.unit.distance_to(self.game.defensive_pos) and not self.game.checkSurrounded(self):
				return False			
		elif self.ownerOrder == 'PriorityTarget':
			#check to make sure there is a priority target near.
			targets = self.closestEnemies.filter(lambda x: x.type_id in {SIEGETANKSIEGED,INFESTOR,INFESTORBURROWED} and x.distance_to(self.unit) < 4)
			if targets:
				center_targets = targets.center
				behind_pos = self.unit.position.towards(center_targets, -3.5)
				behind_targets = self.closestEnemies.filter(lambda x: not x.type_id in {SIEGETANKSIEGED,INFESTOR,INFESTORBURROWED}
															and x.can_attack_ground and x.distance_to(behind_pos) <= 3.5)
				if len(behind_targets) <= 2:
					return False
		elif self.ownerOrder == 'Battle':
			#check to see if the owner was damaged recently, if so, then cancel.
			if self.game.unitList.unitDamaged(self.owner):
				#check around and make sure it's safe.
				behind_targets = self.closestEnemies.filter(lambda x: x.can_attack_ground and x.distance_to(self.unit) <= 3)
				if len(behind_targets) <= 2:
					return False
		elif self.ownerOrder == 'Chase':
			chaseTarget = self.game.unitList.adeptChaseTarget(self.owner)
			if chaseTarget:
				#check if we are closer than the owner, if so, do not cancel.
				dist = owner_pos.distance_to(chaseTarget)
				our_dist = self.unit.distance_to(chaseTarget)
				if our_dist < dist:
					#check to see if it's safe to port here.
					enemies = self.closestEnemies.filter(lambda x: not x.type_id in {PROBE,SCV,DRONE} and x.can_attack_ground and x.distance_to(self.unit) < 8)
					if len(enemies) <= 2:
						return False
		elif self.ownerOrder == 'MoveRally':
			if owner_pos.distance_to(self.game.rally_pos) > self.unit.distance_to(self.game.rally_pos) and not self.game.checkSurrounded(self):
				return False					
	
		#check if we are closer than the owners target, if so, do not cancel.
		if self.owner:
			ownerTarget = self.game.unitList.unitTarget(self.owner)
			if ownerTarget:
				dist = owner_pos.distance_to(ownerTarget)
				our_dist = self.unit.distance_to(ownerTarget)
				if our_dist < dist:
					#check to see if it's safe to port here.
					enemies = self.closestEnemies.filter(lambda x: not x.type_id in {PROBE,SCV,DRONE} and x.can_attack_ground and x.distance_to(self.unit) < 8)
					if len(enemies) <= 2:
						return False

		
		if self.shade_start:
			#cancel the shift.
			if AbilityId.CANCEL_ADEPTSHADEPHASESHIFT in self.abilities and self.game.can_afford(CANCEL_ADEPTSHADEPHASESHIFT):
				self.game.combinedActions.append(self.unit(AbilityId.CANCEL_ADEPTSHADEPHASESHIFT))
				self.shade_start = None
				return True
		return False
	
	def moveToExpansion(self):
		#move to the expansion
		if not self.emptyTarget and (not self.game.defend_only or self.game.moveRally):
			return False
		if self.checkNewAction('move', self.emptyTarget.position[0], self.emptyTarget.position[1]):
			self.game.combinedActions.append(self.unit.move(self.emptyTarget))
		return True		
		
	def searchEnemies(self):
		#search for enemies
		if self.unit.is_moving:
			return True #moving somewhere already
		searchPos = self.game.getSearchPos(self.unit)
		if self.checkNewAction('move', searchPos[0], searchPos[1]):
			self.game.combinedActions.append(self.unit.move(searchPos))
			return True
		return False
		
	def moveToEnemies(self):
		# move to nearest enemy ground unit/building because no enemy unit is closer than 5
		if self.game.known_enemy_units.exclude_type([ADEPTPHASESHIFT]).not_flying.exists:
			closestEnemy = self.game.known_enemy_units.exclude_type([ADEPTPHASESHIFT]).not_flying.furthest_to(self.unit)
			if self.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
				self.game.combinedActions.append(self.unit.move(closestEnemy))
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
		return False
	
	@property
	def isSolo(self) -> bool:
		return self.solo

	@property
	def isHallucination(self) -> bool:
		return False
	
	@property
	def sendHome(self) -> bool:
		return self.comeHome	
									
			
	
		

		
		
		
		
	