import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
'''
This class carried out build orders previously, variables left in case for now.

'''

_print_unit_training = False

class Trainer:

	def __init__(self):
		self.allow_voidrays = False
		self.allow_tempests = False
		self.allow_phoenix = False
		self.allow_zealots = False
		self.allow_stalkers = False
		self.allow_immortals = False
		self.allow_warpprisms = False
		self.allow_sentrys = False
		self.allow_observers = False
		self.allow_colossus = False
		self.allow_adepts = False
		self.allow_hightemplars = False
		self.allow_disruptors = False
		self.allow_carriers = False
		self.allow_mothership = False
	
	async def train_all(self, game):
		self.game = game
	# 
	# 	# if await self.train_hightemplar():
	# 	# 	self.game.can_spend = False
	# 	# 	return
	# 	
	# 	# if self.train_observer():
	# 	# 	self.game.can_spend = False
	# 	# 	return		
	# 	# 
	# 	# if self.train_colossus():
	# 	# 	self.game.can_spend = False
	# 	# 	return
	# 	# if self.train_tempest():
	# 	# 	self.game.can_spend = False
	# 	# 	return
	# 	# if await self.train_stalker():
	# 	# 	self.game.can_spend = False
	# 	# 	return
	# 	# if self.train_voidray():
	# 	# 	self.game.can_spend = False
	# 	# 	return
	# 	# if self.train_phoenix():
	# 	# 	self.game.can_spend = False
	# 	# 	return
	# 	# if self.train_immortal():
	# 	# 	self.game.can_spend = False
	# 	# 	return
	# 	# if self.train_warpprism():
	# 	# 	self.game.can_spend = False
	# 	# 	return
	# 	# if await self.train_adept():
	# 	# 	self.game.can_spend = False
	# 	# 	return
	# 	# if await self.train_sentry():
	# 	# 	self.game.can_spend = False
	# 	# 	return		
	# 	# if await self.train_zealot():
	# 	# 	self.game.can_spend = False
	# 	# 	return
	# 	# if self.train_disruptor():
	# 	# 	self.game.can_spend = False
	# 	# 	return
	# 	# if self.train_carrier():
	# 	# 	self.game.can_spend = False
	# 	# 	return
	# 	# if self.train_mothership():
	# 	# 	self.game.can_spend = False
	# 	# 	return
	# 	
	# def train_mothership(self):
	# 	if self.allow_mothership and self.game.units(FLEETBEACON).ready.exists and self.game.units(NEXUS).ready.noqueue.exists:
	# 		if self.game.can_afford(MOTHERSHIP) and self.game.supply_left > 8:
	# 			nexus = self.game.units(NEXUS).ready.noqueue.random
	# 			self.game.combinedActions.append(nexus.train(MOTHERSHIP))
	# 			if _print_unit_training:				
	# 				print ("Training Mothership")
	# 			return True				
	# 	
	# def train_carrier(self):
	# 	if self.allow_carriers:
	# 		if self.game.units(STARGATE).ready.noqueue.exists and self.game.units(FLEETBEACON).ready.exists:
	# 			if self.game.can_afford(CARRIER) and self.game.supply_left > 6:
	# 				sg = self.game.units(STARGATE).ready.noqueue.random
	# 				self.game.combinedActions.append(sg.train(CARRIER))
	# 				if _print_unit_training:				
	# 					print ("Training Carrier")
	# 				return True
	# 	return False
	# 
	# def train_disruptor(self):
	# 	if self.allow_disruptors:
	# 		if self.game.units(ROBOTICSFACILITY).ready.noqueue.exists and self.game.units(ROBOTICSBAY).ready.exists:
	# 			if self.game.can_afford(DISRUPTOR) and self.game.supply_left >= 6:
	# 				rf = self.game.units(ROBOTICSFACILITY).ready.noqueue.random
	# 				self.game.combinedActions.append(rf.train(DISRUPTOR))
	# 				if _print_unit_training:
	# 					print ("Training Disruptor")
	# 				return True
	# 	return False		
	# 
	# async def warpgate_placement(self, unit_ability):
	# 	#first, check for a warp prism in pylon mode.
	# 	#second, check for proxy pylon.
	# 	if not self.game.under_attack and not self.game.defend_only and self.game._build_manager.check_pylon_loc(self.game.proxy_pylon_loc):
	# 		pylon = self.game.units(PYLON).ready.closer_than(6, self.game.proxy_pylon_loc).first
	# 		pos = pylon.position.to2.random_on_distance(4)
	# 		placement = await self.game.find_placement(unit_ability, pos, placement_step=1)
	# 		if placement:
	# 			return placement			
	# 	
	# 	#else warp them in near super pylons closest to enemies if around.		
	# 	if self.game.units(PYLON).ready.exists and self.game.units(NEXUS).exists:
	# 		#find the nexus we want to warp near.
	# 		nexus = None
	# 		if self.game.known_enemy_units.exists:
	# 			nexus = self.game.units(NEXUS).ready.closest_to(self.game.known_enemy_units.closest_to(self.game.start_location))
	# 		else:
	# 			nexus = self.game.units(NEXUS).ready.closest_to(random.choice(self.game.enemy_start_locations))
	# 		if nexus:
	# 			#find a super pylon near the nexus.
	# 			pylons = self.game.units(PYLON).ready.closer_than(6, nexus)
	# 			for pylon in pylons:
	# 				pos = pylon.position.to2.random_on_distance(4)
	# 				placement = await self.game.find_placement(unit_ability, pos, placement_step=1)
	# 				if placement:
	# 					return placement
	# 	return None
	# 
	# async def train_hightemplar(self):
	# 	if self.allow_hightemplars:
	# 		if self.game.units(WARPGATE).ready.noqueue.exists and self.game.units(TEMPLARARCHIVE).ready.exists:
	# 			if self.game.can_afford(HIGHTEMPLAR) and self.game.supply_left > 0:
	# 				wg = self.game.units(WARPGATE).ready.noqueue.random
	# 				#abilities = await self.game.get_available_abilities(wg)
	# 				abilities = self.game.allAbilities.get(wg.tag)
	# 				if AbilityId.WARPGATETRAIN_HIGHTEMPLAR in abilities:
	# 					#find the closest pylon to enemy.
	# 					placement = await self.warpgate_placement(AbilityId.WARPGATETRAIN_HIGHTEMPLAR)
	# 					if placement:
	# 						self.game.combinedActions.append(wg.warp_in(HIGHTEMPLAR, placement))
	# 						if _print_unit_training:
	# 							print ("Training High Templar")
	# 						return True
	# 		
	# 		if self.game.units(GATEWAY).ready.noqueue.exists and self.game.units(TEMPLARARCHIVE).ready.exists:
	# 			if self.game.can_afford(HIGHTEMPLAR) and self.game.supply_left > 0:
	# 				gw = self.game.units(GATEWAY).ready.noqueue.random
	# 				self.game.combinedActions.append(gw.train(HIGHTEMPLAR))
	# 				if _print_unit_training:
	# 					print ("Training High Templar")
	# 				return True
	# 	return False	
	# 	
	# def train_colossus(self):
	# 	if self.allow_colossus:
	# 		if self.game.units(ROBOTICSFACILITY).ready.noqueue.exists and self.game.units(ROBOTICSBAY).ready.exists:
	# 			if self.game.can_afford(COLOSSUS) and self.game.supply_left >= 6:
	# 				rf = self.game.units(ROBOTICSFACILITY).ready.noqueue.random
	# 				self.game.combinedActions.append(rf.train(COLOSSUS))
	# 				if _print_unit_training:
	# 					print ("Training Colossus")
	# 				return True
	# 	return False
	# 
	# async def train_adept(self):
	# 	if self.allow_adepts:
	# 		if self.game.units(WARPGATE).ready.noqueue.exists:
	# 			if self.game.can_afford(ADEPT) and self.game.supply_left > 0:
	# 				wg = self.game.units(WARPGATE).ready.noqueue.random
	# 				abilities = self.game.allAbilities.get(wg.tag)
	# 				#abilities = await self.game.get_available_abilities(wg)
	# 				if AbilityId.TRAINWARP_ADEPT in abilities:
	# 					#find the closest pylon to enemy.
	# 					placement = await self.warpgate_placement(AbilityId.TRAINWARP_ADEPT)
	# 					# pylon = self.game.units(PYLON).ready.closest_to(random.choice(self.game.enemy_start_locations))
	# 					# pos = pylon.position.to2.random_on_distance(4)
	# 					# placement = await self.game.find_placement(AbilityId.TRAINWARP_ADEPT, pos, placement_step=1)
	# 					if placement:
	# 						self.game.combinedActions.append(wg.warp_in(ADEPT, placement))
	# 						if _print_unit_training:
	# 							print ("Training Adept")
	# 						return True
	# 		if self.game.units(GATEWAY).ready.noqueue.exists and self.game.units(CYBERNETICSCORE).ready.exists:
	# 			if self.game.can_afford(ADEPT) and self.game.supply_left > 1:
	# 				gw = self.game.units(GATEWAY).ready.noqueue.random
	# 				self.game.combinedActions.append(gw.train(ADEPT))
	# 				if _print_unit_training:
	# 					print ("Training Adept")
	# 				return True
	# 	return False
	# 
	# async def train_zealot(self):
	# 	if self.allow_zealots:
	# 		if self.game.units(WARPGATE).ready.noqueue.exists:
	# 			if self.game.can_afford(ZEALOT) and self.game.supply_left > 0:
	# 				wg = self.game.units(WARPGATE).ready.noqueue.random
	# 				abilities = self.game.allAbilities.get(wg.tag)
	# 				if AbilityId.WARPGATETRAIN_ZEALOT in abilities:
	# 					#find the closest pylon to enemy.
	# 					placement = await self.warpgate_placement(AbilityId.WARPGATETRAIN_ZEALOT)
	# 					# pylon = self.game.units(PYLON).ready.closest_to(random.choice(self.game.enemy_start_locations))
	# 					# pos = pylon.position.to2.random_on_distance(4)
	# 					# placement = await self.game.find_placement(AbilityId.WARPGATETRAIN_ZEALOT, pos, placement_step=1)
	# 					if placement:
	# 						self.game.combinedActions.append(wg.warp_in(ZEALOT, placement))
	# 						if _print_unit_training:
	# 							print ("Training Zealot")
	# 						return True
	# 		
	# 		if self.game.units(GATEWAY).ready.noqueue.exists:
	# 			if self.game.can_afford(ZEALOT) and self.game.supply_left > 0:
	# 				gw = self.game.units(GATEWAY).ready.noqueue.random
	# 				self.game.combinedActions.append(gw.train(ZEALOT))
	# 				if _print_unit_training:
	# 					print ("Training Zealot")
	# 				return True
	# 	return False
	# 
	# async def train_sentry(self):
	# 	if self.allow_sentrys:
	# 
	# 		if self.game.units(WARPGATE).ready.noqueue.exists:
	# 			if self.game.can_afford(SENTRY) and self.game.supply_left > 0:
	# 				wg = self.game.units(WARPGATE).ready.noqueue.random
	# 				abilities = self.game.allAbilities.get(wg.tag)
	# 				if AbilityId.WARPGATETRAIN_SENTRY in abilities:
	# 					#find the closest pylon to enemy.
	# 					placement = await self.warpgate_placement(AbilityId.WARPGATETRAIN_SENTRY)
	# 					# pylon = self.game.units(PYLON).ready.closest_to(random.choice(self.game.enemy_start_locations))
	# 					# pos = pylon.position.to2.random_on_distance(4)
	# 					# placement = await self.game.find_placement(AbilityId.WARPGATETRAIN_SENTRY, pos, placement_step=1)
	# 					if placement:
	# 						self.game.combinedActions.append(wg.warp_in(SENTRY, placement))
	# 						if _print_unit_training:
	# 							print ("Training Sentry")
	# 						return True		
	# 
	# 
	# 		if self.game.units(GATEWAY).ready.noqueue.exists and self.game.units(CYBERNETICSCORE).ready.exists:
	# 			if self.game.can_afford(SENTRY) and self.game.supply_left >= 2:
	# 				gw = self.game.units(GATEWAY).ready.noqueue.random
	# 				self.game.combinedActions.append(gw.train(SENTRY))
	# 				if _print_unit_training:
	# 					print ("Training Sentry")
	# 				return True
	# 	return False
	# 
	# async def train_stalker(self):
	# 	if self.allow_stalkers:
	# 		if self.game.units(WARPGATE).ready.noqueue.exists:
	# 			if self.game.can_afford(STALKER) and self.game.supply_left > 0:
	# 				wg = self.game.units(WARPGATE).ready.noqueue.random
	# 				abilities = self.game.allAbilities.get(wg.tag)
	# 				if AbilityId.WARPGATETRAIN_STALKER in abilities:
	# 					#find the closest pylon to enemy.
	# 					placement = await self.warpgate_placement(AbilityId.WARPGATETRAIN_STALKER)
	# 					# pylon = self.game.units(PYLON).ready.closest_to(random.choice(self.game.enemy_start_locations))
	# 					# pos = pylon.position.to2.random_on_distance(4)
	# 					# placement = await self.game.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1)
	# 					if placement:
	# 						self.game.combinedActions.append(wg.warp_in(STALKER, placement))
	# 						if _print_unit_training:
	# 							print ("Training Stalker")
	# 						return True	
	# 
	# 		if self.game.units(GATEWAY).ready.noqueue.exists and self.game.units(CYBERNETICSCORE).ready.exists:
	# 			if self.game.can_afford(STALKER) and self.game.supply_left > 1:
	# 				gw = self.game.units(GATEWAY).ready.noqueue.random
	# 				self.game.combinedActions.append(gw.train(STALKER))
	# 				if _print_unit_training:
	# 					print ("Training Stalker")
	# 				return True
	# 	return False
	# 
	# def train_voidray(self):
	# 	if self.allow_voidrays:
	# 		if self.game.units(STARGATE).ready.noqueue.exists:
	# 			if self.game.can_afford(VOIDRAY) and self.game.supply_left > 3:
	# 				sg = self.game.units(STARGATE).ready.noqueue.random
	# 				self.game.combinedActions.append(sg.train(VOIDRAY))
	# 				if _print_unit_training:
	# 					print ("Training Voidray")
	# 				return True
	# 	return False
	# 
	# def train_phoenix(self):
	# 	if self.allow_phoenix:
	# 		if self.game.units(STARGATE).ready.noqueue.exists:
	# 			if self.game.can_afford(PHOENIX) and self.game.supply_left > 3:
	# 				sg = self.game.units(STARGATE).ready.noqueue.random
	# 				self.game.combinedActions.append(sg.train(PHOENIX))
	# 				if _print_unit_training:
	# 					print ("Training Phoenix")
	# 				return True
	# 	return False
	# 				
	# def train_tempest(self):
	# 	if self.allow_tempests:
	# 		if self.game.units(STARGATE).ready.noqueue.exists and self.game.units(FLEETBEACON).ready.exists:
	# 			if self.game.can_afford(TEMPEST) and self.game.supply_left > 6:
	# 				sg = self.game.units(STARGATE).ready.noqueue.random
	# 				self.game.combinedActions.append(sg.train(TEMPEST))
	# 				if _print_unit_training:				
	# 					print ("Training Tempest")
	# 				return True
	# 	return False
	# 				
	# def train_observer(self):
	# 	if self.allow_observers:
	# 		if self.game.units(ROBOTICSFACILITY).ready.noqueue.exists:
	# 			if self.game.can_afford(OBSERVER) and self.game.supply_left > 0:
	# 				rf = self.game.units(ROBOTICSFACILITY).ready.noqueue.random
	# 				self.game.combinedActions.append(rf.train(OBSERVER))
	# 				if _print_unit_training:
	# 					print ("Training Observer")
	# 				return True
	# 	return False
	# 
	# def train_immortal(self):
	# 	if self.allow_immortals:
	# 		if self.game.units(ROBOTICSFACILITY).ready.noqueue.exists:
	# 			if self.game.can_afford(IMMORTAL) and self.game.supply_left >= 4:
	# 				rf = self.game.units(ROBOTICSFACILITY).ready.noqueue.random
	# 				self.game.combinedActions.append(rf.train(IMMORTAL))
	# 				if _print_unit_training:
	# 					print ("Training Immortal")
	# 				return True
	# 	return False
	# 				
	# def train_warpprism(self):
	# 	if self.allow_warpprisms:
	# 		if self.game.units(ROBOTICSFACILITY).ready.noqueue.exists:
	# 			if self.game.can_afford(WARPPRISM) and self.game.supply_left >= 2:
	# 				rf = self.game.units(ROBOTICSFACILITY).ready.noqueue.random
	# 				self.game.combinedActions.append(rf.train(WARPPRISM))
	# 				if _print_unit_training:
	# 					print ("Training Warp Prism")
	# 				return True
	# 	return False
	# 				
	# 	
