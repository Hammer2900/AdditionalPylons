import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *

_debug = True

class Twilight:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.label = 'Idle'
		#research flags.
		self._blink_researched = False
		self._charge_researched = False
		self._resonating_glaives_researched = False		
		
		self._blink_started = False
		self._charge_started = False
		self._resonating_glaives_started = False

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
		if self.researchCharge():
			return 
		if self.researchBlink():
			return
		if self.researchGlaives():
			return
		
		self.label = 'Idle'
	
	def researchCharge(self):
		if self.game.units(ZEALOT).amount > 2 and not self._charge_started and not self._charge_researched:
			if AbilityId.RESEARCH_CHARGE in self.abilities and self.game.can_afford(RESEARCH_CHARGE):
				self.game.combinedActions.append(self.unit(AbilityId.RESEARCH_CHARGE))
				self._charge_started = True
				self.current_research = 'Charge'
				self.game.can_spend = False
				return True

	def researchBlink(self):
		if self.game.units(STALKER).amount > 2 and not self._blink_started and not self._blink_researched:
			if AbilityId.RESEARCH_BLINK in self.abilities and self.game.can_afford(RESEARCH_BLINK):
				self.game.combinedActions.append(self.unit(AbilityId.RESEARCH_BLINK))
				self._blink_started = True
				self.current_research = 'Blink'
				self.game.can_spend = False
				return True				

	def researchGlaives(self):
		if self.game.units(ADEPT).amount > 2 and not self._resonating_glaives_started and not self._resonating_glaives_researched:
			if AbilityId.RESEARCH_ADEPTRESONATINGGLAIVES in self.abilities and self.game.can_afford(RESEARCH_ADEPTRESONATINGGLAIVES):
				self.game.combinedActions.append(self.unit(AbilityId.RESEARCH_ADEPTRESONATINGGLAIVES))
				self._resonating_glaives_started = True
				self.current_research = 'Glaives'
				self.game.can_spend = False
				return True	

			
	def checkResearched(self):
		if self.current_research:
			if self.current_research == 'Charge':
				self._charge_researched = True
				self._charge_started = False
				self.current_research = None
			elif self.current_research == 'Blink':
				self._blink_researched = True
				self._blink_started = False
				self.current_research = None
			elif self.current_research == 'Glaives':
				self._resonating_glaives_researched = True
				self._resonating_glaives_started = False
				self.current_research = None
			
		
	def resourcesSaved(self):
		if self.game._strat_manager.saving or not self.game.can_spend:
			return True			
			
			
			
			
			
		