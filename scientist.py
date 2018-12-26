import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *

_print_research = False

class Scientist:
	
	def __init__(self):
		#print ("Scientist Loaded")
		self._air_dps_research = False
		self._air_armor_research = False
		self._air_dps2_research = False
		self._air_armor2_research = False
		self._air_dps3_research = False
		self._air_armor3_research = False
		self._ground_armor_research = False
		self._ground_dps_research = False
		self._ground_armor2_research = False
		self._ground_dps2_research = False
		self._ground_armor3_research = False
		self._ground_dps3_research = False		
		self._shield_research = False
		self._shield2_research = False
		self._shield3_research = False
		self._grav_boosters_research = False
		self._blink_research = False
		self._charge_research = False
		self._resonating_glaives_research = False
		self._warpgate_research = False
		self._psionic_storm_research = False
		self._grav_catapult_research = False
		self._pulse_crystals_research = False
		self._grav_drive_research = False
		self._extended_lance_research = False

		self._air_dps_researched = False
		self._air_armor_researched = False
		self._air_dps2_researched = False
		self._air_armor2_researched = False
		self._air_dps3_researched = False
		self._air_armor3_researched = False
		self._ground_armor_researched = False
		self._ground_dps_researched = False
		self._ground_armor2_researched = False
		self._ground_dps2_researched = False
		self._ground_armor3_researched = False
		self._ground_dps3_researched = False		
		self._shield_researched = False
		self._shield2_researched = False
		self._shield3_researched = False
		self._grav_boosters_researched = False
		self._blink_researched = False
		self._charge_researched = False
		self._resonating_glaives_researched = False
		self._warpgate_researched = False
		self._psionic_storm_researched = False
		self._grav_catapult_researched = False
		self._pulse_crystals_researched = False
		self._grav_drive_researched = False	
		self._extended_lance_researched = False
		
	def research_any(self, game):
		self.game = game

		if self.research_grav_cats():
			return
		if self.research_grav_drive():
			return
		if self.research_pulse_crystals():
			return
		if self.research_extended_lance():
			return
		if self.research_air_dps():
			return		
		if self.research_air_dps2():
			return
		if self.research_air_dps3():
			return	
		if self.research_ground_dps():
			return
		if self.research_ground_dps2():
			return
		if self.research_ground_dps3():
			return
		if self.research_shields():
			return
		if self.research_shields2():
			return	
		if self.research_shields3():
			return
		if self.research_ground_armor():
			return
		if self.research_ground_armor2():
			return
		if self.research_ground_armor3():
			return
		if self.research_air_armor():
			return
		if self.research_air_armor2():
			return
		if self.research_air_armor3():
			return
		if self.research_blink():
			return
		if self.research_psionic_storm():
			return
		if self.research_charge():
		 	return
		if self.research_resonating_glaives():
		 	return
		if self.research_warpgate():
		 	return
		if self.research_grav_boosters():
		 	return



####################
#Research Functions#
####################

	
	def research_grav_boosters(self):
		if self._grav_boosters_researched or not self._grav_boosters_research or not self.game.units(ROBOTICSBAY).ready.noqueue.exists:
			return False
		
		robotbay = self.game.units(ROBOTICSBAY).ready.noqueue.random
		abilities = self.game.allAbilities.get(robotbay.tag)
		if AbilityId.RESEARCH_GRAVITICBOOSTER in abilities and self.game.can_afford(RESEARCH_GRAVITICBOOSTER):
			self.game.combinedActions.append(robotbay(AbilityId.RESEARCH_GRAVITICBOOSTER))
			self._grav_boosters_researched = True
			if _print_research:
				print ("Researching Gravitic Boosters")
			return True
		return False	

	def research_psionic_storm(self):
		if self._psionic_storm_researched or not self._psionic_storm_research or not self.game.units(TEMPLARARCHIVE).ready.noqueue.exists:
			return False
		
		arch = self.game.units(TEMPLARARCHIVE).ready.noqueue.random
		abilities = self.game.allAbilities.get(arch.tag)
		if AbilityId.RESEARCH_PSISTORM in abilities and self.game.can_afford(RESEARCH_PSISTORM):
			if _print_research:
				print ('Researching Psionic Storm')
			self.game.combinedActions.append(arch(AbilityId.RESEARCH_PSISTORM))
			self._psionic_storm_researched = True
			return True
		return False
	
	def research_warpgate(self):
		if self._warpgate_researched or not self._warpgate_research or not self.game.units(CYBERNETICSCORE).ready.noqueue.exists:
			return False
		
		core = self.game.units(CYBERNETICSCORE).ready.noqueue.random
		abilities = self.game.allAbilities.get(core.tag)
		if AbilityId.RESEARCH_WARPGATE in abilities and self.game.can_afford(RESEARCH_WARPGATE):
			if _print_research:
				print ('Researching Warpgate')
			self.game.combinedActions.append(core(AbilityId.RESEARCH_WARPGATE))
			self._warpgate_researched = True
			return True
		return False

	def research_resonating_glaives(self):
		if self._resonating_glaives_researched or not self._resonating_glaives_research or not self.game.units(TWILIGHTCOUNCIL).ready.noqueue.exists:
			return False		
		
		tc = self.game.units(TWILIGHTCOUNCIL).ready.random
		abilities = self.game.allAbilities.get(tc.tag)
		if AbilityId.RESEARCH_ADEPTRESONATINGGLAIVES in abilities and self.game.can_afford(RESEARCH_ADEPTRESONATINGGLAIVES):
			if _print_research:
				print ('Researching Resonating Glaives')
			self.game.combinedActions.append(tc(AbilityId.RESEARCH_ADEPTRESONATINGGLAIVES))
			self._resonating_glaives_researched = True
			return True
		return False
	
	def research_charge(self):
		if self._charge_researched or not self._charge_research or not self.game.units(TWILIGHTCOUNCIL).ready.noqueue.exists:
			return False
		
		tc = self.game.units(TWILIGHTCOUNCIL).ready.random
		abilities = self.game.allAbilities.get(tc.tag)
		if AbilityId.RESEARCH_CHARGE in abilities and self.game.can_afford(RESEARCH_CHARGE):
			if _print_research:
				print ('Researching Charge')
			self.game.combinedActions.append(tc(AbilityId.RESEARCH_CHARGE))
			self._charge_researched = True
			return True
		return False

	def research_blink(self):
		if self._blink_researched or not self._blink_research or not self.game.units(TWILIGHTCOUNCIL).ready.noqueue.exists:
			return False		
		
		tc = self.game.units(TWILIGHTCOUNCIL).ready.random
		abilities = self.game.allAbilities.get(tc.tag)
		if AbilityId.RESEARCH_BLINK in abilities and self.game.can_afford(RESEARCH_BLINK):
			if _print_research:					
				print ('Researching Blink')
			self.game.combinedActions.append(tc(AbilityId.RESEARCH_BLINK))
			self._blink_researched = True
			return True
		return False
	
	def research_air_armor(self):
		if self._air_armor_researched or not self._air_armor_research or not self.game.units(CYBERNETICSCORE).ready.noqueue.exists:
			return False
		
		core = self.game.units(CYBERNETICSCORE).ready.noqueue.random
		abilities = self.game.allAbilities.get(core.tag)
		if AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL1 in abilities and self.game.can_afford(CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL1):
			if _print_research:
				print ('Researching Air Armor Level 1')
			self.game.combinedActions.append(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL1))
			self._air_armor_researched = True
			return True
		return False
	
	def research_air_armor2(self):
		if self._air_armor2_researched or not self._air_armor2_research or not self.game.units(FLEETBEACON).ready.exists or not self.game.units(CYBERNETICSCORE).ready.noqueue.exists:
			return False
		
		core = self.game.units(CYBERNETICSCORE).ready.noqueue.random
		abilities = self.game.allAbilities.get(core.tag)
		if AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL2 in abilities and self.game.can_afford(CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL2):
			if _print_research:
				print ('Researching Air Armor Level 2')
			self.game.combinedActions.append(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL2))
			self._air_armor2_researched = True
			return True
		return False

	def research_air_armor3(self):
		if self._air_armor3_researched or not self._air_armor3_research or not self.game.units(FLEETBEACON).ready.exists or not self.game.units(CYBERNETICSCORE).ready.noqueue.exists:
			return False
		
		core = self.game.units(CYBERNETICSCORE).ready.noqueue.random
		abilities = self.game.allAbilities.get(core.tag)
		if AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL3 in abilities and self.game.can_afford(CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL3):
			if _print_research:
				print ('Researching Air Armor Level 3')
			self.game.combinedActions.append(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL3))
			self._air_armor3_researched = True
			return True
		return False

	def research_ground_armor(self):
		if self._ground_armor_researched or not self._ground_armor_research or not self.game.units(FORGE).ready.noqueue.exists:
			return False
		
		forge = self.game.units(FORGE).ready.noqueue.random
		abilities = self.game.allAbilities.get(forge.tag)
		if AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1 in abilities and self.game.can_afford(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1):
			self.game.combinedActions.append(forge(AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1))
			self._ground_armor_researched = True
			if _print_research:
				print ('Researching Ground Armor Level 1')
			return True
		return False

	def research_ground_armor2(self):
		if self._ground_armor2_researched or not self._ground_armor2_research or not self.game.units(TWILIGHTCOUNCIL).ready.exists or not self.game.units(FORGE).ready.noqueue.exists:
			return False
		
		forge = self.game.units(FORGE).ready.noqueue.random
		abilities = self.game.allAbilities.get(forge.tag)
		if AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2 in abilities and self.game.can_afford(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2):
			self.game.combinedActions.append(forge(AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2))
			self._ground_armor2_researched = True
			if _print_research:
				print ('Researching Ground Armor Level 2')
			return True
		return False

	def research_ground_armor3(self):
		if self._ground_armor3_researched or not self._ground_armor3_research or not self.game.units(TWILIGHTCOUNCIL).ready.exists or not self.game.units(FORGE).ready.noqueue.exists:
			return False
		
		forge = self.game.units(FORGE).ready.noqueue.random
		abilities = self.game.allAbilities.get(forge.tag)
		if AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3 in abilities and self.game.can_afford(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3):
			self.game.combinedActions.append(forge(AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3))
			self._ground_armor3_researched = True
			if _print_research:
				print ('Researching Ground Armor Level 3')	
			return True
		return False
	
	def research_shields2(self):
		if self._shield2_researched or not self._shield2_research or not self.game.units(TWILIGHTCOUNCIL).ready.exists or not self.game.units(FORGE).ready.noqueue.exists:
			return False		
		
		forge = self.game.units(FORGE).ready.noqueue.random
		abilities = self.game.allAbilities.get(forge.tag)
		if AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL2 in abilities and self.game.can_afford(FORGERESEARCH_PROTOSSSHIELDSLEVEL2):
			self.game.combinedActions.append(forge(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL2))
			self._shield2_researched = True
			if _print_research:
				print ('Researching Shields Level 2')
			return True
		return False

	def research_shields3(self):
		if self._shield3_researched or not self._shield3_research or not self.game.units(TWILIGHTCOUNCIL).ready.exists or not self.game.units(FORGE).ready.noqueue.exists:		
			return False
		
		forge = self.game.units(FORGE).ready.noqueue.random
		abilities = self.game.allAbilities.get(forge.tag)
		if AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL3 in abilities and self.game.can_afford(FORGERESEARCH_PROTOSSSHIELDSLEVEL3):
			self.game.combinedActions.append(forge(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL3))
			self._shield3_researched = True
			if _print_research:
				print ('Researching Shields Level 3')
			return True
		return False

	def research_shields(self):
		if self._shield_researched or not self._shield_research or not self.game.units(FORGE).ready.noqueue.exists:		
			return False
		
		forge = self.game.units(FORGE).ready.noqueue.random
		abilities = self.game.allAbilities.get(forge.tag)
		if AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1 in abilities and self.game.can_afford(FORGERESEARCH_PROTOSSSHIELDSLEVEL1):
			self.game.combinedActions.append(forge(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1))
			self._shield_researched = True
			if _print_research:
				print ('Researching Shields Level 1')
			return True
		return False
	
	def research_ground_dps3(self):
		if self._ground_dps3_researched or not self._ground_dps3_research or not self.game.units(TWILIGHTCOUNCIL).ready.exists or not self.game.units(FORGE).ready.noqueue.exists:
			return False
		
		forge = self.game.units(FORGE).ready.noqueue.random
		abilities = self.game.allAbilities.get(forge.tag)
		if AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL3 in abilities and self.game.can_afford(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL3):
			self.game.combinedActions.append(forge(AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL3))
			self._ground_dps3_researched = True
			if _print_research:
				print ('Researching Ground Weapons Level 3')
			return True
		return False
	
	def research_ground_dps2(self):
		if self._ground_dps2_researched or not self._ground_dps2_research or not self.game.units(TWILIGHTCOUNCIL).ready.exists or not self.game.units(FORGE).ready.noqueue.exists:
			return False
		
		forge = self.game.units(FORGE).ready.noqueue.random
		abilities = self.game.allAbilities.get(forge.tag)
		if AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2 in abilities and self.game.can_afford(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2):
			self.game.combinedActions.append(forge(AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2))
			self._ground_dps2_researched = True
			if _print_research:
				print ('Researching Ground Weapons Level 2')
			return True
		return False
	
	def research_ground_dps(self):
		if self._ground_dps_researched or not self._ground_dps_research or not self.game.units(FORGE).ready.noqueue.exists:
			return False
		
		forge = self.game.units(FORGE).ready.noqueue.random
		abilities = self.game.allAbilities.get(forge.tag)
		if AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1 in abilities and self.game.can_afford(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1):
			self.game.combinedActions.append(forge(AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1))
			self._ground_dps_researched = True
			if _print_research:
				print ('Researching Ground Weapons Level 1')
			return True
		return False

	def research_air_dps3(self):
		if self._air_dps3_researched or not self._air_dps3_research or not self.game.units(FLEETBEACON).ready.exists or not self.game.units(CYBERNETICSCORE).ready.noqueue.exists:
			return False
		
		core = self.game.units(CYBERNETICSCORE).ready.noqueue.random
		abilities = self.game.allAbilities.get(core.tag)
		if AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL3 in abilities and self.game.can_afford(CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL3):
			if _print_research:
				print ('Researching Air Weapons Level 3')
			self.game.combinedActions.append(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL3))
			self._air_dps3_researched = True
			return True
		return False
	
	def research_air_dps2(self):
		if self._air_dps2_researched or not self._air_dps2_research or not self.game.units(FLEETBEACON).ready.exists or not self.game.units(CYBERNETICSCORE).ready.noqueue.exists:
			return False		
		
		core = self.game.units(CYBERNETICSCORE).ready.noqueue.random
		abilities = self.game.allAbilities.get(core.tag)
		if AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL2 in abilities and self.game.can_afford(CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL2):
			if _print_research:
				print ('Researching Air Weapons Level 2')
			self.game.combinedActions.append(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL2))
			self._air_dps2_researched = True
			return True
		return False

	def research_air_dps(self):
		if self._air_dps_researched or not self._air_dps_research or not self.game.units(CYBERNETICSCORE).ready.noqueue.exists:
			return False
		
		core = self.game.units(CYBERNETICSCORE).ready.noqueue.random
		abilities = self.game.allAbilities.get(core.tag)
		if AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL1 in abilities and self.game.can_afford(CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL1):
			if _print_research:
				print ('Researching Air Weapons Level 1')
			self.game.combinedActions.append(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL1))
			self._air_dps_researched = True
			return True
		return False
	
	def research_extended_lance(self):
		if self._extended_lance_researched or not self._extended_lance_research or not self.game.units(ROBOTICSBAY).ready.noqueue.exists:
			return False			
		robotbay = self.game.units(ROBOTICSBAY).ready.noqueue.random
		#abilities = await self.game.get_available_abilities(beacon)
		abilities = self.game.allAbilities.get(robotbay.tag)
		if AbilityId.RESEARCH_EXTENDEDTHERMALLANCE in abilities and self.game.can_afford(RESEARCH_EXTENDEDTHERMALLANCE):
			self.game.combinedActions.append(robotbay(AbilityId.RESEARCH_EXTENDEDTHERMALLANCE))
			self._extended_lance_researched = True
			if _print_research:
				print ("Researching Extended Lance")
			return True
		return False
	
	def research_pulse_crystals(self):
		if self._pulse_crystals_researched or not self._pulse_crystals_research or not self.game.units(FLEETBEACON).ready.noqueue.exists:
			return False

		beacon = self.game.units(FLEETBEACON).ready.noqueue.random
		abilities = self.game.allAbilities.get(beacon.tag)
		if AbilityId.RESEARCH_PHOENIXANIONPULSECRYSTALS in abilities and self.game.can_afford(RESEARCH_PHOENIXANIONPULSECRYSTALS):
			self.game.combinedActions.append(beacon(AbilityId.RESEARCH_PHOENIXANIONPULSECRYSTALS))
			self._pulse_crystals_researched = True
			if _print_research:
				print ("Researching Pulse Crystals")
			return True
		return False
	
	def research_grav_drive(self):
		if self._grav_drive_researched or not self._grav_drive_research or not self.game.units(ROBOTICSBAY).ready.noqueue.exists:
			return False			
		robotbay = self.game.units(ROBOTICSBAY).ready.noqueue.random
		#abilities = await self.game.get_available_abilities(beacon)
		abilities = self.game.allAbilities.get(robotbay.tag)
		if AbilityId.RESEARCH_GRAVITICDRIVE in abilities and self.game.can_afford(RESEARCH_GRAVITICDRIVE):
			self.game.combinedActions.append(robotbay(AbilityId.RESEARCH_GRAVITICDRIVE))
			self._grav_catapult_researched = True
			if _print_research:
				print ("Researching Gravic Drive")
			return True
		return False	

	def research_grav_cats(self):
		if self._grav_catapult_researched or not self._grav_catapult_research or not self.game.units(FLEETBEACON).ready.noqueue.exists:
			return False
		
		beacon = self.game.units(FLEETBEACON).ready.noqueue.random
		#abilities = await self.game.get_available_abilities(beacon)
		abilities = self.game.allAbilities.get(beacon.tag)
		if AbilityId.RESEARCH_INTERCEPTORGRAVITONCATAPULT in abilities and self.game.can_afford(RESEARCH_INTERCEPTORGRAVITONCATAPULT):
			self.game.combinedActions.append(beacon(AbilityId.RESEARCH_INTERCEPTORGRAVITONCATAPULT))
			self._grav_catapult_researched = True
			if _print_research:
				print ("Researching Gravitonic Catapults")
			return True
		return False	










	














