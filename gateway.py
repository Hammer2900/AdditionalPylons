import random
import sc2
from sc2 import Race
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3
from unit_counters import UnitCounter


_debug = False

class Gateway:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.label = 'Idle'
		self.transform_started = False
		self.warpgate = False
		self.queued = False
		self.unitCounter = UnitCounter()
		self.trainList = ['Zealot', 'Stalker', 'Adept', 'Sentry', 'HighTemplar']

	async def make_decision(self, game, unit):
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)
		self.queueStatus()
		
		if unit.name == 'Gateway':
			self.warpgate = False
		else:
			self.warpgate = True
		
		if not self.queued:
			await self.runList()
		else:
			self.label = "Busy {}".format(str(len(self.abilities)))
		self.label += " {}".format(str(self.queued))
#		self.label += "- {}".format(str(unit.is_idle))
		#debugging info
		if _debug or self.unit.is_selected:
			self.game._client.debug_text_3d(self.label, self.unit.position3d)

	async def runList(self):

		#check to see if we can become a warpgate.
		if self.transformGate():
			self.label = 'Transforming to Warpgate'
			return

		#check to see if saving resources are being requested.
		if self.resourcesSaved():
			self.label = 'Resources being saved'
			return

		if await self.trainUnit():
			return
		
	
	async def trainUnit(self):
		#make sure we can spend.
		if not self.game.can_spend:
			self.label = 'No spending allowed'
			return
		#get unit to train
		trainee = self.bestTrain()
		if trainee:
			if self.warpgate:
				warpAbil = self.unitCounter.getWarpAbility(trainee)
				if warpAbil in self.abilities:
					placement = await self.warpgate_placement(warpAbil)
					if placement:
						self.game.combinedActions.append(self.unit.warp_in(self.unitCounter.getUnitID(trainee), placement))
						self.game.can_spend = False
						return True		
			else:
				self.game.combinedActions.append(self.unit.train(self.unitCounter.getUnitID(trainee)))
				self.game.can_spend = False
				return True

		
	def resourcesSaved(self):
		if self.game._strat_manager.saving:
			return True
	
	
	def transformGate(self):
		#see if we can train into a warpgate.
		#if self.game._science_manager._warpgate_researched:
		if self.game.buildingList.warpgateAvail:
			#warp if we can.
			if AbilityId.MORPH_WARPGATE in self.abilities:
				self.game.combinedActions.append(self.unit(AbilityId.MORPH_WARPGATE))
				self.transform_started = True
				return True
			#see if we are in the process of warping.
			if self.transform_started and not self.warpgate:
				if 'upgradetowarpgate' in str(self.unit.orders).lower():
					return True

		
	
	#utilities
	
	def queueStatus(self):
		if self.warpgate:
			if len(self.abilities) < 2 and (self.game.minerals > 100 or (self.game.vespene > 100 and self.game.minerals > 50)) and self.game.supply_left > 1:
				self.queued = True
			else:
				self.queued = False
		else:
			if self.unit.is_idle:
				self.queued = False
			else:
				self.queued = True		
			

	
	def canBuild(self, trainee):
		if self.game.can_afford(self.unitCounter.getUnitID(trainee)):
			#make sure we can actually build it and the core is finished.
			if self.game.enemy_race == Race.Terran and trainee == 'Zealot' and not self.game.units(CYBERNETICSCORE).ready.exists:
				return False #don't build zealots to start so we can get stalkers out sooner.
			#don't build a sentry before other units.
			
			if self.game._strat_manager.army_power == 0 and trainee == 'Sentry':
				return False
			
			if trainee != 'Zealot':
				if not self.game.units(CYBERNETICSCORE).ready.exists:
					return False
				if trainee == 'HighTemplar' and not self.game.units(TEMPLARARCHIVE).ready.exists:
					return False
			return True
		
	
	
	def bestTrain(self):
		bestName = None
		bestCount = -1
		bestNeeded = False
		for name, count in self.game._strat_manager.able_army.items():
			#check if its one of our types.
			if name in self.trainList:
				#check if it's needed or not.
				if self.game._strat_manager.check_allowed(name):
					bestNeeded = True
					if self.canBuild(name) and count > bestCount:
						bestName = name
						bestCount = count
		if bestName:
			self.label = "Best {}".format(bestName)
			return bestName
		if bestNeeded:
			self.label = 'need resources'
			return None
				
		#apparently couldn't build anything in the ideal list that is being allowed, check for anything to build.
		#if minerals are backing up, then go ahead and build anything.
		if self.game.minerals > 550:
			bestName = None
			bestCount = -1		
			for name, count in self.game._strat_manager.able_army.items():
				#check if its one of our types.
				if name in self.trainList:
					#check if it's needed or not.
					if self.canBuild(name):
						if count > bestCount:
							bestName = name
							bestCount = count
			if bestName:
				self.label = "2nd {}".format(bestName)
				return bestName
			
		self.label = 'Allowing resources elsewhere'
		return None	
	
	async def warpgate_placement(self, unit_ability):
		#todo: first, check for a warp prism in pylon mode.
		if not self.game.under_attack and len(self.game.units(WARPPRISMPHASING).ready) > 0:
			pos = self.game.units(WARPPRISMPHASING).ready.random.position.to2.random_on_distance(3)
			placement = await self.game.find_placement(unit_ability, pos, placement_step=1)
			if placement:
				return placement			

		#find super pylons and sort them closest to the enemy.
		#loop the pylons and find one that isn't in range of an enemy.
		#if no super pylons exist, find any pylon and do it again.
		closestEnemy = None
		if len(self.game.known_enemy_units) > 0:
			closestEnemy = self.game.known_enemy_units.closest_to(self.game.start_location)
		if closestEnemy and self.game.units(PYLON).ready.exists:
			if len(self.game.units.of_type([NEXUS, WARPGATE])) > 0:
	
				for building in self.game.units().of_type([NEXUS, WARPGATE]).ready.sorted(lambda x: x.distance_to(closestEnemy)):
					superPylons = self.game.units(PYLON).ready.closer_than(6, building)
					for pylon in superPylons:
						if len(self.game.cached_enemies.closer_than(12, pylon)) > len(self.game.units.exclude_type(PROBE).not_structure.closer_than(12, pylon)):
							#print ('skipping super', str(len(self.game.cached_enemies.closer_than(12, pylon))), str(len(self.game.units.exclude_type(PROBE).not_structure.closer_than(12, pylon))))
							continue
						else:
							#found a good pylon.
							pos = pylon.position.to2.random_on_distance(4)
							placement = await self.game.find_placement(unit_ability, pos, placement_step=1)
							if placement:
								#print ('super placement', str(len(self.game.cached_enemies.closer_than(12, pylon))), str(len(self.game.units.exclude_type(PROBE).not_structure.closer_than(12, pylon))))
								return placement
			#no valid super found, check all pylons.
			regPylons = self.game.units(PYLON).ready.sorted(lambda x: x.distance_to(closestEnemy))
			for pylon in regPylons:
				if len(self.game.cached_enemies.closer_than(12, pylon)) > len(self.game.units.exclude_type(PROBE).not_structure.closer_than(12, pylon)):
					#print ('skipping regular', str(len(self.game.cached_enemies.closer_than(12, pylon))), str(len(self.game.units.exclude_type(PROBE).not_structure.closer_than(12, pylon))))
					continue
				else:
					#found a good pylon.
					pos = pylon.position.to2.random_on_distance(4)
					placement = await self.game.find_placement(unit_ability, pos, placement_step=1)
					if placement:
						#print ('regular placement', str(len(self.game.cached_enemies.closer_than(12, pylon))), str(len(self.game.units.exclude_type(PROBE).not_structure.closer_than(12, pylon))))
						return placement
			#enemies must be around everywhere, just pick a random pylon and place it.
			pylon = self.game.units(PYLON).ready.random
			if pylon:
				pos = pylon.position.to2.random_on_distance(4)
				placement = await self.game.find_placement(unit_ability, pos, placement_step=1)
				if placement:
					#print ('random placement', str(len(self.game.cached_enemies.closer_than(12, pylon))), str(len(self.game.units.exclude_type(PROBE).not_structure.closer_than(12, pylon))))
					return placement
		else:
			#just place the unit closest to the defensive position.
			if len(self.game.units(PYLON).ready) > 0 and self.game.defensive_pos:
				pylon = self.game.units(PYLON).ready.closest_to(self.game.defensive_pos)
				if pylon:
					pos = pylon.position.to2.random_on_distance(4)
					placement = await self.game.find_placement(unit_ability, pos, placement_step=1)
					if placement:
						#print ('defensive placement')
						return placement
		return None	
	
	
	async def warpgate_placement_working(self, unit_ability):
		#todo: first, check for a warp prism in pylon mode.
		#second, check for proxy pylon.
		startPos = random.choice(self.game.enemy_start_locations)
		if not self.game.under_attack and not self.game.defend_only:
			pylon = self.game.units(PYLON).ready.closest_to(startPos.position)
			pos = pylon.position.to2.random_on_distance(4)
			placement = await self.game.find_placement(unit_ability, pos, placement_step=1)
			if placement:
				return placement
		
		#else warp them in near super pylons closest to enemies if around.		
		if self.game.units(PYLON).ready.exists and self.game.units(NEXUS).exists:
			#find the nexus we want to warp near.
			nexus = None
			if self.game.known_enemy_units.exists:
				nexus = self.game.units(NEXUS).ready.closest_to(self.game.known_enemy_units.closest_to(self.game.start_location))
			else:
				nexus = self.game.units(NEXUS).ready.closest_to(random.choice(self.game.enemy_start_locations))
			if nexus:
				#find a super pylon near the nexus.
				pylons = self.game.units(PYLON).ready.closer_than(6, nexus)
				for pylon in pylons:
					pos = pylon.position.to2.random_on_distance(4)
					placement = await self.game.find_placement(unit_ability, pos, placement_step=1)
					if placement:
						return placement
		return None		
		

	
	@property
	def inQueue(self) -> bool:
		return self.queued


		
		
		
		
		