import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3
from sc2.units import Units
from unit_counters import UnitCounter
from math import sqrt, sin, cos


_debug = False

class Nexus:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.label = 'Idle'
		self.unitCounter = UnitCounter()
		self.defending = False
		self.ineed_workers = False
		self.main_base = False
		self.personal_cheese = False		
		#pylon locations
		self.p1 = None
		self.p2 = None
		self.p3 = None
		self.p4 = None
		self.p5 = None
		self.p6 = None		
		#debug locations
		self.mineral1 = None
		self.mineral2 = None
		#pylon communications
		self.pylons_needed = 0
		self.next_pylon_location = None
		#cannon communications
		self.cannons_needed = 0
		self.next_cannon_location = None
		#shield communications
		self.shields_needed = 0
		self.next_shield_location = None
		#first check
		self.firstframe = False
		self.overworked = False
		self.worker_allin = False
		
		
	async def make_decision(self, game, unit):
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)
		#add pylon locs if needed.
		if not self.firstframe:
			await self.pylonLocations()
			self.main_base = self.mainBaseCheck()
			self.firstframe = True
		#update our communication info.
		self.communicateNeeds()

		await self.runList()

		#debugging info
		if _debug or self.unit.is_selected:
			self.debugit()
			self.game._client.debug_text_3d(self.label, self.unit.position3d)


	async def runList(self):
		
		#if we are still warping in.
		if not self.unit.is_ready:
			#check for cannons near by and cancel as late as possible if true.
			if self.game.cached_enemies.filter(lambda x: x.type_id in {PHOTONCANNON} and x.distance_to(self.unit) < 9):
				#cannon has been found, leave opening stage.
				if not self.game._strat_manager.stage1complete:
					self.game._strat_manager.build.can_build_pylons = True
					self.game._strat_manager.build.can_build_assimilators = True
					self.game._strat_manager.stage1complete = True
					await self.game._client.chat_send(self.unitCounter.cannonRushSaying(), team_only=False)
				#wait until we are at least 95% finished, then cancel ourselves.
				if self.unit.build_progress >= 0.98:
					self.game.combinedActions.append(self.unit(CANCEL))
			return #warping in		
		
		
		self.checkUnderAttack()
		#check to see if we need workers
		self.checkNeedWorkers()
		#check for rush with workers.
		self.detectWorkerAllIn()

		#check to see if saving resources are being requested.
		if self.resourcesSaved():
			self.label = 'Resources being saved'
			return
		
		if self.recallDefense():
		 	self.label = 'Recalling'
		 	return
		#if self.main_base:
		# 	self.findRecallArmy(200)

		await self.chronoBoost()
		#check to make sure we aren't under attack, if we are trigger
		
		if self.game.can_spend:
			
			#build probes if we need them.
			if self.trainProbe():
				self.label = 'Training Unit'
				return
				
			#build a mothership if we can.
			if self.trainMothership():
				self.label = 'Training Unit'
				return		
		
		self.label = 'Idle'





	def recallDefense(self):
		#if we are under attack, count the power of the attacking army.
		if self.main_base and self.defending and self.unit.energy >= 50:
			near_enemies = self.game.cached_enemies.filter(lambda x: not x.name in ['Probe','Drone','SCV'] and (x.can_attack_ground or x.can_attack_air) and x.distance_to(self.unit) <= 40)
			def_enemies = near_enemies.closer_than(20, self.unit)
			score = self.game._strat_manager.score_rally(near_enemies)
			score2 = self.game._strat_manager.score_rally(def_enemies)
			#if we need more units, look to recall
			#make sure most of the enemy units are close.
			#if score2 >= score / 1.5:
			if score > 0:
				#enemies have moved in.
				#print ('enemies close enough for moving')
				#count the power of the army defending near us in a larger range.
				near_friends = self.game.units.filter(lambda x: not x.name in ['Probe'] and (x.can_attack_ground or x.can_attack_air) and x.distance_to(self.unit) <= 20)
				friend_score = self.game._strat_manager.score_rally(near_friends)
				score_needed = score / 1.25
				if friend_score <= score / 1.25:
					#print ('need more defense', score_needed)
					#look to see if we have units in the midfield, or attacking.
					self.findRecallArmy(score_needed)
					
					
				#else:
					#print ('above min:', score_needed)
				
				#print (str(self.unit.tag), str(len(near_friends)), friend_score)
				
			
			#see if there is a group of them in an area with enough power to defend.
			#recall those units to the nexus to defend.
			#print (str(self.unit.tag), str(len(near_enemies)), score, '-', str(len(def_enemies)), score2)
		

	def findRecallArmy(self, scoreMin):
		if self.game.defend_only and AbilityId.EFFECT_MASSRECALL_NEXUS in self.abilities:
			#score the army at the defensive position and see if stuff is there, if so, port it.
			near_friends = self.game.units.filter(lambda x: not x.name in ['Probe'] and (x.can_attack_ground or x.can_attack_air) and x.distance_to(self.game.defensive_pos) <= 2.5)
			score = self.game._strat_manager.score_rally(near_friends)
			#print ('recall scoring:', score, 'min', scoreMin)
			if score >= scoreMin:
				print ('recalling')
				#recall the units to our position.
				self.game.combinedActions.append(self.unit(AbilityId.EFFECT_MASSRECALL_NEXUS, self.game.defensive_pos))


	def findRecallArmyExp(self, scoreMin):
		#get the center of our fighting units.
		possibles = self.game.units.filter(lambda x: not x.is_structure
										   and not x.name in ['Probe']
										   and (x.can_attack_ground or x.can_attack_air)
										   and x.distance_to(self.unit) >= 30)
		if len(possibles) > 0:
			center = possibles.center
			self.game._client.debug_sphere_out(Point3((center.position.x, center.position.y, self.unit.position3d.z)), 2.5, Point3((66, 69, 244))) #blue
			#self.game._client.debug_text_3d('P1', Point3((self.p1.position.x, self.p1.position.y, self.unit.position3d.z)))
			print ('center', center)
			print (len(possibles))
					
		


	def detectWorkerAllIn(self):
		self.worker_allin = False
		if self.game.time > 480:
			return #too late in the game for a worker rush.
		#if we are under attack and if the enemy has brought a large number of workers, then we are being all-in rushed.
		if self.game.cached_enemies.exclude_type([PROBE,DRONE,SCV]).closer_than(20, self.unit).amount > 10:
			#under attack, see if workers are included.
			if self.game.cached_enemies.of_type([PROBE,DRONE,SCV]).closer_than(20, self.unit).amount > 10:
				self.worker_allin = True
		
		
		

	def detectPersonalCheese(self):
		self.personal_cheese = False
		return False
		if self.game.cached_enemies.of_type([REAPER,BANSHEE]).closer_than(20, self.unit).amount > 3:
			self.personal_cheese = True
			#self.reaperCheeseDef()
		else:
			self.personal_cheese = False			


	async def reaperCheeseDef(self):
		#if reaper cheese is detected, build cannons at the mineral lines.
		#only works on the starting nexus, need to rewrite for the rest.
		if self.game.can_spend and self.game.reaper_cheese and self.game.units(FORGE).ready.exists and self.personal_cheese:
			if self.game.can_afford(PHOTONCANNON) and not self.game.already_pending(PHOTONCANNON):
				#put a cannon on p3 and p4.
				if self.game._build_manager.check_pylon_loc(self.p3, searchrange=3) and self.game.units(PHOTONCANNON).closer_than(3, self.p3).amount == 0:
					pylon = self.game.units(PYLON).closer_than(3, self.p3).random
					await self.game.build(PHOTONCANNON, near=pylon)
					self.game.can_spend = False

				if self.game._build_manager.check_pylon_loc(self.p4, searchrange=3) and self.game.units(PHOTONCANNON).closer_than(3, self.p4).amount == 0:
					pylon = self.game.units(PYLON).closer_than(3, self.p4).random
					await self.game.build(PHOTONCANNON, near=pylon)
					self.game.can_spend = False
					
	def trainMothership(self):
		#check to see if we are queued, if so, leave.
		if not self.unit.is_idle:
			return True

		#only build when queues are full to maximize real military production
		if not self.game._strat_manager.allAllowedQueued:
			self.label = 'Building Military Instead'
			return
						
		#build the mothership if we can.
		if self.game.units(FLEETBEACON).ready.amount > 0 and self.game.units.not_structure.exclude_type([PROBE]).amount > 10 and self.game.can_afford(MOTHERSHIP) and self.game.supply_left > 8:
			self.game.combinedActions.append(self.unit.train(MOTHERSHIP))
			return True		

		
	def trainProbe(self):
		#check to see if we are queued, if so, leave.
		if not self.unit.is_idle:
			return True
		#check if it's the start of the game and we don't have a pylon yet.
		if self.game.time < 120 and self.game.units(PYLON).amount == 0 and self.game.units(PROBE).amount >= 13:
			return False #don't build another probe until we have a pylon out.
		
		#check to see if the probe will just die if it's made.
		if self.game.units(PROBE).amount < 5 and self.game.cached_enemies.closer_than(20, self.unit).amount > 5:
			return False #wait until things clear hopefully.
		
		if self.game.cached_enemies(PHOTONCANNON).closer_than(10, self.unit).amount > 0:
			return False #wait until cannon is cleared.
		
		
		#check to see if workers are needed.
		if self.game.buildingList.workersRequested:
			#build worker, sent can_spend false.
			if self.game.rush_detected and self.game.units(GATEWAY).ready.exists:
				return False   #don't build probes.
			else:	
				if self.game.can_afford(PROBE) and self.game.supply_left > 0 and self.game.units(PROBE).amount < self.game._max_workers:
					self.game.combinedActions.append(self.unit.train(PROBE))
					self.game.can_spend = False
					return True

	
	def checkNeedWorkers(self):
		#if we have no ideal workers, minerals are empty, we need nothing.
		if self.unit.ideal_harvesters == 0:
			self.ineed_workers = False
			return
		#find out if we need workers for the mineral lines.
		#workers_needed = self.unit.ideal_harvesters - self.unit.assigned_harvesters + 4
		#find out if we need workers for the assimilators.
		extra_workers = 0
		base_workers =16
		if self.game.already_pending(NEXUS):
			base_workers = 21
		if self.game.units(ASSIMILATOR).ready.closer_than(10, self.unit).filter(lambda x: x.has_vespene):
			extra_workers = self.game.units(ASSIMILATOR).ready.closer_than(10, self.unit).filter(lambda x: x.has_vespene).amount * 2
		#add them together to find out how many total workers we need.
		total_workers_needed = self.unit.ideal_harvesters + extra_workers
		#oversaturate at the start.
		if self.game.units(PROBE).amount < (base_workers + extra_workers):
			total_workers_needed = base_workers + extra_workers
		
		
		#count the probes around us and see if we have enough.
		#if there is a worker doing a nexus build, we don't need workers.
		ineed_workers = False
		if self.game.unitList.nexusBuilderAssigned:
			return

		if self.game.units(PROBE).closer_than(20, self.unit).amount < total_workers_needed:
			#do a check to make sure workers aren't long distance mining giving us less.
			if (len(self.game.units(NEXUS).ready) * (base_workers + extra_workers)) >= len(self.game.units(PROBE)):
				self.ineed_workers = True
				self.overworked = False
		else:
			if self.game.units(PROBE).closer_than(20, self.unit).amount >= total_workers_needed:
				self.ineed_workers = False
				self.overworked = True
		

				
		
	def resourcesSaved(self):
		if self.game._strat_manager.saving or not self.game.can_spend:
			return True
			

	def checkUnderAttack(self):
		if self.game.cached_enemies.exclude_type([PROBE,DRONE,SCV,OVERLORD]).closer_than(30, self.unit).amount > 0:
			self.defending = True
		else:
			self.defending = False			


	def mainBaseCheck(self):
		if self.unit.distance_to(self.game.game_info.player_start_location) < 6:
			return True
		return False			
		
	async def chronoBoost(self):
		if self.game.time < 120 and self.game.units(PYLON).amount == 0:
			return False #don't boost until we have a pylon out.
		#if it's beyond 5 minutes into the game, save for a recall.
		if self.main_base and self.game.time > 300 and self.unit.energy < 100:
			return False
		
		if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in self.abilities:
			#check if research is being done and buff it if so.
			#cyberneticcore
			#if we are being attacked early in game, do the gateway first to get the unit out faster.
			if self.game.cached_enemies.of_type([REAPER]).closer_than(40, self.unit).amount > 0:
				for gateway in self.game.units(GATEWAY):
					if not gateway.is_idle and gateway.orders[0].progress < 0.75 and not gateway.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
						self.game.combinedActions.append(self.unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, gateway))
						return True				
		
			for core in self.game.units(CYBERNETICSCORE):
				if not core.is_idle and core.orders[0].progress < 0.75 and not core.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
					self.game.combinedActions.append(self.unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, core))
					return True
			#forge
			for forge in self.game.units(FORGE):
				if not forge.is_idle and forge.orders[0].progress < 0.75 and not forge.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
					self.game.combinedActions.append(self.unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, forge))
					return True	
			#twilightcouncil
			for tw in self.game.units(TWILIGHTCOUNCIL):
				if not tw.is_idle and tw.orders[0].progress < 0.65 and not tw.has_buff(BuffId.CHRONOBOOSTENERGYCOST):					
					self.game.combinedActions.append(self.unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, tw))
					return True
			#roboticsbay
			for bay in self.game.units(ROBOTICSBAY):
				if not bay.is_idle and bay.orders[0].progress < 0.65 and not bay.has_buff(BuffId.CHRONOBOOSTENERGYCOST):					
					self.game.combinedActions.append(self.unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, bay))
					return True
				
			nexus_boost = False
			if not self.unit.is_idle and not self.unit.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
				if self.unit.orders[0].ability.id == AbilityId.NEXUSTRAIN_PROBE and self.unit.orders[0].progress < 0.25 and self.needWorkers:
					nexus_boost = True
				if self.unit.orders[0].ability.id == AbilityId.NEXUSTRAINMOTHERSHIP_MOTHERSHIP and self.unit.orders[0].progress < 0.75:
					nexus_boost = True
			
			
			if not self.unit.is_idle and nexus_boost and await self.game.can_cast(self.unit, AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, self.unit, cached_abilities_of_unit=self.abilities):
				self.game.combinedActions.append(self.unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, self.unit))
			else:
				for building in self.game.units.structure:
					if not building.is_idle and building.orders[0].progress < 0.35 and await self.game.can_cast(self.unit, AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, building, cached_abilities_of_unit=self.abilities) and not building.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
						self.game.combinedActions.append(self.unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, building))
						return True

	async def pylonLocations(self):
		#find positions around the nexus for pylons, cannons and shields.
		#front = self.unit.position + Point2((cos(self.unit.facing), sin(self.unit.facing))) * 2
		
		#find the edge of the minerals around us.
		if self.game.state.mineral_field.closer_than(15, self.unit):
			
			mins = self.game.state.mineral_field.closer_than(15, self.unit)
			vasp = self.game.state.vespene_geyser.closer_than(15, self.unit)
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
			
			
			self.mineral1 = mineral_1
			self.mineral2 = mineral_2
			
			nf = [mineral_1, mineral_2]
			if len(nf) == 0:
				return
			center_pos = Point2((sum([item.position.x for item in nf]) / len(nf), \
					sum([item.position.y for item in nf]) / len(nf)))
			nexdis = self.unit.distance_to(center_pos)
			fmost = mf.furthest_to(center_pos)
			
	
			self.p1 = self.unit.position.towards(center_pos, -5.5)
			self.p2 = self.unit.position.towards(center_pos, 7)
			self.p3 = fmost.position.towards(self.p1, (3))
			fclose = mf.furthest_to(self.p3)
			self.p4 = fclose.position.towards(self.p1, (3))
			
			self.p5 = self.unit.position.towards(self.midpoint(self.p1, self.p4), 9)
			self.p6 = self.unit.position.towards(self.midpoint(self.p1, self.p3), 9)			

	def communicateNeeds(self):
		#if we are warping in, we don't need anything.
		if not self.unit.is_ready:
			return False

		#check the pylons and see if we need any.
		#by default build pylon 1, then 3, then 4.
		#build pylon 2 if cheese is detected.
		pylons_needed = 0
		self.next_pylon_location = None

		if not self.game._build_manager.check_pylon_loc(self.p6, searchrange=4):
			self.next_pylon_location = self.p6
			
		if not self.game._build_manager.check_pylon_loc(self.p5, searchrange=4):
			self.next_pylon_location = self.p5

		if not self.game._build_manager.check_pylon_loc(self.p4, searchrange=4):
			if self.main_base or self.personal_cheese:
				pylons_needed += 1
			self.next_pylon_location = self.p4
			
		if not self.game._build_manager.check_pylon_loc(self.p3, searchrange=4):
			if self.main_base or self.personal_cheese:
				pylons_needed += 1
			self.next_pylon_location = self.p3
			
		if not self.game._build_manager.check_pylon_loc(self.p1, searchrange=4):
			pylons_needed += 1
			self.next_pylon_location = self.p1
			#add 1 pylon needed

		if self.personal_cheese and not self.game._build_manager.check_pylon_loc(self.p2, searchrange=4):
			pylons_needed += 1
			self.next_pylon_location = self.p2

		self.pylons_needed = pylons_needed
		
		#cannon communications.
		#should always build 1 cannon near pylon 1 for detection and front defense.
		cannons_needed = 0
		if self.game.time > 90 and not self.game._build_manager.check_cannon_loc(self.p1) and self.game._build_manager.check_pylon_loc(self.p1, searchrange=4):
			cannons_needed += 1
			self.next_cannon_location = self.p1

		if self.personal_cheese and not self.game._build_manager.check_cannon_loc(self.p3) and self.game._build_manager.check_pylon_loc(self.p3, searchrange=4):
			cannons_needed += 1
			self.next_cannon_location = self.p3
			
		if self.personal_cheese and not self.game._build_manager.check_cannon_loc(self.p4) and self.game._build_manager.check_pylon_loc(self.p1, searchrange=4):
			cannons_needed += 1
			self.next_cannon_location = self.p4		
		self.cannons_needed = cannons_needed
		
		#shield communications.
		shields_needed = 0
		if self.personal_cheese and not self.game._build_manager.check_shield_loc(self.p2):
			shields_needed += 1
			self.next_shield_location = self.p2
		self.shields_needed = shields_needed

	def midpoint(self, pos1, pos2):
		return Point2(((pos1.position.x + pos2.position.x) / 2, (pos1.position.y + pos2.position.y) /2))		
		

	def debugit(self):
		#base pylon 1 position. 
		self.game._client.debug_sphere_out(Point3((self.p1.position.x, self.p1.position.y, self.unit.position3d.z)), 1, Point3((66, 69, 244))) #blue
		self.game._client.debug_text_3d('P1', Point3((self.p1.position.x, self.p1.position.y, self.unit.position3d.z)))

		#base pylon 2 position. 
		self.game._client.debug_sphere_out(Point3((self.p2.position.x, self.p2.position.y, self.unit.position3d.z)), 1, Point3((66, 69, 244))) #blue
		self.game._client.debug_text_3d('P2', Point3((self.p2.position.x, self.p2.position.y, self.unit.position3d.z)))

		#base pylon 3 position. 
		self.game._client.debug_sphere_out(Point3((self.p3.position.x, self.p3.position.y, self.unit.position3d.z)), 1, Point3((66, 69, 244))) #blue
		self.game._client.debug_text_3d('P3', Point3((self.p3.position.x, self.p3.position.y, self.unit.position3d.z)))

		#base pylon 4 position. 
		self.game._client.debug_sphere_out(Point3((self.p4.position.x, self.p4.position.y, self.unit.position3d.z)), 1, Point3((66, 69, 244))) #blue
		self.game._client.debug_text_3d('P4', Point3((self.p4.position.x, self.p4.position.y, self.unit.position3d.z)))
		
		self.game._client.debug_sphere_out(self.mineral1.position3d, 1, Point3((66, 69, 244)))
		self.game._client.debug_sphere_out(self.mineral2.position3d, 1, Point3((66, 69, 244)))		
		
	@property
	def underAttack(self) -> bool:
		return self.defending
	
	@property
	def underWorkerAllin(self) -> bool:
		return self.worker_allin
		
	@property
	def needWorkers(self) -> bool:
		return self.ineed_workers
	
	@property
	def overWorked(self) -> bool:
		return self.overworked

	@property
	def pylonsRequested(self) -> int:
		return self.pylons_needed
	
	@property
	def nextPylonPosition(self) -> Point2:
		return self.next_pylon_location
	
	@property
	def cannonsRequested(self) -> int:
		return self.cannons_needed
	
	@property
	def nextCannonPosition(self) -> Point2:
		return self.next_cannon_location
	
	@property
	def shieldsRequested(self) -> int:
		return self.shields_needed
	
	@property
	def nextShieldPosition(self) -> Point2:
		return self.next_shield_location
		

		


	
	
	
	