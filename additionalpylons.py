import sc2
import sys
import argparse
from sc2 import run_game, maps, Race, Difficulty, position
from sc2.player import Bot, Computer
from sc2.constants import *
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
import random
import configparser
from math import sqrt, sin, cos, ceil
from operator import itemgetter
import datetime
import time
import pickle
from s2clientprotocol import query_pb2 as query_pb
from s2clientprotocol import raw_pb2 as raw_pb
from s2clientprotocol import sc2api_pb2 as sc_pb

#our own classes
from unit_list import UnitList as unitList
from building_list import BuildingList as buildingList
from builder import Builder as buildControl
from trainer import Trainer as trainControl
from strategist import Strategist as stratControl
from trainingdata import TrainingData as trainingData
from protoss_agent import ProtossAgent as protossAgent
from effects import Effects as effects_obj


_version = 'v1.601'
_collect_data = False  #collect data against protoss enemies if true.
_trainfile = "data/protoss-training"

#load up configuration from the config file.
_ini_parse = configparser.ConfigParser()
_ini_parse.read('config.ini')
_debug = _ini_parse['Debug'].getboolean('debug')
_debug_economy = _ini_parse['Debug'].getboolean('debug_economy')
_debug_positions = _ini_parse['Debug'].getboolean('debug_positions')
_debug_score = _ini_parse['Debug'].getboolean('debug_score')
_debug_counters = _ini_parse['Debug'].getboolean('debug_counters')
_debug_effects = _ini_parse['Debug'].getboolean('debug_effects')
_debug_combat = _ini_parse['Debug'].getboolean('debug_combat')
_local_ladder = _ini_parse['Debug'].getboolean('local_ladder')
_use_data = _ini_parse['Strategy'].getboolean('use_data')
_test_strat_id = int(_ini_parse['Strategy']['test_strat_id'])
_zerg_race_strat_id = int(_ini_parse['Strategy']['zerg_race_strat_id'])
_protoss_race_strat_id = int(_ini_parse['Strategy']['protoss_race_strat_id'])
_terran_race_strat_id = int(_ini_parse['Strategy']['terran_race_strat_id'])
_exclude_list = {ADEPTPHASESHIFT,INTERCEPTOR,EGG,LARVA}

class MyBot(sc2.BotAI, effects_obj):
	def __init__(self):
		self.opp_id = self.findOppId()
		self._build_manager = buildControl(self)
		self._train_manager = trainControl()
		self._strat_manager = stratControl(self)
		self._training_data = trainingData()
		self.unitList = unitList()
		self.buildingList = buildingList()
		self._protossAgent = protossAgent(self)
		self._max_workers = 70
		self._defense_distance = 10
		self._next_status_gap = 30
		self._working_mines = 0
		self._upgrade_scout = False
		self._defend_enemies = []
		self._economic_update_gap = 1/2
		self._next_endgame_check = 120
		self._next_economic_update = -10
		self._emergency_units = 0
		self._wp_cargo = {}
		self._worker_assignments = {}
		self.hm_offset = None
		self.defend_only = True
		self.base_searched = False
		self.expPos = None
		#z = self.ramp.height_at(pos)
		#worker rush variables.
		self.rush_detected = False
		self.update_workers = False
		self.reaper_cheese = False
		self.workerAllin = False
		#end game variables.
		self.victory_detected = None
		self.defeat_detected = None
		#other
		self.worker_force_leave = False
		self.proxy_pylon_loc = None
		self.worker_moved = None #the last time a worker moved.
		self.match_id = None
		self.opp_race = None
		self.map_name = None
		self.defensive_pos = None
		self.rally_pos = None
		self.moveRally = False
		self.prism_pylon_pos = None
		self.unit_engaged = False
		self._next_worker_update = 0
		self.under_attack = False
		self.allAbilities = {}
		self.gg_said = False
		self.alive_said = False
		self.intro_value = None
		self.intro_said = False
		self.opp_unit_history = None
		self.last_iter = -1
		self.unit_moves = {} #tracks if the unit moved since last frame.
		self.unit_positions = {} # tracks the last positions of the units, updates every frame.
		self.burrowed_mines = {}
		self.burrowed_lurkers = {}
		self.cached_enemies = None
		self.saved_enemy_structures = 0
		self.dodge_positions = []
		self.air_dodge_positions = []
		self.obs_dodge_positions = []
		self.savingData = _use_data

	async def on_step(self, iteration):
		#realtime=True fix
		if self.last_iter == iteration:
			return
		self.last_iter = iteration
		self._client.game_step = 2
		#reset the variable to prevent multiple worker kick offs at once.
		self.worker_force_leave = False
		self.unit_engaged = False
		#reset training save
		self._build_manager.last_build = None

		self.combinedActions = []
		#cache enemies for future calls.
		self.cache_enemies()
		self.check_movements()
		#check to see if the amount of enemy buildings has changed, then find a new rally point if so.
		await self.check_enemy_structures()

		#put all effect positions to be dodged into a list.
		self.addEffects()


		self.allAbilities = await self.getAllAbilities()


		if self.time > self._next_endgame_check:
			await self.endGameCheck()
			self._next_endgame_check = self.time + 1

		#say GL and give version info for debugging.
		if not self.intro_said and self.time > 4:
			#await self._client.chat_send(self._strat_manager.unitCounter.getIntroSaying(), team_only=False)
			await self._client.chat_send(self.intro_value, team_only=False)
			if _use_data:
				intro_des = self._strat_manager.unitCounter.getIntroDescription(self._strat_manager.strat_id)
				win_per = self._training_data.stratWinPer()
				full = "I'm starting with {}.{}".format(intro_des, win_per)
				await self._client.chat_send(full, team_only=False)
			else:
				intro_des = self._strat_manager.unitCounter.getIntroDescription(self._strat_manager.strat_id)
				full = "I'm starting with {}.  It's been chosen by opponent race".format(intro_des)
				await self._client.chat_send(full, team_only=False)				
			self.intro_said = True

		#first step stuff
		if iteration == 0:
			self.loadStart()

		self.can_spend = True
		#if iteration % 6 == 0:
		if self.time > self._next_economic_update:
			self._next_economic_update = self.time + 0.33

			#print ('eco', str(iteration))
			#self.expPos = self._get_next_expansion()
			self.checkAttack()
			await self.build_economy()

			###strategist###
			await self._strat_manager.strat_control(self, self._build_manager, self._train_manager)

			###build#####
			if self.can_spend:
				await self._build_manager.build_any(self)
			###save observation data along with the action taken.###
			if _collect_data and self.enemy_race == Race.Protoss:
				await self._protossAgent.save_decision(self)

			###run independent buildings###
			await self.buildingList.make_decisions(self)

			#create Archons if we can.
			await self.createArchons()

		###run all units###
		self.unitList.make_decisions(self)

		#cancel buildings that are being attacked and are low on health.
		self.cancelBuildings()

		if _debug:
			if _debug_counters:
				self._strat_manager.debug_full_counters()
			if _debug_positions:
				await self._strat_manager.debug_positions()
			if _debug_economy:
				self._strat_manager.debug_intel()
			if _debug_effects:
				self.debugEffects()
			await self._client.send_debug()
			#time.sleep(300)
		await self.do_actions(self.combinedActions)

	def on_end(self, result):
		#self._training_data.saveResult(self.opp_id, 2, result)
		if _use_data:
			print (str(result))
			if 'Defeat' in str(result) and not self.defeat_detected:
				print ('removing result')
				self._training_data.removeResult(self.opp_id, self.match_id, self.enemy_race)
		if _collect_data and self.enemy_race == Race.Protoss and 'Victory' in str(result):
			self.saveObs()


	async def on_unit_destroyed(self, unit_tag):
		#remove enemy from intel if possible.
		self._strat_manager.remove_intel(unit_tag)
		#remove enemy from timed intel if possible.
		self._strat_manager.remove_timed(unit_tag)

		#remove friend from unit list if possible.
		self.unitList.remove_object(unit_tag)
		#remove from building list if possible.
		await self.buildingList.remove_object(unit_tag, self)
		#remove from widowmine list if possible.
		self.removeWidowmine(unit_tag)
		self.removeLurker(unit_tag)
		#remove from expansion scout if matches.
		if self._strat_manager.expansion_scout == unit_tag:
			self._strat_manager.expansion_scout = None
		#no way to know if it's a nexus if it was completed, so remove get next expansion just in case.  Hope this is gone later.
		self.expPos = await self.get_next_expansion()

	async def on_unit_created(self, unit):
		self.unitList.load_object(unit)

	async def on_building_construction_complete(self, unit):
		self.buildingList.load_object(unit)

	async def on_building_construction_started(self, unit):
		if unit.name == 'Nexus':
			self.getDefensivePoint()
			await self.getRallyPoint()
			self.expPos = await self.get_next_expansion()
			self.buildingList.load_object(unit)
		#detect nexus on start
		if self.last_iter < 3:
			self.buildingList.load_object(unit)



	async def select_closest_worker(self, pos):
		adj_pos = self.turn3d(pos.position)
		probes = self.units(PROBE).ready
		#best probe = equal height only probes.
		#closest probe = closest for all probes.
		best_probe = None
		best_distance = 10000
		closest_probe = None
		closest_distance = 10000
		if len(probes) > 0:
			for probe in probes:
				adj_probe = self.turn3d(probe.position)
				distance = probe.distance_to(pos)
				#check among all.
				if distance < closest_distance:
					closest_probe = probe
					closest_distance = distance
				#check only same height.
				if adj_probe.z == adj_pos.z and distance < best_distance:
					best_probe = probe
					best_distance = distance
			#take the 2 probes selected so far and get their pathing distance to find the best.
			#if no best probe was found, just return the other one.
			if not best_probe:
				return closest_probe
			#if the are the same probe, then just return it.
			if best_probe == closest_probe:
				return best_probe

			#calculate query pathing distance and choose the real closest.
			bp_dist = await self._client.query_pathing(pos, best_probe.position)
			cp_dist = await self._client.query_pathing(pos, closest_probe.position)
			if bp_dist and cp_dist and bp_dist <= cp_dist:
				return best_probe
			else:
				return closest_probe
		return None


	def checkAttack(self):
		if self.units(NEXUS).not_ready.exists:
			for nexus in self.units(NEXUS).not_ready:
				if self.cached_enemies.exclude_type([PROBE,DRONE,SCV]).closer_than(30, nexus).amount > 0:
					self.under_attack = True
					return
		if self.buildingList.underAttack:
			self.under_attack = True
		else:
			self.under_attack = False

################
#Ob saving code#
################

	def saveObs(self):
		#load the previous training data.
		existing = []
		try:
			with open(_trainfile, "rb") as fp:
				existing = pickle.load(fp)
		except (OSError, IOError) as e:
			print (str(e))
		#append to the existing.
		print (str(len(existing)), 'Existing Build Records')
		mergedList = self._protossAgent.all_obs
		print (str(len(mergedList)), 'New Build Records Found')
		if existing:
			mergedList += existing
		# #only save uniques.
		# mergedTotal = len(mergedList)
		# uniqueList = list()
		# for sublist in mergedList:
		# 	if sublist not in uniqueList:
		# 		uniqueList.append(sublist)
		# uniqueTotal = len(uniqueList)
		# newRecords = uniqueTotal - len(existing)
		# print (str(newRecords), 'New Build Records Added')
		# print (str(uniqueTotal), 'Total Build Uniques')
		#save all the data.
		with open(_trainfile, 'wb') as f:
			pickle.dump(mergedList, f)


############
#micro code#
############

	def moveNearEnemies(self, unit_obj):
		#find the best target, similiar to attack, but in large range so we can move to targets if needed.
		targetEnemy = self.findBestMoveTarget(unit_obj)
		if targetEnemy:
			#check to see if the enemy is already in range.
			#If they are, just stop at the current position instead of running into more danger.
			#unless they are running away, then don't.
			if unit_obj.unit.target_in_range(targetEnemy) and self.targetFacing(unit_obj, targetEnemy):
				if unit_obj.checkNewAction('stop', targetEnemy.position[0], targetEnemy.position[1]):
					self.combinedActions.append(unit_obj.unit.stop())
				return True

			#not in range, move towards the target.
			if unit_obj.checkNewAction('move', targetEnemy.position[0], targetEnemy.position[1]):
				#check if it's an adept, if so run a chasing check.
				if unit_obj.unit.name == 'Adept':
					unit_obj.checkChasing(targetEnemy)

				if unit_obj.unit.name == 'Stalker' and unit_obj.offensiveBlink(targetEnemy):
					return True
				# elif not unit_obj.unit.is_flying and unit_obj.unit.ground_range < 2:
				# 	self.combinedActions.append(unit_obj.unit.attack(self.leadTarget(targetEnemy, unit_obj)))
				#elif unit_obj.unit.name == 'VoidRay' or unit_obj.unit.name == 'Phoenix':
				elif unit_obj.unit.is_flying:
					self.combinedActions.append(unit_obj.unit.attack(targetEnemy))
				elif unit_obj.unit.distance_to(targetEnemy) < targetEnemy.movement_speed:
					if unit_obj.unit.name == 'Zealot':
						self.combinedActions.append(unit_obj.unit.attack(targetEnemy.position))  #a move the zealot so it will attack things around it.
					else:
						self.combinedActions.append(unit_obj.unit.attack(targetEnemy))
				else:
					self.combinedActions.append(unit_obj.unit.move(self.leadTarget(targetEnemy, unit_obj)))
			if unit_obj.unit.is_selected or _debug_combat:
				unit_obj.last_target = Point3((targetEnemy.position3d.x, targetEnemy.position3d.y, (targetEnemy.position3d.z + 1)))
				self._client.debug_line_out(self.unitDebugPos(unit_obj.unit), self.p3AddZ(targetEnemy.position3d), color=Point3((219, 4, 4)))
			return True
		return False

	def searchEnemies(self, unit_obj):
		#search for enemies
		if unit_obj.unit.is_moving or unit_obj.unit.is_attacking:
			return True #moving somewhere already
		searchPos = self.getSearchPos(unit_obj.unit)
		if unit_obj.checkNewAction('move', searchPos[0], searchPos[1]):
			self.combinedActions.append(unit_obj.unit.move(searchPos))

		unit_obj.last_target = Point3((searchPos.position.x, searchPos.position.y, self.getHeight(searchPos.position)))
		return True

	def moveToEnemies(self, unit_obj):
		if not self.cached_enemies:
			return False  # no enemies to move to

		if not self.base_searched:
			startPos = random.choice(self.enemy_start_locations)
			if unit_obj.unit.distance_to(startPos) < 20:
				self.base_searched = True

		#if it's an observer, only go to units
		if unit_obj.unit.name == 'Observer':
			if self.cached_enemies.not_structure.exclude_type(_exclude_list).exists:
				closestEnemy = self.cached_enemies.not_structure.exclude_type(_exclude_list).closest_to(unit_obj.unit.position)
				unit_obj.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
					self.combinedActions.append(unit_obj.unit.attack(self.leadTarget(closestEnemy, unit_obj)))
				return True
			else:
				return False

		# can only attack ground units.
		if unit_obj.unit.can_attack_ground and not unit_obj.unit.can_attack_air:
			#find enemy units that aren't structures first.
			if self.cached_enemies.not_structure.not_flying.exclude_type(_exclude_list).exists:
				closestEnemy = self.cached_enemies.not_structure.not_flying.exclude_type(_exclude_list).closest_to(unit_obj.unit.position)
				leadTarget = self.leadTarget(closestEnemy, unit_obj)

				unit_obj.last_target = Point3((leadTarget.position.x, leadTarget.position.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', leadTarget.position.x, leadTarget.position.y):
					self.combinedActions.append(unit_obj.unit.attack(leadTarget.position))
				return True
			#move to buildings, go to pylon first if they exist.
			if self.cached_enemies.of_type([PYLON,BUNKER]).exists:
				closestEnemy = self.cached_enemies.of_type([PYLON,BUNKER]).closest_to(unit_obj.unit.position)
				unit_obj.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
					self.combinedActions.append(unit_obj.unit.attack(closestEnemy))
				return True
			#move anything not flying
			if self.cached_enemies.not_flying.exclude_type(_exclude_list).exists:
				closestEnemy = self.cached_enemies.not_flying.exclude_type(_exclude_list).closest_to(unit_obj.unit.position)
				leadTarget = self.leadTarget(closestEnemy, unit_obj)
				unit_obj.last_target = Point3((leadTarget.position.x, leadTarget.position.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', leadTarget.position.x, leadTarget.position.y):
					self.combinedActions.append(unit_obj.unit.attack(leadTarget))
				return True
		elif unit_obj.unit.can_attack_air and not unit_obj.unit.can_attack_ground:
			# can only attack air units.
			#find enemy units that aren't structures first.
			if self.cached_enemies.not_structure.flying.exclude_type(_exclude_list).exists:
				closestEnemy = self.cached_enemies.not_structure.flying.exclude_type(_exclude_list).closest_to(unit_obj.unit.position)
				unit_obj.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
					self.combinedActions.append(unit_obj.unit.attack(self.leadTarget(closestEnemy, unit_obj)))
				return True

			#attack anything
			if self.cached_enemies.flying.exclude_type(_exclude_list).exists:
				closestEnemy = self.cached_enemies.flying.exclude_type(_exclude_list).closest_to(unit_obj.unit.position)
				unit_obj.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
					self.combinedActions.append(unit_obj.unit.attack(self.leadTarget(closestEnemy, unit_obj)))
				return True

			#hang out near ground enemies to help.
			# if self.cached_enemies.exclude_type(_exclude_list).exists:
			# 	closestEnemy = self.cached_enemies.exclude_type(_exclude_list).closest_to(unit_obj.unit.position)
			# 	dist = unit_obj.unit.distance_to(closestEnemy) - (12 + closestEnemy.radius)
			# 	targetpoint = unit_obj.unit.position.towards(closestEnemy.position, distance=dist)
			# 	unit_obj.last_target = Point3((targetpoint.position.x, targetpoint.position.y, (closestEnemy.position3d.z + 1)))
			# 	if unit_obj.checkNewAction('move', targetpoint.position[0], targetpoint.position[1]):
			# 		self.combinedActions.append(unit_obj.unit.attack(targetpoint.position))
			# 	return True


		else:
			if self.cached_enemies.not_structure.exclude_type(_exclude_list).exists:
				closestEnemy = self.cached_enemies.not_structure.exclude_type(_exclude_list).closest_to(unit_obj.unit.position)
				unit_obj.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
					self.combinedActions.append(unit_obj.unit.attack(self.leadTarget(closestEnemy, unit_obj)))
				return True
			#now pylons
			if self.cached_enemies.of_type([PYLON,BUNKER]).exists:
				closestEnemy = self.cached_enemies.of_type([PYLON,BUNKER]).closest_to(unit_obj.unit.position)
				unit_obj.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
					self.combinedActions.append(unit_obj.unit.attack(closestEnemy))
				return True

			if self.cached_enemies.exclude_type(_exclude_list).exists:
				closestEnemy = self.cached_enemies.exclude_type(_exclude_list).closest_to(unit_obj.unit.position)
				unit_obj.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
					self.combinedActions.append(unit_obj.unit.attack(self.leadTarget(closestEnemy, unit_obj)))
				return True

		return False

	def rally(self, unit_obj):
		if self.rally_pos and unit_obj.unit.distance_to(self.rally_pos) > 8:
			if unit_obj.checkNewAction('move', self.rally_pos.x, self.rally_pos.y):
				unit_obj.game.combinedActions.append(unit_obj.unit.move(self.rally_pos))
				unit_obj.last_target = None
			return True
		return False

	def defend(self, unit_obj):
		#clear out destructables around the base.
		for nexus in self.units(NEXUS):
			items = self.state.destructables.closer_than(15, nexus)
			if items:
				item = items.closest_to(nexus)
				if item.name == 'CollapsibleTerranTowerDiagonal' or item.name == 'CollapsibleRockTowerDiagonal':
					continue
				unit_obj.game.combinedActions.append(unit_obj.unit.attack(item))
				unit_obj.last_target = None
				unit_obj.last_action = 'Destructables'
				return True

		if self.defensive_pos and unit_obj.unit.distance_to(self.defensive_pos) > 5:
			if unit_obj.checkNewAction('move', self.defensive_pos.x, self.defensive_pos.y):
				unit_obj.game.combinedActions.append(unit_obj.unit.move(self.defensive_pos))
				unit_obj.last_target = None
			return True
		return False

	def waitForce(self, unit_obj, bonus_range=0):
		#evaluates battle conditions before joining the battle.
		#only use early in game for probing, terrible in late game.
		if self.time > 180:
			return False
		#check to see if we are defending and if we are near our own bases, if so attack anyway.
		if self.defend_only and self.units(NEXUS).closer_than(25, unit_obj.unit):
			return False #defending, attack!

		#check to see if we are already in battle, if so just exist.
		#if anyone is in our range or attack, if we are in anyone elses range of attack.
		unit_range = unit_obj.unit.ground_range + bonus_range
		if unit_obj.unit.air_range > unit_obj.unit.ground_range:
			unit_range = unit_obj.unit.air_range + bonus_range
		#see if any enemies are in our range.
		enemyThreats = unit_obj.closestEnemies.not_structure.filter(lambda x: unit_obj.unit.target_in_range(x, bonus_distance=bonus_range))
		if enemyThreats:
			return False #already engaged.
		#stay out of enemy range.
		enemyThreats = unit_obj.closestEnemies.filter(lambda x: x.target_in_range(unit_obj.unit, bonus_distance=1 + bonus_range))
		if enemyThreats:
			return False #already engaged.

		#now evaluate to see if we need to keep moving, or just stand still.
		enemyThreats = unit_obj.closestEnemies.sorted(lambda x: x.distance_to(unit_obj.unit))

		[enemyDPStoGround, enemyDPStoAir, enemyAirHealth, enemyGroundHealth, enemyTotalDPS, closestEnemy, enemyGroundtoAirDPS, enemyAirtoGroundDPS, enemyGroundtoGroundDPS, enemyAirtoAirDPS] = self.getAllEnemyStats(unit_obj)
		#get all the friends near the closest enemy.
		if closestEnemy:
			[friendDPStoGround, friendDPStoAir, friendAirHealth, friendGroundHealth, friendTotalDPS] = self.unitList.friendlyEngagedFighters(closestEnemy)

			###if there is an enemy on the ground but no grounddps, then we can't damage the enemy and need to leave.
			if enemyGroundHealth > 0 and friendDPStoGround == 0 and enemyGroundtoAirDPS > 0:
				self.stayMaxRange(unit_obj, closestEnemy)
				return True
			if enemyAirHealth > 0 and friendDPStoAir == 0 and enemyAirtoGroundDPS > 0:
				self.stayMaxRange(unit_obj, closestEnemy)
				return True


			#calculate our die times.
			enemyAirDieTime = 0
			enemyGroundDieTime = 0
			enemyOverDieTime = 0
			friendAirDieTime = 0
			friendGroundDietime = 0
			friendOverDieTime = 0
			if friendDPStoAir > 0:
				enemyAirDieTime = enemyAirHealth / friendDPStoAir
			if friendDPStoGround > 0:
				enemyGroundDieTime = enemyGroundHealth / friendDPStoGround
			if friendTotalDPS > 0:
				enemyOverDieTime = (enemyAirHealth + enemyGroundHealth) / friendTotalDPS

			if enemyDPStoAir > 0:
				friendAirDieTime = friendAirHealth /enemyDPStoAir

			if enemyDPStoGround > 0:
				friendGroundDietime = friendGroundHealth / enemyDPStoGround

			if enemyTotalDPS > 0:
				friendOverDieTime = (friendAirHealth + friendGroundHealth) / enemyTotalDPS

			if (friendAirDieTime + friendGroundDietime) > 0 and (enemyAirDieTime + enemyGroundDieTime) == 0:
				#print ('Danger found')
				self.stayMaxRange(unit_obj, closestEnemy)
				return True

			#check if overall battle can be won.
			if friendOverDieTime < enemyOverDieTime:
				self.stayMaxRange(unit_obj, closestEnemy)
				return True

			if (friendAirDieTime + friendGroundDietime) < (enemyAirDieTime + enemyGroundDieTime):
				#print ('Danger found')
				self.stayMaxRange(unit_obj, closestEnemy)
				return True

		return False

	def effectSafe(self, unit_obj):
		#stay safe from objects and effects.
		foundEffect = self.dodgeEffects(unit_obj)
		if foundEffect:
			#find the closest movable position away from the effect.
			#create a grid around the unit.
			possibles = []
			if unit_obj.unit.is_flying:
				possibles = self.retreatGrid(foundEffect[0], size=ceil(foundEffect[1] + unit_obj.unit.radius))
			else:
				possibles = self.groundRetreatGrid(foundEffect[0], size=ceil(foundEffect[1] + unit_obj.unit.radius))
			if len(possibles) == 0:
				return False
			#calculate the distance of the remaining grid postions away from the effect
			closestPosition = None
			closestDistance = 100
			for position in possibles:
				effectAwayDist = foundEffect[0].distance_to(position)
				if effectAwayDist < foundEffect[1]:
					continue #remove positions that are less than the radius.
				#calculate the distance of the positions from ourselves.
				ourAwayDist = unit_obj.unit.distance_to(position)
				if ourAwayDist < closestDistance:
					closestDistance = ourAwayDist
					closestPosition = position
			#move the position that is closest to use of the remaining positions.
			if closestPosition:
				if unit_obj.checkNewAction('move', closestPosition[0], closestPosition[1]):
					self.combinedActions.append(unit_obj.unit.move(closestPosition))
				if unit_obj.unit.is_selected or _debug_combat:
					self._client.debug_line_out(self.unitDebugPos(unit_obj.unit), self.p3AddZ(self.turn3d(closestPosition.position)), color=Point3((219, 136, 4)))
					self._client.debug_line_out(self.unitDebugPos(unit_obj.unit), self.p2AddZ(closestPosition), color=Point3((0, 255, 55)))

				if unit_obj.unit.name == 'Probe':
					self.worker_moved = self.time + 3
				return True
		return False

	def keepSafe(self, unit_obj):
		#if it's a ground n
		(danger, closestEnemy) = self.inDangerSimple(unit_obj)
		if danger:
			#if we are a phoenix, drop our target if needed.
			if unit_obj.unit.name == 'Phoenix' and AbilityId.CANCEL_GRAVITONBEAM in unit_obj.abilities:
				unit_obj.beam_unit = None
				self.combinedActions.append(unit_obj.unit(AbilityId.CANCEL_GRAVITONBEAM))
				return True

			if self.goRetreat(unit_obj, closestEnemy):
				return True
		return False

	def KeepKiteRange(self, unit_obj, bonus_range=0):
		#kite if we can.
		targetEnemy = self.findKiteTarget(unit_obj, bonus_range)
		if targetEnemy:
			if not targetEnemy.name in ['Carrier', 'Battlecruiser', 'PlanetaryFortress', 'Bunker'] and not (targetEnemy.can_attack_air or targetEnemy.can_attack_ground) and unit_obj.closestEnemies.filter(lambda x: x.can_attack_air or x.can_attack_ground).exists:
				#print ('found better kite target')
				return False #better targets out there.
			#kitePoint = unit_obj.unit.position.towards(targetEnemy.position, distance=-0.1)
			kitePoint = self.findKiteBackTarget(unit_obj, targetEnemy)
			if kitePoint:
				if unit_obj.checkNewAction('move', kitePoint[0], kitePoint[1]):
					self.combinedActions.append(unit_obj.unit.move(kitePoint))
				if unit_obj.unit.is_selected or _debug_combat:
					unit_obj.last_target = kitePoint.position
					self._client.debug_line_out(self.unitDebugPos(unit_obj.unit), self.p3AddZ(targetEnemy.position3d), color=Point3((0, 206, 3)))
					self._client.debug_line_out(self.unitDebugPos(unit_obj.unit), self.p2AddZ(kitePoint), color=Point3((212, 66, 244)))
				return True
		return False

	def attack(self, unit_obj, bonus_range=0):
		if unit_obj.unit.weapon_cooldown == 0:
			targetEnemy = self.findBestTarget(unit_obj, bonus_range)
			if targetEnemy:

				#check if this is a melee unit, and do a move attack instead of target attack.
				if not unit_obj.unit.is_flying and unit_obj.unit.ground_range < 2:
					self.combinedActions.append(unit_obj.unit.attack(targetEnemy.position))
				else:
					self.combinedActions.append(unit_obj.unit.attack(targetEnemy))
				unit_obj.last_action = 'attack'

				if unit_obj.unit.is_selected or _debug_combat:
					unit_obj.last_target = Point3((targetEnemy.position3d.x, targetEnemy.position3d.y, (targetEnemy.position3d.z + 1)))
					self._client.debug_line_out(self.unitDebugPos(unit_obj.unit), self.p3AddZ(targetEnemy.position3d), color=Point3((219, 4, 4)))
				return True
		return False

	def doNothing(self, unit_obj):
		#if our weapon is on cooldown, but we have enemies in range, then we just do nothing.
		if unit_obj.unit.weapon_cooldown != 0:
			targetEnemy = unit_obj.closestEnemies.in_attack_range_of(unit_obj.unit)
			#targetEnemy = self.findBestTarget(unit_obj.unit)
			if targetEnemy:
				#enemies in range, do nothing.
				if unit_obj.checkNewAction('wait', 0, 0):
					self.combinedActions.append(unit_obj.unit.stop())

				unit_obj.last_target = Point3((targetEnemy.first.position3d.x, targetEnemy.first.position3d.y, (targetEnemy.first.position3d.z + 1)))
				return True
		return False

	def moveToFriendliesExp(self, unit_obj):
		return False
		#if we are moving and no enemies exist, then we must be search, so return false.
		if unit_obj.unit.is_moving and len(self.cached_enemies) == 0:
			return False

		closestFriendly = None
		closestEnemy = None
		fUnits = self.units().exclude_type([WARPPRISM,OBSERVER]).filter(lambda x: x.can_attack_ground or x.can_attack_air)
		if len(fUnits) == 0 or len(self.cached_enemies) == 0:
			#no friends or no enemies.
			return False

		groundEnemies = self.cached_enemies.not_flying
		groundFriendlies = fUnits.filter(lambda x: x.can_attack_ground)
		airEnemies = self.cached_enemies.flying
		airFriendlies = fUnits.filter(lambda x: x.can_attack_air)


		if unit_obj.unit.can_attack_ground and not unit_obj.unit.can_attack_air and len(groundEnemies) > 0 and len(groundFriendlies) > 0:
			#can only attack ground units, so find ground unit enemys.
			closestEnemy = groundEnemies.closest_to(unit_obj.unit)
			closestFriendly = groundFriendlies.closest_to(closestEnemy)
		elif unit_obj.unit.can_attack_air and not unit_obj.unit.can_attack_ground and len(airEnemies) > 0 and len(airFriendlies) > 0:
			# can only attack air units.
			closestEnemy = airEnemies.closest_to(unit_obj.unit)
			closestFriendly = airFriendlies.closest_to(closestEnemy)
		else:
			closestEnemy = self.cached_enemies.closest_to(unit_obj.unit)
			closestFriendly = fUnits.closest_to(closestEnemy)

		if closestEnemy and closestFriendly:
			#check to see if the friendly is closer to the enemy than we are.  If so, move to the friendly, else return false.
			if unit_obj.unit.distance_to(closestEnemy) > closestFriendly.distance_to(closestEnemy):
				if unit_obj.checkNewAction('move', closestFriendly.position.x, closestFriendly.position.y):
					self.combinedActions.append(unit_obj.unit.move(closestFriendly))
				if unit_obj.unit.is_selected or _debug_combat:
					unit_obj.last_target = Point3((closestFriendly.position3d.x, closestFriendly.position3d.y, (closestFriendly.position3d.z + 1)))
				return True
		return False

	def moveToFriendlies(self, unit_obj):
		#if we are moving and no enemies exist, then we must be search, so return false.
		if unit_obj.unit.is_moving and len(self.cached_enemies) == 0:
			return False

		closestFriendly = None
		fUnits = self.units().not_structure.exclude_type([WARPPRISM,OBSERVER,PROBE]).filter(lambda x: x.can_attack_ground or x.can_attack_air)
		if unit_obj.unit.can_attack_ground and not unit_obj.unit.can_attack_air:
			#can only attack ground, so go to enemies that are near ground units.
			if self.cached_enemies.not_flying.exists and fUnits:
				closestFriendly = fUnits.closest_to(self.cached_enemies.not_flying.closest_to(unit_obj.unit))
			elif fUnits:
				closestFriendly = fUnits.closest_to(unit_obj.unit)

		elif unit_obj.unit.can_attack_air and not unit_obj.unit.can_attack_ground:
			# can only attack air units.
			if self.cached_enemies.flying.exists and fUnits:
				closestFriendly = fUnits.closest_to(self.cached_enemies.flying.closest_to(unit_obj.unit))
			elif fUnits:
				closestFriendly = fUnits.closest_to(unit_obj.unit)
		else:
			#can attack anything.
			if self.cached_enemies.exists and fUnits:
				closestFriendly = fUnits.closest_to(self.cached_enemies.closest_to(unit_obj.unit))
			elif fUnits:
				closestFriendly = fUnits.closest_to(unit_obj.unit)

		if closestFriendly:
			#if we are not close to it, then our priority is to get there.
			if unit_obj.unit.distance_to(closestFriendly) > 10:
				if unit_obj.checkNewAction('move', closestFriendly.position.x, closestFriendly.position.y):
					self.combinedActions.append(unit_obj.unit.move(closestFriendly))
				if unit_obj.unit.is_selected or _debug_combat:
					unit_obj.last_target = Point3((closestFriendly.position3d.x, closestFriendly.position3d.y, (closestFriendly.position3d.z + 1)))
				return True
		return False

	def getUnitEnemies(self, unit_obj, radius=25):
		units = None
		if unit_obj.sendHome:
			units = self.cached_enemies
		else:
			units = self.cached_enemies.exclude_type(_exclude_list).closer_than(radius, unit_obj.unit)
			if len(units) > 0:
				self.unit_engaged = True
				self.moveRally = False
		return units

	def	canEscape(self, unit_obj):
		enemyThreatsClose = unit_obj.closestEnemies.filter(lambda x: x.target_in_range(unit_obj.unit)).sorted(lambda x: x.movement_speed, reverse=True)
		if enemyThreatsClose.exists:
			if unit_obj.unit.movement_speed < enemyThreatsClose.first.movement_speed:
				return False
		return True


#####################
#micro utlities code#
#####################

	def checkHome(self, unit_obj):
		#check to see if there is a friendly base near the units.
		if not self.defend_only or not self.under_attack:
			return False
		if len(self.units(NEXUS)) > 0 and len(self.cached_enemies) > 0:
			if self.units(NEXUS).closer_than(30, unit_obj.unit):
				return False
			else:
				#check to make sure we can even attack whatever it is that is attacking.
				allNexus = None
				if unit_obj.unit.can_attack_air and unit_obj.unit.can_attack_ground:
					allNexus = self.units(NEXUS).filter(lambda x: len(self.cached_enemies.closer_than(30, x)) > 0)
				elif unit_obj.unit.can_attack_air and not unit_obj.unit.can_attack_ground:
					allNexus = self.units(NEXUS).filter(lambda x: len(self.cached_enemies.flying.closer_than(30, x)) > 0)
				elif not unit_obj.unit.can_attack_air and unit_obj.unit.can_attack_ground:
					allNexus = self.units(NEXUS).filter(lambda x: len(self.cached_enemies.not_flying.closer_than(30, x)) > 0)


				#find the closest friendly that is under attack.
				#closestNexus = self.game_info.player_start_location
				if allNexus:
					closestNexus = allNexus.sorted(lambda x: x.distance_to(unit_obj.unit)).first
					unit_obj.homeTarget = closestNexus
					return True
		return False


	def checkSurrounded(self, unit_obj) -> bool:
		#check for enemies near the unit.
		if len(unit_obj.closestEnemies) > 0:
			enemyThreats = unit_obj.closestEnemies.closer_than((unit_obj.unit.radius + 1), unit_obj.unit)
			if len(enemyThreats) > 5:
				return True
		return False

	def goRetreat(self, unit_obj, closestEnemy):
		if unit_obj.unit.name == 'Probe':
			self.worker_moved = self.time + 3

		unit_obj.retreating = True
		#first just do a simple move if possible.
		retreatPoint = self.findSimpleRetreatPoint(unit_obj.unit, closestEnemy)
		if retreatPoint:
			#self.last_target = retreatPoint.position
			if unit_obj.checkNewAction('move', retreatPoint[0], retreatPoint[1]):
				self.combinedActions.append(unit_obj.unit.move(retreatPoint))
			if unit_obj.unit.is_selected or _debug_combat:
				self._client.debug_line_out(self.unitDebugPos(unit_obj.unit), self.p3AddZ(self.turn3d(closestEnemy.position)), color=Point3((219, 136, 4)))
				self._client.debug_line_out(self.unitDebugPos(unit_obj.unit), self.p2AddZ(retreatPoint), color=Point3((0, 255, 55)))
			return True

		#if nothing has been found, look around for an area
		retreatPoint = None
		if not unit_obj.unit.is_flying:
			retreatPoint = self.findGroundRetreatTarget(unit_obj.unit, inc_size=1, enemy_radius=10)
		else:
			retreatPoint = self.findAirRetreatTarget(unit_obj.unit, inc_size=1, enemy_radius=10)

		if retreatPoint:
			#self.last_target = retreatPoint.position
			if unit_obj.checkNewAction('move', retreatPoint[0], retreatPoint[1]):
				self.combinedActions.append(unit_obj.unit.move(retreatPoint))
			if unit_obj.unit.is_selected or _debug_combat:
				self._client.debug_line_out(self.unitDebugPos(unit_obj.unit), self.p3AddZ(self.turn3d(closestEnemy.position)), color=Point3((216, 0, 101)))
				self._client.debug_line_out(self.unitDebugPos(unit_obj.unit), self.p2AddZ(retreatPoint), color=Point3((10, 2, 234)))
			return True
		return False

	def stayMaxRange(self, unit_obj, enemy):
		#stay minimum of 9 range from closest.
		#get the distance of the enemy - our attack range and move that far back.
		#dist = unit_obj.unit.distance_to(enemy) - (unit_obj.unit.radius + enemy.radius + use_range)
		#move away from the target that much.
		if unit_obj.unit.position != enemy.position:
			#check to see if we should move away.
			if unit_obj.unit.distance_to(enemy.position) < 9:
				targetpoint = unit_obj.unit.position.towards(enemy.position, distance=-2)
				unit_obj.last_target = Point3((targetpoint.position.x, targetpoint.position.y, (unit_obj.unit.position3d.z + 1)))
				if unit_obj.checkNewAction('move', targetpoint.position[0], targetpoint.position[1]):
					self.combinedActions.append(unit_obj.unit.move(targetpoint))
				return
			else:
				if unit_obj.checkNewAction('move', unit_obj.unit.position[0], unit_obj.unit.position[1]):
					self.combinedActions.append(unit_obj.unit.stop())#(unit_obj.unit.position))
				return

	def targetFacing(self, unit_obj, enemy) -> bool:
		#return True on units that don't face a certain direction.
		if enemy.name in ['MissileTurret','SporeCrawler','SpineCrawler', 'PhotonCannon', 'Bunker']:
			return True

		#find out if the unit is facing
		faceTarget = self.towardsDirection(enemy.position, enemy.facing, 1)
		if unit_obj.unit.distance_to(faceTarget) > unit_obj.unit.distance_to(enemy):
			return False
		return True

	def leadTarget(self, enemy, unit_obj):
		#get the point that is enemy speed in distance ahead of enemy, if the enemy is moving.
		#print ('moving', str(enemy.is_moving), enemy.position, enemy.facing, enemy.movement_speed)
		#self._client.debug_text_3d(str(enemy.facing), enemy.position3d)
		if self.unit_moves.get(enemy.tag):
			leadTarget = self.towardsDirection(enemy.position, enemy.facing, enemy.movement_speed)
			#check to see if the leadtarget is closer than the target, if so the target is moving towards us, so just run to the unit.
			if unit_obj.unit.distance_to(leadTarget) < unit_obj.unit.distance_to(enemy.position):
				return enemy.position
			if _debug_combat:
				self._client.debug_sphere_out(Point3((leadTarget.position.x, leadTarget.position.y, enemy.position3d.z + 1)), 1, Point3((66, 69, 244)))
			return leadTarget

			#enemy.movement_speed
		else:
			#not moving, just return the current position
			return enemy.position

	def towardsDirection(self, p, direction, distance):
		#finds the point in front of unit that is distance ahead of it.
		return p.position + Point2((cos(direction), sin(direction))) * distance

	def calculateEnemyScore(self, unit_obj, enemy):
		dpsperhp = 0
		unit_range = 0
		if (enemy.health + enemy.shield) > 0:
			if unit_obj.unit.name == 'Colossus':
				usedps = enemy.ground_dps
				if enemy.air_dps > enemy.ground_dps:
					usedps = enemy.air_dps
				dpsperhp = usedps / (enemy.health + enemy.shield)
				unit_range = unit_obj.unit.ground_range
			elif unit_obj.unit.is_flying:
				dpsperhp = enemy.air_dps / (enemy.health + enemy.shield)
				unit_range = unit_obj.unit.air_range
			else:
				dpsperhp = enemy.ground_dps / (enemy.health + enemy.shield)
				unit_range = unit_obj.unit.ground_range
			#if no dps is found, see if it's just to us.   If it's dangerous to others, take it's dps, but divide by it by 2 for lower scores.
			if dpsperhp == 0:
				if enemy.ground_dps > 0:
					dpsperhp = (enemy.ground_dps / (enemy.health + enemy.shield)) / 2
				if enemy.air_dps > 0:
					dpsperhp = (enemy.air_dps / (enemy.health + enemy.shield)) / 2

		#enemies that have range on us are the only real dps, so double their threat.
		if enemy.target_in_range(unit_obj.unit):
		 	dpsperhp = dpsperhp * 200
		else:
			dpsperhp = dpsperhp * 100
		score = dpsperhp
		#get the a score bonus from the unit object.
		score += unit_obj.getTargetBonus(enemy.name)

		#adjust for SCV's when defending.
		if enemy.name == 'SCV' and not self.checkSCVHealer(enemy):
			score -= unit_obj.getTargetBonus(enemy.name)


		# if enemy.name == 'SCV' and self.defend_only:
		# 	score -= 100
		#don't target interceptors.
		if enemy.name == 'Interceptor':
			score = 0
		#start enemy structures that don't attack out with -1000 pts so they are always below units.
		if score == 0 and enemy.is_structure:
			#building, so lets just subtract the distance.
			hp_lost = (enemy.health_max + enemy.shield_max) - (enemy.health + enemy.shield)
			if enemy.name == 'Pylon':
				#going less than -400 can result in positive points, might mess things up, but might be good to finish off a pylon - test later.
				score = self.scorePylon(enemy, unit_obj)
				if score == 0:
					score = (hp_lost - (enemy.health_max + enemy.shield_max))
			elif enemy.name == 'Bunker':
				score = 0
			else:
				score = (hp_lost - (enemy.health_max + enemy.shield_max))

		#distance to enemy matters.  Use % of max range distance, then subtract it from 100.
		dist = 0
		if unit_obj.sendHome:
			dist = enemy.distance_to(unit_obj.homeTarget) - unit_obj.unit.radius - enemy.radius - unit_range
		else:
			dist = enemy.distance_to(unit_obj.unit) - unit_obj.unit.radius - enemy.radius - unit_range

		if dist > 0:
			if score < 0:
				score = score * dist
			else:
				score = score / dist
		
		if self.checkStolenUnit(enemy):
			score = -100000 #stolen unit, do not attack.

		#debug if the unit is selected.
		if _debug and _debug_score and unit_obj.unit.is_selected:
			label = "{_name} {_score} {_dpsperhp} {_perc}".format(_name=enemy.name, _score=str(int(score)), _dpsperhp=str(int(dpsperhp)), _perc=str(int(dist)))
			self._client.debug_text_3d(label, enemy.position3d)
			time.sleep(0.1)
		return score


	def checkStolenUnit(self, enemy) -> bool:
		if self.enemy_race != Race.Zerg:
			return False
		possibles = {MOTHERSHIP, COLOSSUS, ZEALOT, STALKER, HIGHTEMPLAR, DARKTEMPLAR, SENTRY, PHOENIX, CARRIER, VOIDRAY, WARPPRISM, OBSERVER, IMMORTAL, ADEPT, ORACLE, TEMPEST, DISRUPTOR, ARCHON, PHOTONCANNON}
		if enemy.type_id in possibles:
			return True
		return False

	def checkSCVHealer(self, scv) -> bool:
		#find the postion 1d ahead of scv.
		healTarget = self.towardsDirection(scv.position, scv.facing, scv.radius)
		#check if any unit has a radius in range of it.
		healed = self.cached_enemies.filter(lambda x:
			x.name in ['Battlecruiser', 'MissileTurret', 'PlanetaryFortress', 'CommandCenter', 'Bunker', 'SiegeTank', 'SiegeTankSieged', 'Thor', 'Medivac', 'LiberatorAG', 'Liberator']
			and x.distance_to(healTarget) <= x.radius)
		#if so, return true.
		if len(healed) > 0:
			return True
		return False



	def scorePylon(self, pylon, unit_obj):
		#loop the buildings around and see if they are powered by more than 1 pylon.
		score = 0
		important_buildings = {GATEWAY,WARPGATE,STARGATE,ROBOTICSFACILITY,PHOTONCANNON}
		cached_buildings = self.cached_enemies.filter(lambda building: building.type_id in important_buildings and building.distance_to(pylon) < 6.5)
		for building in cached_buildings:
			allPylons = self.cached_enemies.filter(lambda other_pylon: other_pylon.type_id == PYLON and other_pylon.distance_to(building) < 6.5)
			if len(allPylons) == 1:
				#single pylon building, add to the pylon score.
				if building.name == 'ShieldBattery':
					print ('shield found')
					score += 100
				elif building.name == 'PhotonCannon':
					score += 25
				else:
					score += 15
		return score

	def findBestMoveTarget(self, unit_obj):
		enemyThreats = unit_obj.closestEnemies
		#if we can't attack air units, only target no flying.  Or only fly if we can't attack ground.
		if unit_obj.unit.name == 'Disruptor':
			enemyThreats = unit_obj.closestEnemies.not_flying
		elif unit_obj.unit.can_attack_ground and not unit_obj.unit.can_attack_air:
			enemyThreats = unit_obj.closestEnemies.not_flying
		elif unit_obj.unit.can_attack_air and not unit_obj.unit.can_attack_ground:
			enemyThreats = unit_obj.closestEnemies.flying
		#add colossus if unit is a phoenix.
		if unit_obj.unit.name == 'Phoenix':
		 	enemyThreats += unit_obj.closestEnemies.of_type([COLOSSUS])
		#score the threats and pick the best one.
		if enemyThreats.exists:
			topscore = -10000
			topEnemy = None
			for enemy in enemyThreats:
				score = self.calculateEnemyScore(unit_obj, enemy)
				if score > topscore:
					topscore = score
					topEnemy = enemy
				#units with energy in reserves deserve more score.
			return topEnemy

	def findEnergyTarget(self, unit_obj, ability_range):
		enemyThreats = unit_obj.closestEnemies.filter(lambda x: x.energy > 0).closer_than(ability_range, unit_obj.unit).sorted(lambda x: x.distance_to(unit_obj.unit))
		if enemyThreats.exists:
			return enemyThreats[0]

	def findDrawFireTarget(self, unit_obj, draw_range):
		#find atleast 3 targets in radius that can attack us.
		useableEnemies = None
		if unit_obj.unit.is_flying:
			#only look for units that attack the air.
			useableEnemies = unit_obj.closestEnemies.filter(lambda x: x.can_attack_air and x.distance_to(unit_obj.unit) <= draw_range)
		else:
			useableEnemies = unit_obj.closestEnemies.filter(lambda x: x.can_attack_ground and x.distance_to(unit_obj.unit) <= draw_range)
		if useableEnemies:
			enemycenter =  self.center3d(useableEnemies)
			return enemycenter

	def findAOETarget(self, unit_obj, ability_range, ability_radius, minEnemies=3):
		#find atleast 3 targets in radius.
		if unit_obj.closestEnemies.closer_than(ability_range, unit_obj.unit):
			enemycenter =  self.center3d(unit_obj.closestEnemies.closer_than(ability_range, unit_obj.unit))
			#check if there are 3 targets in the radius.
			enemies = unit_obj.closestEnemies.closer_than(ability_radius, enemycenter).amount
			if enemies >= minEnemies:
				return enemycenter

	def findBestTarget(self, unit_obj, bonus_range=0):
		#first thing is to get all the targets in our units range.
		enemyThreats = unit_obj.closestEnemies.in_attack_range_of(unit_obj.unit, bonus_distance=bonus_range)
		if unit_obj.unit.name == 'Phoenix':
		 	enemyThreats += unit_obj.closestEnemies.of_type([COLOSSUS]).closer_than((7 + bonus_range), unit_obj.unit)
		if enemyThreats.exists:
			topscore = -10000
			topEnemy = None
			for enemy in enemyThreats:
				score = self.calculateEnemyScore(unit_obj, enemy)
				if score > topscore:
					topscore = score
					topEnemy = enemy

			return topEnemy

	def findKiteBackTarget(self, unit_obj, enemy):
		#get the attack range of the enemy.
		enemy_attack_range = 0
		if unit_obj.unit.is_flying:
			enemy_attack_range = enemy.air_range
		elif enemy.can_attack_air and unit_obj.unit.name == 'Colossus':
			enemy_attack_range = enemy.air_range
		else:
			enemy_attack_range = enemy.ground_range
		if enemy.name == 'Carrier':
			enemy_attack_range = 8
		if enemy.name == 'Battlecruiser':
			enemy_attack_range = 10
		if enemy.name == 'WidowMine':
			enemy_attack_range = 5
		if enemy.name == 'Bunker':
			enemy_attack_range = 6
		#get our attack range.

		unit_attack_range = 0
		if unit_obj.unit.can_attack_ground and not enemy.is_flying:
			unit_attack_range = unit_obj.unit.ground_range
		elif unit_obj.unit.can_attack_air and enemy.is_flying:
			unit_attack_range = unit_obj.unit.air_range
		else:
			unit_attack_range = 0

		if unit_attack_range == 0:
			#we can't attack the unit, stay away by it's distance.
			away_range = unit_obj.unit.radius + enemy.radius + enemy.ground_range
			if unit_obj.unit.is_flying:
				away_range = unit_obj.unit.radius + enemy.radius + enemy.air_range

			#dist = center distance
			dist = unit_obj.unit.distance_to(enemy) - away_range

			#move away from the target that much.
			if unit_obj.unit.position != enemy.position:
				targetpoint = unit_obj.unit.position.towards(enemy.position, distance=dist)
				return targetpoint
		else:
			use_range = unit_attack_range + unit_obj.unit.radius
			#check it has 0 range, then it's probably a building, so let's shorten things by 1 for better viewing and to enable more units behind us.
			if enemy_attack_range == 0 and enemy.is_structure:
				use_range = 2

			if use_range >= unit_attack_range:
				#print ('cheat kiting', unit_obj.unit.name, enemy.name)
				use_range = unit_attack_range - 0.1

			#things with no range themselves like carriers and disruptors.
			if enemy_attack_range > unit_attack_range and unit_attack_range == 0:
				use_range = enemy_attack_range + 1
				if use_range < 8:
					use_range = 8

			#something is wrong that this is needed
			# if unit_obj.unit.name == 'VoidRay':
			# 	use_range += 1

			#get the distance of the enemy - our attack range and move that far back.
			#dist = center distance
			dist = unit_obj.unit.distance_to(enemy) - (unit_obj.unit.radius + enemy.radius + use_range)

			#move away from the target that much.
			if unit_obj.unit.position != enemy.position:
				targetpoint = unit_obj.unit.position.towards(enemy.position, distance=dist)
				return targetpoint

	def findKiteBackTargetWorkingOld(self, unit_obj, enemy):
		#this version keeps us at their range plus some.

		enemy_attack_range = 0
		if unit_obj.unit.is_flying:
			enemy_attack_range = enemy.air_range
		else:
			enemy_attack_range = enemy.ground_range
		if enemy.name == 'Carrier':
			enemy_attack_range = 8
		if enemy.name == 'Battlecruiser':
			enemy_attack_range = 10
		if enemy.name == 'WidowMine':
			enemy_attack_range = 5

		unit_attack_range = 0
		if unit_obj.unit.can_attack_ground and not enemy.is_flying:
			unit_attack_range = unit_obj.unit.ground_range
		elif unit_obj.unit.can_attack_air and enemy.is_flying:
			unit_attack_range = unit_obj.unit.air_range
		elif unit_obj.unit.can_attack_air and not enemy.is_flying and unit_obj.unit.name == 'Colossus':
			unit_attack_range = unit_obj.unit.ground_range
		elif unit_obj.unit.can_attack_air:
			unit_attack_range = unit_obj.unit.air_range
		else:
			unit_attack_range = unit_obj.unit.ground_range



		use_range = unit_attack_range + unit_obj.unit.radius


		#if the enemy is slower than us, just stay at their max range plus extra:
		# if unit_obj.unit.movement_speed > enemy.movement_speed and enemy_attack_range < unit_attack_range:
		# 	#we are faster than the enemy and have better range, stay at their range with extra.
		# 	print ('close kiting', unit_obj.unit.name, unit_attack_range, enemy.name, enemy_attack_range)
		# 	use_range = enemy_attack_range + 1

		#if we can't attack it, stay it's range + 1

		#check it has 0 range, then it's probably a building, so let's shorten things by 1 for better viewing and to enable more units behind us.
		if enemy_attack_range == 0 and enemy.is_structure:
			use_range = 2

		if use_range >= unit_attack_range:
			#print ('cheat kiting', unit_obj.unit.name, enemy.name)
			use_range = unit_attack_range - 0.1

		#things with no range themselves like carriers and disruptors.
		if enemy_attack_range > unit_attack_range and unit_attack_range == 0:
			use_range = enemy_attack_range + 1
			if use_range < 8:
				use_range = 8

		if unit_obj.unit.name == 'VoidRay':
			use_range += 1

		#get the distance of the enemy - our attack range and move that far back.
		#dist = center distance
		dist = unit_obj.unit.distance_to(enemy) - (unit_obj.unit.radius + enemy.radius + use_range)

		#move away from the target that much.
		if unit_obj.unit.position != enemy.position:
			targetpoint = unit_obj.unit.position.towards(enemy.position, distance=dist)
			return targetpoint

	def findBestKiteTarget(self, targetpoint, enemy):
		#build a grid around the targetpoint and select the highest value point.
		fullRetreatPoints = self.retreatGrid(targetpoint, size=4)
		retreatPoints = {x for x in fullRetreatPoints if self.abovePathingScore(x)}
		#if we have a good retreatPoint then just select the point that is closest to us.
		if retreatPoints:
			retreatPoint = targetpoint.position.closest(retreatPoints)
			#retreatPoint = enemy.position.furthest(retreatPoints)
			return retreatPoint
		#didn't find a retreatPoint in the good range, just get the highest valued one and move to it.
		retreatPoint = self.findBestPoint(fullRetreatPoints, enemy)
		if retreatPoint:
			return retreatPoint

	def findBestPoint(self, points, enemy):
		goodPoints = []
		bestPoint = 0
		for point in points:
			score = self.regPathingScore(point)
			if score > bestPoint:
				bestPoint = score
				del goodPoints[:]
				#add this one to goodPoints
				goodPoints.append(point)
			elif score == bestPoint:
				goodPoints.append(point)
		#now that we have all the points with equal value, move to the one that is furthest away from the enemy.
		if goodPoints:
			retreatPoint = enemy.position.furthest(goodPoints)
			return retreatPoint

	def findBestKiteTargetFurthestEnemy(self, targetpoint, enemy):
		#build a grid around the targetpoint and select the highest value point.
		fullRetreatPoints = self.retreatGrid(targetpoint, size=1)
		retreatPoints = {x for x in fullRetreatPoints if self.abovePathingScore(x)}
		#if we have a good retreatPoint then just select the point that is furthest from the enemy
		if retreatPoints:
			retreatPoint = enemy.position.furthest(retreatPoints)
			return retreatPoint
		#didn't find a retreatPoint in the good range, just get the highest valued one and move to it.
		retreatPoint = self.findBestPoint(fullRetreatPoints, enemy)
		if retreatPoint:
			return retreatPoint

	def findBestPointFurthestEnemy(self, points, enemy):
		goodPoints = []
		bestPoint = 0
		for point in points:
			score = self.regPathingScore(point)
			if score > bestPoint:
				bestPoint = score
				del goodPoints[:]
				#add this one to goodPoints
				goodPoints.append(point)
			elif score == bestPoint:
				goodPoints.append(point)
		#now that we have all the points with equal value, move to the one that is furthest away from the enemy.
		if goodPoints:
			retreatPoint = enemy.position.furthest(goodPoints)
			return retreatPoint

	def findKiteTarget(self, unit_obj, bonus_range=0):
		#find the closest unit to us and move away from it.
		unit_range = unit_obj.unit.ground_range + bonus_range
		if unit_obj.unit.air_range > unit_obj.unit.ground_range:
			unit_range = unit_obj.unit.air_range + bonus_range

		enemy_bonus_range = 0
		kitables = unit_obj.closestEnemies.filter(lambda x: x.name in ['Bunker', 'Battlecruiser', 'Carrier', 'MissileTurret', 'WidowMine', 'Mothership', 'PhotonCannon', 'SpineCrawler', 'SporeCrawler'] \
			or ((x.can_attack_ground or x.can_attack_air) and ( \
				(x.ground_range + x.radius + unit_obj.unit.radius) < (x.radius + unit_obj.unit.radius + unit_range) \
				and (x.air_range + x.radius + unit_obj.unit.radius) < (x.radius + unit_obj.unit.radius + unit_range)) \
				and self.targetFacing(unit_obj, x)))

		# enemy_total = (x.ground_range + x.radius + unit_obj.unit.radius)
		# unit_total = x.radius + unit_obj.unit.radius
		# 	(x.ground_range + x.radius +  < unit_range and x.air_range < unit_range)
		if unit_obj.unit.name in {'Colossus','Mothership'}:
			#run from ravens.
			enemyThreats = kitables.filter(lambda x: x.name == 'Raven'
										   and x.distance_to(unit_obj.unit) < (unit_obj.unit.radius + x.radius + 9)
										   ).sorted(lambda x: x.distance_to(unit_obj.unit))
			if enemyThreats:
				return enemyThreats[0]

		#stay out of enemy range.
		if unit_obj.unit.can_attack_air:
			enemyThreats = kitables.filter(lambda x: (x.target_in_range(unit_obj.unit, bonus_distance=1) or x.name in ['Battlecruiser', 'Carrier']) and (x.ground_range <= unit_range or x.air_range <= unit_range)).sorted(lambda x: x.distance_to(unit_obj.unit))
			if enemyThreats:
				return enemyThreats[0]
		else:
			enemyThreats = kitables.filter(lambda x: (not x.is_flying and x.target_in_range(unit_obj.unit, bonus_distance=1) and x.ground_range <= unit_range) or x.name in ['PlanetaryFortress', 'Bunker']).sorted(lambda x: x.distance_to(unit_obj.unit))
			if enemyThreats:
				return enemyThreats[0]
		#if nothing has us in range, find out what we have in our range.
		enemyThreats = kitables.filter(lambda x: unit_obj.unit.target_in_range(x, bonus_distance=bonus_range)).sorted(lambda x: x.distance_to(unit_obj.unit))
		if enemyThreats:
			return enemyThreats[0]


	def findKiteTarget_KitesAll(self, unit_obj, bonus_range=0):
		#find the closest unit to us and move away from it.
		unit_range = unit_obj.unit.ground_range + bonus_range
		if unit_obj.unit.air_range > unit_obj.unit.ground_range:
			unit_range = unit_obj.unit.air_range + bonus_range

		enemy_bonus_range = 0
		kitables = unit_obj.closestEnemies.filter(lambda x: x.name in ['Battlecruiser', 'Carrier', 'MissileTurret', 'WidowMine', 'Mothership', 'PhotonCannon', 'SpineCrawler', 'SporeCrawler', 'PlanetaryFortress'] or ((x.can_attack_ground or x.can_attack_air) and self.targetFacing(unit_obj, x)))

		if unit_obj.unit.name == 'Colossus':
			#any enemy that can attack ground or air.
			enemyThreats = kitables.closer_than(9 + bonus_range, unit_obj.unit).sorted(lambda x: x.distance_to(unit_obj.unit))
			if enemyThreats:
				return enemyThreats[0]

		#stay out of enemy range.
		if unit_obj.unit.can_attack_air:
			enemyThreats = kitables.filter(lambda x: (x.target_in_range(unit_obj.unit, bonus_distance=1) or x.name in ['Battlecruiser', 'Carrier', 'PlanetaryFortress']) and (x.ground_range <= unit_range or x.air_range <= unit_range)).sorted(lambda x: x.distance_to(unit_obj.unit))
			if enemyThreats:
				return enemyThreats[0]
		else:
			enemyThreats = kitables.filter(lambda x: (not x.is_flying and x.target_in_range(unit_obj.unit, bonus_distance=1) and x.ground_range <= unit_range) or x.name in ['PlanetaryFortress']).sorted(lambda x: x.distance_to(unit_obj.unit))
			if enemyThreats:
				return enemyThreats[0]
		#if nothing has us in range, find out what we have in our range.
		enemyThreats = kitables.filter(lambda x: unit_obj.unit.target_in_range(x, bonus_distance=bonus_range)).sorted(lambda x: x.distance_to(unit_obj.unit))
		if enemyThreats:
			return enemyThreats[0]

	def findKiteTargetOld(self, unit_obj, bonus_range=0):
		#find the closest unit to us and move away from it.
		unit_range = unit_obj.unit.ground_range + bonus_range
		if unit_obj.unit.air_range > unit_obj.unit.ground_range:
			unit_range = unit_obj.unit.air_range + bonus_range

		if unit_obj.unit.name == 'Colossus':
			#any enemy that can attack ground or air.
			enemyThreats = unit_obj.closestEnemies.closer_than(9 + bonus_range, unit_obj.unit).filter(lambda x: x.can_attack_ground or x.can_attack_air).sorted(lambda x: x.distance_to(unit_obj.unit))
			if enemyThreats:
				return enemyThreats[0]

		#stay out of enemy range.
		enemyThreats = unit_obj.closestEnemies.filter(lambda x: x.target_in_range(unit_obj.unit, bonus_distance=1 + bonus_range)).sorted(lambda x: x.distance_to(unit_obj.unit))
		if enemyThreats:
			return enemyThreats[0]
		#if nothing has us in range, find out what we have in our range.
		enemyThreats = unit_obj.closestEnemies.not_structure.filter(lambda x: unit_obj.unit.target_in_range(x, bonus_distance=bonus_range)).sorted(lambda x: x.distance_to(unit_obj.unit))
		if enemyThreats:
			return enemyThreats[0]

	def findSimpleRetreatPointMapVals(self, unit, enemy):
		#this function is a retreat point value that uses the map vals instead of 0 and 1 pathing grid.

		if unit.position == enemy.position:
			return None
		if unit.is_flying:
			targetpoint = unit.position.towards(enemy.position, distance=-2)
			return targetpoint
		else:
			targetpoint = unit.position.towards(enemy.position, distance=-1)
#			if not self.inPathingGrid(targetpoint):
#				return None
			#check to make sure the dist value of the position is atleast 2.
			if self.abovePathingScore(targetpoint):
				return targetpoint
		return None

	def getSearchPos(self, unit):
		#grab a random enemy start location.
		#if distance of that start location is less than 10,then search nearby areas.
		startPos = random.choice(self.enemy_start_locations)
		if unit.distance_to(startPos) > 10 and not self.base_searched:
			return startPos
		else:
			self.base_searched = True
			#search random among the nearest 10 expansion slots to unit.
			locations = []
			for possible in self.expansion_locations:
				if not self.units().of_type([NEXUS,PROBE]).closer_than(6, possible).exists:
					distance = sqrt((possible[0] - unit.position[0])**2 + (possible[1] - unit.position[1])**2)
					locations.append([distance, possible])
			locations = sorted(locations, key=itemgetter(0))
			#add duplicate locations to add weight towards enemy base.
			start_weight = len(locations)
			for loc in locations:
				thisweight = 0
				while thisweight < start_weight:
					locations.append([loc[0], loc[1]])
					thisweight += 1
				start_weight -= 1

			#del locations[10:]
			return random.choice(locations)[1]

	def dodgeEffects(self, unit_obj):
		#check to see which dodge effects to use, air or ground.
		use_positions = None
		if unit_obj.unit.name == 'Observer':
			use_positions = self.obs_dodge_positions

		elif unit_obj.unit.is_flying:
			use_positions = self.air_dodge_positions
		else:
			use_positions = self.dodge_positions

		if len(use_positions) == 0:
			return False
		closestDodge = None
		closestDistance = 1000
		closestRadius = 0
		for [position, radius] in use_positions:
			#get the distance to the position.
			if unit_obj.unit.name in ['Zealot'] and radius > 2:
				continue
			dist = unit_obj.unit.distance_to(position) - unit_obj.unit.radius
			if dist < closestDistance:
				closestDodge = position
				closestDistance = dist
				closestRadius = radius
		if closestDistance <= radius:
			return [closestDodge, closestRadius]
		return None

	def inDanger(self, unit_obj):
		#get the stats of the enemies around us.
		[enemyDPStoGround, enemyDPStoAir, enemyAirHealth, enemyGroundHealth, enemyTotalDPS, closestEnemy, enemyGroundtoAirDPS, enemyAirtoGroundDPS, enemyGroundtoGroundDPS, enemyAirtoAirDPS] = self.getEnemyStats(unit_obj)
		#before we do anything, lets check to see if the enemy can even attack us.
		if not closestEnemy:
			return False, None #never gonna die.

		if unit_obj.unit.is_flying and enemyDPStoAir == 0:
			#print ('no air dps detected', enemyDPStoAir)
			return False, closestEnemy #never gonna die
		if not unit_obj.unit.is_flying and enemyDPStoGround == 0 and unit_obj.unit.name != 'Colossus':
			#print ('something wrong')
			return False, closestEnemy #never gonna die

		#in danger, if shields are gone, retreat.
		if unit_obj.unit.shield == 0 and unit_obj.unit.name == 'Probe':
			return True, closestEnemy


		#get the stats of our nearest friendlies.
		[friendDPStoGround, friendDPStoAir, friendAirHealth, friendGroundHealth, friendTotalDPS] = self.unitList.friendlyFighters(unit_obj.unit)

		###if there is an enemy on the ground but no grounddps, then we can't damage the enemy and need to leave.
		if enemyGroundHealth > 0 and friendDPStoGround == 0 and enemyGroundtoAirDPS > 0:
			return True, closestEnemy
		if enemyAirHealth > 0 and friendDPStoAir == 0 and enemyAirtoGroundDPS > 0:
			return True, closestEnemy


		#calculate our die times.
		enemyAirDieTime = 0
		enemyGroundDieTime = 0
		enemyOverDieTime = 0
		friendAirDieTime = 0
		friendGroundDietime = 0
		friendOverDieTime = 0
		if friendDPStoAir > 0:
			enemyAirDieTime = enemyAirHealth / friendDPStoAir
		if friendDPStoGround > 0:
			enemyGroundDieTime = enemyGroundHealth / friendDPStoGround
		if friendTotalDPS > 0:
			enemyOverDieTime = (enemyAirHealth + enemyGroundHealth) / friendTotalDPS

		if enemyDPStoAir > 0:
			friendAirDieTime = friendAirHealth /enemyDPStoAir

		if enemyDPStoGround > 0:
			friendGroundDietime = friendGroundHealth / enemyDPStoGround

		if enemyTotalDPS > 0:
			friendOverDieTime = (friendAirHealth + friendGroundHealth) / enemyTotalDPS

		if (friendAirDieTime + friendGroundDietime) > 0 and (enemyAirDieTime + enemyGroundDieTime) == 0:
			#print ('Danger found')
			return True, closestEnemy

		#check if overall battle can be won.
		if friendOverDieTime < enemyOverDieTime:
			return True, closestEnemy

		if (friendAirDieTime + friendGroundDietime) < (enemyAirDieTime + enemyGroundDieTime):
			#print ('Danger found')
			return True, closestEnemy

		return False, closestEnemy



	def inDangerSimple(self, unit_obj):
		#get the stats of the enemies around us.
#		[enemyDPStoGround, enemyDPStoAir, enemyAirHealth, enemyGroundHealth, enemyTotalDPS, closestEnemy, enemyGroundtoAirDPS, enemyAirtoGroundDPS, enemyGroundtoGroundDPS, enemyAirtoAirDPS] = self.getEnemyStats(unit_obj)
		[enemyDPStoGround, enemyDPStoAir, enemyAirHealth, enemyGroundHealth, enemyTotalDPS, closestEnemy, enemyGroundtoAirDPS, enemyAirtoGroundDPS, enemyGroundtoGroundDPS, enemyAirtoAirDPS] = self.getEnemyCenteredStats(unit_obj)

		if not closestEnemy:
			return False, None #never gonna die.

		if unit_obj.unit.is_flying and enemyDPStoAir == 0:
			#print ('no air dps detected', enemyDPStoAir)
			return False, closestEnemy #never gonna die
		if not unit_obj.unit.is_flying and enemyDPStoGround == 0:# and unit_obj.unit.name != 'Colossus':
			#print ('something wrong')
			return False, closestEnemy #never gonna die
		#get the stats of our nearest friendlies.
		[friendDPStoGround, friendDPStoAir, friendAirHealth, friendGroundHealth, friendTotalDPS] = self.unitList.friendlyFighters(unit_obj.unit)
		###if there is an enemy on the ground but no grounddps, then we can't damage the enemy and need to leave.
		if enemyGroundHealth > 0 and friendDPStoGround == 0 and enemyGroundtoAirDPS > 0:
			return True, closestEnemy
		if enemyAirHealth > 0 and friendDPStoAir == 0 and enemyAirtoGroundDPS > 0:
			return True, closestEnemy
		#made it past the basic threat checks, check to see if we are in a winning situation.
		enemyOverDieTime = 100000000
		if friendTotalDPS > 0:
			enemyOverDieTime = (enemyAirHealth + enemyGroundHealth) / friendTotalDPS

		if enemyTotalDPS > 0:
			friendOverDieTime = (friendAirHealth + friendGroundHealth) / enemyTotalDPS
		#check if overall battle can be won.
		if friendOverDieTime * 2 < enemyOverDieTime:
			return True, closestEnemy
		return False, closestEnemy




	def findSimpleRetreatPoint(self, unit, enemy):
		if unit.position == enemy.position:
			return None
		if unit.is_flying:
			targetpoint = unit.position.towards(enemy.position, distance=-3)
			return targetpoint
		else:
			targetpoint = unit.position.towards(enemy.position, distance=-2)
			if self.inPathingGrid(targetpoint):
				return targetpoint
			#no point found, so go back even further, then look for the closest expansion point.
			newpoint = unit.position.towards(enemy.position, distance=-9)
			#find the closest expansion to newpoint.
			finalpoint = self.closestExpansion(newpoint, enemy)
			if finalpoint:
				return finalpoint
			#still nothing, just move to the closest nexus.
			if self.units(NEXUS).exists:
				cNexus = self.units(NEXUS).closest_to(unit)
				return cNexus.position

		return None



	def closestExpansion(self, position, enemy):
		locations = []
		for possible in self.expansion_locations:
			#make sure we aren't trying to go into an enemy base.
			if len(self.cached_enemies.closer_than(10, position)) > 0:
				continue

			distance = position.distance_to(possible)
			#make sure the enemy is not closer to the point we are going to.
			e_distance = enemy.distance_to(possible)
			if distance < e_distance:
				locations.append([distance, possible])
		if len(locations) > 0:
			return sorted(locations, key=itemgetter(0))[0][1]
		return None


	def findGroundRetreatTarget(self, unit, inc_size=3, enemy_radius=10):
		#get all possible retreat points around us.
		retreatPoints = self.retreatGrid(unit.position, size=inc_size)
		#filter out the retreat points that we can't move too.
		retreatPoints = {x for x in retreatPoints if self.inPathingGrid(x)}
		if retreatPoints:
			#get the center of all the ground units that can attack us.
			if self.cached_enemies.filter(lambda x: x.can_attack_ground).closer_than(enemy_radius, unit):
				#enemyThreatsCenter = self.known_enemy_units.filter(lambda x: x.can_attack_ground).closer_than(enemy_radius, unit).center
				enemyThreatsCenter = self.center3d(self.cached_enemies.filter(lambda x: x.can_attack_ground).closer_than(enemy_radius, unit))
				#retreatPoint = max(retreatPoints, key=lambda x: x.distance_to(enemyThreatsCenter) - x.distance_to(unit))
				retreatPoint = enemyThreatsCenter.position.furthest(retreatPoints)
				#debug info below.
				#if unit.is_selected or _debug:
				#	self._client.debug_line_out(self.unitDebugPos(unit), self.p3AddZ(enemyThreatsCenter), (244, 217, 66))
				#	self._client.debug_line_out(self.unitDebugPos(unit), self.p2AddZ(retreatPoint), (176, 66, 244))
				return retreatPoint

################################
#map val kite/retreat functions#
################################
	def findGroundRetreatTargetMapVals(self, unit, inc_size=3, enemy_radius=10):
		#get all possible retreat points around us.
		fullRetreatPoints = self.retreatGrid(unit.position, size=inc_size)
		#filter out the retreat points that we can't move too.
		#retreatPoints = {x for x in retreatPoints if self.inPathingGrid(x)}
		retreatPoints = {x for x in fullRetreatPoints if self.abovePathingScore(x)}
		if not retreatPoints:
			retreatPoints = {x for x in fullRetreatPoints if self.inPathingGrid(x)}
		if retreatPoints:
			#get the center of all the ground units that can attack us.
			if self.cached_enemies.filter(lambda x: x.can_attack_ground).closer_than(enemy_radius, unit):
				#enemyThreatsCenter = self.known_enemy_units.filter(lambda x: x.can_attack_ground).closer_than(enemy_radius, unit).center
				enemyThreatsCenter = self.center3d(self.cached_enemies.filter(lambda x: x.can_attack_ground).closer_than(enemy_radius, unit))
				#retreatPoint = max(retreatPoints, key=lambda x: x.distance_to(enemyThreatsCenter) - x.distance_to(unit))
				retreatPoint = enemyThreatsCenter.position.furthest(retreatPoints)
				#debug info below.
				#if unit.is_selected or _debug:
				#	self._client.debug_line_out(self.unitDebugPos(unit), self.p3AddZ(enemyThreatsCenter), (244, 217, 66))
				#	self._client.debug_line_out(self.unitDebugPos(unit), self.p2AddZ(retreatPoint), (176, 66, 244))
				return retreatPoint


###############
#odd functions#
###############

	async def createArchons(self):
		#count the number of high templars and morph if 2 of them exists.
#		if self.units(HIGHTEMPLAR).amount > 1:
		if self.units(UnitTypeId.HIGHTEMPLAR).idle.ready.amount >= 2:
			ht1 = self.units(UnitTypeId.HIGHTEMPLAR).idle.ready.random
			ht2 = next((ht for ht in self.units(UnitTypeId.HIGHTEMPLAR).idle.ready if ht.tag != ht1.tag), None)
			if ht2:

				command = raw_pb.ActionRawUnitCommand(
					ability_id=AbilityId.MORPH_ARCHON.value,
					unit_tags=[ht1.tag, ht2.tag],
					queue_command=False
				)
				action = raw_pb.ActionRaw(unit_command=command)
				await self._client._execute(action=sc_pb.RequestAction(
					actions=[sc_pb.Action(action_raw=action)]
				))

			#self.combinedActions.append(self.units(HIGHTEMPLAR)[0](AbilityId.MORPH_ARCHON, [self.units(HIGHTEMPLAR)[0], self.units(HIGHTEMPLAR)[1]]))


	async def endGameCheck(self):
		#check if we are about to lose
		if not self.defeat_detected and self._strat_manager.checkDefeat() and self.cached_enemies.structure.amount > 0:
			self.defeat_detected = self.time + 10
			#print ('lost', self.defeat_detected)
			if _use_data:
				self._training_data.removeResult(self.opp_id, self.match_id, self.enemy_race)
				self._training_data.saveResult(self.opp_id, self._strat_manager.strat_id, 'l', self.match_id, self.enemy_race, self.map_name)
			if not self.gg_said:
				await self._client.chat_send(self._strat_manager.unitCounter.getLossSaying(), team_only=False)
				self.gg_said = True


		#check if we are not losing now.
		if self.defeat_detected and self.units.structure.amount >= 5:
			self.defeat_detected = None
			#print ('not dead yet')
			if _use_data:
				self._training_data.removeResult(self.opp_id, self.match_id, self.enemy_race)
				#divert back to win.
				self._training_data.saveResult(self.opp_id, self._strat_manager.strat_id, 'w', self.match_id, self.enemy_race, self.map_name)
			if not self.alive_said:
				#await self._client.chat_send('trouble finishing?  I should be dead already', team_only=False)
				self.alive_said = True

	def cancelBuildings(self):
		#find the buildings that are building, and have low health.
		for building in self.units.filter(lambda x: x.build_progress < 1 and x.health + x.shield < 10):
			self.combinedActions.append(building(CANCEL))

###############
#utlities code#
###############


	def loadStart(self):

		#set the worker time as now.
		self.worker_moved = self.time

		#get the heightmap offset.
		nexus = self.units(NEXUS).ready.random
		if nexus:
			hmval = self.getHeight(nexus.position)
			self.hm_offset = hmval - nexus.position3d.z - 1

		if not _use_data:
			#select starting strat by race.
			if self.enemy_race == Race.Zerg:
				self._strat_manager.strat_id = _zerg_race_strat_id
				self._strat_manager.start_build_order = ['Gateway', 'CyberneticsCore', 'Gateway', 'RoboticsFacility']
			elif self.enemy_race == Race.Protoss:
				self._strat_manager.strat_id = _protoss_race_strat_id
				self._strat_manager.start_build_order = ['Gateway', 'Gateway', 'CyberneticsCore', 'RoboticsFacility']
			elif self.enemy_race == Race.Terran:
				self._strat_manager.strat_id = _terran_race_strat_id
				self._strat_manager.start_build_order = ['Gateway', 'CyberneticsCore', 'Gateway', 'RoboticsFacility']
			else:
				self._strat_manager.strat_id = 1
				self._strat_manager.start_build_order = ['Gateway', 'CyberneticsCore', 'Gateway', 'RoboticsFacility']
			print ('using race strat:', self._strat_manager.strat_id)
			self.intro_value = "(glhf) {version}:{strat_id}".format(version=_version, strat_id=self._strat_manager.strat_id)


		else:
			self.map_name = "{}-{}-{}".format(self.game_info._proto.map_name, self.game_info.player_start_location.x, self.game_info.player_start_location.y)
			#get map width and height:
			#self.map_name = 'NoMapSeeding'
			#self._game_info.pathing_grid.width
			if not self.opp_id:
				if self.enemy_race == Race.Zerg:
					self.opp_id = 2
				elif self.enemy_race == Race.Protoss:
					self.opp_id = 3
				elif self.enemy_race == Race.Terran:
					self.opp_id = 4
				else:
					self.opp_id = 5
			#load up the pickle info and the opp info.
			if _local_ladder:
				print ('playing vs', self.opp_id)
			self._training_data.loadData()

			#generate a unique id that will be used to identify this match.
			self.match_id = time.strftime("%y%m%d%H%M", time.gmtime())
			#find out which strat we want to use.
			self._strat_manager.strat_id = self._training_data.findStrat(self.opp_id, self.enemy_race, self.map_name)
			if _test_strat_id > 0:
				self._strat_manager.strat_id = _test_strat_id

			print ('using strat:', self._strat_manager.strat_id)
			#save this as a victory in case the opponent crashes or leaves before we are able to log it.
			#get length of training data.
			trainingLen = len(self._training_data.data_dict.items())
			oppLen = self._training_data.totalOppDataCount(self.opp_id, self.enemy_race)
			trainingLen = self._training_data.totalDataCount()
			self._training_data.saveResult(self.opp_id, self._strat_manager.strat_id, 'w', self.match_id, self.enemy_race, self.map_name)
			self.intro_value = "(glhf) {version}:{strat_id}.{olen}.{tlen}".format(version=_version, strat_id=self._strat_manager.strat_id, tlen=trainingLen, olen=oppLen)
			#print (self.intro_value)

			#load up the units the opp used the last time.
			self.opp_unit_history = None
			if self._strat_manager.strat_id != 1:
				self.opp_unit_history = self._training_data.getOppHistory(self.opp_id, self.enemy_race)

			if self.opp_unit_history:
				self.start_unit_ratio = self._strat_manager.calc_starter_counters(self.opp_unit_history)


	async def check_enemy_structures(self):
		if len(self.cached_enemies.structure) != self.saved_enemy_structures:
			self.saved_enemy_structures = len(self.cached_enemies.structure)
			await self.getRallyPoint()

	async def getRallyPoint(self):
		if not self.cached_enemies:
			#first frame or we killed them all, just use the defensive point.
			self.rally_pos = self.defensive_pos
			self.prism_pylon_pos = self.defensive_pos
			return
		#get the closest enemy structure.
		#get the midpoint between the enemy structure and the defensive position.
		#find the closest placement for a nexus in that area, make that the rally point.
		#closestEnemyStructure = self.cached_enemies.structure.closest_to(self.defensive_pos)
		if len(self.cached_enemies.structure) == 0:
			self.rally_pos = self.defensive_pos
			self.prism_pylon_pos = self.defensive_pos
			return

		closestEnemyStructure = self.cached_enemies.structure.furthest_to(random.choice(self.enemy_start_locations))


		#self.debug_rally_es = closestEnemyStructure.position
		mid = self.midpoint(closestEnemyStructure.position, self.defensive_pos)
		#move a little closer to the enemy by getting another midpoint and use it for warpprisms.
		closer_mid = self.midpoint(closestEnemyStructure.position, mid)
		placement = await self.find_placement(NEXUS, mid)
		placement2 = await self.find_placement(NEXUS, closer_mid)
		if placement:
			self.rally_pos = placement
		else:
			print ('could not find rally position')
			self.rally_pos = self.defensive_pos
		#make sure to place after rally pos because it is used below.
		if placement2:
			self.prism_pylon_pos = placement2
		else:
			print ('cound not find prism position')
			self.prism_pylon_pos = self.rally_pos



	def midpoint(self, pos1, pos2):
		return Point2(((pos1.position.x + pos2.position.x) / 2, (pos1.position.y + pos2.position.y) /2))

	def getDefensivePoint(self):
		#make sure nexus exists.
		if len(self.units(NEXUS)) == 0:
			return

		#get the center point of our nexus.
		center = self.units(NEXUS).center
		#print ('center', center)
		closestNexus = self.units(NEXUS).closest_to(self.enemy_start_locations[0])
		NexusDistance = closestNexus.distance_to(self.enemy_start_locations[0])

		#loop the ramps and find ramps that are closer than nexus.
		possibles = []
		for ramp in self.game_info.map_ramps:
			#get the distance of the ramp to the enemy location and see if it's a qualifying ramp.
			#if the ramp is too far away, then don't use it.
			nexus_ramp_distance = closestNexus.distance_to(ramp.top_center)
			if nexus_ramp_distance < 30 and ramp.top_center.distance_to(self.enemy_start_locations[0]) < NexusDistance + 10:
				#print ('adding', nexus_ramp_distance, NexusDistance, ramp.top_center.distance_to(self.enemy_start_locations[0]))
				possibles.append(ramp)

		#loop the ramps that are left and get the one that is closest to the center point.
		closestDistance = 1000
		closestRamp = self.main_base_ramp
		for ramp in possibles:
			distance = sqrt((ramp.top_center[0] - center[0])**2 + (ramp.top_center[1] - center[1])**2)
			if distance < closestDistance:
				closestRamp = ramp
				closestDistance = distance

		if closestRamp:
			#this is our defensive point, get the position 2 distance behind it.
			if closestRamp.bottom_center.position != closestRamp.top_center.position:
				self.defensive_pos = closestRamp.bottom_center.towards(closestRamp.top_center, 9)

	def findOppId(self):
		parser = argparse.ArgumentParser()
		parser.add_argument('--OpponentId', type=str, nargs="?", help='Opponent Id')
		args, unknown = parser.parse_known_args()
		if args.OpponentId:
			return args.OpponentId
		return None


	def getEnemyCenteredStats(self, unit_obj, enemy_range=10):
		#find all the enemy units that are near us.
		enemyThreatsClose = unit_obj.closestEnemies.closer_than(enemy_range, unit_obj.unit).filter(lambda x: x.name not in ['Probe', 'SCV', 'Drone'] and (x.can_attack_air or x.can_attack_ground))

		enemyGroundtoAirDPS = 0
		enemyAirtoGroundDPS = 0
		enemyGroundtoGroundDPS = 0
		enemyAirtoAirDPS = 0

		enemyDPStoGround = 0
		enemyDPStoAir = 0
		enemyAirHealth = 0
		enemyGroundHealth = 0
		enemyTotalDPS = 0
		closestEnemy = None
		if enemyThreatsClose:
			for enemy in enemyThreatsClose:
				if enemy.can_attack_ground or enemy.can_attack_air:
					if enemy.is_flying:
						enemyAirHealth += enemy.health + enemy.shield
						if unit_obj.unit.is_flying:
							enemyAirtoAirDPS += enemy.air_dps
						else:
							enemyAirtoGroundDPS += enemy.ground_dps
					else:
						enemyGroundHealth += enemy.health + enemy.shield
						if unit_obj.unit.is_flying:
							enemyGroundtoAirDPS += enemy.air_dps
						else:
							enemyGroundtoGroundDPS = enemy.ground_dps

				enemyDPStoGround += enemy.ground_dps
				enemyDPStoAir += enemy.air_dps
				if enemy.ground_dps > enemy.air_dps:
					enemyTotalDPS += enemy.ground_dps
				else:
					enemyTotalDPS += enemy.air_dps


			#get the closest enemy.
			if unit_obj.unit.is_flying and enemyThreatsClose.filter(lambda x: x.can_attack_air):
				closestEnemy = enemyThreatsClose.filter(lambda x: x.can_attack_air).closest_to(unit_obj.unit)
			elif not unit_obj.unit.is_flying and enemyThreatsClose.filter(lambda x: x.can_attack_ground):
				closestEnemy = enemyThreatsClose.filter(lambda x: x.can_attack_ground).closest_to(unit_obj.unit)
			else:
				closestEnemy = enemyThreatsClose.closest_to(unit_obj.unit)
		return [enemyDPStoGround, enemyDPStoAir, enemyAirHealth, enemyGroundHealth, enemyTotalDPS, closestEnemy, enemyGroundtoAirDPS, enemyAirtoGroundDPS, enemyGroundtoGroundDPS, enemyAirtoAirDPS]




	def getAllEnemyStats(self, unit_obj, enemy_range=10):
		#find all the enemy units that are near us.
		#enemyThreatsClose = unit_obj.closestEnemies.exclude_type([PROBE,SCV,DRONE]).filter(lambda x: x.can_attack_air or x.can_attack_ground)
		enemyThreatsClose = unit_obj.closestEnemies.filter(lambda x: not x.name in ['Probe', 'SCV', 'Drone'] and (x.can_attack_air or x.can_attack_ground))

		enemyGroundtoAirDPS = 0
		enemyAirtoGroundDPS = 0
		enemyGroundtoGroundDPS = 0
		enemyAirtoAirDPS = 0

		enemyDPStoGround = 0
		enemyDPStoAir = 0
		enemyAirHealth = 0
		enemyGroundHealth = 0
		enemyTotalDPS = 0
		closestEnemy = None
		if enemyThreatsClose:
			for enemy in enemyThreatsClose:
				if enemy.can_attack_ground or enemy.can_attack_air:
					if enemy.is_flying:
						enemyAirHealth += enemy.health + enemy.shield
						if unit_obj.unit.is_flying:
							enemyAirtoAirDPS += enemy.air_dps
						else:
							enemyAirtoGroundDPS += enemy.ground_dps
					else:
						enemyGroundHealth += enemy.health + enemy.shield
						if unit_obj.unit.is_flying:
							enemyGroundtoAirDPS += enemy.air_dps
						else:
							enemyGroundtoGroundDPS = enemy.ground_dps

				enemyDPStoGround += enemy.ground_dps
				enemyDPStoAir += enemy.air_dps
				if enemy.ground_dps > enemy.air_dps:
					enemyTotalDPS += enemy.ground_dps
				else:
					enemyTotalDPS += enemy.air_dps


			#get the closest enemy.
			if unit_obj.unit.is_flying and enemyThreatsClose.filter(lambda x: x.can_attack_air):
				closestEnemy = enemyThreatsClose.filter(lambda x: x.can_attack_air).closest_to(unit_obj.unit)
			elif not unit_obj.unit.is_flying and enemyThreatsClose.filter(lambda x: x.can_attack_ground):
				closestEnemy = enemyThreatsClose.filter(lambda x: x.can_attack_ground).closest_to(unit_obj.unit)
			else:
				closestEnemy = enemyThreatsClose.closest_to(unit_obj.unit)
		return [enemyDPStoGround, enemyDPStoAir, enemyAirHealth, enemyGroundHealth, enemyTotalDPS, closestEnemy, enemyGroundtoAirDPS, enemyAirtoGroundDPS, enemyGroundtoGroundDPS, enemyAirtoAirDPS]



	def getEnemyStats(self, unit_obj, enemy_range=10):
		#find all the enemy units that are near us.
		enemyThreatsClose = unit_obj.closestEnemies.closer_than(enemy_range, unit_obj.unit).filter(lambda x: x.can_attack_air or x.can_attack_ground)

		enemyGroundtoAirDPS = 0
		enemyAirtoGroundDPS = 0
		enemyGroundtoGroundDPS = 0
		enemyAirtoAirDPS = 0

		enemyDPStoGround = 0
		enemyDPStoAir = 0
		enemyAirHealth = 0
		enemyGroundHealth = 0
		enemyTotalDPS = 0
		closestEnemy = None
		if enemyThreatsClose:
			for enemy in enemyThreatsClose:
				if enemy.can_attack_ground or enemy.can_attack_air:
					if enemy.is_flying:
						enemyAirHealth += enemy.health + enemy.shield
						if unit_obj.unit.is_flying:
							enemyAirtoAirDPS += enemy.air_dps
						else:
							enemyAirtoGroundDPS += enemy.ground_dps
					else:
						enemyGroundHealth += enemy.health + enemy.shield
						if unit_obj.unit.is_flying:
							enemyGroundtoAirDPS += enemy.air_dps
						else:
							enemyGroundtoGroundDPS = enemy.ground_dps

				enemyDPStoGround += enemy.ground_dps
				enemyDPStoAir += enemy.air_dps
				if enemy.ground_dps > enemy.air_dps:
					enemyTotalDPS += enemy.ground_dps
				else:
					enemyTotalDPS += enemy.air_dps


			#get the closest enemy.
			if unit_obj.unit.is_flying and enemyThreatsClose.filter(lambda x: x.can_attack_air):
				closestEnemy = enemyThreatsClose.filter(lambda x: x.can_attack_air).closest_to(unit_obj.unit)
			elif not unit_obj.unit.is_flying and enemyThreatsClose.filter(lambda x: x.can_attack_ground):
				closestEnemy = enemyThreatsClose.filter(lambda x: x.can_attack_ground).closest_to(unit_obj.unit)
			else:
				closestEnemy = enemyThreatsClose.closest_to(unit_obj.unit)
		return [enemyDPStoGround, enemyDPStoAir, enemyAirHealth, enemyGroundHealth, enemyTotalDPS, closestEnemy, enemyGroundtoAirDPS, enemyAirtoGroundDPS, enemyGroundtoGroundDPS, enemyAirtoAirDPS]




	async def getAllAbilities(self, ignore_resources=False):
		result = await self._client._execute(query=query_pb.RequestQuery(
				abilities=[query_pb.RequestQueryAvailableAbilities(
				unit_tag=unit.tag) for unit in self.units],
				ignore_resource_requirements=ignore_resources)
			)
		ab_dict = {}
		for unit in result.query.abilities:
			abils = []
			for abil in unit.abilities:
				abils.append(AbilityId(abil.ability_id))
			ab_dict.update({unit.unit_tag:abils})

		return ab_dict


	def cache_enemies(self):
		self.cached_enemies = self.known_enemy_units

	def check_movements(self):
		new_positions = {}
		new_moves = {}
		#loop units and compare their current positions with the previous positions.
		for unit in self.cached_enemies:
			#get old position.
			o_pos = None
			moved = False
			if self.unit_positions.get(unit.tag):
				o_pos = self.unit_positions.get(unit.tag)
			if o_pos:
				if o_pos != unit.position:
					#moved.
					moved = True
			#update the new_moves dict
			new_moves.update({unit.tag:moved})
			new_positions.update({unit.tag:unit.position})

		self.unit_positions = new_positions
		self.unit_moves = new_moves

	def get_mapvals(self):
		#check to see if we can get a cached version.
		cache_dict = self._training_data.loadMapVals(self.map_name)
		if cache_dict:
			print ('map vals loaded from cache')
			self.mapDistances = cache_dict
			return
		print ('running map vals')
		#get all teh valid points in the pathing map.
		all_points = [
			Point2((x, y))
			for x in range(self._game_info.pathing_grid.width)
			for y in range(self._game_info.pathing_grid.height)
			#if self._game_info.pathing_grid[(x, y)] != 0
			if not self.inPathingGrid(Point2((x,y)))
		]
		#print (all_points)
		valdict = {}
		for pos in all_points:
			#find the distance to the nearest non valid point.
			distance = self.nearestNonValid(pos)
			self._client.debug_text_3d(str(int(distance)), self.turn3d(pos))
			posStr = "{}:{}".format(pos.x, pos.y)
			valdict.update({posStr:int(distance)})
			#print (pos, distance)
		#find ramps and intersections and increase the value for pathing through them.



		#save it.
		self._training_data.saveMapVals(self.map_name, valdict)
		self.mapDistances = valdict

	def nearestNonValid(self, pos):
		#create a grid around the position that is 6 points around it.
		grid = self.retreatGrid(pos, size=3)
		#filter out the retreat points that we can move too.
		grid = {x for x in grid if self.inPathingGrid(x)}
		#loop through the grid and find the closest distance.
		if grid:
			#print ('g', grid, pos)
			return pos.position.distance_to_closest(grid)
		#print ('no grid')
		return 20




##################
#unorganized code#
##################

	def _get_next_expansion(self):
		locations = []
		for possible in self.expansion_locations:
			#make sure the location doesn't have a nexus already.
			if not self.units(NEXUS).closer_than(12, possible).exists:
				distance = sqrt((possible[0] - self.start_location[0])**2 + (possible[1] - self.start_location[1])**2)
				locations.append([distance, possible])
		return sorted(locations, key=itemgetter(0))[0][1]

	def findRangeRetreatTarget(self, unit, enemyThreats, inc_size=1):
		#get all possible retreat points around us.
		retreatPoints = self.retreatGrid(unit.position, size=inc_size)
		if retreatPoints:
			#get the center of all the ground units that can attack us.
			if enemyThreats:
				#enemyThreatsCenter = self.known_enemy_units.filter(lambda x: x.can_attack_ground).closer_than(enemy_radius, unit).center
				enemyThreatsCenter = self.center3d(enemyThreats)
				#retreatPoint = max(retreatPoints, key=lambda x: x.distance_to(enemyThreatsCenter) - x.distance_to(unit))
				retreatPoint = enemyThreatsCenter.position.furthest(retreatPoints)
				#debug info below.
				if unit.is_selected or _debug_combat:
					self._client.debug_line_out(self.unitDebugPos(unit), self.p3AddZ(enemyThreatsCenter), (244, 217, 66))
					self._client.debug_line_out(self.unitDebugPos(unit), self.p2AddZ(retreatPoint), (176, 66, 244))
				return retreatPoint

	def inRange(self, unit):
		#find out if any enemies have us in their range.
		enemyThreats = self.cached_enemies.exclude_type([ADEPTPHASESHIFT]).filter(lambda x: x.target_in_range(unit, 1)).sorted(lambda x: x.distance_to(unit))
		if enemyThreats:
			return True, enemyThreats
		return False, None

	def turn3d(self, p2):
		return Point3((p2.position.x, p2.position.y, self.getHeight(p2.position)))

	def checkCargo(self, unit, cargo):
		cargo_unit = self.units().find_by_tag(cargo)
		if cargo_unit:
			#if len(cargo_unit.orders) == 0:
			#if 'attack' in str(probe.orders).lower():
			distance = sqrt((cargo_unit.position[0] - unit.position[0])**2 + (cargo_unit.position[1] - unit.position[1])**2)
			print (cargo, unit.position, cargo_unit.position, distance, cargo_unit.orders, len(cargo_unit.orders))
			if distance < 6 or len(cargo_unit.orders) == 0:
				return True
		return False

	def findDropTarget(self, unit, enemy, dis1=6, dis2=8):
		#dropPoints = self.neighbors8(enemy.position, distance=dis1) | self.neighbors8(enemy.position, distance=dis2)
		dropPoints = self.retreatGrid(unit.position, size=3)
		if dropPoints:
			dropPoints = {x for x in dropPoints if self.inPathingGrid(x)}
			if dropPoints:
				dropPoint = max(dropPoints, key=lambda x: x.distance_to(unit) - x.distance_to(enemy))
				return dropPoint

	def inList(self, triedList, tPoint):
		nposx = round(tPoint[0], 2)
		nposy = round(tPoint[1], 2)
		newPos = (nposx, nposy)
		if newPos not in triedList:
			return True
		return False

	def center3d(self, units):
		pos = Point3((sum([unit.position.x for unit in units]) / units.amount, sum([unit.position.y for unit in units]) / units.amount, sum([unit.position3d.z for unit in units]) / units.amount))
		return pos

	def unitDebugPos(self, unit):
		return Point3((unit.position3d.x, unit.position3d.y, (unit.position3d.z + 1)))

	def p3AddZ(self, pos):
		return Point3((pos.x, pos.y, (pos.z + 1)))

	def getHeight(self, pos):
		off = 0
		if self.hm_offset:
			off = self.hm_offset
		x = int(pos.x)
		y = int(pos.y)
		if x < 1:
			x = 1
		if y < 1:
			y = 1
		return self.game_info.terrain_height[x, y] - off

	def p2AddZ(self, pos):
		return Point3((pos.x, pos.y, self.getHeight(pos)))

	def p2RelZ(self, pos, unit):
		return Point3((pos.x, pos.y, (unit.position3d.z + 0.5)))

	def findAirRetreatTarget(self, unit, inc_size=3, enemy_radius=10):
		#get all possible retreat points around us.
		retreatPoints = self.retreatGrid(unit.position, size=inc_size)
		if retreatPoints:
			#get the center of all the ground units that can attack us.
			if self.cached_enemies.filter(lambda x: x.can_attack_air).closer_than(enemy_radius, unit):
				#enemyThreatsCenter = self.known_enemy_units.filter(lambda x: x.can_attack_ground).closer_than(enemy_radius, unit).center
				enemyThreatsCenter = self.center3d(self.cached_enemies.filter(lambda x: x.can_attack_air).closer_than(enemy_radius, unit))
				#retreatPoint = max(retreatPoints, key=lambda x: x.distance_to(enemyThreatsCenter) - x.distance_to(unit))
				retreatPoint = enemyThreatsCenter.position.furthest(retreatPoints)
				#debug info below.
				if unit.is_selected or _debug_combat:
					self._client.debug_line_out(self.unitDebugPos(unit), self.p3AddZ(enemyThreatsCenter), (244, 217, 66))
					self._client.debug_line_out(self.unitDebugPos(unit), self.p2AddZ(retreatPoint), (176, 66, 244))
				return retreatPoint


	def findRetreatTarget(self, unit, enemy, is_flying=False, dis1=2, dis2=4, inc_size=3):
		retreatPoints = self.retreatGrid(unit.position, size=inc_size)
		#retreatPoints = self.neighbors8(unit.position, distance=dis1) | self.neighbors8(unit.position, distance=dis2)
		if not is_flying:
			retreatPoints = {x for x in retreatPoints if self.inPathingGrid(x)}
		if retreatPoints:
			retreatPoint = enemy.position.furthest(retreatPoints)
			#retreatPoint = max(retreatPoints, key=lambda x: x.distance_to(enemy) - x.distance_to(unit))
			return retreatPoint

	def findFlyingTarget(self, unit, can_target_air=False, max_enemy_distance=5, target_hitpoints=True, target_buildings=False):
		enemyThreats = []
		if target_buildings:
			enemyThreats = self.cached_enemies.flying.closer_than(max_enemy_distance, unit)
		else:
			if can_target_air:
				#look for medivac MEDIVAC .of_type([ADEPTPHASESHIFT])
				enemyThreats = self.cached_enemies.of_type([MEDIVAC]).in_attack_range_of(unit) #.closer_than(max_enemy_distance, unit)
				if not enemyThreats:
					enemyThreats = self.cached_enemies.flying.filter(lambda x: x.can_attack_air).in_attack_range_of(unit)#.closer_than(max_enemy_distance, unit)
			else:
				enemyThreats = self.cached_enemies.flying.filter(lambda x: x.can_attack_ground).in_attack_range_of(unit)#.closer_than(max_enemy_distance, unit)
		if enemyThreats.exists:
			if target_hitpoints:
				enemyThreats = enemyThreats.sorted(lambda x: x.health + x.shield)
				return enemyThreats[0]
			else:
				enemyThreats = enemyThreats.sorted(lambda x: x.distance_to(unit))
				return enemyThreats[0]

	def findGroundTarget(self, unit, can_target_air=False, max_enemy_distance=5, target_hitpoints=True, target_buildings=False):
		enemyThreats = []
		if target_buildings:
			#in_attack_range_of
			#enemyThreats = self.known_enemy_units.not_flying.closer_than(max_enemy_distance, unit)
			enemyThreats = self.cached_enemies.not_flying.in_attack_range_of(unit)
		else:
			if can_target_air:
				#enemyThreats = self.known_enemy_units.exclude_type([ADEPTPHASESHIFT]).not_flying.filter(lambda x: x.can_attack_air).closer_than(max_enemy_distance, unit)
				enemyThreats = self.cached_enemies.exclude_type([ADEPTPHASESHIFT]).not_flying.filter(lambda x: x.can_attack_air).in_attack_range_of(unit)
			else:
				enemyThreats = self.cached_enemies.exclude_type([ADEPTPHASESHIFT]).not_flying.filter(lambda x: x.can_attack_ground).in_attack_range_of(unit)
		if enemyThreats.exists:
			if target_hitpoints:
				enemyThreats = enemyThreats.sorted(lambda x: x.health + x.shield)
				return enemyThreats[0]
			else:
				enemyThreats = enemyThreats.sorted(lambda x: x.distance_to(unit))
				return enemyThreats[0]

	def filterTargets(self, unit, enemyThreats):
		pass


	def findDetectors(self, unit, detect_range):
		enemyThreats = self.cached_enemies.filter(lambda x: x.detect_range > 0).closer_than(detect_range, unit).sorted(lambda x: x.distance_to(unit))
		if enemyThreats:
			return enemyThreats[0]

	def findTargetExp(self, unit, can_target_air=False, max_enemy_distance=5, target_hitpoints=False, target_buildings=False, target_dangerous=True):
		#filter down to all enemies in the distance with radius added.
		enemyThreats = []
		if target_buildings:
			enemyThreats = self.cached_enemies.structure.closer_than(20, unit)
		else:
			if can_target_air:
				enemyThreats = self.cached_enemies.exclude_type([ADEPTPHASESHIFT]).filter(lambda x: x.can_attack_air).closer_than(20, unit)
			else:
				enemyThreats = self.cached_enemies.exclude_type([ADEPTPHASESHIFT]).filter(lambda x: x.can_attack_ground).closer_than(20, unit)

		#keep only the threats that are in our range.
		#print ('len1', len(enemyThreats))
		if enemyThreats.exists:
			if target_dangerous:
				#target the enemies that we are in range of first, of those in range
				if unit.is_flying:
					enemyThreats = enemyThreats.sorted(lambda x: x.distance_to(unit) - (x.radius + x.air_range + unit.radius))
				else:
					enemyThreats = enemyThreats.sorted(lambda x: x.distance_to(unit) - (x.radius + x.ground_range + unit.radius))

			elif target_hitpoints:
				enemyThreats = enemyThreats.sorted(lambda x: x.health + x.shield)
			else:
				enemyThreats = enemyThreats.sorted(lambda x: x.distance_to(unit))

		ct = 0
		enemyInRange = []
		for enemy in enemyThreats:
			#distance = unit.radius + range + enemy.radius
			#print (ct)
			ct += 1
			attack_range = 0
			if unit.can_attack_ground and not enemy.is_flying:
				attack_range = unit.ground_range
			elif unit.can_attack_air and enemy.is_flying:
				attack_range = unit.air_range

			enemy_attack_range = 0
			if enemy.can_attack_ground and not unit.is_flying:
				enemy_attack_range = enemy.ground_range
			elif enemy.can_attack_air and unit.is_flying:
				enemy_attack_range = enemy.air_range


			full_range = enemy.radius + attack_range + unit.radius
			enemy_range =  enemy.radius + enemy_attack_range + unit.radius
			#print ('seeing', full_range, unit.distance_to(enemy), enemy_range)
			if unit.distance_to(enemy) < enemy.radius + attack_range + unit.radius:
				return enemy
				#enemyInRange.append(enemy)
				#print ('adding', full_range, unit.distance_to(enemy))
				#enemyThreats.remove(enemy)
		#print ('len2', len(enemyInRange))
		if len(enemyInRange) > 0:
			return enemyInRange[0]

	def findTarget(self, unit, can_target_air=False, max_enemy_distance=5, target_hitpoints=True, target_buildings=False):
		enemyThreats = []
		if target_buildings:
			enemyThreats = self.cached_enemies.in_attack_range_of(unit)#.closer_than(max_enemy_distance, unit)
		else:
			if can_target_air:
				enemyThreats = self.cached_enemies.of_type([MEDIVAC,CARRIER,BATTLECRUISER]).in_attack_range_of(unit) #.closer_than(max_enemy_distance, unit)
				if not enemyThreats:
					enemyThreats = self.cached_enemies.exclude_type([ADEPTPHASESHIFT]).filter(lambda x: x.can_attack_air).in_attack_range_of(unit)#.closer_than(max_enemy_distance, unit)
			else:
				enemyThreats = self.cached_enemies.exclude_type([ADEPTPHASESHIFT]).filter(lambda x: x.can_attack_ground).in_attack_range_of(unit)#.closer_than(max_enemy_distance, unit)
		if enemyThreats.exists:
			if target_hitpoints:
				enemyThreats = enemyThreats.sorted(lambda x: x.health + x.shield)
				return enemyThreats[0]
			else:
				enemyThreats = enemyThreats.sorted(lambda x: x.distance_to(unit))
				return enemyThreats[0]

	def regPathingScore(self, pos):
		if pos[0] < 0 or pos[1] < 0:
			return False
		if pos[0] >= self._game_info.pathing_grid.width or pos[1] >= self._game_info.pathing_grid.height:
			return False
		posStr = "{}:{}".format(str(int(pos.x)), str(int(pos.y)))
		if self.mapDistances.get(str(pos)):
			return self.mapDistances.get(str(pos))
		return 0

	def abovePathingScore(self, pos):
		if pos[0] < 0 or pos[1] < 0:
			return False
		if pos[0] >= self._game_info.pathing_grid.width or pos[1] >= self._game_info.pathing_grid.height:
			return False
		posStr = "{}:{}".format(str(int(pos.x)), str(int(pos.y)))
		if self.mapDistances.get(str(pos)) and self.mapDistances.get(str(pos)) >= 3:
		 	return True
		return False


	#stolen and edited from burny
	def inPathingGrid(self, pos):
		if pos[0] < 0 or pos[1] < 0:
			return False
		if pos[0] >= self._game_info.pathing_grid.width or pos[1] >= self._game_info.pathing_grid.height:
			return False
		# returns True if it is possible for a ground unit to move to pos - doesnt seem to work on ramps or near edges
		assert isinstance(pos, (Point2, Point3, Unit))
		pos = pos.position.to2.rounded
		return self._game_info.pathing_grid[(pos)] != 0

	def retreatGrid(self, position, size=2):
		#create a grid size by size around the unit for possible retreat points.
		#eg: size=2 equals a 5 by 5 grid with position in the center.

		p = position
		d = ((size * 2) + 1)
		rdone = 0 - size
		retreatPoints = []
		while rdone < d:
			cdone = 0 - size
			while cdone < d:
				if (p.x - rdone) > 0 and (p.y - cdone) > 0:
					retreatPoints.append(Point2((p.x -rdone, p.y - cdone)))
				cdone += 1
			rdone += 1
		return retreatPoints

	def groundRetreatGrid(self, position, size=2):
		#create a grid size by size around the unit for possible retreat points.
		#eg: size=2 equals a 5 by 5 grid with position in the center.
		#checks for valid spots for ground units.
		p = position
		d = ((size * 2) + 1)
		rdone = 0 - size
		retreatPoints = []
		while rdone < d:
			cdone = 0 - size
			while cdone < d:
				if (p.x - rdone) > 0 and (p.y - cdone) > 0:
					possible = Point2((p.x -rdone, p.y - cdone))
					#check to make sure ground unit can move there.
					if self.inPathingGrid(possible):
						retreatPoints.append(possible)
				cdone += 1
			rdone += 1
		return retreatPoints


	def getDefensiveSearchPos(self):
		#get the nearest locations.
		locations = []
		for possible in self.expansion_locations:
			distance = sqrt((possible[0] - self.start_location.position[0])**2 + (possible[1] - self.start_location.position[1])**2)
			locations.append([distance, possible])
		locations = sorted(locations, key=itemgetter(0))
		del locations[5:]
		return random.choice(locations)[1]


		#if distance of that start location is less than 10,then search nearby areas.
		startPos = self.start_location
		if unit.distance_to(self.start_location) > 10:
			return startPos
		else:
			#search random among the nearest 10 expansion slots to unit.
			locations = []
			for possible in self.expansion_locations:
				distance = sqrt((possible[0] - unit.position[0])**2 + (possible[1] - unit.position[1])**2)
				locations.append([distance, possible])
			locations = sorted(locations, key=itemgetter(0))
			del locations[10:]
			return random.choice(locations)[1]


	#properties
	@property
	def main_ramp_bottom_center(self) -> Point2:
		pos = Point2((sum([p.x for p in self.main_base_ramp.lower]) / len(self.main_base_ramp.lower), \
			sum([p.y for p in self.main_base_ramp.lower]) / len(self.main_base_ramp.lower)))
		return pos

	@property
	def trueGates(self) -> int:
		#total = self.units(GATEWAY).amount + self.units(WARPGATE).amount
		return self.units(GATEWAY).amount + self.units(WARPGATE).amount

	@property
	def queuedGates(self) -> bool:
		return self.buildingList.gatesQueued

	@property
	def queuedStarGates(self) -> bool:
		return self.buildingList.stargatesQueued

	@property
	def queuedRobos(self) -> bool:
		return self.buildingList.robosQueued

	@property
	def allQueued(self) -> bool:
		return self.buildingList.allQueued

	@property
	def productionBuildings(self) -> int:
		#count all our production facilities.
		return self.units.of_type([GATEWAY,WARPGATE,STARGATE,ROBOTICSFACILITY]).amount

###############
#old code area#
###############


	def inDangerWorking(self, unit, is_flying=False, friend_range=10, enemy_range=10, min_shield_attack=0):
		friendlyClose = self.units().closer_than(friend_range, unit)
		enemyThreatsClose = []
		closestEnemy = None
		if unit.is_flying:
			enemyThreatsClose = self.cached_enemies.exclude_type([ADEPTPHASESHIFT]).filter(lambda x: x.can_attack_air).closer_than(enemy_range, unit)
		else:
			enemyThreatsClose = self.cached_enemies.exclude_type([ADEPTPHASESHIFT]).filter(lambda x: x.can_attack_ground).closer_than(enemy_range, unit)
		if enemyThreatsClose.exists:
			closestEnemy = enemyThreatsClose.closest_to(unit)
			if unit.shield_percentage < min_shield_attack:
				return True, closestEnemy

		enemyDPStoGround = 0
		enemyDPStoAir = 0
		enemyAirHealth = 0
		enemyGroundHealth = 0
		for enemy in enemyThreatsClose:
			if enemy.can_attack_ground or enemy.can_attack_air:
				if enemy.is_flying:
					enemyAirHealth += enemy.health + enemy.shield
				else:
					enemyGroundHealth += enemy.health + enemy.shield
			enemyDPStoGround += enemy.ground_dps
			enemyDPStoAir += enemy.air_dps

		friendDPStoGround = 0
		friendDPStoAir = 0
		friendAirHealth = 0
		friendGroundHealth = 0

		for friend in friendlyClose:
			if friend.is_flying:
				friendAirHealth += friend.health + friend.shield
			else:
				friendGroundHealth += friend.health + friend.shield
			friendDPStoGround += friend.ground_dps
			friendDPStoAir += friend.air_dps
		#calcuate the damage that could be done to those who can attack us, vs our own dps.


		enemyAirDieTime = 0
		enemyGroundDieTime = 0
		friendAirDieTime = 0
		friendGroundDietime = 0
		if friendDPStoAir > 0:
			enemyAirDieTime = enemyAirHealth / friendDPStoAir
		if friendDPStoGround > 0:
			enemyGroundDieTime = enemyGroundHealth / friendDPStoGround

		if enemyDPStoAir > 0:
			friendAirDieTime = friendAirHealth /enemyDPStoAir

		if enemyDPStoGround > 0:
			friendGroundDietime = friendGroundHealth / enemyDPStoGround
		#
		# if unit.name == 'Phoenix':
		# # if enemyThreatsClose:
		#  	print ('dps:', friendDPStoGround, friendDPStoAir, enemyDPStoGround, enemyDPStoAir)
		#  	print ('hp:', friendGroundHealth, friendAirHealth, enemyGroundHealth, enemyAirHealth)
		#  	print ('dt:', friendGroundDietime, friendAirDieTime, enemyGroundDieTime, enemyAirDieTime)

		if is_flying and enemyDPStoAir == 0:
			#never gonna die
			return False, closestEnemy
		if not is_flying and enemyDPStoGround == 0:
			#never gonna die
			return False, closestEnemy

		if (friendAirDieTime + friendGroundDietime) > 0 and (enemyAirDieTime + enemyGroundDieTime) == 0:
			#print ('Danger found')
			return True, closestEnemy

		if (friendAirDieTime + friendGroundDietime) < (enemyAirDieTime + enemyGroundDieTime):
			#print ('Danger found')
			return True, closestEnemy
		return False, closestEnemy


	def closest_enemy_structure(self):
		structures = []
		for structure in self.known_enemy_structures:
			dist = structure.distance_to(self.game_info.player_start_location)
			if len(self.units(NEXUS)):
				dist = structure.distance_to(self.units(NEXUS).closest_to(structure).position)
			structures.append([dist, structure])
		structures = sorted(structures, key=itemgetter(0))
		if len(structures) > 0:
			return structures[0][1]
		else:
			return self.enemy_start_locations[0]

	async def detect_enemies(self):
		defend_enemies = []
		if len(self.cached_enemies) > 0:
			for enemy in self.cached_enemies:
				nearest_pos  = self.game_info.player_start_location
				closest_enemy_structure = self.closest_enemy_structure()
				if len(self.units(NEXUS)) > 0:
					nearest_pos = self.units(NEXUS).closest_to(enemy).position
				dist = enemy.distance_to(nearest_pos)
				#e_dist = enemy.distance_to(closest_enemy_structure)
				if dist < self._defense_distance:
					defend_enemies.append([dist, enemy])
		defend_enemies = sorted(defend_enemies, key=itemgetter(0))
		self._defend_enemies = defend_enemies



	async def build_economy(self):
#		if not self._strat_manager.stage1complete or self.minerals < 650 or not self.can_afford(NEXUS) or self.already_pending(NEXUS) or self.units(PROBE).amount == 0:
		if not self._strat_manager.stage1complete or not self.can_afford(NEXUS) or self.already_pending(NEXUS) or self.units(PROBE).amount == 0:
			return False
		if self.under_attack and self.minerals < 1000 and not self.reaper_cheese:
			return False
		#make sure we have a place to expand too.
		if not self.expPos:
			return False

		#check to see if we need another base for more gas.
		if self.minerals > 2500 and self.vespene < 500 and self.state.creep[int(self.expPos.x), int(self.expPos.y)] == 0:
			self._build_manager.last_build = 5
			await self.expand_now(location=self.expPos, max_distance=0)
			self.can_spend = False
			return


		#count needed workers.
		workers_needed = 0
		total_ideal = 0
		total_assigned = 0
		for nexus in self.units(NEXUS).ready:
			workers_needed += nexus.ideal_harvesters - nexus.assigned_harvesters
			total_ideal += nexus.ideal_harvesters
			total_assigned += nexus.assigned_harvesters

		for assim in self.units(ASSIMILATOR).ready:
			workers_needed += assim.ideal_harvesters - assim.assigned_harvesters
			total_ideal += assim.ideal_harvesters
			total_assigned += assim.assigned_harvesters

		if self._strat_manager.saving:
			workers_needed -= 1

		if self.expPos and workers_needed <= 0 and self.state.creep[int(self.expPos.x), int(self.expPos.y)] == 0:
			#check to see if the area is clear of enemy before expanding.  If it is, move on to the next one.
			self._build_manager.last_build = 5
			await self.expand_now(location=self.expPos)
			self.can_spend = False



if __name__ == '__main__':
	try:
		run_game(maps.get(random.choice(allmaps)), [
		   Bot(Race.Protoss, AdditionalPylons()),
	#	   Bot(Race.Protoss, WorkerRushBot())
	#	   Bot(Race.Protoss, CannonRushBot())
		   Computer(_opponent, _difficulty)
		   ], realtime=_realtime)
	except Exception as e:
		print("type error: " + str(e))


