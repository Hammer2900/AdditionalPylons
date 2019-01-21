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
from math import sqrt, sin, cos
from operator import itemgetter
from examples.protoss.cannon_rush import CannonRushBot
from examples.worker_rush import WorkerRushBot
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


_debug = False
_version = 'v0.820'
_exclude_list = {ADEPTPHASESHIFT,INTERCEPTOR,EGG,LARVA}

class AdditionalPylons(sc2.BotAI):
	def __init__(self):
		self.opp_id = self.findOppId()
		self._build_manager = buildControl(self)
		self._train_manager = trainControl()
		self._strat_manager = stratControl(self)
		self._training_data = trainingData()
		self.unitList = unitList()
		self.buildingList = buildingList()
		self._max_workers = 60
		self._defense_distance = 10
		self._next_status_gap = 30
		self._working_mines = 0
		self._upgrade_scout = False
		self._defend_enemies = []
		self._economic_update_gap = 1/2
		self._next_endgame_check = 120
		self._last_economic_update = 0
		self._emergency_units = 0
		self._wp_cargo = {}
		self._worker_assignments = {}
		self.hm_offset = None
		self.defend_only = True
		self.base_searched = False
		self.expPos = None
		self.warpgates_noqueue = False
		#z = self.ramp.height_at(pos)
		#worker rush variables.
		self.rush_detected = False
		self.update_workers = False
		self.reaper_cheese = False
		#end game variables.
		self.victory_detected = None
		self.defeat_detected = None
		#other
		self.proxy_pylon_loc = None
		self.worker_moved = None #the last time a worker moved.
		self.match_id = None
		self.opp_race = None
		self.map_name = None
		self.defensive_pos = None
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
		
	async def on_step(self, iteration):
		#realtime=True fix
		if self.last_iter == iteration:
			return
		self.last_iter = iteration		
		
		
		self.combinedActions = []
		#cache enemies for future calls.
		self.cache_enemies()
		self.check_movements()
		
		#put all effect positions to be dodged into a list.
		self.dodge_positions = []
		for effect in self.state.effects:
			if effect.id in [EffectId.LURKERMP, EffectId.RAVAGERCORROSIVEBILECP]:
				self.dodge_positions += effect.positions

		#say GL and give version info for debugging.
		if not self.intro_said and self.time > 10:
			await self._client.chat_send(self._strat_manager.unitCounter.getIntroSaying(), team_only=False)
			await self._client.chat_send(self.intro_value, team_only=False)
			self.intro_said = True

		
		self.allAbilities = await self.getAllAbilities()

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



		if self.time > self._next_endgame_check:
			await self.endGameCheck()		
			self._next_endgame_check = self.time + 1
			
		#first step stuff, move to function soon.
		if iteration == 0:
			#get the map name.
			self.map_name = "{}-{}-{}".format(self.game_info._proto.map_name, self.game_info.player_start_location.x, self.game_info.player_start_location.y)
			#get map width and height:
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
			self._training_data.loadData()
			#set the worker time as now.
			self.worker_moved = self.time
			#generate a unique id that will be used to identify this match.
			self.match_id = time.strftime("%y%m%d%H%M", time.gmtime())
			#find out which strat we want to use.
			self._strat_manager.strat_id = self._training_data.findStrat(self.opp_id, self.enemy_race, self.map_name)
			#self._strat_manager.strat_id = 5
			#print ('using strat:', self._strat_manager.strat_id)
			#save this as a victory in case the opponent crashes or leaves before we are able to log it.
			#get length of training data.
			trainingLen = len(self._training_data.data_dict.items())
			oppLen = self._training_data.totalOppDataCount(self.opp_id)
			trainingLen = self._training_data.totalDataCount()
			self._training_data.saveResult(self.opp_id, self._strat_manager.strat_id, 'w', self.match_id, self.enemy_race, self.map_name)
			self.intro_value = "You are playing vs {version}:{strat_id}.{olen}.{tlen}".format(version=_version, strat_id=self._strat_manager.strat_id, tlen=trainingLen, olen=oppLen)
			print (self.intro_value)
			#load up the units the opp used the last time.
			self.opp_unit_history = self._training_data.getOppHistory(self.opp_id)
			if self.opp_unit_history:
				#print (self.opp_unit_history)
				self.start_unit_ratio = self._strat_manager.calc_starter_counters(self.opp_unit_history)
			
			nexus = self.units(NEXUS).ready.random
			if nexus:
				hmval = self.getHeight(nexus.position)
				self.hm_offset = hmval - nexus.position3d.z - 1

			#get the map vals to be used.
			#self.get_mapvals()

		
		if self.time > self._next_worker_update:
			if not self.rush_detected: # or self.update_workers:
				if self.time > self.worker_moved:
					pass
					#await self.distribute_workers()
				self.update_workers = False			
			self._next_worker_update = self.time + 3
		
		if self.time > self._last_economic_update:
			self.expPos = self._get_next_expansion()
			self.checkAttack()
			await self.build_economy()
			self._last_economic_update = self.time + self._economic_update_gap
			#check if warpgates are available.
			await self.warpgatesReady()
					
		self.can_spend = True
		###strategist###
		await self._strat_manager.strat_control(self, self._build_manager, self._train_manager)
	
		###run independent buildings###
		await self.buildingList.make_decisions(self)

		###build#####
		if self.can_spend:
			await self._build_manager.build_any(self)

		###run all units###
		self.unitList.make_decisions(self)
		
		#cancel buildings that are being attacked and are low on health.
		self.cancelBuildings()
		
		if _debug:
			await self._client.send_debug()
			#time.sleep(300)
		await self.do_actions(self.combinedActions)

	def on_end(self, result):
		#self._training_data.saveResult(self.opp_id, 2, result)
		if 'Defeat' in str(result) and not self.defeat_detected:
			self._training_data.removeResult(self.opp_id, self.match_id)
	
	async def on_unit_destroyed(self, unit_tag):
		#remove enemy from intel if possible.
		self._strat_manager.remove_intel(unit_tag)
		#remove friend from unit list if possible.
		self.unitList.remove_object(unit_tag)
		#remove from expansion scout if matches.
		if self._strat_manager.expansion_scout == unit_tag:
			self._strat_manager.expansion_scout = None

	async def on_unit_created(self, unit):
		self.unitList.load_object(unit)
		
	async def on_building_construction_complete(self, unit):
		self.buildingList.load_object(unit)

			
	async def on_building_construction_started(self, unit):
		if unit.name == 'Nexus':
			self.getDefensivePoint()
		#detect nexus on start
		if self.last_iter < 3:
			self.buildingList.load_object(unit)

			
	def checkAttack(self):
		if self.buildingList.underAttack:
			self.under_attack = True
		else:
			self.under_attack = False


############
#micro code#
############

	def moveNearEnemies(self, unit_obj):
		#find the best target, similiar to attack, but in large range so we can move to targets if needed.
		targetEnemy = self.findBestMoveTarget(unit_obj)
		if targetEnemy:
			if unit_obj.checkNewAction('move', targetEnemy.position[0], targetEnemy.position[1]):
				if not unit_obj.unit.is_flying and unit_obj.unit.ground_range < 2:
					self.combinedActions.append(unit_obj.unit.attack(self.leadTarget(targetEnemy)))
				else:
					self.combinedActions.append(unit_obj.unit.attack(self.leadTarget(targetEnemy)))
			if unit_obj.unit.is_selected or _debug:
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
					self.combinedActions.append(unit_obj.unit.attack(self.leadTarget(closestEnemy)))
				return True
			else:
				return False
			

		if unit_obj.unit.can_attack_ground and not unit_obj.unit.can_attack_air:
			# can only attack ground units.
			#find enemy units that aren't structures first.
			if self.cached_enemies.not_structure.not_flying.exclude_type(_exclude_list).exists:
				closestEnemy = self.cached_enemies.not_structure.not_flying.exclude_type(_exclude_list).closest_to(unit_obj.unit.position)
				leadTarget = self.leadTarget(closestEnemy)
		
				unit_obj.last_target = Point3((leadTarget.position.x, leadTarget.position.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', leadTarget.position.x, leadTarget.position.y):
					self.combinedActions.append(unit_obj.unit.attack(leadTarget.position))
				return True
			#move to buildings, go to pylon first if they exist.
			if self.cached_enemies.of_type([PYLON]).exists:
				closestEnemy = self.cached_enemies.of_type([PYLON]).closest_to(unit_obj.unit.position)
				unit_obj.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
					self.combinedActions.append(unit_obj.unit.attack(closestEnemy))
				return True
			#move anything not flying
			if self.cached_enemies.not_flying.exclude_type(_exclude_list).exists:
				closestEnemy = self.cached_enemies.not_flying.exclude_type(_exclude_list).closest_to(unit_obj.unit.position)
				leadTarget = self.leadTarget(closestEnemy)
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
					self.combinedActions.append(unit_obj.unit.attack(self.leadTarget(closestEnemy)))
				return True				
			
			#attack anything
			if self.cached_enemies.flying.exclude_type(_exclude_list).exists:
				closestEnemy = self.cached_enemies.flying.exclude_type(_exclude_list).closest_to(unit_obj.unit.position)
				unit_obj.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
					self.combinedActions.append(unit_obj.unit.attack(self.leadTarget(closestEnemy)))
				return True		
		else:
			if self.cached_enemies.not_structure.exclude_type(_exclude_list).exists:
				closestEnemy = self.cached_enemies.not_structure.exclude_type(_exclude_list).closest_to(unit_obj.unit.position)
				unit_obj.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
					self.combinedActions.append(unit_obj.unit.attack(self.leadTarget(closestEnemy)))
				return True
			#now pylons
			if self.cached_enemies.of_type([PYLON]).exists:
				closestEnemy = self.cached_enemies.of_type([PYLON]).closest_to(unit_obj.unit.position)
				unit_obj.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
					self.combinedActions.append(unit_obj.unit.attack(closestEnemy))
				return True			
			
			if self.cached_enemies.exclude_type(_exclude_list).exists:
				closestEnemy = self.cached_enemies.exclude_type(_exclude_list).closest_to(unit_obj.unit.position)
				unit_obj.last_target = Point3((closestEnemy.position3d.x, closestEnemy.position3d.y, (closestEnemy.position3d.z + 1)))
				if unit_obj.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
					self.combinedActions.append(unit_obj.unit.attack(self.leadTarget(closestEnemy)))
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
				#print (item)
				#attack the destructable.
				#if unit_obj.checkNewAction('attack', item.position.x, item.position.y):
				unit_obj.game.combinedActions.append(unit_obj.unit.attack(item))
				unit_obj.last_target = None
				return True

		if self.defensive_pos and unit_obj.unit.distance_to(self.defensive_pos) > 5:
			if unit_obj.checkNewAction('move', self.defensive_pos.x, self.defensive_pos.y):
				unit_obj.game.combinedActions.append(unit_obj.unit.move(self.defensive_pos))
				unit_obj.last_target = None
			return True
		return False

	def keepSafe(self, unit_obj):
		#if it's a ground n
		danger = False		
		closestEnemy = self.dodgeEffects(unit_obj)
		if closestEnemy:
			danger = True
		else:
			#if unit_obj.unit.name == 'Probe': # or (self.defend_only and not self.under_attack):
			#	(danger, closestEnemy) = self.inDanger(unit_obj)
			#else:
			(danger, closestEnemy) = self.inDangerSimple(unit_obj)
			
		if danger:
			if unit_obj.unit.name == 'Probe':
				self.worker_moved = self.time + 3
			
			unit_obj.retreating = True
			#first just do a simple move if possible.
			retreatPoint = self.findSimpleRetreatPoint(unit_obj.unit, closestEnemy)
			if retreatPoint:
				#self.last_target = retreatPoint.position
				if unit_obj.checkNewAction('move', retreatPoint[0], retreatPoint[1]):
					self.combinedActions.append(unit_obj.unit.move(retreatPoint))
				if unit_obj.unit.is_selected or _debug:
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
				if unit_obj.unit.is_selected or _debug:
					self._client.debug_line_out(self.unitDebugPos(unit_obj.unit), self.p3AddZ(self.turn3d(closestEnemy.position)), color=Point3((216, 0, 101)))
					self._client.debug_line_out(self.unitDebugPos(unit_obj.unit), self.p2AddZ(retreatPoint), color=Point3((10, 2, 234)))					
				return True
		return False

	def KeepKiteRange(self, unit_obj, bonus_range=0):
		#kite if we can.	
		targetEnemy = self.findKiteTarget(unit_obj, bonus_range)
		if targetEnemy:
			if not (targetEnemy.can_attack_air or targetEnemy.can_attack_ground) and unit_obj.closestEnemies.filter(lambda x: x.can_attack_air or x.can_attack_ground).exists:
				#print ('found better kite target')
				return False #better targets out there.
			
			#kitePoint = unit_obj.unit.position.towards(targetEnemy.position, distance=-0.1)
			kitePoint = self.findKiteBackTarget(unit_obj, targetEnemy)
			if kitePoint:
				if unit_obj.checkNewAction('move', kitePoint[0], kitePoint[1]):
					self.combinedActions.append(unit_obj.unit.move(kitePoint))
					
				if unit_obj.unit.is_selected or _debug:
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

				if unit_obj.unit.is_selected or _debug:
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

	def moveToFriendlies(self, unit_obj):
		#if we are moving and no enemies exist, then we must be search, so return false.
		if unit_obj.unit.is_moving and self.cached_enemies.amount == 0:
			return False
		
		closestFriendly = None
		fUnits = self.units().not_structure.exclude_type([SENTRY,WARPPRISM]).filter(lambda x: x.can_attack_ground or x.can_attack_air)
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
				if unit_obj.unit.is_selected or _debug:
					unit_obj.last_target = Point3((closestFriendly.position3d.x, closestFriendly.position3d.y, (closestFriendly.position3d.z + 1)))
				return True
		return False	
		
	def getUnitEnemies(self, unit_obj):
		return self.cached_enemies.exclude_type(_exclude_list).closer_than(14, unit_obj.unit)

	def	canEscape(self, unit_obj):
		enemyThreatsClose = unit_obj.closestEnemies.filter(lambda x: x.target_in_range(unit_obj.unit)).sorted(lambda x: x.movement_speed, reverse=True)
		if enemyThreatsClose.exists:
			if unit_obj.unit.movement_speed < enemyThreatsClose.first.movement_speed:
				return False
		return True


#####################
#micro utlities code#
#####################


	def leadTarget(self, enemy):
		#get the point that is enemy speed in distance ahead of enemy, if the enemy is moving.
		#print ('moving', str(enemy.is_moving), enemy.position, enemy.facing, enemy.movement_speed)
		#self._client.debug_text_3d(str(enemy.facing), enemy.position3d)
		if self.unit_moves.get(enemy.tag):
			leadTarget = self.towardsDirection(enemy.position, enemy.facing, enemy.movement_speed)
			if _debug:
				self._client.debug_sphere_out(Point3((leadTarget.position.x, leadTarget.position.y, enemy.position3d.z + 1)), 1, Point3((66, 69, 244))) 
			return leadTarget
			
			#enemy.movement_speed
		else:
			#not moving, just return the current position
			return enemy.position
		
		

	def towardsDirection(self, p, direction, distance):
		#finds the point in front of unit that is distance ahead of it.
		return p.position + Point2((cos(direction), sin(direction))) * distance

	def findBestMoveTarget(self, unit_obj):
		enemyThreats = unit_obj.closestEnemies
		if unit_obj.unit.can_attack_ground and not unit_obj.unit.can_attack_air:
			enemyThreats = unit_obj.closestEnemies.not_flying
		elif unit_obj.unit.can_attack_air and not unit_obj.unit.can_attack_ground:
			enemyThreats = unit_obj.closestEnemies.flying
		
		#score the threats and pick the best one.
		if enemyThreats.exists:
			topscore = -1000
			topEnemy = None			
			for enemy in enemyThreats:
				score = 0
				dpsperhp = 0
				
				if (enemy.health + enemy.shield) > 0:
					if unit_obj.unit.is_flying:
						dpsperhp = enemy.air_dps / (enemy.health + enemy.shield)
					else:
						dpsperhp = enemy.ground_dps / (enemy.health + enemy.shield)
				#enemies that have range on us are the only real dps, so double their threat.
				if enemy.target_in_range(unit_obj.unit):
					dpsperhp = dpsperhp * 200
				else:
					dpsperhp = dpsperhp * 100

				score += dpsperhp
				#kill medivacs off first if at all possible.
				if enemy.name == 'Medivac':
					score += 300
				if enemy.name == 'SiegeTank':
					score += 300					
				if enemy.name == 'Interceptor':
					score = 0
				#distance to enemy matters.  Use % of max range distance, then subtract it from 100.
				if score > topscore:
					topscore = score
					topEnemy = enemy
				#units with energy in reserves deserve more score.
			return topEnemy
		
	def findEnergyTarget(self, unit_obj, ability_range):
		enemyThreats = unit_obj.closestEnemies.filter(lambda x: x.energy > 0).closer_than(ability_range, unit_obj.unit).sorted(lambda x: x.distance_to(unit_obj.unit))
		if enemyThreats.exists:
			return enemyThreats[0]

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
			topscore = -1000
			topEnemy = None			
			for enemy in enemyThreats:
				score = 0
				dpsperhp = 0
				
				if (enemy.health + enemy.shield) > 0:
					if unit_obj.unit.is_flying:
						dpsperhp = enemy.air_dps / (enemy.health + enemy.shield)
					else:
						dpsperhp = enemy.ground_dps / (enemy.health + enemy.shield)
				#enemies that have range on us are the only real dps, so double their threat.
				if enemy.target_in_range(unit_obj.unit):
					dpsperhp = dpsperhp * 200
				else:
					dpsperhp = dpsperhp * 100

				score += dpsperhp
				#kill medivacs off first if at all possible.
				if enemy.name == 'Medivac':
					score += 300
				if enemy.name == 'SiegeTank':
					score += 300						
				if enemy.name == 'Interceptor':
					score = 0
				#distance to enemy matters.  Use % of max range distance, then subtract it from 100.
				dist = enemy.distance_to(unit_obj.unit) - unit_obj.unit.radius - enemy.radius
				perc = 0
				if dist > 0:
					if unit_obj.unit.is_flying:
						perc = ((unit_obj.unit.air_range / dist) / 2)
					else:
						perc = ((unit_obj.unit.ground_range / dist) / 2)
						
				#if we are in their range, they are more dangerous, double distance score.
				score += perc
				#calculate their DPS per HP remaining.  The higher DPS per HP remaining, the more valuable.
				#show some debuging.
				# if _debug or unit.is_selected:
				# 	label = "{_score} {_dpsperhp} {_perc}".format(_score=str(score), _dpsperhp=str(dpsperhp), _perc=str(perc))
				# 	#print (label)
				# 	self._client.debug_text_3d(label, Point3((enemy.position3d.x, enemy.position3d.y, enemy.position3d.z + 1)))
				
				if score > topscore:
					topscore = score
					topEnemy = enemy
				#units with energy in reserves deserve more score.

				
			return topEnemy
		
	def findKiteBackTarget(self, unit_obj, enemy):
		#this version keeps us at their range plus some.
		
		enemy_attack_range = 0
		if unit_obj.unit.is_flying:
			enemy_attack_range = enemy.air_range
		else:
			enemy_attack_range = enemy.ground_range
		unit_attack_range = 0
		if unit_obj.unit.can_attack_ground and not enemy.is_flying:
			unit_attack_range = unit_obj.unit.ground_range
		elif unit_obj.unit.can_attack_air and enemy.is_flying:
			unit_attack_range = unit_obj.unit.air_range
		elif unit_obj.unit.can_attack_air:
			unit_attack_range = unit_obj.unit.air_range
		else:
			unit_attack_range = unit_obj.unit.ground_range
			
		use_range = unit_attack_range
		if enemy_attack_range > unit_attack_range and unit_attack_range == 0:
			use_range = enemy_attack_range + 1
		
		#check it has 0 range, then it's probably a building, so let's shorten things by 1 for better viewing and to enable more units behind us.
		if enemy_attack_range == 0:
			use_range -= 1
		
		
		#get the distance of the enemy - our attack range and move that far back.
		dist = unit_obj.unit.distance_to(enemy) - (unit_obj.unit.radius + enemy.radius + use_range)
		#move away from the target that much.
		if unit_obj.unit.position != enemy.position:
			targetpoint = unit_obj.unit.position.towards(enemy.position, distance=dist)
			#check to make sure the value of this box is greater than 2.  If it isn't, then find a new kite point.
			#if self.abovePathingScore(targetpoint):			
			return targetpoint
			#print ('bad targetpoint, need to find new one')
			# bestTargetPoint = self.findBestKiteTarget(targetpoint, enemy)
			# if bestTargetPoint:
			# 	#get  our attack range - the distance of the enemy and move that far back.
			# 	#different than above
			# 	dist = (unit_obj.unit.radius + enemy.radius + use_range) - unit_obj.unit.distance_to(enemy) 
			# 	targetpoint2 = unit_obj.unit.position.towards(bestTargetPoint, distance=dist)
			# 	return targetpoint2
			# 
			# #couldn't find a better targetpoint for some reason, go back to default.
			# return targetpoint			
			
			
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
		#enemyThreats = self.known_enemy_units.exclude_type([ADEPTPHASESHIFT]).in_attack_range_of(unit).sorted(lambda x: x.distance_to(unit))
		unit_range = unit_obj.unit.ground_range + bonus_range
		if unit_obj.unit.air_range > unit_obj.unit.ground_range:
			unit_range = unit_obj.unit.air_range + bonus_range
			
		if unit_obj.unit.name == 'Colossus':
			#any enemy that can attack ground or air.
			enemyThreats = unit_obj.closestEnemies.closer_than(9 + bonus_range, unit_obj.unit).filter(lambda x: x.can_attack_ground or x.can_attack_air).sorted(lambda x: x.distance_to(unit_obj.unit))
			if enemyThreats:
				return enemyThreats[0]			
		
		enemyThreats = unit_obj.closestEnemies.filter(lambda x: x.target_in_range(unit_obj.unit, bonus_distance=1 + bonus_range)).sorted(lambda x: x.distance_to(unit_obj.unit))
		#enemyThreats = self.known_enemy_units.exclude_type([ADEPTPHASESHIFT]).closer_than(unit_range, unit).filter(lambda x: x.target_in_range(unit)).sorted(lambda x: x.distance_to(unit))
		if enemyThreats:
			return enemyThreats[0]
		#if nothing has us in range, find out what we have in our range.
		enemyThreats = unit_obj.closestEnemies.filter(lambda x: unit_obj.unit.target_in_range(x, bonus_distance=bonus_range)).sorted(lambda x: x.distance_to(unit_obj.unit))
		#enemyThreats = self.known_enemy_units.exclude_type([ADEPTPHASESHIFT]).closer_than(unit_range, unit).filter(lambda x: x.target_in_range(unit)).sorted(lambda x: x.distance_to(unit))
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
		if len(self.dodge_positions) == 0:
			return False
		closestDodge = None
		closestDistance = 1000
		for position in self.dodge_positions:
			#get the distance to the position.
			dist = unit_obj.unit.distance_to(position)
			if dist < closestDistance:
				closestDodge = position
				closestDistance = dist
		if closestDistance < 2:
			return closestDodge
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
		if not unit_obj.unit.is_flying and enemyDPStoGround == 0 and unit_obj.unit.name != 'Colossus':
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
			targetpoint = unit.position.towards(enemy.position, distance=-2)
			return targetpoint	
		else:
			targetpoint = unit.position.towards(enemy.position, distance=-1)
			if not self.inPathingGrid(targetpoint):
				return None
			return targetpoint
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

	async def endGameCheck(self):
		#check if we are about to lose
		if not self.defeat_detected and self._strat_manager.checkDefeat() and self.cached_enemies.structure.amount > 0:
			self.defeat_detected = self.time + 10
			#print ('lost', self.defeat_detected)
			self._training_data.removeResult(self.opp_id, self.match_id)
			self._training_data.saveResult(self.opp_id, self._strat_manager.strat_id, 'l', self.match_id, self.enemy_race, self.map_name)
			if not self.gg_said:
				await self._client.chat_send(self._strat_manager.unitCounter.getLossSaying(), team_only=False)
				self.gg_said = True
			
			
		#check if we are not losing now.
		if self.defeat_detected and self.units.structure.amount >= 5:
			self.defeat_detected = None
			#print ('not dead yet')
			self._training_data.removeResult(self.opp_id, self.match_id)
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

	def getDefensivePoint(self):
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
				if unit.is_selected or _debug:
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
				if unit.is_selected or _debug:
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
				enemyThreats = self.cached_enemies.of_type([MEDIVAC]).in_attack_range_of(unit) #.closer_than(max_enemy_distance, unit)
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

	@property
	def main_ramp_bottom_center(self) -> Point2:
		pos = Point2((sum([p.x for p in self.main_base_ramp.lower]) / len(self.main_base_ramp.lower), \
			sum([p.y for p in self.main_base_ramp.lower]) / len(self.main_base_ramp.lower)))
		return pos
	
	#properties
	@property
	def trueGates(self) -> int:
		#total = self.units(GATEWAY).amount + self.units(WARPGATE).amount
		return self.units(GATEWAY).amount + self.units(WARPGATE).amount

	async def warpgatesReady(self):
		if self.units(WARPGATE).ready:
			abilities = await self.get_available_abilities(self.units(WARPGATE).ready)
			#print (abilities)
			for abilitylist in abilities:
				if len(abilitylist) > 1:
					self.warpgates_noqueue = True
					return					
		self.warpgates_noqueue = False

	@property
	def queuedGates(self) -> bool:
		if self.warpgates_noqueue:
			return False
		if self.units(GATEWAY).ready.noqueue:
			return False
		return True	
	
	@property
	def queuedStarGates(self) -> bool:
		if self.units(STARGATE).ready.noqueue.exists:
			return False
		return True	
		
	@property
	def allQueued(self) -> bool:
		if self.units(GATEWAY).ready.noqueue:
			return False
		if self.units(WARPGATE).ready.noqueue:
			return False
		if self.units(STARGATE).ready.noqueue.exists:
			return False
		if self.units(ROBOTICSFACILITY).ready.noqueue.exists:
			return False
		return True	
			
	
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
		if not self._strat_manager.stage1complete or self.minerals < 650 or not self.can_afford(NEXUS) or self.already_pending(NEXUS) or self.units(PROBE).amount == 0:
			return False
		if self.under_attack and self.minerals < 1000:
			return False
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
			
		if workers_needed <= 0 and self.state.creep[int(self.expPos.x), int(self.expPos.y)] == 0:
			#print ('expand', workers_needed)
			await self.expand_now(location=self.expPos)


#Bot(Race.Protoss, CannonRushBot())

if __name__ == '__main__':
	try:
		run_game(maps.get(random.choice(allmaps)), [
		   Bot(Race.Protoss, RuleMeBot()),
	#	   Bot(Race.Protoss, WorkerRushBot())	   
	#	   Bot(Race.Protoss, CannonRushBot())
		   Computer(_opponent, _difficulty)
		   ], realtime=_realtime)
	except Exception as e:
		print("type error: " + str(e))	
		
	
	