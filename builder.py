import random
import sc2
from sc2 import position
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2, Point3
from sc2.constants import *
from sc2.units import Units
'''
This class contains our build orders.


MORPH_WARPGATE = 1518
UPGRADETOWARPGATE_CANCEL = 1519
MORPH_GATEWAY = 1520
MORPHBACKTOGATEWAY_CANCEL = 1521
'''

_print_building = False

class Builder:
	
	def __init__(self, game):
		self.game = game
		self.basepylons = True
		self.pylon1Loc = None
		self.pylon2Loc = None
		self.pylon3Loc = None
		self.pylon4Loc = None
		self.pylon5Loc = None
		self.pylon6Loc = None
		self.pylon7Loc = None
		self.pylon8Loc = None
		self.pylon9Loc = None

		self.gateways = 0
		self.cores = 0
		self.stargates = 0
		self.forges = 0
		self.fleetbeacons = 0
		self.twilights = 0
		self.roboticsfacility = 0
		self.roboticsbay = 0
		self.cannons = 0
		self.darkshrines = 0
		self.templararchives = 0
		self.can_build_assimilators = False
		self.can_build_pylons = False
		self.bypass_assim_wait = False
		
		#individual build trigger.
		self.build_pylon1 = False
		self.build_pylon2 = False
		self.build_pylon3 = False
		self.build_pylon4 = False
		self.build_pylon5 = False
		self.build_pylon6 = False
		self.build_pylon7 = False
		self.build_pylon8 = False
		self.build_pylon9 = False		
		#building built
		self.pylon1_built = False
		self.pylon2_built = False
		self.pylon3_built = False
		self.pylon4_built = False
		self.pylon5_built = False
		self.pylon6_built = False
		self.pylon7_built = False
		self.pylon8_built = False
		self.pylon9_built = False
		self.last_pylon_check = 0
		#training save
		self.last_build = None
		
		
	async def build_any(self, game):
		self.game = game
		#check the status of our base pylons and replace them if needed.
		if self.game.time > self.last_pylon_check:
			self.last_pylon_check = self.game.time + 5
			self.check_pylons_exist()

		#reset training save
		self.last_build = None		
		
		#if we have no probes, might as well exit because we can't build anything.
		if self.game.units(PROBE).ready.amount == 0:
			return

		#build pylons.
		if self.canBuildPylon() and await self.buildPylon():
			self.game.can_spend = False
			return #built something, leave so cost doesn't mess up.

		#build cannons
		if self.canBuildCannon() and await self.buildCannon():
			self.game.can_spend = False
			return
		#build shields.
		if self.canBuildShield() and await self.buildShield():
			self.game.can_spend = False
			return

		if self.canBuildGateway() and await self.build_gateway():
			self.game.can_spend = False
			return
		if self.canBuildCore() and await self.build_cyberneticscore():
			self.game.can_spend = False
			return		
		if self.canBuildForge() and await self.build_forge():
			self.game.can_spend = False
			return


		#if we are under attack, then leave because we don't ned to build anything, we need to defend.
		if self.game.under_attack and self.game.minerals < 500:
			return				


		#always build assimilators if needed.
		if self.build_assimilators():
			self.game.can_spend = False
			return
		
		#build a stargate
		if self.canBuildStargate() and await self.build_stargate():
			self.game.can_spend = False
			return
		
		#build a robo
		if self.canBuildRobo() and await self.build_roboticsfacility():
			self.game.can_spend = False
			return

		if self.canBuildFleetBeacon() and await self.build_fleetbeacon():
			self.game.can_spend = False
			return
		if self.canBuildTwilight() and await self.build_twilightcouncil():
			self.game.can_spend = False
			return
		if self.canBuildRoboBay() and await self.build_roboticsbay():
			self.game.can_spend = False
			return
		if self.canBuildArchive() and await self.build_templararchive():
			self.game.can_spend = False
			return
		if self.canBuildShrine() and await self.build_darkshrine():
			self.game.can_spend = False
			return

		


###################
#Build base pylons#
###################
	async def buildPylon1(self):
		if self.build_pylon1 and self.pylon1Loc and self.game.can_afford(PYLON):
			worker = self.game.select_build_worker(self.pylon1Loc)
			if worker:
				location = await self.game.find_placement(PYLON, self.pylon1Loc.position)
				if location:
					self.game.combinedActions.append(worker.build(PYLON, location))
					self.build_pylon1 = False
					self.pylon1_built = True
					return True
				else:
					self.build_pylon1 = False
					self.pylon1_built = True
					return False					

	async def buildPylon2(self):
		if self.build_pylon2 and self.pylon2Loc and self.game.can_afford(PYLON):
			worker = self.game.select_build_worker(self.pylon2Loc)
			if worker:
				location = await self.game.find_placement(PYLON, self.pylon2Loc.position)
				if location:				
					self.game.combinedActions.append(worker.build(PYLON, location))
					self.build_pylon2 = False
					self.pylon2_built = True
					return True
				else:
					self.build_pylon2 = False
					self.pylon2_built = True
					return False

	async def buildPylon3(self):
		if self.build_pylon3 and self.pylon3Loc and self.game.can_afford(PYLON):
			worker = self.game.select_build_worker(self.pylon3Loc)
			if worker:
				location = await self.game.find_placement(PYLON, self.pylon3Loc.position)
				if location:				
					self.game.combinedActions.append(worker.build(PYLON, location))
					self.build_pylon3 = False
					self.pylon3_built = True
					return True
				else:
					self.build_pylon3 = False
					self.pylon3_built = True
					return False					

	async def buildPylon4(self):
		if self.build_pylon4 and self.pylon4Loc and self.game.can_afford(PYLON):
			worker = self.game.select_build_worker(self.pylon4Loc)
			if worker:
				location = await self.game.find_placement(PYLON, self.pylon4Loc.position)
				if location:				
					self.game.combinedActions.append(worker.build(PYLON, location))
					self.build_pylon4 = False
					self.pylon4_built = True
					return True
				else:
					self.build_pylon4 = False
					self.pylon4_built = True
					return False					

	async def buildPylon5(self):
		if self.build_pylon5 and self.pylon5Loc and self.game.can_afford(PYLON):
			worker = self.game.select_build_worker(self.pylon5Loc.position)
			if worker:
				location = await self.game.find_placement(PYLON, self.pylon5Loc.position)
				if location:				
					self.game.combinedActions.append(worker.build(PYLON, location))
					self.build_pylon5 = False
					self.pylon5_built = True
					return True
				else:
					self.build_pylon5 = False
					self.pylon5_built = True
					return False				

	async def buildPylon6(self):
		if self.build_pylon6 and self.pylon6Loc and self.game.can_afford(PYLON):
			worker = self.game.select_build_worker(self.pylon6Loc)
			if worker:
				location = await self.game.find_placement(PYLON, self.pylon6Loc.position)
				if location:				
					self.game.combinedActions.append(worker.build(PYLON, location))
					self.build_pylon6 = False
					self.pylon6_built = True
					return True
				else:
					self.build_pylon6 = False
					self.pylon6_built = True
					return False							

	async def buildPylon7(self):
		if self.build_pylon7 and self.pylon7Loc and self.game.can_afford(PYLON):
			worker = self.game.select_build_worker(self.pylon7Loc)
			if worker:
				location = await self.game.find_placement(PYLON, self.pylon7Loc.position)
				if location:				
					self.game.combinedActions.append(worker.build(PYLON, location))
					self.build_pylon7 = False
					self.pylon7_built = True
					return True
				else:
					self.build_pylon7 = False
					self.pylon7_built = True
					return False				

	async def buildPylon8(self):
		if self.build_pylon8 and self.pylon8Loc and self.game.can_afford(PYLON):
			worker = self.game.select_build_worker(self.pylon8Loc)
			if worker:
				location = await self.game.find_placement(PYLON, self.pylon8Loc.position)
				if location:				
					self.game.combinedActions.append(worker.build(PYLON, location))
					self.build_pylon8 = False
					self.pylon8_built = True
					return True
				else:
					self.build_pylon8 = False
					self.pylon8_built = True
					return False	

	async def buildPylon9(self):
		if self.build_pylon9 and self.pylon9Loc and self.game.can_afford(PYLON):
			worker = self.game.select_build_worker(self.pylon9Loc)
			if worker:
				location = await self.game.find_placement(PYLON, self.pylon9Loc.position)
				if location:				
					self.game.combinedActions.append(worker.build(PYLON, location))
					self.build_pylon9 = False
					self.pylon9_built = True
					return True
				else:
					self.build_pylon9 = False
					self.pylon9_built = True
					return False	

##################
#Can Build Checks#
##################

	def canBuildPylon(self):
		#check to see if pylons are being requested, if so - bypass the other checks and build them.
		if self.game.buildingList.pylonsRequested and (self.game._strat_manager.stage1complete or self.game.reaper_cheese) and self.game.can_afford(PYLON) and self.game.already_pending(PYLON) < self.game.buildingList.pylonsRequested:
			return True
		
		#check to see if we can build a pylon before calling it async.
		add_on = 4
		if self.game.supply_cap > 150:
			add_on = 20
		elif self.game.supply_cap > 125:
			add_on = 18
		elif self.game.supply_cap > 100:
			add_on = 15
		elif self.game.supply_cap > 50:
			add_on = 8
		elif self.game.supply_cap > 20:
			add_on = 6
			
		if self.can_build_pylons and self.game.supply_left < add_on and self.game.already_pending(PYLON) < 1 and not self.game.supply_cap >= 200 and self.game.units(NEXUS).amount > 0 and self.game.can_afford(PYLON):
			return True
		return False

	
	def canBuildStargate(self):
		if self.game.units(CYBERNETICSCORE).ready.exists and self.game.units(STARGATE).amount < self.stargates:
			if self.game.units(NEXUS).exists and self.game.can_afford(STARGATE) and not self.game.already_pending(STARGATE):
				return True
		return False
	
	def canBuildGateway(self):
		if (self.game.units(GATEWAY).amount + self.game.units(WARPGATE).amount) < self.gateways:
			if self.game.units(PYLON).exists and self.game.units(NEXUS).exists and self.game.can_afford(GATEWAY) and not self.game.already_pending(GATEWAY):
				return True
	
	def canBuildRobo(self):
		if self.game.units(CYBERNETICSCORE).ready.exists and len(self.game.units(ROBOTICSFACILITY)) < self.roboticsfacility:
			if self.game.units(NEXUS).exists and self.game.can_afford(ROBOTICSFACILITY) and not self.game.already_pending(ROBOTICSFACILITY):
				return True
		return False
	
	def canBuildCore(self):
		if self.game.units(GATEWAY).ready.exists and len(self.game.units(CYBERNETICSCORE)) < self.cores:
			if self.game.units(NEXUS).exists and self.game.can_afford(CYBERNETICSCORE) and not self.game.already_pending(CYBERNETICSCORE):
				return True
			
	def canBuildForge(self):
		if len(self.game.units(FORGE)) < self.forges and self.game.units(NEXUS).exists and self.game.units(PYLON).exists:
			if self.game.can_afford(FORGE) and not self.game.already_pending(FORGE):
				return True
	
	def canBuildFleetBeacon(self):
		if self.game.units(STARGATE).ready.exists and len(self.game.units(FLEETBEACON)) < self.fleetbeacons and self.game.units(NEXUS).exists:
			if self.game.can_afford(FLEETBEACON) and not self.game.already_pending(FLEETBEACON):
				return True

	def canBuildTwilight(self):
		if self.game.units(CYBERNETICSCORE).ready.exists and len(self.game.units(TWILIGHTCOUNCIL)) < self.twilights:
			if self.game.can_afford(TWILIGHTCOUNCIL) and not self.game.already_pending(TWILIGHTCOUNCIL):
				return True
	
	def canBuildRoboBay(self):
		if self.game.units(ROBOTICSFACILITY).ready.exists and len(self.game.units(ROBOTICSBAY)) < self.roboticsbay:
			if self.game.can_afford(ROBOTICSBAY) and not self.game.already_pending(ROBOTICSBAY):
				return True
	
	def canBuildArchive(self):
		if self.game.units(TWILIGHTCOUNCIL).ready.exists and len(self.game.units(TEMPLARARCHIVE)) < self.templararchives:
			if self.game.can_afford(TEMPLARARCHIVE) and not self.game.already_pending(TEMPLARARCHIVE):
				return True
	
	def canBuildShrine(self):
		if self.game.units(TWILIGHTCOUNCIL).ready.exists and self.game.units(DARKSHRINE).amount < self.darkshrines:
			if self.game.can_afford(DARKSHRINE) and not self.game.already_pending(DARKSHRINE):
				return True

	def canBuildShrine(self):
		if self.game.units(TWILIGHTCOUNCIL).ready.exists and self.game.units(DARKSHRINE).amount < self.darkshrines:
			if self.game.can_afford(DARKSHRINE) and not self.game.already_pending(DARKSHRINE):
				return True

	def canBuildCannon(self):
		if self.game.units(FORGE).ready.exists and self.game.can_afford(PHOTONCANNON) and not self.game.already_pending(PHOTONCANNON):
			return True

	def canBuildShield(self):
		if self.game.units(CYBERNETICSCORE).ready.exists and self.game.can_afford(SHIELDBATTERY) and not self.game.already_pending(SHIELDBATTERY):
			return True			
			
############################
#Do Actions Build functions#
############################
	def build_assimilators(self):
		if self.game.vespene < 750:
			if self.can_build_assimilators and (not self.game.already_pending(ASSIMILATOR) or self.bypass_assim_wait) and self.game.can_afford(ASSIMILATOR) and self.game.units(NEXUS).ready:
				nexus = self.game.units(NEXUS).ready.random
				vaspenes = self.game.state.vespene_geyser.closer_than(15.0, nexus)
				for vaspene in vaspenes:
					if not self.game.units(ASSIMILATOR).closer_than(1.0, vaspene).exists:
						worker = self.game.select_build_worker(vaspene.position)
						if worker:
							if _print_building:
								print ("Building Assimilator")
							self.last_build = 16
							self.game.combinedActions.append(worker.build(ASSIMILATOR, vaspene))
							return True
		return False



	async def buildPylon(self):
		#check to make sure probes exist.
		if len(self.game.units(PROBE)) == 0:
			return False #no probes!
		
		#first check to see if we have a pylon near the current defensive position.
		goto = self.game.buildingList.nextPylonLoc
		# if not goto and not self.check_pylon_loc(self.game.defensive_pos):
		# 	goto = self.game.defensive_pos
		if not goto:
			#check to see if we can get a free position from a nexus.
			goto = self.game.buildingList.nextFreePylonLoc
		if not goto:
			nexus = self.game.units(NEXUS).furthest_to(self.game.start_location)
			#find all the minerals near the nexus and place the pylons on the opposite side.
			if self.game.state.mineral_field.closer_than(15, nexus).exists:
				mf = self.game.state.mineral_field.closer_than(15, nexus).random
				xnew = nexus.position[0] + (nexus.position[0] - mf.position[0])
				ynew = nexus.position[1] + (nexus.position[1] - mf.position[1])
				goto = position.Point2(position.Pointlike((xnew,ynew)))
			else:
				return False
		#find placement and select worker.
		if goto:
			worker = self.game.select_build_worker(goto.position, force=True)
			if worker:
				placement = await self.game.find_placement(PYLON, goto)
				if placement:
					if _print_building:
						print ("Building Pylon")
					self.game.combinedActions.append(worker.build(PYLON, placement.position))
					self.last_build = 2
					return True
		return False


	async def build_pylons(self):
		#build our positioned pylons first.
		#if we are supply blocked, just build one.
		if self.game.supply_left > 10:

			if not self.pylon1_built:
				self.build_pylon1 = True
				return True
			if not self.pylon2_built:
				self.build_pylon2 = True
				return True
			if not self.pylon3_built:
				self.build_pylon3 = True
				return True
			if not self.pylon4_built:
				self.build_pylon4 = True
				return True
			if not self.pylon5_built:
				self.build_pylon5 = True
				return True
			
			
			if not self.pylon6_built:
				self.build_pylon6 = True
				return True
			
			if not self.pylon7_built:
				self.build_pylon7 = True
				return True
			
			if not self.pylon8_built:
				self.build_pylon8 = True
				return True
			
			if not self.pylon9_built:
				self.build_pylon9 = True
				return True
		
		#build the rest as far from the start location as possible.
		nexus = self.game.units(NEXUS).furthest_to(self.game.start_location)
		#make sure nexus is the original.
		if nexus.distance_to(self.game.start_location) > 10:
			#find all the minerals near the nexus and place the pylons on the opposite side.
			mf = self.game.state.mineral_field.closer_than(15, nexus).random
			xnew = nexus.position[0] + (nexus.position[0] - mf.position[0])
			ynew = nexus.position[1] + (nexus.position[1] - mf.position[1])
			goto = position.Point2(position.Pointlike((xnew,ynew)))
			#find placement and select worker.
			worker = self.game.select_build_worker(goto.position, force=True)
			if worker:
				placement = await self.game.find_placement(PYLON, goto)
				if placement:
					if _print_building:
						print ("Building Pylon")
					self.game.combinedActions.append(worker.build(PYLON, placement.position))
					self.last_build = 2
					return True
		return False

	async def build_stargate(self):
		#build them near pylon 4
		goto = self.buildingPlacement(self.pylon4Loc)
		if goto:
			worker = self.game.select_build_worker(goto.position, force=True)
			if worker:
				placement = await self.game.find_placement(STARGATE, goto.position)
				if placement:
					if _print_building:
						print ("Building Stargate")					
					self.game.combinedActions.append(worker.build(STARGATE, placement.position))
					self.last_build = 7
					return True			
		return False

	async def build_roboticsfacility(self):
		goto = self.buildingPlacement(self.pylon1Loc)
		if goto:
			worker = self.game.select_build_worker(goto.position, force=True)
			if worker:
				placement = await self.game.find_placement(ROBOTICSFACILITY, goto.position)
				if placement:
					if _print_building:
						print ("Building Robitics Facility")				
					self.game.combinedActions.append(worker.build(ROBOTICSFACILITY, placement.position))
					self.last_build = 6
					return True			
		return False



	async def build_gateway(self):
		#get position.
		goto = self.buildingPlacement(self.pylon3Loc)
		#place it
		if goto:
			worker = self.game.select_build_worker(goto.position, force=True)
			if worker:
				placement = await self.game.find_placement(GATEWAY, goto.position)
				if placement:
					if _print_building:
						print ("Building Gateway")				
					self.game.combinedActions.append(worker.build(GATEWAY, placement.position))
					self.last_build = 3
					return True					

	async def build_cyberneticscore(self):
		#place it near pylon3.
		goto = self.buildingPlacement(self.pylon4Loc)
		if goto:
			worker = self.game.select_build_worker(goto.position, force=True)
			if worker:
				placement = await self.game.find_placement(CYBERNETICSCORE, goto.position)
				if placement:
					if _print_building:
						print ("Building Cybernetics Core")				
					self.game.combinedActions.append(worker.build(CYBERNETICSCORE, placement.position))
					self.last_build = 4
					return True			

	async def build_forge(self):
		#place it near pylon2
		goto = self.buildingPlacement(self.pylon3Loc)
		if goto:
			worker = self.game.select_build_worker(goto.position, force=True)
			if worker:
				placement = await self.game.find_placement(FORGE, goto.position)
				if placement:
					if _print_building:
						print ("Building Forge")				
					self.game.combinedActions.append(worker.build(FORGE, placement.position))
					self.last_build = 13
					return True

	async def build_fleetbeacon(self):
		goto = self.buildingPlacement(self.pylon4Loc)
		if goto:
			worker = self.game.select_build_worker(goto.position, force=True)
			if worker:
				placement = await self.game.find_placement(FLEETBEACON, goto.position)
				if placement:
					if _print_building:
						print ("Building Fleet Beacon")
					self.last_build = 10
					self.game.combinedActions.append(worker.build(FLEETBEACON, placement.position))
					return True			
			
	async def build_twilightcouncil(self):
		goto = self.buildingPlacement(self.pylon3Loc)
		if goto:
			worker = self.game.select_build_worker(goto.position, force=True)
			if worker:
				placement = await self.game.find_placement(TWILIGHTCOUNCIL, goto.position)
				if placement:
					if _print_building:
						print ("Building Twilight Council")				
					self.game.combinedActions.append(worker.build(TWILIGHTCOUNCIL, placement.position))
					self.last_build = 8
					return True		

	async def build_roboticsbay(self):
		goto = self.buildingPlacement(self.pylon1Loc)
		if goto:
			worker = self.game.select_build_worker(goto.position, force=True)
			if worker:
				placement = await self.game.find_placement(ROBOTICSBAY, goto.position)
				if placement:
					if _print_building:
						print ("Building Robotics Bay")				
					self.game.combinedActions.append(worker.build(ROBOTICSBAY, placement.position))
					self.last_build = 9
					return True							

	async def build_templararchive(self):
		#place it near pylon2.
		goto = self.buildingPlacement(self.pylon4Loc)
		if goto:
			worker = self.game.select_build_worker(goto.position, force=True)
			if worker:
				placement = await self.game.find_placement(TEMPLARARCHIVE, goto.position)
				if placement:
					if _print_building:
						print ("Building Templar Archive")				
					self.game.combinedActions.append(worker.build(TEMPLARARCHIVE, placement.position))
					self.last_build = 11
					return True						

	async def build_darkshrine(self):
		#place it near pylon2.
		goto = self.buildingPlacement(self.pylon4Loc)
		if goto:
			worker = self.game.select_build_worker(goto.position, force=True)
			if worker:
				placement = await self.game.find_placement(DARKSHRINE, goto.position)
				if placement:
					if _print_building:
						print ("Building Dark Shrine")				
					self.game.combinedActions.append(worker.build(DARKSHRINE, placement.position))
					self.last_build = 12
					return True						

###########
#Utilities#
###########

	def buildingPlacement(self, pref_pylon):
		goto = None
		if self.check_pylon_loc(pref_pylon):
			#place the stargate from pos3 towards 9.
			goto = pref_pylon.position.towards(self.game.start_location.position, -9)
			
		else:
			if len(self.game.units(NEXUS)) > 0 and len(self.game.units(PYLON)) > 0:
				nexus = self.game.units(NEXUS).closest_to(self.game.start_location)
				goto = self.game.units(PYLON).closest_to(nexus).position.towards(nexus, -9)
		return goto

#################
#Maintain Pylons#
#################

	def check_pylons_exist(self):
		
		if self.game.already_pending(PYLON):
			return 
			#get the build progress of it.
			# if self.game.units(PYLON).not_ready:
			# 	if self.game.units(PYLON).not_ready.first.build_progress > 0:
			# 		cannon_build = True		
		
		
		if self.pylon1_built:
			if not self.check_pylon_loc(self.pylon1Loc, 3):
				self.pylon1_built = False
				self.build_pylon1 = True
		if self.pylon2_built:
			if not self.check_pylon_loc(self.pylon2Loc, 3):
				self.pylon2_built = False
				self.build_pylon2 = True
		if self.pylon3_built:
			if not self.check_pylon_loc(self.pylon3Loc, 3):
				self.pylon3_built = False
				self.build_pylon3 = True
		if self.pylon4_built:
			if not self.check_pylon_loc(self.pylon4Loc, 3):
				self.pylon4_built = False
				self.build_pylon4 = True
		if self.pylon5_built:
			if not self.check_pylon_loc(self.pylon5Loc, 3):
				self.pylon5_built = False
				self.build_pylon5 = True
		if self.pylon6_built:
			if not self.check_pylon_loc(self.pylon6Loc, 3):
				self.pylon6_built = False
				self.build_pylon6 = True
		if self.pylon7_built:
			if not self.check_pylon_loc(self.pylon7Loc, 3):
				self.pylon7_built = False
				self.build_pylon7 = True
		if self.pylon8_built:
			if not self.check_pylon_loc(self.pylon8Loc, 3):
				self.pylon8_built = False
				self.build_pylon8 = True
		if self.pylon9_built:
			if not self.check_pylon_loc(self.pylon9Loc, 3):
				self.pylon9_built = False
				self.build_pylon9= True


	async def buildCannon(self):
		#check to make sure probes exist.
		if len(self.game.units(PROBE)) == 0:
			return False #no probes!		
		goto = self.game.buildingList.nextCannonLoc
		# if not goto and self.check_pylon_loc(self.game.defensive_pos) and not self.check_cannon_loc(self.game.defensive_pos, searchrange=7):
		# 	#build cannon between pylon and nearest ramp.
		# 	goto = self.game.defensive_pos
		if goto:
			await self.game.build(PHOTONCANNON, near=goto)
			if _print_building:
				print ("Building Photon Cannon")
			self.last_build = 14
			return True
		return False
		
		
	async def buildShield(self):
		#check to make sure probes exist.
		if len(self.game.units(PROBE)) == 0:
			return False #no probes!		
		goto = self.game.buildingList.nextShieldLoc
		# if not goto and self.check_pylon_loc(self.game.defensive_pos) and not self.check_shield_loc(self.game.defensive_pos, searchrange=7):
		# 	goto = self.game.defensive_pos
		if goto:
			await self.game.build(SHIELDBATTERY, near=goto)
			if _print_building:
				print ("Building Shield Battery")
			self.last_build = 15
			return True
		return False		
		

	def check_pylon_loc(self, pylonloc, searchrange=7):
		#check if there is a pylon within  distance of the pylon loc.
		return self.game.units(PYLON).closer_than(searchrange, pylonloc).exists
	
	def check_cannon_loc(self, cannonloc, searchrange=4):
		return self.game.units(PHOTONCANNON).closer_than(searchrange, cannonloc).exists
	
	def check_shield_loc(self, shieldloc, searchrange=4):
		return self.game.units(SHIELDBATTERY).closer_than(searchrange, shieldloc).exists
	

#######################
#unorganized functions#
#######################
		
		
	async def build_shield_battery(self, nearPos):
		if self.game.units(CYBERNETICSCORE).ready.exists:
			if self.game.can_afford(SHIELDBATTERY):
				await self.game.build(SHIELDBATTERY, near=nearPos)
				if _print_building:
					print ("Building Shield Battery")
				self.last_build = 15
				return True
		return False
		
	async def build_photoncannon(self, nearPos):
		if self.game.units(FORGE).ready.exists:
			if self.game.can_afford(PHOTONCANNON):
				await self.game.build(PHOTONCANNON, near=nearPos)
				if _print_building:
					print ("Building Photon Cannon")
				self.last_build = 14
				return
			
	async def build_assimilator(self):
		if self.game.can_afford(ASSIMILATOR) and self.game.units(NEXUS).ready:
			nexus = self.game.units(NEXUS).ready.random
			vaspenes = self.game.state.vespene_geyser.closer_than(15.0, nexus)
			for vaspene in vaspenes:
				if not self.game.units(ASSIMILATOR).closer_than(1.0, vaspene).exists:
					worker = self.game.select_build_worker(vaspene.position)
					if worker:
						if _print_building:
							print ("Building Assimilator")						
						self.game.combinedActions.append(worker.build(ASSIMILATOR, vaspene))
						self.last_build = 16
						return
	
			


