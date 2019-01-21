import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *

_debug = False

class Archive:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.label = 'Idle'
		#research flags.
		self._psionic_storm_researched = False
		self._psionic_storm_started = False
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
		
		#see if we can research anything.
		if self.researchPsionicStorm():
			return

		self.label = 'Idle'
		
			
	def researchPsionicStorm(self):
		if self.game.units(HIGHTEMPLAR).amount >= 4 and not self._psionic_storm_started and not self._psionic_storm_researched:
			if AbilityId.RESEARCH_PSISTORM in self.abilities and self.game.can_afford(RESEARCH_PSISTORM):
				self.game.combinedActions.append(self.unit(AbilityId.RESEARCH_PSISTORM))
				self._psionic_storm_started = True
				self.current_research = 'PsionicStorm'
				self.game.can_spend = False
				return True

			

			
	def checkResearched(self):
		if self.current_research:
			if self.current_research == 'PsionicStorm':
				self._psionic_storm_researched = True
				self._psionic_storm_started = False
				self.current_research = None




			
		
	def resourcesSaved(self):
		if self.game._strat_manager.saving or not self.game.can_spend:
			return True			
			
			
			
			
			
		