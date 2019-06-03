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
		self.nexus_builder = False
		self.nexus_position = None
		#gathering variables.
		self.gather_target = None
		self.vas_miner = False
		self.next_assim_update = 0
		self.comeHome = False
		self.homeTarget = None
		self.shield_regen = False
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
		self.game = game
		if not self.nexus_builder and not self.rush_defender and not self.lite_defender and self.game.last_iter % 5 != 0:
			return #don't need to run so often.

		self.unit = unit
		self.saved_position = unit.position
		self.assigned = Counter(self.game._worker_assignments.values())
		#self.current_tag = self.assigned.get(self.unit.tag)
		self.target_vespene = self.game._strat_manager.target_vespene
		#print ('t', self.assigned)

		if (self.game.rush_detected or self.game.workerAllin) and not self.collect_only and self.unit.shield > 15:
			self.rush_defender = True
			self.lite_defender = False			
			self.removeGatherer()


		#check if we need to come home and defend.
		self.comeHome = self.game.checkHome(self)

		#choose our action by role.
		if self.scout:
			self.scoutList()
		elif self.rush_defender:
			self.rushDefense()
		elif self.lite_defender:
			self.clearWorkers()
		elif self.nexus_builder:
			self.nexusBuilder()
		else:
			self.gatherList()

		#debugging info
		if _debug or self.unit.is_selected:
			if self.last_target:
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, self.last_target, color=Point3((155, 255, 25)))
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
			#keep safe from effects
			if self.game.effectSafe(self):
				self.label = 'Dodging'
				return #dodging effects.
			
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
		
		if self.LongDistanceMine():
			self.label = 'Long Distance Mining'
			return

		self.label = 'Need Orders'
		
	def scoutList(self):
		#keep safe from effects
		if self.game.effectSafe(self):
			self.label = 'Dodging'
			return #dodging effects.
			
		#mine until it's 10 seconds of game time.
		if self.game.time < 10 or self.checkHaveMinerals():
			self.label = 'Temp Mining'
			self.last_action = 'miner'
			return #building
		
		#check if we are being asked to build something, if so just build it.
		if not self.knownActions():
			self.label = 'Building'
			self.last_action = 'build'
			return #building

		#make sure we have scouted the enemy base.
		if self.searchBase():
			return
		#if it's under 3 minutes in the game, check for proxies near our base.
		if self.searchProxies():
			self.label = 'Searching for Enemy Proxies'
			return
		#after 3 minutes, start to place proxy pylons.
		if self.placeProxies():
			self.label = 'Placing Proxy Pylon'
			return
		#after 3 minutes, scout the enemy.
		if self.searchEnemy():
			self.label = 'Scouting the Enemy'
			return
		# 
		# if self.game.searchEnemies(self):
		# 	self.label = 'Search'
		# 	return #looking for targets

		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:			
			if self.game.keepSafe(self):
				self.label = 'Retreating Safe'
				#print ('triggered')
				return #staying alive


	def clearWorkers(self):
		
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			#enemies around us mode.
			if self.game.effectSafe(self):
				self.label = 'Dodging'
				return #dodging effects.

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
		if len(self.game.cached_enemies.of_type([PROBE,SCV,DRONE,REAPER,ZERGLING,ZEALOT])) == 0:
			self.rush_defender = False
	

	def nexusBuilder(self):
		#print (str(self.unit.orders).lower())
		self.enemyWorkers = self.game.getUnitEnemies(self, radius=6)
		#check for a worker rush incoming, if so, move back to base.
		if len(self.enemyWorkers.of_type([PROBE,SCV,DRONE])) > 2:
			#go back to work.
			self.game.unitList.freeNexusBuilders()
			self.label = 'Incoming Rush'
			return

		self.closestEnemies = None
		if self.game.expPos:
			self.closestEnemies = self.game.cached_enemies.closer_than(4, self.game.expPos)
		#self.closestEnemies = self.game.getUnitEnemies(self, radius=6)
		if self.closestEnemies:
			#keep safe from effects
			if self.game.effectSafe(self):
				self.label = 'Dodging'
				return #dodging effects.
			
			#always attack if we can.
			if self.game.attack(self):
				self.label = 'Attacking'
				return #attacked already this step.
			
			#move the closest known enemy.
			if self.game.moveToEnemies(self):
				self.label = 'C Moving Enemy'
				return #moving to next target.	
		
		#make sure we arne't holding minerals.
		if self.checkHaveMinerals():
			self.label = 'Returning Minerals'
			return

		#check if we are being asked to build something, if so just build it.
		if not self.knownActions():
			self.label = 'Building'
			return #building

		if self.moveToExpansion():
			self.label = 'Moving to Expansion'
			return
		
		self.label = 'Waiting to build Nexus'

		
######################
#Nexus Build Function#
######################

	def moveToExpansion(self):
		#get the distance to expansion, if it's more than 1, move to it.
		#find a mineral patch close to the location and move to it.
		if not self.nexus_position:
			self.nexus_position = self.game.state.vespene_geyser.closer_than(15.0, self.game.expPos).first
			self.nexus_position = self.game.expPos
		
		dist = self.unit.distance_to(self.nexus_position)
		if dist > 6.5:
			if self.checkNewAction('move', self.nexus_position.position.x, self.nexus_position.position.y):
				self.game.combinedActions.append(self.unit.move(self.nexus_position))
			self.last_target = Point3((self.nexus_position.position.x, self.nexus_position.position.y, self.game.getHeight(self.nexus_position.position)))
			return True
		elif dist < 5.5:
			#move away.
			move_distance = dist - 6
			targetpoint = self.unit.position.towards(self.nexus_position, distance=move_distance)	
			if self.checkNewAction('move', targetpoint.position.x, targetpoint.position.y):
				self.game.combinedActions.append(self.unit.move(targetpoint))
			self.last_target = Point3((targetpoint.position.x, targetpoint.position.y, self.game.getHeight(targetpoint.position)))
			return True
			
		return False
	
	

####################
#Scouting Functions#
####################
	def searchBase(self):
		#search for enemy base
		if self.unit.is_moving or self.unit.is_attacking:
			return True #moving somewhere already
		
		startPos = random.choice(self.game.enemy_start_locations)
		if self.unit.distance_to(startPos) > 10 and not self.game.base_searched:
			if self.checkNewAction('move', startPos[0], startPos[1]):
				self.game.combinedActions.append(self.unit.move(startPos))
			self.last_target = Point3((startPos.position.x, startPos.position.y, self.game.getHeight(startPos.position)))
			self.label = 'Searching for Enemy Base'
			return True
		else:
			self.game.base_searched = True

	def searchProxies(self):
		#if it's more than 2:20 minutes into the game, don't search anymore.
		if self.game.time > 140:
			return False
		
		if self.unit.is_moving or self.unit.is_attacking:
			return True #moving somewhere already		
		#search random among the nearest 10 expansion slots to unit.
		locations = []
		knockoff = 2
		startloc = self.game.game_info.player_start_location
		for possible in self.game.expansion_locations:
			if not self.game.units().of_type([NEXUS,PROBE]).closer_than(6, possible).exists:
				
				#distance = sqrt((possible[0] - startloc.position[0])**2 + (possible[1] - startloc.position[1])**2)
				distance = startloc.distance_to(possible.position)
				locations.append([distance, possible])
			else:
				knockoff += 1				
		locations = sorted(locations, key=itemgetter(0))
		#add duplicate locations to add weight towards enemy base.
		totalLocs = int(len(self.game.expansion_locations) / 2) - knockoff
		#print (totalLocs, knockoff)
		#only use the ones near our base.
		del locations[totalLocs:]
		if len(locations) > 0:
			nextPos = random.choice(locations)[1]
			if self.checkNewAction('move', nextPos[0], nextPos[1]):
				self.game.combinedActions.append(self.unit.move(nextPos))
			self.last_target = Point3((nextPos.position.x, nextPos.position.y, self.game.getHeight(nextPos.position)))
			self.label = 'Searching for Enemy Proxies'
			return True
		return False
			
	def placeProxies(self):
		if  self.game.time < 12240 or not self.game.can_spend or self.game._strat_manager.saving or self.game.buildingList.pylonsRequested:
			return False
			
		if self.unit.is_moving or self.unit.is_attacking:
			return True #moving somewhere already		
		#search random among the nearest 10 expansion slots to unit.
		locations = []
		knockoff = 2
		startloc = self.game.game_info.player_start_location
		for possible in self.game.expansion_locations:
			#if not self.game.units().of_type([NEXUS,PROBE]).closer_than(6, possible).exists:
			if not self.game.known_enemy_units.closer_than(6, possible).exists:
				distance = sqrt((possible[0] - startloc.position[0])**2 + (possible[1] - startloc.position[1])**2)
				locations.append([distance, possible])
			else:
				knockoff += 1
		locations = sorted(locations, key=itemgetter(0), reverse=True)
		#add duplicate locations to add weight towards enemy base.
		totalLocs = int(len(self.game.expansion_locations) / 2) - knockoff
		#print (totalLocs, knockoff)
		#only use the ones near our base.
		del locations[totalLocs:]
		if len(locations) == 0:
			return False
		nextPos = random.choice(locations)[1]
		#check to see if a pylon already exists at this locatoin.
		if self.game.units(PYLON).closer_than(6, nextPos).exists:
			return False
		
		if not self.game.can_afford(PYLON):
			return False
		
		if self.checkNewAction('pylon', nextPos.position.x, nextPos.position.y):
			self.game.combinedActions.append(self.unit.build(PYLON, nextPos.position))
		self.last_target = Point3((nextPos.position.x, nextPos.position.y, self.game.getHeight(nextPos.position)))
		self.label = 'Placing a Proxy'
		return True	
	
	def searchEnemy(self):
		
		if self.unit.is_moving or self.unit.is_attacking:
			return True #moving somewhere already		
		#search random among the nearest 10 expansion slots to unit.
		locations = []
		knockoff = 0
		startloc = self.game.game_info.player_start_location
		for possible in self.game.expansion_locations:
			if not self.game.known_enemy_units.closer_than(6, possible).exists:
				distance = sqrt((possible[0] - startloc.position[0])**2 + (possible[1] - startloc.position[1])**2)
				locations.append([distance, possible])
			else:
				knockoff += 1
		locations = sorted(locations, key=itemgetter(0), reverse=True)
		#add duplicate locations to add weight towards enemy base.
		totalLocs = int(len(self.game.expansion_locations) / 2) - knockoff
		#print (totalLocs, knockoff)
		#only use the ones near our base.
		del locations[totalLocs:]
		if len(locations) > 0:
			nextPos = random.choice(locations)[1]
			if self.checkNewAction('move', nextPos[0], nextPos[1]):
				self.game.combinedActions.append(self.unit.move(nextPos))
			self.last_target = Point3((nextPos.position.x, nextPos.position.y, self.game.getHeight(nextPos.position)))
			self.label = 'Searching for Enemy Bases'
			return True
		return False

#####################
#Gathering Functions#
#####################

	def LongDistanceMine(self):
		if len(self.unit.orders) == 0:
			for nexus in self.game.units(NEXUS).ready:
				#print (self.unit.tag, 'checking for minerals')
				if self.game.state.mineral_field.closer_than(100, nexus).exists:
					mf = self.game.state.mineral_field.closer_than(100, nexus).closest_to(self.unit)
					self.game.combinedActions.append(self.unit.gather(mf, queue=False))
					return True
		else:
			if 'gather' in str(self.unit.orders).lower() or 'return' in str(self.unit.orders).lower():
				return True		

	def OverMine(self):
		if len(self.unit.orders) == 0:
			for nexus in self.game.units(NEXUS).ready:
				#print (self.unit.tag, 'checking for minerals')
				if self.game.state.mineral_field.closer_than(10, nexus).exists:
					mf = self.game.state.mineral_field.closer_than(10, nexus).random
					self.game.combinedActions.append(self.unit.gather(mf, queue=False))
					return True
		else:
			if 'gather' in str(self.unit.orders).lower() or 'return' in str(self.unit.orders).lower():
				return True

	def checkAssim(self):
		if self.vas_miner and self.game.time > self.next_assim_update:
			update_time = 5
			assim = self.game.units.find_by_tag(self.gather_target.tag)
			if len(self.game._worker_assignments) == 0:
				#nobody is mining, we need to switch.
				if not self.game.worker_force_leave:
					self.gather_target = None
					self.vas_miner = False
					self.game.worker_force_leave = True
					self.removeGatherer()
				else:
					update_time = 1			
			if assim and assim.assigned_harvesters > assim.ideal_harvesters:
				#overcrowded, leave - but only if no other probes have already lef this frame.
				if not self.game.worker_force_leave:
					self.gather_target = None
					self.vas_miner = False
					self.game.worker_force_leave = True
					self.removeGatherer()
				else:
					update_time = 1

			self.next_assim_update = self.game.time + update_time

	def removeGatherer(self):
		if not self.game:
			return
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


	def checkHaveMinerals(self):
		if 'return' in str(self.unit.orders).lower():
			return True
		if 'returncargo' in str(self.unit.orders).lower():
			return True
		return False

	def checkReturning(self):
		if 'return' in str(self.unit.orders).lower() and self.gather_target:
			return True
		if 'returncargo' in str(self.unit.orders).lower() and self.gather_target:
			return True
		return False
	
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
					self.game.worker_force_leave = True
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
				self.game.worker_force_leave = True
				return True

	def findVespene(self):
		#get a list of assimilators, sorted by distance to us and loop to find one with an open space.
		if self.game.worker_force_leave:
			return None
		for assimilator in self.game.units(ASSIMILATOR).ready.filter(lambda x:x.vespene_contents > 0 and x.assigned_harvesters < 3).sorted(lambda x: x.distance_to(self.unit.position)):
			#make sure there is a nexus near the assimilator.
			if self.game.units(NEXUS).ready.closer_than(10, assimilator):
				#print (self.unit.tag, 'gas found')
				return assimilator
		return None
		
	def findMinerals(self):
		#get a list of mineral fields that are near a nexus, sorted by distance to us and loop to find open space.
		nexuslist = self.game.units(NEXUS).ready.sorted(lambda x: self.unit.distance_to(x.position))
		#for nexus in self.game.units(NEXUS).ready:
		for nexus in nexuslist:
			#print (self.unit.tag, 'checking for minerals')
			for mf in self.game.state.mineral_field.closer_than(12, nexus).sorted(lambda x: self.unit.distance_to(nexus.position)):
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
		#if our shield + health is less than 8, retreat.
		#stay retreated until our shield is regen to 15, so 23 total.
		total_health = self.unit.shield + self.unit.health		
		if self.shield_regen and total_health >= 23:
			self.shield_regen = False
		elif not self.shield_regen and total_health <= 8:
			self.shield_regen = True
		else:
			self.shield_regen = False
		
		#if our shield is at 0, then find the nearest mineral to start location and go to it.
		if self.shield_regen and self.closestEnemies:		
			#move to mineral patch closes to start location.
			mining_target = self.findRushDefMinerals()
			#get the distance of the nearest enemy and the distance to the mining target.  If it's less than 2, then keep fighting.
			closestEnemy = self.closestEnemies.closest_to(self.unit)
			if closestEnemy:
				away_dist = closestEnemy.distance_to(mining_target)
				if away_dist > 2:
					self.game.combinedActions.append(self.unit.gather(mining_target, queue=False))
					self.game.update_workers = True
					return True
		return False
	

	def stopFightingOld(self):
		#if our shield is at 0, then find the nearest mineral to start location and go to it.
		if self.unit.shield == 0 and self.closestEnemies:		
			#move to mineral patch closes to start location.
			mining_target = self.findRushDefMinerals()
			#get the distance of the nearest enemy and the distance to the mining target.  If it's less than 2, then keep fighting.
			closestEnemy = self.closestEnemies.closest_to(self.unit)
			if closestEnemy:
				away_dist = closestEnemy.distance_to(mining_target)
				if away_dist > 2:
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
			
	def becomeScout(self):
		self.scout = True
		self.removeGatherer()
		return

####################################
#Properties and Must Have Functions#
####################################

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
	
	@property
	def isHallucination(self) -> bool:
		return False
		
	@property
	def sendHome(self) -> bool:
		return self.comeHome

			
