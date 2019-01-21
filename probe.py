import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3
from collections import Counter
from math import sqrt
from operator import itemgetter



'''
Probe Info
----------------
Description: Small Ground Unit
Built From: Nexus
Cost:
	Minerals: 50
	Vespene: 0
	GameSpeed: 12
	Armor: 1
Attributes: Light, Mechanical
Attack 1:
	Targets:	Ground
	Damage:	 	5
	DPS:	 	4.67
	Cooldown:	1.07
	Range:	 	0.1
Defence:
	Health: 20
	Shield: 20
	Armor: 0 (+1)
Sight: 8
Speed: 3.94
Cargo Size: 1
'''
_debug = False

class Probe:
	
	def __init__(self, unit):
		self.unit = unit
		self.tag = unit.tag
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'
		self.scout = False
		self.collect_only = False
		self.rush_defender = False
		self.lite_defender = False
		self.proxy_placed = False
		#gathering variables.
		self.gather_target = None
		self.vas_miner = False
		self.next_assim_update = 0
		
		
	def make_decision(self, game, unit):
		self.game = game
		self.unit = unit
		self.saved_position = unit.position
		self.assigned = Counter(self.game._worker_assignments.values())
		#self.current_tag = self.assigned.get(self.unit.tag)
		self.target_vespene = self.game._strat_manager.target_vespene
		#print ('t', self.assigned)

		if self.game.rush_detected and not self.collect_only and self.unit.shield > 15:
			self.rush_defender = True
			self.lite_defender = False			
			self.removeGatherer()

		#choose our action by role.
		if self.scout:
			self.scoutList()
		elif self.rush_defender:
			self.rushDefense()
		elif self.lite_defender:
			self.clearWorkers()
		else:
			self.gatherList()

		#debugging info
		if _debug or self.unit.is_selected:
			if self.last_target:
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, self.last_target, (155, 255, 25))
			self.game._client.debug_text_3d(self.label, self.unit.position3d)
		
################
#Role Functions#
################
	def gatherList(self):
		#print(str(self.unit.orders).lower())
		#every 5 seconds, check the assim to see if it's being over-worked.
		self.checkAssim()
		self.closestEnemies = self.game.getUnitEnemies(self)
		if not self.collect_only and self.closestEnemies.amount > 0:
			#always attack if we can.
			if self.game.attack(self):
				self.removeGatherer()
				self.label = 'Attacking'
				return #attacked already this step.
	
			#2 priority is to save our butts if we can
			if self.game.keepSafe(self):
				self.removeGatherer()
				self.label = 'Retreating Death'
				return #staying alive
	
			#3 priority is to keep our distance from enemies
			if self.game.doNothing(self):
				self.label = 'Do Nothing'
				return #kiting

		#make sure we aren't being called on to build something.
		if self.busyBuilding():
			self.label = 'Building ' + str(self.vas_miner)
			return
		
		#make sure we are mining the correct target.
		if self.checkMiningTarget():
			self.label = 'Fixing'
			return

		#check our orders and see if we are already gathering.
		if self.checkReturning():
			self.label = 'Returning ' + str(self.vas_miner)
			return #already gathering something, don't do anything.
		
		if self.checkGathering():
			self.label = 'Gathering ' + str(self.vas_miner)
			return #already gathering something, don't do anything.
		
		#make sure we have a target.
		if self.getMiningTarget():
			self.label = 'Targeting'
			return
		
		if self.gather_target:
			#time to drop our target because it's not working for us.
			self.gather_target = None
			self.vas_miner = False
			self.label = 'Dropped Target'
		
		if self.OverMine():
			self.label = 'OverMining'
			return

		self.label = 'Need Orders'
		
	def scoutList(self):
		#if self.game.canEscape(self.unit):
			#1b priority is to save our butts if we can because we have to stop to attack.
		#check if we are being asked to build something, if so just leave.
		#mine until it's 20 seconds of game time.
		if self.game.time < 10:
			self.label = 'Temp Mining'
			self.last_action = 'miner'
			return #building			
		
		if not self.knownActions():
			self.label = 'Building'
			self.last_action = 'build'
			return #building


		if self.game.searchEnemies(self):
			self.label = 'Search'
			return #looking for targets

		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:			
			if self.game.keepSafe(self):
				self.label = 'Retreating Safe'
				#print ('triggered')
				return #staying alive

		#go to the first enemy expansion and put a pylon on it.
		# if self.placeProxyPylon():
		# 	self.label = 'Moving to Proxy Location'
		# 	return #moving to proxy.

		#7 find the enemy


	def clearWorkers(self):
		
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			if self.game.canEscape(self) and self.game.keepSafe(self):
				self.label = 'C Retreating Safe'
				return #staying alive		

			#always attack if we can.
			if self.game.attack(self):
				self.label = 'C Attacking'
				return #attacked already this step.

			#2 priority is to save our butts if we can
			if self.game.keepSafe(self):
				self.label = 'C Retreating Death'
				return #staying alive

			#3 priority is to keep our distance from enemies
			if self.game.doNothing(self):
				self.label = 'C Do Nothing'
				return #kiting

		#5 move the closest known enemy.
		if self.game.moveToEnemies(self):
			self.label = 'C Moving Enemy'
			return #moving to next target.		

	def rushDefense(self):
		#if building, stop being an attacker.
		if self.needBuilding():
			self.label = 'Def Building'
			return #no longer a fighter.

		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			#always attack if we can.
			if self.game.attack(self):
				self.label = 'Def Attacking'
				return #attacked already this step.

		#if shield is at 0, go back to the minerals.
		if self.stopFighting():
			self.label = 'Def Retreating Gather'
			return #go back to mining.

		#move to the enemy that is closest to the nexus.
		#5 move the closest known enemy.
		if self.moveToEnemies():
			self.label = 'Def Moving Enemy2'
			return #moving to next target.
		
		#no enemies exist, go back to work.
		if self.game.units.of_type([PROBE,SCV,DRONE,REAPER]).amount == 0:
			self.rush_defender = False
	
		# if self.game.searchEnemies(self):
		# 	self.label = 'Search'			
		# 	return #looking for targets	
		
#####################
#Gathering Functions#
#####################
	def OverMine(self):
		if len(self.unit.orders) == 0:
			for nexus in self.game.units(NEXUS).ready:
				#print (self.unit.tag, 'checking for minerals')
				for mf in self.game.state.mineral_field.closer_than(10, nexus).sorted(lambda x: self.unit.distance_to(x.position)):
					self.game.combinedActions.append(self.unit.gather(mf, queue=False))
					return True
		else:
			if 'gather' in str(self.unit.orders).lower() or 'return' in str(self.unit.orders).lower():
				return True

	def checkAssim(self):
		if self.vas_miner and self.game.time > self.next_assim_update:
			assim = self.game.units.find_by_tag(self.gather_target.tag)
			if assim and assim.assigned_harvesters > assim.ideal_harvesters:
				#overcrowded, leave.
				self.gather_target = None
				self.vas_miner = False
			self.next_assim_update = self.game.time + 5

	def removeGatherer(self):
		if self.game._worker_assignments.get(self.unit.tag):
			del self.game._worker_assignments[self.unit.tag]		
		
	def checkMiningTarget(self):
		if 'gather' in str(self.unit.orders).lower() and self.gather_target and self.unit.order_target != self.gather_target.tag:
			# print ('targets', self.unit.order_target, self.gather_target.tag)
			# print (str(self.unit.orders).lower())
			#move to the correct target.
			#make sure the target exists.
			if self.checkMinerals():
				self.game.combinedActions.append(self.unit.gather(self.gather_target, queue=False))
				return True
			#this mineral no longer exists, time to find a new one.
			self.gather_target = None
			self.vas_miner = False
			if self.game._worker_assignments.get(self.unit.tag):
				del self.game._worker_assignments[self.unit.tag]

	def checkGathering(self):
		if 'gather' in str(self.unit.orders).lower() and self.gather_target:
			return True

	def checkReturning(self):
		if 'return' in str(self.unit.orders).lower() and self.gather_target:
			return True
		if 'returncargo' in str(self.unit.orders).lower() and self.gather_target:
			return True		
	
	def busyBuilding(self):
		if not self.knownActions():
			if self.game._worker_assignments.get(self.unit.tag):
				del self.game._worker_assignments[self.unit.tag]
			self.gather_target = None
			self.last_action = 'building'
			self.last_target = None
			self.vas_miner = False
			return True
		return False

	def getMiningTarget(self):
		if not self.gather_target:
			###find a target.
			if self.game._strat_manager.target_vespene:
				#find a vaspene to mine if possible.
				closestTarget = self.findVespene()
				if closestTarget:
					#add the targets object as our target.
					self.gather_target = closestTarget
					#start mining the target.
					self.last_target = Point3((closestTarget.position3d.x, closestTarget.position3d.y, (closestTarget.position3d.z + 1)))
					self.game.combinedActions.append(self.unit.gather(closestTarget, queue=False))
					self.vas_miner = True
					return True
			#target the minerals.
			closestMineral = self.findMinerals()
			if closestMineral:
				#add the mineral target to list.
				self.game._worker_assignments.update({self.unit.tag:closestMineral.tag})
				#add the targets object as our target.
				self.gather_target = closestMineral
				#start mining the target.
				self.last_target = Point3((closestMineral.position3d.x, closestMineral.position3d.y, (closestMineral.position3d.z + 1)))
				self.game.combinedActions.append(self.unit.gather(closestMineral, queue=False))
				self.vas_miner = False
				return True
			closestTarget = self.findVespene()
			if closestTarget:
				#add the targets object as our target.
				self.gather_target = closestTarget
				#start mining the target.
				self.last_target = Point3((closestTarget.position3d.x, closestTarget.position3d.y, (closestTarget.position3d.z + 1)))
				self.game.combinedActions.append(self.unit.gather(closestTarget, queue=False))
				self.vas_miner = True
				return True

	def findVespene(self):
		#get a list of assimilators, sorted by distance to us and loop to find one with an open space.
		for assimilator in self.game.units(ASSIMILATOR).ready.filter(lambda x:x.vespene_contents > 0 and x.assigned_harvesters < 3).sorted(lambda x: x.distance_to(self.unit.position)):
			#print (self.unit.tag, 'gas found')
			return assimilator
		return None
		
	def findMinerals(self):
		#get a list of mineral fields that are near a nexus, sorted by distance to us and loop to find open space.
		nexuslist = self.game.units(NEXUS).ready.sorted(lambda x: self.unit.distance_to(x.position))
		#for nexus in self.game.units(NEXUS).ready:
		for nexus in nexuslist:
			#print (self.unit.tag, 'checking for minerals')
			for mf in self.game.state.mineral_field.closer_than(10, nexus).sorted(lambda x: self.unit.distance_to(nexus.position)):
				if self.assigned[mf.tag] < 2:
					#print (self.unit.tag, 'mineral found')
					return mf
		return None

	def knownActions(self):
		if 'gather' in str(self.unit.orders).lower():
			return True
		if 'return' in str(self.unit.orders).lower():
			return True
		if 'move' in str(self.unit.orders).lower():
			return True
		if 'attack' in str(self.unit.orders).lower():
			return True
		if len(self.unit.orders) == 0:
			return True
		return False
	
	def checkMinerals(self):
		if not self.vas_miner:
			#check the tag to see if the mineral still exists.
			if self.game.state.mineral_field.find_by_tag(self.gather_target.tag):
				return True


#################
#Micro Functions#
#################

	def stopFighting(self):
		#if our shield is at 0, then find the nearest mineral to start location and go to it.
		if self.unit.shield == 0:
			#move to mineral patch closes to start location.
			mining_target = self.findRushDefMinerals()
			self.game.combinedActions.append(self.unit.gather(mining_target, queue=False))
			self.game.update_workers = True
			return True
		return False

	def placeProxyPylon(self):
		if self.proxy_placed:
			return False #already done
		#get the expansion closest to the enemy's base and put a pylon on it.
		if len(self.game.enemy_start_locations) > 1:
			return False  #this map has multiple start locations
				
		#check to see if there is a pylon near the location.
		if self.game.units(PYLON).closer_than(6, self.game.proxy_pylon_loc).exists:
			self.proxy_placed = True
			return False
		
		#check to see if we are in range.
		if self.unit.distance_to(self.game.proxy_pylon_loc) < 5:
			#check to see if we can build a pylon there.
			if self.game.can_afford(PYLON):
				if self.checkNewAction('pylon', self.game.proxy_pylon_loc[0], self.game.proxy_pylon_loc[1]):
					self.game.combinedActions.append(self.unit.build(PYLON, self.game.proxy_pylon_loc))
				return True #building pylon

		#move to proxy_loc
		if self.checkNewAction('move', self.game.proxy_pylon_loc[0], self.game.proxy_pylon_loc[1]):
			self.game.combinedActions.append(self.unit.move(self.game.proxy_pylon_loc))
		return True

	def moveToEnemies(self):
		#move to the enemy that is closest to the nexus.
		if self.game.units(NEXUS).exists and self.game.known_enemy_units.not_flying.exclude_type([ADEPTPHASESHIFT]).exists:
			nexus = self.game.units(NEXUS).random
			closestEnemy = self.game.known_enemy_units.not_flying.exclude_type([ADEPTPHASESHIFT]).closest_to(nexus)
			#get the distance to the closest Enemy and if it's in attack range, then don't move.
			if closestEnemy.distance_to(self.unit.position) > self.unit.ground_range + self.unit.radius + closestEnemy.radius - 0.05:
				self.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
				if self.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
					self.game.combinedActions.append(self.unit.attack(closestEnemy.position))
				return True

	def needBuilding(self):
		if not self.knownActions():
			self.rush_defender = False
			return True
		return False
	
	def findRushDefMinerals(self):
		#get a list of mineral fields that are near a nexus, sorted by distance to us and loop to find open space.
		for nexus in self.game.units(NEXUS).ready:
			#print (self.unit.tag, 'checking for minerals')
			for mf in self.game.state.mineral_field.closer_than(10, nexus).sorted(lambda x: self.unit.distance_to(x.position)):
				return mf
		return None		
			


####################################
#Properties and Must Have Functions#
####################################

	def checkNewAction(self, action, posx, posy):
		actionStr = (action + '-' + str(posx) + '-' + str(posy))
		if actionStr == self.last_action:
			return False
		self.last_action = actionStr
		return True

	
	@property
	def targetTag(self) -> int:
		return self.target_tag

	@property
	def noTargetTag(self) -> bool:
		if self.current_tag:
			return False
		return True
		
	@property
	def position(self) -> Point2:
		return self.saved_position
	
	@property
	def isRetreating(self) -> bool:
		return self.retreating
	
	
