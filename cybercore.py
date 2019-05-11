import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *

_debug = False

class CyberCore:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.label = 'Idle'
		#research flags.
		self._warpgate_researched = False
		self._air_dps_researched = False
		self._air_dps2_researched = False		
		self._air_dps3_researched = False						
		self._air_armor_researched = False
		self._air_armor2_researched = False
		self._air_armor3_researched = False		

		self._warpgate_started = False
		self._air_dps_started = False
		self._air_dps2_started = False		
		self._air_dps3_started = False						
		self._air_armor_started = False
		self._air_armor2_started = False
		self._air_armor3_started = False		
	
		self.current_research = None

		
		
	async def make_decision(self, game, unit):
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)
		
		if self.unit.is_idle:
			await self.runList()
		else:
			self.label = 'Researching {}'.format(self.current_research)

		#debugging info
		if _debug or self.unit.is_selected:
			self.game._client.debug_text_3d(self.label, self.unit.position3d)

	async def runList(self):
		#check if we need to mark a research as finished.
		self.checkResearched()

		#check to see if saving resources are being requested.
		if self.resourcesSaved():
			self.label = 'Resources being saved'
			return		
		
		#see if we can research anything.
		if self.researchWarpgate():
			return
		
		#check to make sure everything is queued up before researching.
		if not self.game._strat_manager.allAllowedQueued:
			self.label = 'Building Military Instead'
			return
		
		
		if self.researchAirDPS():
			return
		if self.researchAirDPS2():
			return
		if self.researchAirDPS3():
			return
		if self.researchAirArmor():
			return
		if self.researchAirArmor2():
			return
		if self.researchAirArmor3():
			return			
		self.label = 'Idle'
	
	def researchAirArmor3(self):
		if self._air_armor2_researched and not self._air_armor3_started and not self._air_armor3_researched:
			if AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL3 in self.abilities and self.game.can_afford(CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL3):
				self.game.combinedActions.append(self.unit(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL3))
				self._air_armor3_started = True
				self.current_research = 'AirArmor3'
				self.game.can_spend = False
				return True

	def researchAirArmor2(self):
		if self._air_armor_researched and not self._air_armor2_started and not self._air_armor2_researched and self.game.units(FLEETBEACON).ready.exists:
			if AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL2 in self.abilities and self.game.can_afford(CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL2):
				self.game.combinedActions.append(self.unit(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL2))
				self._air_armor2_started = True
				self.current_research = 'AirArmor2'
				self.game.can_spend = False
				return True				

	def researchAirArmor(self):
		if self._air_dps3_researched and not self._air_armor_started and not self._air_armor_researched:
			if AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL1 in self.abilities and self.game.can_afford(CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL1):
				self.game.combinedActions.append(self.unit(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL1))
				self._air_armor_started = True
				self.current_research = 'AirArmor'
				self.game.can_spend = False
				return True	
			

	def researchAirDPS3(self):
		if self._air_dps2_researched and not self._air_dps3_started and not self._air_dps3_researched:
			if AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL3 in self.abilities and self.game.can_afford(CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL3):
				self.game.combinedActions.append(self.unit(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL3))
				self._air_dps3_started = True
				self.current_research = 'AirDPS3'
				self.game.can_spend = False
				return True

	def researchAirDPS2(self):
		if self._air_dps_researched and not self._air_dps2_started and not self._air_dps2_researched and self.game.units(FLEETBEACON).ready.exists:
			if AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL2 in self.abilities and self.game.can_afford(CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL2):
				self.game.combinedActions.append(self.unit(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL2))
				self._air_dps2_started = True
				self.current_research = 'AirDPS2'
				self.game.can_spend = False
				return True			


	def researchAirDPS(self):
		if self.game.units(STARGATE).amount > 1 and not self._air_dps_started and not self._air_dps_researched:
			if AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL1 in self.abilities and self.game.can_afford(CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL1):
				self.game.combinedActions.append(self.unit(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL1))
				self._air_dps_started = True
				self.current_research = 'AirDPS'
				self.game.can_spend = False
				return True
	

		
	def researchWarpgate(self):
		#always train warpgate asap.
		if not self._warpgate_started and not self._warpgate_researched and len(self.game.units.filter(lambda x: not x.name in ['Probe'] and (x.can_attack_ground or x.can_attack_air))) > 0:
			if AbilityId.RESEARCH_WARPGATE in self.abilities and self.game.can_afford(RESEARCH_WARPGATE):
				self.game.combinedActions.append(self.unit(AbilityId.RESEARCH_WARPGATE))
				self._warpgate_started = True
				self.current_research = 'Warpgate'
				self.game.can_spend = False
				return True
			
			
	def checkResearched(self):
		if self.current_research:
			if self.current_research == 'Warpgate':
				self._warpgate_researched = True
				self._warpgate_started = False
				self.current_research = None
			elif self.current_research == 'AirDPS':
				self._air_dps_researched = True
				self._air_dps_started = False
				self.current_research = None
			elif self.current_research == 'AirDPS2':
				self._air_dps2_researched = True
				self._air_dps2_started = False
				self.current_research = None
			elif self.current_research == 'AirDPS3':
				self._air_dps3_researched = True
				self._air_dps3_started = False
				self.current_research = None

			elif self.current_research == 'AirArmor':
				self._air_armor_researched = True
				self._air_armor_started = False
				self.current_research = None
			elif self.current_research == 'AirArmor2':
				self._air_armor2_researched = True
				self._air_armor2_started = False
				self.current_research = None
			elif self.current_research == 'AirArmor3':
				self._air_armor3_researched = True
				self._air_armor3_started = False
				self.current_research = None				
		
	def resourcesSaved(self):
		if self.game._strat_manager.saving or not self.game.can_spend:
			return True			
			
			
	@property
	def warpReady(self) -> bool:
		return self._warpgate_researched
			
			
		