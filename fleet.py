import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *

_debug = False

class Fleet:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.label = 'Idle'
		#research flags.
		self._pulse_crystals_researched = False
		self._grav_catapult_researched = False

		self._pulse_crystals_started = False
		self._grav_catapult_started = False


		self.current_research = None

		
		
	async def make_decision(self, game, unit):
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)
		
		if self.unit.noqueue:
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
		
		#only build when queues are full to maximize military production
		if not self.game._strat_manager.allAllowedQueued:
			self.label = 'Building Military Instead'
			return
				
		#see if we can research anything.
		if self.researchPulseCrystals():
			return
		
		#gravcats were removed.
		# if self.researchGravCat():
		# 	return
		
		self.label = 'Idle'
		
			
	def researchPulseCrystals(self):
		if self.game.units(PHOENIX).amount >= 3 and not self._pulse_crystals_started and not self._pulse_crystals_researched:
			if AbilityId.RESEARCH_PHOENIXANIONPULSECRYSTALS in self.abilities and self.game.can_afford(RESEARCH_PHOENIXANIONPULSECRYSTALS):
				self.game.combinedActions.append(self.unit(AbilityId.RESEARCH_PHOENIXANIONPULSECRYSTALS))
				self._pulse_crystals_started = True
				self.current_research = 'PulseCrystals'
				self.game.can_spend = False
				return True

	def researchGravCat(self):
		if self.game.units(CARRIER).amount >= 2 and not self._grav_catapult_started and not self._grav_catapult_researched:
			if AbilityId.RESEARCH_INTERCEPTORGRAVITONCATAPULT in self.abilities and self.game.can_afford(RESEARCH_INTERCEPTORGRAVITONCATAPULT):
				self.game.combinedActions.append(self.unit(AbilityId.RESEARCH_INTERCEPTORGRAVITONCATAPULT))
				self._grav_catapult_started = True
				self.current_research = 'GravCat'
				self.game.can_spend = False
				return True				

			
	def checkResearched(self):
		if self.current_research:
			if self.current_research == 'PulseCrystals':
				self._pulse_crystals_researched = True
				self._pulse_crystals_started = False
				self.current_research = None
			elif self.current_research == 'GravCat':
				self._grav_catapult_researched = True
				self._grav_catapult_started = False
				self.current_research = None


			
		
	def resourcesSaved(self):
		if self.game._strat_manager.saving or not self.game.can_spend:
			return True			
			
	
	@property
	def pulseCrystalsReady(self) -> bool:
		return self._pulse_crystals_researched			
			
			
			
		