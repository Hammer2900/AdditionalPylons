import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *


_debug = False

class Forge:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.label = 'Idle'
		#research flags.
		self._ground_dps_researched = False
		self._ground_dps2_researched = False		
		self._ground_dps3_researched = False						
		self._ground_armor_researched = False
		self._ground_armor2_researched = False
		self._ground_armor3_researched = False
		self._shields_researched = False	
		self._shields2_researched = False
		self._shields3_researched = False			

		self._ground_dps_started = False
		self._ground_dps2_started = False		
		self._ground_dps3_started = False						
		self._ground_armor_started = False
		self._ground_armor2_started = False
		self._ground_armor3_started = False		
		self._shields_started = False		
		self._shields2_started = False
		self._shields3_started = False
		
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
		
		#only research when queues are full to maximize military
		if not self.game._strat_manager.allAllowedQueued:
			self.label = 'Building Military Instead'
			return
				
		#see if we can research anything.
		if self.researchGroundDPS():
			return
		if self.researchGroundDPS2():
			return
		if self.researchGroundDPS3():
			return
		if self.researchGroundArmor():
			return
		if self.researchGroundArmor2():
			return
		if self.researchGroundArmor3():
			return
		if self.researchShields():
			return
		if self.researchShields2():
			return
		if self.researchShields3():
			return
		#nothing to do
		self.label = 'Idle'
	
	def researchGroundArmor3(self):
		if self._ground_armor2_researched and not self._ground_armor3_started and not self._ground_armor3_researched:
			if AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3 in self.abilities and self.game.can_afford(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3):
				self.game.combinedActions.append(self.unit(AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3))
				self._ground_armor3_started = True
				self.current_research = 'GroundArmor3'
				self.game.can_spend = False
				return True

	def researchGroundArmor2(self):
		if self._ground_dps3_researched and self._ground_armor_researched and not self._ground_armor2_started and not self._ground_armor2_researched and self.game.units(TWILIGHTCOUNCIL).ready.exists:
			if AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2 in self.abilities and self.game.can_afford(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2):
				self.game.combinedActions.append(self.unit(AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2))
				self._ground_armor2_started = True
				self.current_research = 'GroundArmor2'
				self.game.can_spend = False
				return True				

	def researchGroundArmor(self):
		if (len(self.game.units(ZEALOT)) > 5 or self._ground_dps3_researched) and not self._ground_armor_started and not self._ground_armor_researched:
			if AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1 in self.abilities and self.game.can_afford(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1):
				self.game.combinedActions.append(self.unit(AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1))
				self._ground_armor_started = True
				self.current_research = 'GroundArmor'
				self.game.can_spend = False
				return True	
			

	def researchGroundDPS3(self):
		if self._ground_dps2_researched and not self._ground_dps3_started and not self._ground_dps3_researched:
			if AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL3 in self.abilities and self.game.can_afford(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL3):
				self.game.combinedActions.append(self.unit(AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL3))
				self._ground_dps3_started = True
				self.current_research = 'GroundDPS3'
				self.game.can_spend = False
				return True

	def researchGroundDPS2(self):
		if self._ground_dps_researched and not self._ground_dps2_started and not self._ground_dps2_researched and self.game.units(TWILIGHTCOUNCIL).ready.exists:
			if AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2 in self.abilities and self.game.can_afford(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2):
				self.game.combinedActions.append(self.unit(AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2))
				self._ground_dps2_started = True
				self.current_research = 'GroundDPS2'
				self.game.can_spend = False
				return True			


	def researchGroundDPS(self):
		if self.game.trueGates + self.game.units(ROBOTICSFACILITY).amount > 1 and not self._ground_dps_started and not self._ground_dps_researched:
			if AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1 in self.abilities and self.game.can_afford(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1):
				self.game.combinedActions.append(self.unit(AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1))
				self._ground_dps_started = True
				self.current_research = 'GroundDPS'
				self.game.can_spend = False
				return True

	def researchShields3(self):
		if self._shields2_researched and not self._shields3_started and not self._shields3_researched:
			if AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL3 in self.abilities and self.game.can_afford(FORGERESEARCH_PROTOSSSHIELDSLEVEL3):
				self.game.combinedActions.append(self.unit(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL3))
				self._shields3_started = True
				self.current_research = 'Shields3'
				self.game.can_spend = False
				return True

	def researchShields2(self):
		if self._shields_researched and not self._shields2_started and not self._shields2_researched:
			if AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL2 in self.abilities and self.game.can_afford(FORGERESEARCH_PROTOSSSHIELDSLEVEL2):
				self.game.combinedActions.append(self.unit(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL2))
				self._shields2_started = True
				self.current_research = 'Shields2'
				self.game.can_spend = False
				return True
	
	def researchShields(self):
		if self._ground_armor3_researched and not self._shields_started and not self._shields_researched:
			if AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1 in self.abilities and self.game.can_afford(FORGERESEARCH_PROTOSSSHIELDSLEVEL1):
				self.game.combinedActions.append(self.unit(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1))
				self._shields_started = True
				self.current_research = 'Shields'
				self.game.can_spend = False
				return True
			
			
	def checkResearched(self):
		if self.current_research:
			if self.current_research == 'GroundDPS':
				self._ground_dps_researched = True
				self._ground_dps_started = False
				self.current_research = None
			elif self.current_research == 'GroundDPS2':
				self._ground_dps2_researched = True
				self._ground_dps2_started = False
				self.current_research = None
			elif self.current_research == 'GroundDPS3':
				self._ground_dps3_researched = True
				self._ground_dps3_started = False
				self.current_research = None

			elif self.current_research == 'GroundArmor':
				self._ground_armor_researched = True
				self._ground_armor_started = False
				self.current_research = None
			elif self.current_research == 'GroundArmor2':
				self._ground_armor2_researched = True
				self._ground_armor2_started = False
				self.current_research = None
			elif self.current_research == 'GroundArmor3':
				self._ground_armor3_researched = True
				self._ground_armor3_started = False
				self.current_research = None
				
			elif self.current_research == 'Shields':
				self._shields_researched = True
				self._shields_started = False
				self.current_research = None				
			elif self.current_research == 'Shields2':
				self._shields2_researched = True
				self._shields2_started = False
				self.current_research = None
			elif self.current_research == 'Shields3':
				self._shields3_researched = True
				self._shields3_started = False
				self.current_research = None					
		
	def resourcesSaved(self):
		if self.game._strat_manager.saving or not self.game.can_spend:
			return True			
			
			
			
			
			
		