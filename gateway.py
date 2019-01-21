import random
import sc2
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
			if len(self.abilities) == 1 and self.game.minerals > 100 and self.game.supply_left > 1:
				self.queued = True
			else:
				self.queued = False
		else:
			if self.unit.noqueue:
				self.queued = False
			else:
				self.queued = True		
			

	
	def canBuild(self, trainee):
		if self.game.can_afford(self.unitCounter.getUnitID(trainee)):
			#make sure we can actually build it and the core is finished.
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
		#first, check for a warp prism in pylon mode.
		#second, check for proxy pylon.
		if not self.game.under_attack and not self.game.defend_only and self.game._build_manager.check_pylon_loc(self.game.proxy_pylon_loc):
			pylon = self.game.units(PYLON).ready.closer_than(6, self.game.proxy_pylon_loc).first
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


		
		
		
		
		