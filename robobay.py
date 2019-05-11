import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *

_debug = False

class RoboBay:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.label = 'Idle'
		#research flags.
		self._grav_boosters_researched = False
		self._extended_lance_researched = False
		self._grav_drive_researched = False

		self._grav_boosters_started = False
		self._extended_lance_started = False
		self._grav_drive_started = False

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
		
		#only build when queues are full to maximize military production
		if not self.game._strat_manager.allAllowedQueued:
			self.label = 'Building Military Instead'
			return
				
		#see if we can research anything.
		if self.researchGravBoosters():
			return 
		if self.researchGravDrive():
			return
		if self.researchExtendedLance():
			return
		
		self.label = 'Idle'
		
		
	
	
	def researchGravBoosters(self):
		if self.game.units(WARPPRISM).amount >= 2 and not self._grav_boosters_started and not self._grav_boosters_researched:
			if AbilityId.RESEARCH_GRAVITICBOOSTER in self.abilities and self.game.can_afford(RESEARCH_GRAVITICBOOSTER):
				self.game.combinedActions.append(self.unit(AbilityId.RESEARCH_GRAVITICBOOSTER))
				self._grav_boosters_started = True
				self.current_research = 'GravBoosters'
				self.game.can_spend = False
				return True

	def researchGravDrive(self):
		if self.game.units(OBSERVER).amount >= 4 and not self._grav_drive_started and not self._grav_drive_researched:
			if AbilityId.RESEARCH_GRAVITICDRIVE in self.abilities and self.game.can_afford(RESEARCH_GRAVITICDRIVE):
				self.game.combinedActions.append(self.unit(AbilityId.RESEARCH_GRAVITICDRIVE))
				self._grav_drive_started = True
				self.current_research = 'GravDrive'
				self.game.can_spend = False
				return True				

	def researchExtendedLance(self):
		if self.game.units(COLOSSUS).amount >= 1 and not self._extended_lance_started and not self._extended_lance_researched:
			if AbilityId.RESEARCH_EXTENDEDTHERMALLANCE in self.abilities and self.game.can_afford(RESEARCH_EXTENDEDTHERMALLANCE):
				self.game.combinedActions.append(self.unit(AbilityId.RESEARCH_EXTENDEDTHERMALLANCE))
				self._extended_lance_started = True
				self.current_research = 'ExtendedLance'
				self.game.can_spend = False
				return True	

			
	def checkResearched(self):
		if self.current_research:
			if self.current_research == 'GravBoosters':
				self._grav_boosters_researched = True
				self._grav_boosters_started = False
				self.current_research = None
			elif self.current_research == 'GravDrive':
				self._grav_drive_researched = True
				self._grav_drive_started = False
				self.current_research = None
			elif self.current_research == 'ExtendedLance':
				self._extended_lance_researched = True
				self._extended_lance_started = False
				self.current_research = None
			
		
	def resourcesSaved(self):
		if self.game._strat_manager.saving or not self.game.can_spend:
			return True			
			
			
	@property
	def lanceReady(self) -> bool:
		return self._extended_lance_researched
						
			
			
		