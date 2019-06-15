import random
import sc2
import math
from sc2.ids.ability_id import AbilityId
from sc2 import Race
from sc2.units import Units
from sc2.constants import *
from sc2.position import Point2, Point3
from math import sqrt, ceil, floor
from operator import itemgetter
from unit_counters import UnitCounter

'''
This class makes our build/macro decisions.

'''
_debug = False

class Strategist:
	
	def __init__(self, game):
		self.game = game
		self.target_vespene = True
		self.target_minerals = False
		self.enemy_aircraft = False
		self.min_defense = False
		self.worker_tag = False
		#1 or 2 ramps.
		self.ramp2search = False
		self.ramp2 = None
		
		#building positions
		self.pylon1Pos = None
		self.forgePos = None
		self.gateway1Pos = None
		
		
		#flags
		self.pylon1 = False
		self.stage1complete = False
		self.forge = False
		self.saving = False
		
		#enemyintel
		self.unitTimes = {}
		self.unitCounter = UnitCounter()
		self.enemy_intel = {}
		self.counted_enemy = {}
		self.ideal_army = {}
		self.raw_all_counters = {}
		self.able_army = {}
		self.buildings_needed = {}
		self.enemy_power = 0
		self.army_power = 0
		self.raw_ideal_army = {}
		self.gateway_needed = False
		self.robotics_needed = False
		self.stargate_needed = False
		self.expansion_scout = None
		self.enemy_cannons = {}
		self.unique_enemies = []
		self.ghost_units = {}
		
		#worker detected
		self.worker_detected = False
		#production facility demand.
		self.gate_demand = 0
		self.robo_demand = 0
		self.star_demand = 0
		#####
		self.strat_id = 0
		self.start_build_order = ['Gateway', 'CyberneticsCore', 'Gateway', 'Gateway']
		####ramp1 positions.
		self.ramp1forgePos = None
		self.ramp1pylon1Pos = None
		self.cannon1Pos = None
		self.cannon2Pos = None
		self.cannon3Pos = None
		self.cannon4Pos = None
		self.cannon5Pos = None
		self.cannon6Pos = None
		
	async def strat_control(self, game, build, train):
		self.game = game
		self.build = build
		self.train = train
		
		
		#find 2nd ramp
		if not self.ramp2search:
			self.ramp2 = self.findRamp2()
			await self.setupPositions()
			self.ramp2search = True
		###collect intel and develop a strat.
		self.collect_intel()
		self.count_intel()
		#develop a strat
		self.calc_counters()
		self.needed_buildings()
		self.unit_ratios()
		
		#self.check_reqs()
	
		self.detect_rush()
		self.detect_single_worker()
		self.detect_reaper_cheese()
		self.army_score()
		self.detect_allinWorker_rush()
		self.assign_nexus_builder()
		#if self.game.minerals >= self.game.vespene:
		if self.game.vespene < 500:
			self.target_vespene = True
		else:
			self.target_vespene = False

		self.safe_workers()

		# if _debug:
		# 	await self.debug_positions()
		# 	self.debug_intel()
			#self.debug_map_vals()
		
		#if minerals are adding up, something probably happened in stage1, so skip it.
		if not self.stage1complete and self.game.minerals > 1000:
			await self.game._client.chat_send(self.unitCounter.gets1failSaying(), team_only=False)
			print ('stage failed')
			self.stage1complete = True
			self.build.can_build_assimilators = True				
			self.build.can_build_pylons = True	
	
	
		
		self.attack_command()
		self.check_rally()
		if not self.stage1complete:
			#run it based on the selected strat id.
			if self.strat_id == 1:
				await self.setup_onebase_production()
				self.train_queue()
			elif self.strat_id == 2:
				await self.setup_onebase_defense()
				self.train_queue()
			elif self.strat_id == 3:
				await self.setup_twobase_production()
				self.train_queue()
			elif self.strat_id == 4:
				await self.setup_twobase_defense()
				self.train_queue()
			elif self.strat_id == 5:
				await self.setup_threebase()
				self.train_queue()				
			else:
				self.stage1complete = True
				if self.game.trueGates > 0:
					self.build.can_build_assimilators = True
				else:
					self.build.can_build_assimilators = False
				
				#make sure we don't just build a bunch of pylons.
				if len(self.game.units(PYLON)) > 0 and self.game.trueGates == 0:
					self.build.can_build_pylons = False
				else:
					self.build.can_build_pylons = True
			return
		
		if self.stage1complete:
			if self.game.trueGates > 0:
				self.build.can_build_assimilators = True
			else:
				self.build.can_build_assimilators = False
				
			if len(self.game.units(PYLON)) > 0 and self.game.trueGates == 0:
				self.build.can_build_pylons = False
			else:
				self.build.can_build_pylons = True
				
			if not self.game.under_attack and self.need_expand() and self.game.trueGates > 0 and self.army_power > 0:
				#turn off all queues.
				self.save_expand()
			else:
				self.saving = False
				self.build_queue()
				self.train_queue()
				self.research_queue()
				self.exp_scout()
				self.build.cores = 1

	
	
	

#########################
#Starting Dynamic Strats#
#########################
	async def setup_threebase(self):
		#build pylons
		if self.game.units(PYLON).amount == 0:
			self.build.can_build_pylons = True
		else:
			self.build.can_build_pylons = False

		if self.game.units(PYLON).amount > 0 and self.game.units(NEXUS).amount < 3 and self.game.minerals > 225:
			self.assign_nexus_builder(direct=True)
			

		#build a nexus at the expansion.
		if self.game.can_afford(NEXUS) and not self.game.already_pending(NEXUS) and self.game.units(NEXUS).amount == 1 and not self.game.rush_detected and self.allAllowedQueued:
			if len(self.game.units(PROBE)) > 0:
				self.game._build_manager.last_build = 5
				await self.game.expand_now()
				return

		#build the 1st gateway.
		if self.game.units(NEXUS).amount > 1:
			self.build.gateways = 1
			
		if self.game.units(GATEWAY).amount > 0 and self.game.units(ASSIMILATOR).amount < 1:
			self.build.can_build_assimilators = True
		else:
			self.build.can_build_assimilators = False				
		
		
		#expand a 3rd time.
		if self.startBuildingCount > 0 and self.game.can_afford(NEXUS) and self.game.units(NEXUS).amount == 2 and not self.game.rush_detected and self.allAllowedQueued:
			if len(self.game.units(PROBE)) > 0:
				self.game._build_manager.last_build = 5
				await self.game.expand_now()
				return

		#build pylon 2
		if len(self.game.units(PYLON)) == 1 and self.game.units(NEXUS).amount > 2 and not self.game.rush_detected:
			if self.game.can_afford(PYLON) and self.game.already_pending(PYLON) == 0:
				await self.game._build_manager.buildPylon()
				self.game.can_spend = False
				return


	
		#add in stop for easy assim fix.
		if self.game.units(NEXUS).amount < 3:
			return
			
		#build 2nd assims
		if self.game.units(PYLON).amount > 1 and self.game.units(ASSIMILATOR).amount < 2:
		 	self.build.can_build_assimilators = True
		else:
		 	self.build.can_build_assimilators = False		
		#build a 2nd gateways.
		if self.game.units(ASSIMILATOR).exists:
			self.buildBuilding(1)
						
		
		#build the core building.
		if self.game.units(NEXUS).amount > 2 and self.startBuildingCount >= 2 and self.allAllowedQueued:		
			self.buildBuilding(2)

		#build the 4th production building.
		if self.startBuildingCount >= 3 and self.allAllowedQueued:		
			self.buildBuilding(3)
					
		#go to the main phase
		if self.startBuildingCount >= 4:
			self.build.can_build_pylons = True
			self.build.can_build_assimilators = True
			self.stage1complete = True
			await self.game._client.chat_send(self.unitCounter.gets1successSaying(), team_only=False)	

	async def setup_onebase_production(self):
		#this opener will build one base with 3 production buildings quickly.
		#build the 1st gateway.
		#always have to build a gateway first.
		self.build.gateways = 1
		self.build.can_build_pylons = True
		#after we have a gateway, build 1 gas.
		#if cannons exists, build 2 assims.
		if self.game.units(GATEWAY).amount > 0 and self.game.units(ASSIMILATOR).amount < 2:
			self.build.bypass_assim_wait = True
			self.build.can_build_assimilators = True
		else:
			self.build.can_build_assimilators = False
			self.build.bypass_assim_wait = False
		#build a 2nd gateway.
		if self.startBuildingCount >= 1 and not self.game.rush_detected:
			#allow the building of the second on list.
			self.buildBuilding(1)
		
		if self.startBuildingCount < 2:
			return
		#build the cybercore.
		if self.startBuildingCount >= 2 and self.allAllowedQueued:
			self.buildBuilding(2)
	
		#build the 4th production building.
		if self.startBuildingCount >= 3 and self.allAllowedQueued:		
			self.buildBuilding(3)

		#just in case
		if self.startBuildingCount >= 4:
			self.build.cores = 1
		
		#go to the main phase
		if self.startBuildingCount >= 4:
			self.build.can_build_assimilators = True
			self.stage1complete = True
			await self.game._client.chat_send(self.unitCounter.gets1successSaying(), team_only=False)
			return

	async def setup_onebase_defense(self):
		#build the pylon at the end of the ramp.
		if not self.game.under_attack and not self.pylon1 and self.game.can_afford(PYLON):
			await self.game.build(PYLON, near=self.ramp1pylon1Pos)
			self.pylon1 = True
			return
		#build a forge.
		self.build.forges = 1
	
		#build gateway.
		if self.game.units(FORGE).exists:
			self.build.gateways = 1

		#build an assim while gateway builds
		if self.game.units(GATEWAY).exists and self.game.units(ASSIMILATOR).amount < 2:
			self.build.can_build_assimilators = True
			self.build.bypass_assim_wait = True
		else:
			self.build.can_build_assimilators = False
			self.build.bypass_assim_wait = False
			
			
		#build cannons
		if self.game.units(FORGE).ready.exists and self.game.can_afford(PHOTONCANNON) and self.game.units(PHOTONCANNON).amount < 4:
			if self.build.check_pylon_loc(self.ramp1pylon1Pos, searchrange=3):
				self.game._build_manager.last_build = 14
				await self.game.build(PHOTONCANNON, near=self.ramp1pylon1Pos)
				return
		
		#leave here if 2 cannons haven't been built.
		if self.game.units(PHOTONCANNON).amount < 2:
			return
		
		#build the 2nd pylon
		if self.game.units(GATEWAY).exists:
			self.build.can_build_pylons = True
			
		#leave here if 4 cannons haven't been built.
		if self.game.units(PHOTONCANNON).amount < 4:
			return


		#build a 2nd building
		if self.game.units(GATEWAY).exists:
			self.buildBuilding(1)

		#build building 3
		if self.startBuildingCount >= 2 and self.game.units(ASSIMILATOR).amount > 1 and self.allAllowedQueued:
			self.buildBuilding(2)
			
		#build building 4
		if self.startBuildingCount >= 3 and self.allAllowedQueued:
			self.buildBuilding(3)

		#finish
		if self.startBuildingCount >= 4:
			self.build.cores = 1
			self.build.can_build_pylons = True
			self.build.can_build_assimilators = True
			self.stage1complete = True
			await self.game._client.chat_send(self.unitCounter.gets1successSaying(), team_only=False)

	async def setup_twobase_production(self):
		#build 1st pylon.
		self.build.can_build_pylons = True
		#build the 1st gateway.
		self.build.gateways = 1
		if self.game.units(GATEWAY).amount > 0 and self.game.units(ASSIMILATOR).amount < 1:
			self.build.can_build_assimilators = True
		else:
			self.build.can_build_assimilators = False
			
		if self.game.minerals > 225 and self.game.units(GATEWAY).amount > 0 and self.game.units(ASSIMILATOR).amount > 0 and self.game.units(NEXUS).amount < 2:
			self.assign_nexus_builder(direct=True)
		
		#build a nexus at the expansion.
		if not self.game.under_attack and self.game.units(GATEWAY).amount > 0 and self.game.can_afford(NEXUS) and not self.game.already_pending(NEXUS) and self.game.units(NEXUS).amount == 1 and not self.game.rush_detected and self.allAllowedQueued:
			if len(self.game.units(PROBE)) > 0:
				self.game._build_manager.last_build = 5
				await self.game.expand_now()
				return

		#leave until nexus is built.
		if self.game.units(NEXUS).amount < 2:
			return


		#build 1st assims
		if self.game.units(PYLON).amount > 1 and self.game.units(ASSIMILATOR).amount < 2:
		 	self.build.can_build_assimilators = True
		else:
		 	self.build.can_build_assimilators = False		
		#build a 2nd gateway.
		if self.game.units(ASSIMILATOR).exists:
			self.buildBuilding(1)

		#build the core building.
		if self.startBuildingCount >= 2 and self.allAllowedQueued:		
			self.buildBuilding(2)

		#build the 4th production building.
		if self.startBuildingCount >= 3 and self.allAllowedQueued:
			self.buildBuilding(3)
					
		#go to the main phase
		if self.startBuildingCount >= 4:
			self.build.can_build_pylons = True
			self.build.can_build_assimilators = True
			self.stage1complete = True
			await self.game._client.chat_send(self.unitCounter.gets1successSaying(), team_only=False)	

	async def setup_twobase_defense(self):
		#build the pylon that the cannons will be placed near.
		if not self.game.under_attack and not self.pylon1 and self.game.can_afford(PYLON):
			await self.game.build(PYLON, near=self.pylon1Pos)
			self.game._build_manager.last_build = 2
			return
		
		if not self.pylon1 and self.build.check_pylon_loc(self.pylon1Pos, searchrange=3):
			self.pylon1 = True
			
		#build a forge at that pylon.
		self.build.forges = 1
		
		#build an assim while forge builds
		if self.game.units(FORGE).amount > 0 and self.game.units(ASSIMILATOR).amount < 1:
			self.build.can_build_assimilators = True
		else:
			self.build.can_build_assimilators = False				
		

		if self.game.minerals > 225 and self.game.units(FORGE).amount > 0 and self.game.units(NEXUS).amount < 2:
			self.assign_nexus_builder(direct=True)
		
		#build a nexus at the expansion.
		if not self.game.under_attack and self.game.units(FORGE).amount > 0 and self.game.can_afford(NEXUS) and not self.game.already_pending(NEXUS) and self.game.units(NEXUS).amount == 1 and not self.game.rush_detected and self.allAllowedQueued:
			if len(self.game.units(PROBE)) > 0:
				self.game._build_manager.last_build = 5
				await self.game.expand_now()
				return

		#build a gateway after nexus
		if self.game.units(NEXUS).amount >= 2 and self.game.can_afford(GATEWAY) and self.game.units(GATEWAY).amount == 0:
			self.build.gateways = 1	
		
		#build cannons at the original pylon.
		if self.game.units(FORGE).ready.exists and self.game.units(GATEWAY).amount >= 1 and self.game.can_afford(PHOTONCANNON) and self.game.units(PHOTONCANNON).amount < 4:
			if self.build.check_pylon_loc(self.pylon1Pos, searchrange=3):
				self.game._build_manager.last_build = 14
				await self.game.build(PHOTONCANNON, near=self.pylon1Pos)		
	
		#build our next production building.
		if self.startBuildingCount >= 1:
			self.buildBuilding(1)
			
		#leave for easy assim fix.
		if self.startBuildingCount < 2:
			return


		#if cannons exists, build 2 assims.
		if self.startBuildingCount >= 2 and self.game.units(ASSIMILATOR).amount < 2:
			self.build.can_build_assimilators = True
		else:
			self.build.can_build_assimilators = False					
		
		#build a pylon in the main base.
		if self.startBuildingCount >= 2:
			self.build.can_build_pylons = True	
			
		#build the core building.
		if self.startBuildingCount >= 2 and self.allAllowedQueued:		
			self.buildBuilding(2)
			
		#build some shields.
		if len(self.game.units(PYLON)) > 1 and self.game.units(CYBERNETICSCORE).ready.exists and self.game.can_afford(SHIELDBATTERY) and self.game.units(SHIELDBATTERY).amount == 0 and self.startBuildingCount >= 3:
			#build shield 1.
			self.game._build_manager.last_build = 15
			await self.build.build_shield_battery(self.r2battery1Pos)
			return

		#build some shields.
		if len(self.game.units(PYLON)) > 1 and self.game.units(CYBERNETICSCORE).ready.exists and self.game.can_afford(SHIELDBATTERY) and self.game.units(SHIELDBATTERY).amount == 1 and self.startBuildingCount >= 3:
			#build shield 2.
			self.game._build_manager.last_build = 15
			await self.build.build_shield_battery(self.r2battery1Pos)
			return
						
			
		#build the 4th production building.
		if self.startBuildingCount >= 3 and self.allAllowedQueued and self.game.units(SHIELDBATTERY).amount > 1:
			self.buildBuilding(3)	
		
		#just in case
		if self.startBuildingCount >= 4:
			self.build.cores = 1
		
		#go to the main phase
		if self.startBuildingCount >= 4 and self.game.units(SHIELDBATTERY).amount >= 2:
			self.build.can_build_pylons = True
			self.build.can_build_assimilators = True
			self.stage1complete = True
			await self.game._client.chat_send(self.unitCounter.gets1successSaying(), team_only=False)	


#################
#Queue Decisions#
#################

	def research_queue(self):
		#formerly managed what could be researched, now just builds support for further resources if needed
			
		if self.game.trueGates + self.game.units(ROBOTICSFACILITY).amount >= 3:
			if self.build.forges == 0:
				self.build.forges = 1
				
		if self.game.trueGates >= 2:
			if self.build.twilights == 0:
				self.build.twilights = 1
				
		if self.game.units(STARGATE).amount >= 2:
			if self.build.fleetbeacons == 0:
				self.build.fleetbeacons = 1			
			
	def train_queue(self):
		#reset all training to 0.
		self.reset_allowed()

		#need to maintain the ratio of units we want.
		#count the number of sets for each unit.
		#get the average set number.
		#if the unit is above the average set number, then turn it off.
		tsets = 0
		minset = 100
		maxset = 0
		for name, count in self.able_army.items():
			#count number of these units we have.
			unitID = self.unitCounter.getUnitID(name)
			amt = self.game.units(unitID).amount + self.game.already_pending(unitID)
			sets = round(amt / count)
			if sets < minset:
				minset = sets
			if sets > maxset:
				maxset = sets
			tsets += sets
			
		minset = ceil(minset + 1)
		maxset = ceil(maxset + 1)

		# avgset = 1
		# if len(self.able_army) > 0:
		# 	avgset = round(tsets / len(self.able_army))
		#loop again, don't like it but need a quick fix.
		for name, count in self.able_army.items():
			unitID = self.unitCounter.getUnitID(name)
			amt = self.game.units(unitID).amount + self.game.already_pending(unitID)
			sets = floor(amt / count)
			#if sets > avgset:
			if sets >= minset and minset != maxset:
				#turn off
				self.change_allowed(name, False)
			else:
				#turn on
				self.change_allowed(name, True)

	def build_queue(self):
		#grab the first item on the list and see if we can build it.
		if len(self.buildings_needed) == 0:
			#check to see if any gateways exist, if not build one.
			if self.game.trueGates == 0:
				self.build.gateways = 1
		
		for name, count in self.buildings_needed.items():
			if name == 'Gateway':
				#count gateways and add 1.
				self.build.gateways = self.game.trueGates + 1
			if name == 'CyberneticsCore':
				self.build.cores = 1
				self.build.can_build_assimilators = True

			if name == 'RoboticsBay':
				self.build.roboticsbay = 1

			if name == 'RoboticsFacility':
				self.build.roboticsfacility = self.game.units(ROBOTICSFACILITY).amount + 1
				
			if name == 'TwilightCouncil':
				self.build.twilights = 1
				
			if name == 'FleetBeacon':
				self.build.fleetbeacons = 1
				
			if name == 'Stargate':
				self.build.stargates = self.game.units(STARGATE).amount + 1
			
			if name == 'TemplarArchive':
				self.build.templararchives = 1			

			if name == 'DarkShrine':
				print ('darksrhine triggered?')
				self.build.darkshrines = 1				

	def check_rally(self):
		#if we aren't rallying, just lave.
		if not self.game.moveRally:
			return
		#if a unit is engaged, then the battle has already started, abort the rally.
		if self.game.unit_engaged:
#			self.game.moveRally = False		
			return
		
		#if we are under attack, stop rallying and go defend.
		if self.game.under_attack:
			self.game.moveRally = False
			self.game.defend_only = True			
			return
		#get the minimum power we can attack with.
		min_power = self.min_attack()
		#get the power of the army in the radius of the rally point and compare it against the known enemy army.
		#When it exceeds the minimum requirements, start attack
		rallyed = self.game.units.not_structure.exclude_type([PROBE,ADEPTPHASESHIFT,DISRUPTORPHASED]).closer_than(7, self.game.rally_pos)
		rallyScore = self.score_rally(rallyed)

		#currently in rally mode, don't attack until we have 20% more force than them.
		if rallyScore > min_power and rallyScore > (self.enemy_power + (self.enemy_power * .2)) or self.game.supply_used > 195:
			self.game.defend_only = False
			self.game.moveRally = False		
		
	def min_attack(self):
		min_power = 4000
		if self.strat_id == 1:
			min_power = 200
		elif self.strat_id == 2:
			min_power = 1500
		elif self.strat_id == 3:
			min_power = 2000
		elif self.strat_id == 4:
			min_power = 2500	
		elif self.strat_id == 5:
			min_power = 3000
			
		#if it's beyond 7 minutes in the game, min_power is too high to ever get too.
		# if self.game.time > 420:
		# 	min_power = 1000000
		
		#check to see if we just need to attack to collect enemy units.
		if self.enemy_power < 5:    
			min_power = 0
		return min_power

	def score_rally(self, army):
		army_score = 0
		for friendly in army:
			if self.unitCounter.getUnitPower(friendly.name):
				army_score += self.unitCounter.getUnitPower(friendly.name)
			else:
				print ('army_score missing', friendly.name)
		return army_score
	
	def score_hallucinations(self):
		hall_score = 0
		halls = self.game.unitList.hallucinationList()
		for unit_obj in halls:
			#score the unit
			hall_score += self.unitCounter.getUnitPower(unit_obj.unit.name)
		return hall_score
			

	def score_attack(self):
		#get the distance of our starting point to the midpoint of the map.
		mid = self.game.midpoint(self.game.start_location, random.choice(self.game.enemy_start_locations))
		dist = mid.distance_to(self.game.start_location)
		#get the distance of the furtherest friendly base and add 20 distance to it.
		#if it's a longer distance, use it instead of the midpoint.
		if len(self.game.units(NEXUS)) > 0:
			fdist = self.game.units(NEXUS).furthest_to(self.game.start_location).distance_to(self.game.start_location)
			if dist < (fdist + 20) :
				dist = fdist + 20
		
		
		#find all enemy units in that radius and score them.
		#attacking_enemies = self.game.cached_enemies.closer_than(dist, self.game.start_location)
		attacking_enemies = self.game.cached_enemies.filter(lambda x: (x.can_attack_ground or x.can_attack_air) and x.distance_to(self.game.start_location) < dist)
		enemy_score = 0
		for enemy in attacking_enemies:
			if self.unitCounter.getUnitPower(enemy.name):
				enemy_score += self.unitCounter.getUnitPower(enemy.name)
			else:
				print ('enemy_score missing', enemy.name)
		defend_score = 0
		friendlies = self.game.units.filter(lambda x: not x.name in ['Probe'] and (x.can_attack_ground or x.can_attack_air) and x.distance_to(self.game.start_location) <= dist)
		for friendly in friendlies:
			if self.unitCounter.getUnitPower(friendly.name):
				defend_score += self.unitCounter.getUnitPower(friendly.name)
			else:
				print ('army_score missing', friendly.name)		
		
		return [enemy_score, defend_score]	
		

	def attack_command(self):
		#check to see if we are under attack, if we are under attack don't issue an attack command.
		if self.game.defend_only and self.game.under_attack:
			return

		#if we are attacking and we are also under attack, then lets find out if we need to defend ourselves.
		if not self.game.defend_only and self.game.under_attack:
			[attack_score, defend_score] = self.score_attack()
			# print ('attscore', attack_score)
			# print ('defscore', defend_score)
			if attack_score > defend_score + 200:
				self.game.defend_only = True
				self.game.moveRally = False
				print ('going back to defense')

		#get the minimum power we can attack with.
		min_power = self.min_attack()
		if self.game.defend_only:
			#currently in defend mode, don't attack until we have 20% more force than them.
			if self.army_power > min_power and self.army_power > (self.enemy_power + (self.enemy_power * .2)) or self.game.supply_used > 195 or self.game.under_attack:
				self.game.defend_only = False
				self.game.moveRally = True
		else:
			#currently attacking, don't defend unless we have less force than enemy.
			if (self.army_power < self.enemy_power or self.army_power < min_power) and self.game.supply_used < 190 and not self.game.under_attack:
				self.game.defend_only = True
				self.game.moveRally = False
		#if all nexus are dead, might as well just attack and hope for the best.
		if self.game.units(NEXUS).amount == 0:
			self.game.defend_only = False
			self.game.moveRally = False
		#self.game.defend_only = True		


####################
#end game functions#
####################
	def checkVictory(self):
		if self.enemy_power > self.army_power:
			return False  #not even worth going further

		#if the enemy base has been scouted and the number of known enemy structures is 2, then gg.
		if self.game.base_searched and self.game.known_enemy_units.structure.amount < 3 and self.game.known_enemy_units.not_structure.amount < 4:
			#print ('gg')
			return True
	
		
		return False
	
	def checkDefeat(self):
		if self.game.units.structure.amount <= 3:
			return True
		# if self.game.units.of_type([PROBE,PHOTONCANNON]).amount == 0 and self.army_power == 0 and self.game.minerals < 50:
		# 	print ('lost 2')
		# 	return True #boned no matter how many structures we have.
		return False

#####################
#debugging functions#
#####################

	def debug_full_counters(self):
		#show enemy army found.
		xpos = 0.005
		for name, count in self.counted_enemy.items():
			if count == 0:
				continue
			displayList = ''
			counterList = self.unitCounter.getCounterUnits(name)
			#multiple the enemy count by the counter suggested.
			if not counterList:
				print ('counterlist missing', name)
			[best_list, canbuild] = self.parse_counterlist(counterList)
			for countList in best_list:
				#print ('counter', countList[0])
				needed = countList[1] * count
				displayList += "{}-{}, ".format(countList[0], needed)
				
			label = "{_name}: {_count} [{_counters}]".format(_name=name, _count=count, _counters=displayList)
			self.game._client.debug_text_screen(label, pos=(0.001, xpos), size=12)
			xpos += 0.025
		#add enemy power label
		xpos += 0.025
		elab = "Power: {_power}".format(_power=self.enemy_power)
		self.game._client.debug_text_screen(elab, pos=(0.001, xpos), size=12)
		
		#show what our army would look like if we built the best counter wanted.
		#show best army
		xpos = 0.055
		for name, count in self.raw_all_counters.items():
			#count number of these units we have.
			unitID = self.unitCounter.getUnitID(name)
			amt = self.game.units(unitID).amount + self.game.already_pending(unitID)

			allowed = self.check_allowed(name)

			label = "{_name}: {_count} - {_amt} [{_queued}] - {_allowed}".format(_name=name, _count=ceil(count), _amt=amt, _queued=str(self.game.already_pending(unitID)), _allowed=str(allowed))
			self.game._client.debug_text_screen(label, pos=(0.7, xpos), size=12)
			xpos += 0.025
		
	async def debug_positions(self):
		#show defensive position.
		if self.game.defensive_pos:
			self.game._client.debug_sphere_out(self.game.turn3d(self.game.defensive_pos.position), 1, Point3((132, 0, 66))) #purple
			self.game._client.debug_text_3d('DP', self.game.turn3d(self.game.defensive_pos.position))

		if self.game.rally_pos:
			self.game._client.debug_sphere_out(self.game.turn3d(self.game.rally_pos.position), 8, Point3((255,255,153))) #yellow
			self.game._client.debug_text_3d('RALLY POINT', self.game.turn3d(self.game.rally_pos.position))

		
		#show main ramp.
		self.game._client.debug_sphere_out(self.ramp1pylon1Pos.position, 1, Point3((244, 66, 125))) #pink
		self.game._client.debug_text_3d('Pylon1', self.ramp1pylon1Pos.position)

		self.game._client.debug_sphere_out(self.ramp1forgePos.position, 1, Point3((244, 66, 125))) #pink
		self.game._client.debug_text_3d('Forge', self.ramp1forgePos.position)		

		for ramp in self.game.game_info.map_ramps:
			self.game._client.debug_sphere_out(self.game.turn3d(ramp.top_center), 1, (252, 248, 0)) #yellow
		
	def debug_intel(self):
		xpos = 0.005
		for name, count in self.counted_enemy.items():
			label = "{_name}: {_count}".format(_name=name, _count=count)
			self.game._client.debug_text_screen(label, pos=(0.001, xpos), size=10)
			xpos += 0.025
		#add enemy power label
		xpos += 0.025
		elab = "Power: {_power}".format(_power=self.enemy_power)
		self.game._client.debug_text_screen(elab, pos=(0.001, xpos), size=10)

		#show best army
		xpos = 0.055
		for name, count in self.able_army.items():
			#count number of these units we have.
			unitID = self.unitCounter.getUnitID(name)
			amt = self.game.units(unitID).amount + self.game.already_pending(unitID)

			allowed = self.check_allowed(name)

			label = "{_name}: {_count} - {_amt} [{_queued}] - {_allowed}".format(_name=name, _count=ceil(count), _amt=amt, _queued=str(self.game.already_pending(unitID)), _allowed=str(allowed))
			self.game._client.debug_text_screen(label, pos=(0.7, xpos), size=10)
			xpos += 0.025
		
		#add army power label
		xpos += 0.025
		elab = "Power: {_power}".format(_power=self.army_power)
		self.game._client.debug_text_screen(elab, pos=(0.7, xpos), size=10)


		#show best raw army
		xpos = 0.055
		for name, count in self.ideal_army.items():
			#count number of these units we have.
			unitID = self.unitCounter.getUnitID(name)
			amt = self.game.units(unitID).amount + self.game.already_pending(unitID)

			allowed = self.check_allowed(name)

			label = "{_name}: {_count} - {_amt} [{_queued}] - {_allowed}".format(_name=name, _count=ceil(count), _amt=amt, _queued=str(self.game.already_pending(unitID)), _allowed=str(allowed))
			self.game._client.debug_text_screen(label, pos=(0.5, xpos), size=10)
			xpos += 0.025


			
		#show building requests
		xpos = 0.105
		for name, count in self.buildings_needed.items():
			label = "{_name}: {_count}".format(_name=name, _count=ceil(count))
			self.game._client.debug_text_screen(label, pos=(0.9, xpos), size=10)
			xpos += 0.025
		#show the production building counts.
		xpos += 0.025
		elab = "Gateways: {_ordered} : {_gates} : {_demand}".format(_ordered=str(self.build.gateways), _gates=str(self.game.trueGates), _demand=self.gate_demand)
		self.game._client.debug_text_screen(elab, pos=(0.85, xpos), size=10)			

		xpos += 0.025
		elab = "Robotics: {_ordered} : {_robo} : {_demand}".format(_ordered=str(self.build.roboticsfacility), _robo=str(self.game.units(ROBOTICSFACILITY).amount), _demand=self.robo_demand)
		self.game._client.debug_text_screen(elab, pos=(0.85, xpos), size=10)			
		
		xpos += 0.025
		elab = "Stargate: {_ordered} : {_star} : {_demand}".format(_ordered=str(self.build.stargates), _star=str(self.game.units(STARGATE).amount), _demand=self.star_demand)
		self.game._client.debug_text_screen(elab, pos=(0.85, xpos), size=10)


		# xpos += 0.025
		# elab = "Gate Q: {_ordered}".format(_ordered=str(self.game.queuedGates))
		# self.game._client.debug_text_screen(elab, pos=(0.9, xpos), size=10)

		#add saving label
		xpos += 0.025
		elab = "Saving: {_saving}".format(_saving=str(self.saving))
		self.game._client.debug_text_screen(elab, pos=(0.85, xpos), size=10)
		
		#add queue label
		xpos += 0.025
		elab = "All Queue: {_saving}".format(_saving=str(self.allAllowedQueued))
		self.game._client.debug_text_screen(elab, pos=(0.85, xpos), size=10)
		
		#add queue label
		xpos += 0.025
		elab = "Gate Queued: {_saving} : {_needed}".format(_saving=str(self.gateway_needed), _needed=str(self.game.queuedGates))
		self.game._client.debug_text_screen(elab, pos=(0.85, xpos), size=10)		
		
		#add queue label
		xpos += 0.025
		elab = "Robo Queued: {_saving} : {_needed}".format(_saving=str(self.robotics_needed), _needed=str(self.game.queuedRobos))
		self.game._client.debug_text_screen(elab, pos=(0.85, xpos), size=10)
		
		#add queue label
		xpos += 0.025
		elab = "Star Queued: {_saving} : {_needed}".format(_saving=str(self.stargate_needed), _needed=str(self.game.queuedStarGates))
		self.game._client.debug_text_screen(elab, pos=(0.85, xpos), size=10)			
	
		#add Rush label
		xpos += 0.025
		elab = "Rush Detected: {_rush}".format(_rush=str(self.game.rush_detected))
		self.game._client.debug_text_screen(elab, pos=(0.85, xpos), size=10)		

	def debug_map_vals(self):
		#loop the map dict and put a val on the spot.
		for key, distance in self.game.mapDistances.items():
			key = key.split(":")
			pos = Point2((int(key[0]), int(key[1])))
			self.game._client.debug_text_3d(str(int(distance)), self.game.turn3d(pos))
		
##################
#helper functions#
##################

	def countBuildings(self, num, building):
		c = 0
		i = 0
		for item in self.start_build_order:
			if item == building:
				c += 1
			if i == num:
				return c
			i += 1

	def buildBuilding(self, num):
		#num -= 1
		#grab the correct item, parse the building type, and count how many of them there should be at that point.
		if self.start_build_order[num] == 'Gateway':
			self.build.gateways = self.countBuildings(num, 'Gateway')
			
		elif self.start_build_order[num] == 'Stargate':
			self.build.stargates = self.countBuildings(num, 'Stargate')
			
		elif self.start_build_order[num] == 'RoboticsFacility':
			self.build.roboticsfacility = self.countBuildings(num, 'RoboticsFacility')
	
		elif self.start_build_order[num] == 'CyberneticsCore':
			self.build.cores = 1
			
		elif self.start_build_order[num] == 'RoboticsBay':
			self.build.roboticsbay = 1
			
		elif self.start_build_order[num] == 'FleetBeacon':
			self.build.fleetbeacons = 1
			
		elif self.start_build_order[num] == 'TwilightCouncil':
			self.build.twilights = 1			

	def rotate(self, origin, point, angle):
		qx = origin.x + math.cos(angle) * (point.x - origin.x) - math.sin(angle) * (point.y - origin.y)
		qy = origin.y + math.sin(angle) * (point.x - origin.x) + math.cos(angle) * (point.y - origin.y)
		return Point2((qx, qy))

	def midpoint(self, pos1, pos2):
		return Point2(((pos1.position.x + pos2.position.x) / 2, (pos1.position.y + pos2.position.y) /2))

	def findRamp2(self):
		
		#broken maps, return none on them.
		#print (self.game.game_info._proto.map_name)
		
		#try to locate the 2nd ramp.
		ramps = []
		for ramp in self.game.game_info.map_ramps:
			distance = sqrt((ramp.top_center[0] - self.game.main_base_ramp.top_center[0])**2 + (ramp.top_center[1] - self.game.main_base_ramp.top_center[1])**2)
			ramps.append([distance, ramp])
		ramps = sorted(ramps, key=itemgetter(0))
		if ramps[1][0] < 20:
			return ramps[1][1]
		#debug_sphere_out(self, p: Union[Unit, Point2, Point3], r: Union[int, float], color=None):
		return None

####################
#Start up functions#
####################

	async def setupPositions(self):
		#setup on main ramp.
		#self.ramp1forgePos
		#find the position for the forge.
		#self.ramp1pylon1Pos = self.game.turn3d(self.game.main_base_ramp.bottom_center.towards(self.game.main_base_ramp.top_center, 18))
		self.ramp1forgePos = self.game.turn3d(self.game.main_base_ramp.top_center.towards(self.game.main_base_ramp.bottom_center, -5.5))		
		self.ramp1pylon1Pos = self.game.turn3d(self.game.main_base_ramp.top_center.towards(self.game.main_base_ramp.bottom_center, -5.5))
		#self.ramp1forgePos = self.game.turn3d(self.game.game_info.player_start_location.towards(self.game.main_base_ramp.top_center, 6))
		#cannon1pos

		self.cannon1Pos = self.game.turn3d(self.rotate(self.ramp1pylon1Pos.position, self.ramp1pylon1Pos.towards(self.game.main_base_ramp.bottom_center, -1.5), 1))
		self.cannon2Pos = self.game.turn3d(self.rotate(self.ramp1pylon1Pos.position, self.ramp1pylon1Pos.towards(self.game.main_base_ramp.bottom_center, -1.5), 2))
		self.cannon3Pos = self.game.turn3d(self.rotate(self.ramp1pylon1Pos.position, self.ramp1pylon1Pos.towards(self.game.main_base_ramp.bottom_center, -1.5), 3))
		self.cannon4Pos = self.game.turn3d(self.rotate(self.ramp1pylon1Pos.position, self.ramp1pylon1Pos.towards(self.game.main_base_ramp.bottom_center, -1.5), 4))
		self.cannon5Pos = self.game.turn3d(self.rotate(self.ramp1pylon1Pos.position, self.ramp1pylon1Pos.towards(self.game.main_base_ramp.bottom_center, -1.5), 2.5))
		self.cannon6Pos = self.game.turn3d(self.rotate(self.ramp1pylon1Pos.position, self.ramp1pylon1Pos.towards(self.game.main_base_ramp.bottom_center, -1.5), 1.5))
		#add in 3 shield battery positions.
		self.battery1Pos = self.game.turn3d(self.rotate(self.ramp1pylon1Pos.position, self.ramp1pylon1Pos.towards(self.game.main_base_ramp.bottom_center, -3), 0.5))
		self.battery2Pos = self.game.turn3d(self.rotate(self.ramp1pylon1Pos.position, self.ramp1pylon1Pos.towards(self.game.main_base_ramp.bottom_center, -3), 5.5))
		self.battery3Pos = self.game.turn3d(self.rotate(self.ramp1pylon1Pos.position, self.ramp1pylon1Pos.towards(self.game.main_base_ramp.bottom_center, -3), 0))


		#setup main base pylons.
		nexus = self.game.units(NEXUS).closest_to(self.game.start_location)
		if nexus:
			mins = self.game.state.mineral_field.closer_than(15, nexus)
			vasp = self.game.state.vespene_geyser.closer_than(15, nexus)
#			mf = Units((mins + vasp), self.game)
			mf = Units((mins + vasp))			
			if mf:
				center_pos = Point2((sum([item.position.x for item in mf]) / len(mf), \
						sum([item.position.y for item in mf]) / len(mf)))
				nexdis = nexus.distance_to(center_pos)
				fmost = mf.furthest_to(center_pos)
				
	
				p1 = nexus.position.towards(center_pos, -5.5)
				p2 = nexus.position.towards(center_pos, (5.0 + nexdis))
				p3 = fmost.position.towards(p1, (3))
				fclose = mf.furthest_to(p3)
				p4 = fclose.position.towards(p1, (3))
	
				#find extended locations,
				#p6 = midpoint between 4 and 1,out from nexus.
				p6 = nexus.position.towards(self.midpoint(p1, p4), 9)
				#p7 = midpoint between 3 adn 1, out from nexus.
				p7 = nexus.position.towards(self.midpoint(p1, p3), 9)
				
				#p8 = midpoint between 1 and 4, out towards the midpoint between 6 and 4.
				p8 = self.midpoint(p1, p4).position.towards(self.midpoint(p6, p4), 9)
				#p9 = midpoint between 1 and 3, out towards the midpoint btween 7 and 3
				p9 = self.midpoint(p1, p3).position.towards(self.midpoint(p7, p3), 9)
	
				
				p2 = await self.game.find_placement(PYLON, p2)
				p3 = await self.game.find_placement(PYLON, p3)
				p4 = await self.game.find_placement(PYLON, p4)
				p6 = await self.game.find_placement(PYLON, p6)
				p7 = await self.game.find_placement(PYLON, p7)
				p8 = await self.game.find_placement(PYLON, p8)
				p9 = await self.game.find_placement(PYLON, p9)				
				self.build.pylon1Loc = self.game.turn3d(p1)
				self.build.pylon2Loc = self.game.turn3d(p2)
				self.build.pylon3Loc = self.game.turn3d(p3)
				self.build.pylon4Loc = self.game.turn3d(p4)
				self.build.pylon6Loc = self.game.turn3d(p6)
				self.build.pylon7Loc = self.game.turn3d(p7)
				self.build.pylon8Loc = self.game.turn3d(p8)
				self.build.pylon9Loc = self.game.turn3d(p9)
				
		#find placement for pylon 5.
		placement = await self.game.find_placement(PYLON, self.game.main_base_ramp.top_center)
		if placement:
			self.build.pylon5Loc = self.game.turn3d(placement)
	
	
		#find the proxy pylon position for the scout to place.
		startPos = random.choice(self.game.enemy_start_locations)
		proxy_distance = 10000
		proxy_loc = None
		for possible in self.game.expansion_locations:
			d = await self.game._client.query_pathing(startPos.position, possible)
			if d:
				if d > 10 and d < proxy_distance:
					proxy_distance = d
					proxy_loc = possible
		self.game.proxy_pylon_loc = await self.game.find_placement(PYLON, near=proxy_loc, max_distance=4)		
		
		
		#setup on 2nd ramp.
		if self.ramp2:
			ramp_bot_center = self.findRampBottomCenter(self.ramp2)
			self.pylon1Pos = self.game.turn3d(self.ramp2.top_center.towards(ramp_bot_center, -4))
			self.forgePos = self.game.turn3d(self.ramp2.top_center.towards(ramp_bot_center, -1.5))
			self.gateway1Pos = self.game.turn3d(self.ramp2.top_center.towards(ramp_bot_center, -1.5))
			
			self.r2battery1Pos = self.game.turn3d(self.rotate(self.pylon1Pos.position, self.pylon1Pos.towards(ramp_bot_center, -3), 0.5))
			self.r2battery2Pos = self.game.turn3d(self.rotate(self.pylon1Pos.position, self.pylon1Pos.towards(ramp_bot_center, -3), 5.5))
			self.r2battery3Pos = self.game.turn3d(self.rotate(self.pylon1Pos.position, self.pylon1Pos.towards(ramp_bot_center, -3), 0))
				
			
		else:
			# expanse = await self.game.get_next_expansion()
			# mf2 = self.game.state.mineral_field.closer_than(15, expanse)
			# vf = self.game.state.vespene_geyser.closer_than(15, expanse)
			# mf = Units((mf2 + vf), self.game)
			# center_pos = Point2((sum([item.position.x for item in mf]) / len(mf), \
			# 					sum([item.position.y for item in mf]) / len(mf)))
			# 
			# #find closest mineral field.
			# clmin = mf.closest_to(center_pos)
			# goto = center_pos.position.towards(expanse, 15.5)
			# bot_center = self.game.main_ramp_bottom_center
			
			#build off the first ramp.
			goto = self.game.turn3d(self.game.main_base_ramp.top_center.towards(self.game.main_base_ramp.bottom_center, 15.5))
			#check to see if we are close to the minerals, and if we are, then move towards the center of the map.
			if self.game.state.mineral_field.closer_than(6, goto) or self.game.state.vespene_geyser.closer_than(6, goto):
				#print ('moving pylon')
				goto = goto.towards(self.game._game_info.map_center, 10)
			
			self.pylon1Pos = self.game.turn3d(goto)
			self.forgePos = self.game.turn3d(goto)
			self.gateway1Pos = self.game.turn3d(goto)
			self.r2battery1Pos = self.game.turn3d(self.rotate(self.pylon1Pos.position, self.pylon1Pos.towards(self.game.main_base_ramp.bottom_center, 3), 0.5))
			self.r2battery2Pos = self.game.turn3d(self.rotate(self.pylon1Pos.position, self.pylon1Pos.towards(self.game.main_base_ramp.bottom_center, 3), 5.5))
			self.r2battery3Pos = self.game.turn3d(self.rotate(self.pylon1Pos.position, self.pylon1Pos.towards(self.game.main_base_ramp.bottom_center, 3), 0))
							

#####################
#Detection functions#
#####################

	def detect_reaper_cheese(self):
		#detect if the reaper is near the starting nexus, and if it is, set to true and then build cannons.
		if not self.game.reaper_cheese and self.game.known_enemy_units.of_type([REAPER,BANSHEE]).closer_than(20, self.game.start_location).amount > 1:
			self.game.reaper_cheese = True
			#print ('reaper/banshee cheese detected')
			#self.build.forges = 1

	def detect_allinWorker_rush(self):
		self.game.workerAllin = False
		#check the building list to see if any nexus have detected workers.
		if self.game.buildingList.underWorkerAllin:
			print ('all in detected')
			self.game.workerAllin = True
		
		
		

	def detect_rush(self):
		#print (self.game.units().not_structure.exclude_type(PROBE).amount, self.game.known_enemy_units.exists)
		detected = False
		if self.game.units.not_structure.exclude_type(PROBE).amount < 3 and self.game.units(PHOTONCANNON).ready.amount < 3 and self.game.units.structure.amount < 5:
			for nexus in self.game.units(NEXUS):
				#if not self.game.rush_detected and self.game.known_enemy_units.exclude_type(PROBE).not_flying.closer_than(20, nexus).amount > 5:
				if not self.game.rush_detected and self.game.known_enemy_units.not_flying.closer_than(20, nexus).amount > 2:
					detected = True
		#detected = True
		if detected:
			self.game.rush_detected = True
			#drop opening strats, just go into auto mode.
			
			self.stage1complete = True
			self.build.can_build_assimilators = True				
			self.build.can_build_pylons = True			
		else:
			self.game.rush_detected = False

#######################
#unorganized functions#
#######################

	def exp_scout(self):
		#if we have observers that exist, make sure one of them is assigned to the expansion scout job.
		if not self.expansion_scout and self.game.units(OBSERVER).ready.amount > 1:
			#nothing assigned get an observer to assign to duty.
			if self.game.units(OBSERVER).ready.exists:
				otag = self.game.units(OBSERVER).ready.random.tag
				obj = self.game.unitList.getObjectByTag(otag)
				if obj:
					obj.expansionScout = True
					self.expansion_scout = otag

	def save_expand(self):
		self.train.allow_voidrays = False
		self.train.allow_tempests = False
		self.train.allow_phoenix = False
		self.train.allow_zealots = False
		self.train.allow_stalkers = False
		self.train.allow_immortals = False
		self.train.allow_warpprisms = False
		self.train.allow_sentrys = False
		self.train.allow_observers = False
		self.train.allow_colossus = False
		self.train.allow_adepts = False
		self.train.allow_hightemplars = False
		self.train.allow_carriers = False
		
		self.build.gateways = 0
		self.build.cores = 0
		self.build.stargates = 0
		self.build.forges = 0
		self.build.fleetbeacons = 0
		self.build.twilights = 0
		self.build.roboticsfacility = 0
		self.build.roboticsbay = 0
		self.build.darkshrines = 0
		self.build.templararchives = 0		

		self.saving = True
		

	def safe_workers(self):
		if not self.worker_tag:
			#assign workers that will work no matter what to keep economy going.
			ct = 0
			for worker in self.game.units(PROBE):
				obj = self.game.unitList.getObjectByTag(worker.tag)
				#obj = self.game._pb_objects.get(worker.tag)
				if ct == 0:
					obj.scout = True
				if ct > 0 and ct < 2:
					obj.collect_only = True
				if ct >= 2:
					break
				ct += 1
			self.worker_tag = True
			
		
	def findRampBottomCenter(self, ramp):
		pos = Point2((sum([p.x for p in ramp.lower]) / len(ramp.lower), \
			sum([p.y for p in ramp.lower]) / len(ramp.lower)))
		return pos		
		

	def need_expand(self):
		# if self.game.buildingList.underAttack:
		# 	return False
		if self.game.time > 120 and self.game.minerals < 1250 and not self.game.already_pending(NEXUS) and self.game.units(NEXUS).ready.exists:   #don't save in the first 2 minutes.
			if not self.game.buildingList.workersRequested:
				return True
		return False
	
	def army_score(self):
		protoss_units = [COLOSSUS, ZEALOT, STALKER, HIGHTEMPLAR, DARKTEMPLAR, SENTRY, PHOENIX, CARRIER, VOIDRAY, WARPPRISM, OBSERVER, IMMORTAL, ADEPT, ORACLE, TEMPEST, DISRUPTOR, ARCHON]
		friendlyUnits = self.game.units().of_type(protoss_units)
		army_score = 0
		for friendly in friendlyUnits:
			if self.unitCounter.getUnitPower(friendly.name):
				army_score += self.unitCounter.getUnitPower(friendly.name)
			else:
				print ('army_score missing', friendly.name)
		#subtract hallucinations
		#hall_score = self.score_hallucinations()
		self.army_power = army_score - self.game.unitList.hallucinationScore


	def unit_ratios(self):
		#turn the ideal army into the ideal unit ratio.
		leastnum = sorted(self.ideal_army.items(), key=itemgetter(1), reverse=False)[0][1]
		if leastnum < 1:
			leastnum = 1
		for name, count in self.ideal_army.items():
			#divide the count of this unit by the leastnum, then round up.
			if count < 1:
				count = 1
			ecount = ceil(count / leastnum)
			#update the dictionary with new value.
			self.ideal_army.update({name:ecount})
			
		# if len(self.ideal_army) == 0:
		# 	self.ideal_army.update({'Zealot':1})		

		leastnum = sorted(self.able_army.items(), key=itemgetter(1), reverse=False)[0][1]
		if leastnum < 1:
			leastnum = 1		
		#do the same with the allowed so we can look at buildings to build.
		for name, count in self.able_army.items():
			#divide the count of this unit by the leastnum, then round up.
			if count < 1:
				count = 1			
			ecount = ceil(count / leastnum)
			#update the dictionary with new value.
			self.able_army.update({name:ecount})
			

	def needed_buildings(self):
		buildings_needed = {}
		demand_dict = {}
		self.buildersNeeded()
		for name, count in self.ideal_army.items():
			if not self.unitCounter.getUnitReqs(name):
				print ('unit req not found', name)
			req_buildings = self.unitCounter.getUnitReqs(name)
			madeit = 0
			for building in req_buildings:
				building_id = self.unitCounter.getUnitID(building)
				if building == 'Gateway':
					if self.game.units(WARPGATE).exists:
						building_id = WARPGATE
					
				if not self.game.units(building_id).exists:
					#doesn't exist, add to build queue.
					if not buildings_needed.get(building):
						buildings_needed.update({building:1})
					else:
						val = buildings_needed.get(building) + 1
						buildings_needed.update({building:val})
						
			#find the building that makes this unit and add into the demand.
			building = self.unitCounter.getUnitTrainer(name)
			if self.isBuilderNeeded(building):
				if not demand_dict.get(building):
					demand_dict.update({building:count})
				else:
					val = demand_dict.get(building) + count
					demand_dict.update({building:val})


		if len(demand_dict) > 0:
			#create the ratio we want based on the demand.
			leastnum = sorted(demand_dict.items(), key=itemgetter(1), reverse=False)[0][1]
			if leastnum < 1:
				leastnum = 1
			ratio = {}
			for name, count in demand_dict.items():
				#divide the count of this unit by the leastnum, then round up.
				if count < 1:
					count = 1
				ecount = ceil(count / leastnum)
				#update the dictionary with new value.
				ratio.update({name:ecount})
			
			if _debug:
				#update for debugging.
				demands = sorted(demand_dict.items(), key=itemgetter(1), reverse=True)
				t_gate = 0
				t_robo = 0
				t_star = 0
				r_gate = 0
				r_robo = 0
				r_star = 0			
				for demand in demands:
					if demand[0] == 'Gateway':
						t_gate = demand[1]
						r_gate = ratio.get(demand[0])
					if demand[0] == 'RoboticsFacility':
						t_robo = demand[1]
						r_robo = ratio.get(demand[0])
					if demand[0] == 'Stargate':
						t_star = demand[1]
						r_star = ratio.get(demand[0])
						
				self.gate_demand = "{ratio} : {raw}".format(raw=t_gate, ratio=r_gate)
				self.robo_demand = "{ratio} : {raw}".format(raw=t_robo, ratio=r_robo)
				self.star_demand = "{ratio} : {raw}".format(raw=t_star, ratio=r_star)

			#if we can build, then build the most requested.
			if len(buildings_needed) == 0 and self.allAllowedQueued and self.game.minerals > 400 and self.game.vespene > 350:
				min_sets = self.calc_minset(ratio)
				demanded = self.find_demanded(ratio, min_sets)
				#print (min_sets, demanded, ratio, buildings_needed)
			
				#demanded = sorted(demand_dict.items(), key=itemgetter(1), reverse=True)[0][0]
				#append the new value to buildings_needed
				if not buildings_needed.get(demanded):
					buildings_needed.update({demanded:1})
				else:
					val = buildings_needed.get(demanded) + 1
					buildings_needed.update({demanded:val})
					
				#print (buildings_needed)
				#turn off the others.
				if demanded == 'Gateway':
					self.build.roboticsfacility = 0
					self.build.stargates = 0
				elif demanded == 'RoboticsFacility':
					self.build.gateways = 0
					self.build.stargates = 0					
				elif demanded == 'Stargate':
					self.build.gateways = 0
					self.build.roboticsfacility = 0
					
					
			else:
				self.build.roboticsfacility = 0
				self.build.stargates = 0
				self.build.gateways = 0
		
		elif self.stage1complete:
			self.build.gateways = 0
			self.build.roboticsfacility = 0
			self.build.stargates = 0
			self.gate_demand = 0
			self.robo_demand = 0
			self.star_demand = 0
		else:
			self.gate_demand = 0
			self.robo_demand = 0
			self.star_demand = 0
			
			
		if not self.allAllowedQueued:
			if self.game.minerals > 500 and self.gateway_needed and self.game.queuedGates:
				buildings_needed.update({'Gateway':1})
			else:
			 	self.buildings_needed = {}
		else:
			self.buildings_needed = buildings_needed
		
	
	def find_demanded(self, ratio, sets):
		#multiple the ratio by the min_sets to get the current wanted amount of the building.
		#then subtract how many actual buildings we have from them, and the one with the least is the most demanded.
		demanded = None
		most_needed = -1
		demanded_count = 100
		for building, count in ratio.items():
			[needed, d_count] = self.calc_need(building, count, sets)
			if needed > most_needed and d_count < demanded_count:
				demanded_count = d_count
				most_needed = needed
				demanded = building
	

		return demanded
	
	def calc_minset(self, ratio):
		min_sets = 100
		for building, count in ratio.items():
			sets = self.calc_set(building, count)
			if sets < min_sets:
				min_sets = sets
		min_sets += 1
		return ceil(min_sets)


	def calc_need(self, building, count, sets):
		need = 0
		dcount = 0
		if building == 'Gateway':
			need = (count * sets) - self.game.trueGates
			dcount = self.game.trueGates
		if building == 'Stargate':
			need = (count * sets) - self.game.units(STARGATE).amount
			dcount = self.game.units(STARGATE).amount
		if building == 'RoboticsFacility':
			need = (count * sets) - self.game.units(ROBOTICSFACILITY).amount
			dcount = self.game.units(ROBOTICSFACILITY).amount
		return [need, dcount]

	
	def calc_set(self, building, count):
		sets = 1
		if building == 'Gateway':
			if self.game.trueGates > count:
				sets = count / self.game.trueGates
		if building == 'Stargate':
			if self.game.units(STARGATE).amount > count:
				sets = count / self.game.units(STARGATE).amount			
		if building == 'RoboticsFacility':
			if self.game.units(ROBOTICSFACILITY).amount > count:
				sets = count / self.game.units(ROBOTICSFACILITY).amount
		return sets	
	

	def calc_demand(self, building, demand):
		new_demand = demand
		if building == 'Gateway':
			if self.game.trueGates > 0:
				new_demand = demand / self.game.trueGates
		if building == 'Stargate':
			if self.game.units(STARGATE).exists:
				new_demand = demand / self.game.units(STARGATE).amount			
		if building == 'RoboticsFacility':
			if self.game.units(ROBOTICSFACILITY).exists:
				new_demand = demand / self.game.units(ROBOTICSFACILITY).amount
		return new_demand
			
	
	def checkUnitReq(self, name):
		#check to see if we have all the requirements of the unit.
		if not self.unitCounter.getUnitReqs(name):
			print ('unit not found in requirements', name)
			return False
		
		req_buildings = self.unitCounter.getUnitReqs(name)
		for building in req_buildings:
			#convert building name to id
			building_id = self.unitCounter.getUnitID(building)
			if building == 'Gateway':
				if self.game.units(WARPGATE).exists:
					building_id = WARPGATE
			if not self.game.units(building_id).ready.exists:
				#doesn't exist, can't build it yet.
				return False
		return True


	def parse_counterlist(self, counters):
		canbuild = []
		best_list = []
		listnum = 0
		for counter in counters:
			#[['Phoenix', 0.5]],
			templist = []
			passtest = True
			for unit in counter:
				#if this is the first line, append it to the best list for future building goals.
				if listnum == 0:
					best_list.append(unit)
				#find out if we are able to build the unit.
				if passtest:
					if self.checkUnitReq(unit[0]):
						#able to build it.
						templist.append(unit)
					else:
						passtest = False
						continue
				
			if passtest:
				canbuild = templist
				break
			listnum += 1
		return [best_list, canbuild]
		
	def calc_starter_counters_old(self, inc_units):
		counters = {}
		#loop units and get the counters.
		for name in inc_units:
			self.ghost_units.update({name:0})
			counterList = self.unitCounter.getCounterUnits(name)
			#multiple the enemy count by the counter suggested.
			if not counterList:
				print ('counterlist missing', name)
			[best_list, canbuild] = self.parse_counterlist(counterList)	
			for countList in best_list:
				#add the counter to the existing for a total needed of unit.
				needed = countList[1]
				if not counters.get(countList[0]):
					counters.update({countList[0]:needed})
				else:
					val = counters.get(countList[0]) + needed
					counters.update({countList[0]:val})
		self.starting_army = counters
		#now calculate the buildings we need.
		#print (counters)
		buildings_needed = {}
		demand_dict = {}
		for name, count in self.starting_army.items():
			#print (name, count)
			#find the building that makes this unit and add into the demand.
			building = self.unitCounter.getUnitTrainer(name)
			unitValue = self.unitCounter.getUnitCost(name) * count
			if not demand_dict.get(building):
				demand_dict.update({building:unitValue})
			else:
				val = demand_dict.get(building) + unitValue
				demand_dict.update({building:val})
		#get the building we need the most.
		most_requested = 'Gateway'
		most_requested_count = 0
		for building, count in demand_dict.items():
			#print (building, count)
			if count > most_requested_count:
				most_requested_count = count
				most_requested = building
		
		most_requested2 = most_requested
		if most_requested == 'RoboticsFacility' and not self.starting_army.get('Immortal'):
			most_requested2 = 'RoboticsBay'
		
		if most_requested == 'Stargate':
			if not self.starting_army.get('VoidRay') and not self.starting_army.get('Phoenix'):
				most_requested2 = 'FleetBeacon'
		
		if most_requested == 'Gateway':
			most_requested2 = 'TwilightCouncil'

		self.start_build_order = ['Gateway', 'CyberneticsCore', most_requested, most_requested2]
#		self.start_build_order = ['Gateway', 'CyberneticsCore', 'Gateway', 'RoboticsFacility']		
		
		if self.game.enemy_race == Race.Protoss and most_requested == 'Gateway':
			self.start_build_order = ['Gateway', 'Gateway', 'CyberneticsCore', most_requested2]


		print (self.start_build_order)

	def calc_starter_counters(self, inc_units):
		counters = {}
		#loop units and get the counters.
		for name in inc_units:
			self.ghost_units.update({name:0})
			counterList = self.unitCounter.getCounterUnits(name)
			#multiple the enemy count by the counter suggested.
			if not counterList:
				print ('counterlist missing', name)
			[best_list, canbuild] = self.parse_counterlist(counterList)	
			for countList in best_list:
				#add the counter to the existing for a total needed of unit.
				needed = countList[1]
				if not counters.get(countList[0]):
					counters.update({countList[0]:needed})
				else:
					val = counters.get(countList[0]) + needed
					counters.update({countList[0]:val})
		self.starting_army = counters
		#now calculate the buildings we need.
		#print (counters)
		buildings_needed = {}
		demand_dict = {}
		for name, count in self.starting_army.items():
			#print (name, count)
			#find the building that makes this unit and add into the demand.
			building = self.unitCounter.getUnitTrainer(name)
			unitValue = self.unitCounter.getUnitCost(name) * count
			if not demand_dict.get(building):
				demand_dict.update({building:unitValue})
			else:
				val = demand_dict.get(building) + unitValue
				demand_dict.update({building:val})
		#get the building we need the most.
		most_requested = 'Gateway'
		most_requested_count = 0
		requestedList = []
		for building, count in demand_dict.items():
			#print (building, count)
			if count > 0:
				requestedList.append(building)
			if count > most_requested_count:
				most_requested_count = count
				most_requested = building

		most_requested2 = most_requested
		if 'Stargate' in requestedList and 'RoboticsFacility' in requestedList:
			if most_requested == 'Stargate':
				most_requested2 = 'RoboticsFacility'
			elif most_requested == 'RoboticsFacility':
				most_requested2 = 'Stargate'
			else:
				most_requested2 = 'RoboticsFacility'
		else:
			if most_requested == 'RoboticsFacility':
				if not self.starting_army.get('Immortal'):
					most_requested2 = 'RoboticsBay'
				else:
					most_requested = 'Gateway'
					most_requested2 = 'RoboticsFacility'
			elif most_requested == 'Stargate':
				if not self.starting_army.get('VoidRay') and not self.starting_army.get('Phoenix'):
					most_requested2 = 'FleetBeacon'
				else:
					most_requested = 'Gateway'
					most_requested2 = 'Stargate'
			elif most_requested == 'Gateway':
				if 'RoboticsFacility' in requestedList:
					most_requested2 = 'RoboticsFacility'
				elif 'TemplarArchive' in requestedList:
					most_requested2 = 'TemplarArchive'
				else:
					most_requested2 = 'TwilightCouncil'
		self.start_build_order = ['Gateway', 'CyberneticsCore', most_requested, most_requested2]
		
		if self.game.enemy_race == Race.Protoss and most_requested == 'Gateway':
			self.start_build_order = ['Gateway', 'Gateway', 'CyberneticsCore', most_requested2]
		print (self.start_build_order)
		return self.start_build_order
		
	def calc_counters(self):
		counters = {}
		possible_counters = {}
		enemy_power = 0
		ground_units = 0
		ground_supply = 0
		#add in ghost units.
		
		for name, count in self.counted_enemy.items():
			counterList = self.unitCounter.getCounterUnits(name)
			#multiple the enemy count by the counter suggested.
			if not counterList:
				print ('counterlist missing', name)
				
			[best_list, canbuild] = self.parse_counterlist(counterList)	
			for countList in best_list:
				# if len (countList) < 2:
				# 	print (countList)
				needed = countList[1] * count
				if not counters.get(countList[0]):
					counters.update({countList[0]:needed})
				else:
					val = counters.get(countList[0]) + needed
					counters.update({countList[0]:val})

				if self.unitCounter.getUnitOpArea(countList[0]) == 'Ground':
					ground_units += count
					#add supply cost to ground supply.
					#print ('cs',  self.unitCounter.getUnitCargo(counterList[0]))
					ground_supply += self.unitCounter.getUnitCargo(countList[0]) * count					
			#calculate a power score.
			if count > 0:
				enemy_power += (self.unitCounter.getUnitPower(name) * count)

			#make our possible counters list.
			for countList in canbuild:
				needed = countList[1] * count
				if not possible_counters.get(countList[0]):
					possible_counters.update({countList[0]:needed})
				else:
					val = possible_counters.get(countList[0]) + needed
					possible_counters.update({countList[0]:val})			
			
			
		#basic building if we have nothing in our list.
		if len(possible_counters) == 0:
			if self.game.enemy_race == Race.Protoss:
				if self.game.units(ZEALOT).amount > 0:
					possible_counters.update({'Stalker':2})
				else:
					possible_counters.update({'Zealot':1})
			elif self.game.enemy_race == Race.Terran:
				possible_counters.update({'Stalker':1})
			elif self.game.enemy_race == Race.Zerg:
				possible_counters.update({'Zealot':1})
			else:
				possible_counters.update({'Zealot':1})
				

		if len(counters) == 0:
			if self.game.enemy_race == Race.Protoss:
				if self.game.units(ZEALOT).amount > 0:
					counters.update({'Stalker':2})
				else:
					counters.update({'Zealot':1})
			elif self.game.enemy_race == Race.Terran:
				counters.update({'Stalker':1})
			elif self.game.enemy_race == Race.Zerg:
				counters.update({'Zealot':1})
			else:
				counters.update({'Zealot':1})
	
		self.raw_all_counters = dict(counters)
		self.enemy_power = enemy_power
		self.ideal_army = counters
		self.raw_ideal_army = dict(counters)
		self.able_army = possible_counters



	def reset_allowed(self):
		self.train.allow_voidrays = False
		self.train.allow_tempests = False
		self.train.allow_phoenix = False
		self.train.allow_zealots = False
		self.train.allow_stalkers = False
		self.train.allow_immortals = False
		self.train.allow_warpprisms = False
		self.train.allow_sentrys = False
		self.train.allow_observers = False
		self.train.allow_colossus = False
		self.train.allow_adepts = False
		self.train.allow_hightemplars = False
		self.train.allow_disruptors = False		

	def change_allowed(self, name, allowed):
		if name == 'VoidRay':
			self.train.allow_voidrays = allowed
		if name == 'Tempest':
			self.train.allow_tempests = allowed
		if name == 'Phoenix':
			self.train.allow_phoenix = allowed
		if name == 'Zealot':
			self.train.allow_zealots = allowed
		if name == 'Stalker':
			self.train.allow_stalkers = allowed
		if name == 'Immortal':
			self.train.allow_immortals = allowed
		if name == 'WarpPrism':
			self.train.allow_warpprisms = allowed
		if name == 'Sentry':
			self.train.allow_sentrys = allowed
		if name == 'Observer':
			self.train.allow_observer = allowed
		if name == 'Colossus':
			self.train.allow_colossus = allowed
		if name == 'Adept':
			self.train.allow_adepts = allowed		
		if name == 'HighTemplar':
			self.train.allow_hightemplars = allowed	
		if name == 'Disruptor':
			self.train.allow_disruptors = allowed	
		if name == 'Carrier':
			self.train.allow_carriers = allowed		
		if name == 'Mothership':
			self.train.allow_mothership = allowed	
	def check_allowed(self, name):
		if name == 'VoidRay':
			return self.train.allow_voidrays
		if name == 'Tempest':
			return self.train.allow_tempests
		if name == 'Phoenix':
			return self.train.allow_phoenix
		if name == 'Zealot':
			return self.train.allow_zealots
		if name == 'Stalker':
			return self.train.allow_stalkers
		if name == 'Immortal':
			return self.train.allow_immortals
		if name == 'WarpPrism':
			return self.train.allow_warpprisms
		if name == 'Sentry':
			return self.train.allow_sentrys
		if name == 'Observer':
			return self.train.allow_observers
		if name == 'Colossus':
			return self.train.allow_colossus
		if name == 'Adept':
			return self.train.allow_adepts
		if name == 'HighTemplar':
			return self.train.allow_hightemplars
		if name == 'Disruptor':
			return self.train.allow_disruptors
		if name == 'Carrier':
			return self.train.allow_carriers
		if name == 'Mothership':
			return self.train.allow_mothership		

	def remove_timed(self, tag):
		if self.unitTimes.get(tag):
			del self.unitTimes[tag]		

	def remove_intel(self, tag):
		if self.enemy_intel.get(tag):
			del self.enemy_intel[tag]
				
	def count_intel(self):
		#count how many of each unit we have and report.
		counted_enemy = {}
		for tag, name in self.enemy_intel.items():
			if not counted_enemy.get(name):
				counted_enemy.update({name:1})
			else:
				val = counted_enemy.get(name) + 1
				counted_enemy.update({name:val})
		#add in any ghost units needed.
		for name, count in self.ghost_units.items():
			if not counted_enemy.get(name):
				counted_enemy.update({name:0})
		self.counted_enemy = counted_enemy
		#print (self.counted_enemy)

	def cannonReplace(self, enemy):
		#check to see if this cannon exists by position.
		if self.enemy_cannons.get(enemy.position):
			#one already exists, get the old tag out of the value and remove it.
			tag = self.enemy_cannons.get(enemy.position)
			self.remove_intel(tag)
		#update the new tag for the position.
		self.enemy_cannons.update({enemy.position:enemy.tag})

	def collect_intel(self):
		#collect all the known enemy names, tags
		zerg_units = [LURKERMP, LURKERMPBURROWED, ZERGLINGBURROWED, OVERLORDTRANSPORT, HYDRALISKBURROWED, ROACHBURROWED, SPINECRAWLERUPROOTED, SPORECRAWLERUPROOTED, SPINECRAWLER, SPORECRAWLER, OVERLORD, BANELING, ZERGLING, HYDRALISK, MUTALISK, ULTRALISK, ROACH, INFESTOR, BROODLORD, QUEEN, OVERSEER, RAVAGER, LURKER, CORRUPTOR, VIPER]
		terran_units = [BUNKER, LIBERATORAG, HELLIONTANK, PLANETARYFORTRESS, COMMANDCENTER, MARINE, SIEGETANK, SIEGETANKSIEGED, REAPER, GHOST, MARAUDER, THOR, MEDIVAC, BANSHEE, RAVEN, BATTLECRUISER, VIKINGASSAULT, VIKINGFIGHTER, LIBERATOR, HELLION, WIDOWMINEBURROWED, WIDOWMINE, CYCLONE, MISSILETURRET]
		protoss_units = [MOTHERSHIP, COLOSSUS, ZEALOT, STALKER, HIGHTEMPLAR, DARKTEMPLAR, SENTRY, PHOENIX, CARRIER, VOIDRAY, WARPPRISM, OBSERVER, IMMORTAL, ADEPT, ORACLE, TEMPEST, DISRUPTOR, ARCHON, PHOTONCANNON]
		all_units = zerg_units + terran_units + protoss_units
		enemyThreats = self.game.known_enemy_units.of_type(all_units)
		new_unit = False
		removals = {}
		for enemy in enemyThreats:
			#check if a new unique type of unit.
			if enemy.name not in self.unique_enemies:
				self.unique_enemies.append(enemy.name)
				new_unit = True
				#populate it into the ghost units if needed.
				self.ghost_units.update({enemy.name:0})
			#check if already exists, if it doesn't, add it.
			if not self.enemy_intel.get(enemy.tag):
				self.enemy_intel.update({enemy.tag:enemy.name})
				#enemy structurs seem to change tags, use the position to get rid of the old tag.
				if enemy.is_structure:
					self.cannonReplace(enemy)
				#check to see if it's a unit that morphed in, if so add it to removals.
				if enemy.name in ['Archon']:
					#check to see if it exists already, if so add more.
					if removals.get(enemy.name):
						val = removals.get(enemy.name) + 1
						removals.update({enemy.name:val})
					else:
						removals.update({enemy.name:1})

			# Keep the last time a unit that can morph into another was seen
			if enemy.name in ['HighTemplar', 'DarkTemplar']:
				self.unitTimes.update({enemy.tag:[enemy.name, self.game.time]})
				
		if new_unit and self.game.savingData:
			#save if unique unit found
			self.game._training_data.saveUnitResult(self.game.opp_id, self.unique_enemies, self.game.enemy_race)

		#if morphed unit was found, remove oldest previous unit if possible.
		if len(removals) > 0:
			#sort the time based unit dictionary
			sorted_units = sorted(self.unitTimes.items(), key=itemgetter(1), reverse=False)
			for name, num in removals.items():
				if name == 'Archon':
					remove_total = num * 2
					removed = []
					for tag, [pname, ltime] in self.unitTimes.items():
						if pname in ['HighTemplar', 'DarkTemplar']:
							#remove from lists.
							self.remove_intel(tag)
							removed.append(tag)
							if len(removed) >= remove_total:
								break
					#clear units from unitTimes
					for tag in removed:
						self.remove_timed(tag)


		
	def assign_nexus_builder(self, direct=False):
		if not self.game.expPos:
			return False
		if (self.saving and self.game.minerals > 225) or direct:
			#select the worker closes to the next expansion slot.
			#mark him as being the next expansion builder.
			if not self.game.unitList.nexusBuilderAssigned and len(self.game.units(PROBE).ready) > 0:
				probes = self.game.units(PROBE).sorted(lambda x: x.distance_to(self.game.expPos))
				for probe in probes:
					#get the unit obj by tag.
					probe_obj = self.game.unitList.getObjectByTag(probe.tag)
					if not probe_obj.collect_only and not probe_obj.scout:
						probe_obj.nexus_builder = True
						probe_obj.rush_defender = False
						probe_obj.lite_defender = False
						probe_obj.removeGatherer()
						return
		elif not direct:
			#clear any that might have been marked.
			self.game.unitList.freeNexusBuilders()
			
						




	def detect_single_worker(self):
		if not self.worker_detected and self.game.time < 180:
			#check for the single worker and assign 2 workers to attack it.
			if self.game.known_enemy_units.of_type([PROBE,DRONE,SCV,PHOTONCANNON,REAPER]).closer_than(25, self.game.game_info.player_start_location).amount == 1:
				#grab the 1 worker closest to the enemy that aren't marked as collectors or scouts
				defenders = 0
				self.worker_detected = True
				#for tag, obj in self.game._pb_objects.items():
				for tag, obj in self.game.unitList.getWorkers():
					if not obj.collect_only and not obj.scout:
						obj.lite_defender = True
						obj.removeGatherer()
						
						defenders += 1
						if defenders > 1:
							break
		elif self.worker_detected:
			#send workers back to work when it's over.
			if self.game.known_enemy_units.of_type([PROBE,DRONE,SCV,PHOTONCANNON]).closer_than(25, self.game.game_info.player_start_location).amount == 0:
				self.worker_detected = False
				#for tag, obj in self.game._pb_objects.items():
				for tag, obj in self.game.unitList.getWorkers():
					obj.lite_defender = False	
					#obj.removeGatherer()	
			

					
	def findUnworkedAssimilators(self):
		return self.game.units(ASSIMILATOR).ready.filter(lambda x:x.vespene_contents > 0 and x.assigned_harvesters < 3)
				
		
		
	def isBuilderNeeded(self, building):
		if building == 'Gateway':
			return self.gateway_needed
		if building == 'RoboticsFacility':
			return self.robotics_needed
		if building == 'Stargate':
			return self.stargate_needed
		
		
	def buildersNeeded(self):
		needed = []
		#loop over unit ratio and if true, set as needed.
		for unit in self.ideal_army:
			#check if allowed is true.
			if self.check_allowed(unit):
				#find the builder and add it to the list.
				if not self.unitCounter.getUnitTrainer(unit):
					print ('builder crash', unit)
				needed.append(self.unitCounter.getUnitTrainer(unit))
		
		self.gateway_needed = False
		self.robotics_needed = False
		self.stargate_needed = False		
			
		for builder in needed:
			if builder == 'Gateway':
				self.gateway_needed = True
					
			if builder == 'RoboticsFacility':
				self.robotics_needed = True
			
			if builder == 'Stargate':
				self.stargate_needed = True				


	@property
	def startBuildingCount(self) -> int:
		return self.game.units(CYBERNETICSCORE).amount + self.game.productionBuildings + self.game.units(ROBOTICSBAY).amount + self.game.units(FLEETBEACON).amount + self.game.units(TWILIGHTCOUNCIL).amount

	@property
	def allAllowedQueued(self) -> bool:
		self.buildersNeeded()
		if self.gateway_needed and not self.game.buildingList.gatesQueued:
			return False
		if self.stargate_needed and not self.game.buildingList.stargatesQueued:
			return False
		if self.robotics_needed and not self.game.buildingList.robosQueued:
			return False
		return True
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		

