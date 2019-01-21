import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3
from unit_counters import UnitCounter


_debug = False

class Nexus:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.label = 'Idle'
		self.unitCounter = UnitCounter()
		self.defending = False
		self.ineed_workers = False
	
		
		
	async def make_decision(self, game, unit):
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)

		await self.runList()

		#debugging info
		if _debug or self.unit.is_selected:
			self.game._client.debug_text_3d(self.label, self.unit.position3d)

	async def runList(self):
		#see if we can chronoboost anything.
		await self.chronoBoost()
		#check to make sure we aren't under attack, if we are trigger
		self.checkUnderAttack()
		#check to see if we need workers
		self.checkNeedWorkers()

		#check to see if saving resources are being requested.
		if self.resourcesSaved():
			self.label = 'Resources being saved'
			return
		
		#check to see if we need to build reaper cheese defense.
		await self.reaperCheeseDef()
		await self.generalDef()
			
		#build probes if we need them.
		if self.trainProbe():
			self.label = 'Training Unit'
			return
			
		#build a mothership if we can.
		if self.trainMothership():
			self.label = 'Training Unit'
			return		
		
		self.label = 'Idle'


	async def generalDef(self):
		#build a pylon and cannon in front of nexus to provide vision
		#make sure not in stage 1.
		if self.game.can_spend and self.game._strat_manager.stage1complete:
			#make see if there is a pylon near us.
			if not self.game.units(PYLON).closer_than(6, self.unit).exists:
				#if there is no pylon near us, put one in front of us.
				if self.game.can_afford(PYLON) and not self.game.already_pending(PYLON):
					mf = self.game.state.mineral_field.closer_than(15, self.unit)
					if len(mf) > 0:
						center_pos = Point2((sum([item.position.x for item in mf]) / len(mf), \
											sum([item.position.y for item in mf]) / len(mf)))
						goto = self.unit.position.towards(center_pos, -1.5)
						await self.game.build(PYLON, near=goto)
						self.game.can_spend = False
						return True
			#find cannons near us, build 1 if none exist.
			else:
				if not self.game.units(PHOTONCANNON).closer_than(12, self.unit).exists and self.game.units(PYLON).closer_than(6, self.unit).ready.exists and self.game.units(FORGE).ready.exists:
					if self.game.can_afford(PHOTONCANNON) and not self.game.already_pending(PHOTONCANNON):
						pylon = self.game.units(PYLON).closer_than(6, self.unit).ready.random
						await self.game.build(PHOTONCANNON, near=pylon)
						self.game.can_spend = False
						return True


	async def reaperCheeseDef(self):
		#if reaper cheese is detected, build cannons at the mineral lines.
		#only works on the starting nexus, need to rewrite for the rest.
		if self.game.can_spend and self.game.reaper_cheese and self.game.units(FORGE).ready.exists and self.unit.distance_to(self.game.start_location) < 5:
			if self.game.can_afford(PHOTONCANNON) and not self.game.already_pending(PHOTONCANNON):
				#put a cannon on p3 and p4.
				if self.game._build_manager.pylon3_built and self.game._build_manager.check_pylon_loc(self.game._build_manager.pylon3Loc, searchrange=3) and self.game.units(PHOTONCANNON).closer_than(3, self.game._build_manager.pylon3Loc).amount == 0:
					pylon = self.game.units(PYLON).closer_than(3, self.game._build_manager.pylon3Loc).random
					await self.game.build(PHOTONCANNON, near=pylon)
					self.game.can_spend = False

				if self.game._build_manager.pylon4_built and self.game._build_manager.check_pylon_loc(self.game._build_manager.pylon4Loc, searchrange=3) and self.game.units(PHOTONCANNON).closer_than(3, self.game._build_manager.pylon4Loc).amount == 0:
					pylon = self.game.units(PYLON).closer_than(3, self.game._build_manager.pylon4Loc).random
					await self.game.build(PHOTONCANNON, near=pylon)
					self.game.can_spend = False
					




	def trainMothership(self):
		#check to see if we are queued, if so, leave.
		if not self.unit.noqueue:
			return True
		#build the mothership if we can.
		if self.game.units(FLEETBEACON).ready.amount > 0 and self.game.units.not_structure.exclude_type([PROBE]).amount > 10 and self.game.can_afford(MOTHERSHIP) and self.game.supply_left > 8:
			self.game.combinedActions.append(self.unit.train(MOTHERSHIP))
			return True		

		
	def trainProbe(self):
		#check to see if we are queued, if so, leave.
		if not self.unit.noqueue:
			return True
		#check to see if workers are needed.
		if self.game.buildingList.workersRequested:
			#build worker, sent can_spend false.
			if self.game.rush_detected and self.game.units(GATEWAY).ready.exists:
				return False   #don't build probes.
			else:	
				if self.game.can_afford(PROBE) and self.game.supply_left > 0:
					self.game.combinedActions.append(self.unit.train(PROBE))
					self.game.can_spend = False
					return True
		
		
			
		
	
	def checkNeedWorkers(self):
		#find out if we need workers for the mineral lines.
		workers_needed = self.unit.ideal_harvesters - self.unit.assigned_harvesters
		#find out if we need workers for the assimilators.
		extra_workers = 0
		if self.game.units(ASSIMILATOR).ready.closer_than(10, self.unit).filter(lambda x: x.has_vespene):
			extra_workers = self.game.units(ASSIMILATOR).ready.closer_than(10, self.unit).filter(lambda x: x.has_vespene).amount * 2
		#add them together to find out how many total workers we need.
		total_workers_needed = self.unit.ideal_harvesters + extra_workers
		#count the probes around us and see if we have enough.
		ineed_workers = False
		if self.game.units(PROBE).closer_than(20, self.unit).amount < total_workers_needed:
			self.ineed_workers = True
		else:
			self.ineed_workers = False
	

				
		
	def resourcesSaved(self):
		if self.game._strat_manager.saving or not self.game.can_spend:
			return True
			

	def checkUnderAttack(self):
		if self.game.cached_enemies.closer_than(30, self.unit).amount > 0:
			self.defending = True
		else:
			self.defending = False			
			
		
	async def chronoBoost(self):
		if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in self.abilities:
			#check if research is being done and buff it if so.
			#cyberneticcore
			for core in self.game.units(CYBERNETICSCORE):
				if not core.noqueue and core.orders[0].progress < 0.75:
					self.game.combinedActions.append(self.unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, core))
					break
			#forge
			for forge in self.game.units(FORGE):
				if not forge.noqueue and forge.orders[0].progress < 0.75:
					self.game.combinedActions.append(self.unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, forge))
					break	
			#twilightcouncil
			for tw in self.game.units(TWILIGHTCOUNCIL):
				if not tw.noqueue and tw.orders[0].progress < 0.65:					
					self.game.combinedActions.append(self.unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, tw))
					break
			#roboticsbay
			for bay in self.game.units(ROBOTICSBAY):
				if not bay.noqueue and bay.orders[0].progress < 0.65:					
					self.game.combinedActions.append(self.unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, bay))
					break
				
			nexus_boost = False
			if not self.unit.noqueue:
				if self.unit.orders[0].ability.id == AbilityId.NEXUSTRAIN_PROBE and self.unit.orders[0].progress < 0.25:
					nexus_boost = True
				if self.unit.orders[0].ability.id == AbilityId.NEXUSTRAINMOTHERSHIP_MOTHERSHIP and self.unit.orders[0].progress < 0.75:
					nexus_boost = True
				if self.unit.orders[0].ability.id == AbilityId.NEXUSTRAINMOTHERSHIPCORE_MOTHERSHIPCORE and self.unit.orders[0].progress < 0.75:
					nexus_boost = True						
			
			if not self.unit.noqueue and nexus_boost and await self.game.can_cast(self.unit, AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, self.unit, cached_abilities_of_unit=self.abilities):
				self.game.combinedActions.append(self.unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, self.unit))
			else:
				for building in self.game.units.structure:
					if not building.noqueue and building.orders[0].progress < 0.35 and await self.game.can_cast(self.unit, AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, building, cached_abilities_of_unit=self.abilities):
						self.game.combinedActions.append(self.unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, building))
						break


	@property
	def underAttack(self) -> bool:
		return self.defending		
		
	@property
	def needWorkers(self) -> bool:
		return self.ineed_workers

		


	
	
	
	