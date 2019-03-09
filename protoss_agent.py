import os
import pickle
import numpy as np
import operator
import random
import sc2
from sc2.units import Units
from sc2.constants import *


'''
Observe the enemy.

'''
_debug = False

class ProtossAgent:
	
	def __init__(self, game):
		self.game = game
		self.previous_observation = None
		self.previous_action = 0
		self.builder = self.game._build_manager
		self.enemy_intel = {}
		self.enemy_mobiles = {}
		self.counted_enemy = {}
		self.last_actions = [0,0,0,0,0,0,0,0,0,0]
		self.actions_run = 0
		self.last_raw_action = []
		self.all_obs = []
	
	
	async def save_decision(self, game):
		self.game = game
		#first thing to do is get the observation for this frame.
		observation = self.getObservation()
		action = 0 #do nothing.
		#check to see if saving resources is flagged.
		if self.game._strat_manager.saving:
			action = 1
		elif self.game._build_manager.last_build:
			action = self.game._build_manager.last_build
		#make an array for this decision
		#print ([observation, action])
		self.all_obs.append([observation, action])
		
		
	def actionList(self, action):
		self.previous_action = action
		if len(self.last_actions) >= 10:
			del self.last_actions[-1]
		self.last_actions.insert(0, action)


	def getObservation(self):
		#get the observation array to send to the NN.
		#count the enemy units and add them.
		self.count_intel()
		
		observation = [
			self.game.buildingList.pylonsRequested,
			self.game.buildingList.cannonsRequested,
			self.game.buildingList.shieldsRequested,
			int(self.game.time / 60),
			self.defendStatus,
			self.attackStatus,
			self.savingStatus,
			int(self.game.minerals / 50),
			int(self.game.vespene / 50),
			len(self.game.units(NEXUS).ready),
			len(self.game.units(NEXUS).not_ready),
			len(self.game.units(PYLON).ready),
			len(self.game.units(PYLON).not_ready),
			len(self.game.units(GATEWAY).ready),
			len(self.game.units(GATEWAY).not_ready),
			len(self.game.units(CYBERNETICSCORE).ready),
			len(self.game.units(CYBERNETICSCORE).not_ready),
			len(self.game.units(ROBOTICSFACILITY).ready),
			len(self.game.units(ROBOTICSFACILITY).not_ready),
			len(self.game.units(STARGATE).ready),
			len(self.game.units(STARGATE).not_ready),
			len(self.game.units(TWILIGHTCOUNCIL).ready),
			len(self.game.units(TWILIGHTCOUNCIL).not_ready),
			len(self.game.units(ROBOTICSBAY).ready),
			len(self.game.units(ROBOTICSBAY).not_ready),
			len(self.game.units(FLEETBEACON).ready),
			len(self.game.units(FLEETBEACON).not_ready),
			len(self.game.units(TEMPLARARCHIVE).ready),
			len(self.game.units(TEMPLARARCHIVE).not_ready),
			len(self.game.units(DARKSHRINE).ready),
			len(self.game.units(DARKSHRINE).not_ready),
			len(self.game.units(FORGE).ready),
			len(self.game.units(FORGE).not_ready),
			len(self.game.units(PHOTONCANNON).ready),
			len(self.game.units(PHOTONCANNON).not_ready),
			len(self.game.units(SHIELDBATTERY).ready),
			len(self.game.units(SHIELDBATTERY).not_ready),
			len(self.game.units(ASSIMILATOR).ready),
			len(self.game.units(ASSIMILATOR).not_ready),
			len(self.game.units(PROBE)),
			len(self.game.units(ZEALOT)),
			len(self.game.units(STALKER)),
			len(self.game.units(ADEPT)),
			len(self.game.units(SENTRY)),
			len(self.game.units(HIGHTEMPLAR)),
			len(self.game.units(DARKTEMPLAR)),
			len(self.game.units(COLOSSUS)),
			len(self.game.units(DISRUPTOR)),
			len(self.game.units(OBSERVER)),
			len(self.game.units(IMMORTAL)),
			len(self.game.units(WARPPRISM)),
			len(self.game.units(ORACLE)),
			len(self.game.units(PHOENIX)),
			len(self.game.units(VOIDRAY)),
			len(self.game.units(TEMPEST)),
			len(self.game.units(CARRIER)),
			len(self.game.units(MOTHERSHIP)),
			len(self.game.units(ARCHON)),
			self.enemyUnitCount('Nexus'),
			self.enemyUnitCount('Pylon'),
			self.enemyUnitCount('Gateway'),
			self.enemyUnitCount('CyberneticsCore'),
			self.enemyUnitCount('RoboticsFacility'),
			self.enemyUnitCount('Stargate'),
			self.enemyUnitCount('TwilightCouncil'),
			self.enemyUnitCount('RoboticsBay'),
			self.enemyUnitCount('FleetBeacon'),
			self.enemyUnitCount('TemplarArchive'),
			self.enemyUnitCount('DarkShrine'),
			self.enemyUnitCount('Forge'),
			self.enemyUnitCount('PhotonCannon'),
			self.enemyUnitCount('ShieldBattery'),
			self.enemyUnitCount('Assimiliator'),
			self.enemyUnitCount('Probe'),
			self.enemyUnitCount('Zealot'),
			self.enemyUnitCount('Stalker'),
			self.enemyUnitCount('Adept'),
			self.enemyUnitCount('Sentry'),
			self.enemyUnitCount('HighTemplar'),
			self.enemyUnitCount('DarkTemplar'),
			self.enemyUnitCount('Colossus'),
			self.enemyUnitCount('Disruptor'),
			self.enemyUnitCount('Observer'),
			self.enemyUnitCount('Immortal'),
			self.enemyUnitCount('WarpPrism'),
			self.enemyUnitCount('Oracle'),
			self.enemyUnitCount('Phoenix'),
			self.enemyUnitCount('VoidRay'),
			self.enemyUnitCount('Tempest'),
			self.enemyUnitCount('Carrier'),
			self.enemyUnitCount('Mothership'),
			self.enemyUnitCount('Archon'),
			self.last_actions[0],
			self.last_actions[1],
			self.last_actions[2],
			self.last_actions[3],
			self.last_actions[4],
			self.last_actions[5],
			self.last_actions[6],
			self.last_actions[7],
			self.last_actions[8],
			self.last_actions[9]
		]
		
		#print (str(observation))
		#return np.array(observation)
		return observation


###################################
#Intelligence Collection Functions#
###################################

	def enemyUnitCount(self, enemyName):
		if self.counted_enemy.get(enemyName):
			return self.counted_enemy.get(enemyName)
		return 0

	def collectIntel(self):
		protoss_units = [MOTHERSHIP, COLOSSUS, ZEALOT, STALKER, HIGHTEMPLAR, DARKTEMPLAR, SENTRY, PHOENIX, CARRIER, VOIDRAY, WARPPRISM, OBSERVER, IMMORTAL, ADEPT, ORACLE, TEMPEST, DISRUPTOR, ARCHON]
		protoss_buildings = [NEXUS, PYLON, GATEWAY, CYBERNETICSCORE, ROBOTICSFACILITY, STARGATE, FORGE, FLEETBEACON, TWILIGHTCOUNCIL, ROBOTICSBAY, TEMPLARARCHIVE, DARKSHRINE, ASSIMILATOR, SHIELDBATTERY, PHOTONCANNON]
		all_units = protoss_buildings + protoss_units
		enemyThreats = self.game.known_enemy_units.of_type(protoss_units)
		for enemy in enemyThreats:
			#check if already exists, if it doesn't, add it.
			if not self.enemy_intel.get(enemy.tag):
				self.enemy_intel.update({enemy.tag:enemy.name})
					
		enemyThreats = self.game.known_enemy_units.of_type(protoss_buildings)
		for enemy in enemyThreats:
			#check if already exists, if it doesn't, add it.
			if not self.enemy_intel.get(enemy.tag):
				self.enemy_intel.update({enemy.tag:enemy.name})
				self.tagReplace(enemy)
		if _debug:
			xpos = 0.025
			if len(self.last_raw_action) > 0:
				elab = "Last Action: {_action} - {_score:.2f}%".format(_action=self.actionLabel(self.previous_action), _score=self.prettyNums(self.last_raw_action[self.previous_action]))
				self.game._client.debug_text_screen(elab, pos=(0.001, xpos), size=10)
			# xpos = 0.055
			# elab = "Last 10 Actions: {_action}".format(_action=self.last_actions)
			# self.game._client.debug_text_screen(elab, pos=(0.001, xpos), size=10)				
			self.labelActions()
					
	def tagReplace(self, enemy):
		#check to see if this cannon exists by position.
		if self.enemy_mobiles.get(enemy.position):
			#one already exists, get the old tag out of the value and remove it.
			tag = self.enemy_mobiles.get(enemy.position)
			self.remove_intel(tag)
		#update the new tag for the position.
		self.enemy_mobiles.update({enemy.position:enemy.tag})

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
		self.counted_enemy = counted_enemy

############
#Properties#
############

	@property
	def defendStatus(self) -> int:
		if self.game.under_attack:
			return 150
		return 0

	@property
	def attackStatus(self) -> int:
		if self.game.defend_only:
			return 150
		return 0

	@property
	def savingStatus(self) -> int:
		if self.game._strat_manager.saving:
			return 150
		return 0

