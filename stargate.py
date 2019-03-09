import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3
from unit_counters import UnitCounter


_debug = False

class Stargate:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.label = 'Idle'
		self.queued = False
		self.unitCounter = UnitCounter()
		self.trainList = ['VoidRay', 'Phoenix', 'Tempest', 'Carrier']
		
		
		
	async def make_decision(self, game, unit):
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)
		self.queueStatus()

		if self.unit.noqueue:
			await self.runList()
		else:
			self.label = "Busy {}".format(str(len(self.abilities)))

		#debugging info
		if _debug or self.unit.is_selected:
			self.game._client.debug_text_3d(self.label, self.unit.position3d)

	async def runList(self):

		#check to see if saving resources are being requested.
		if self.resourcesSaved():
			self.label = 'Resources being saved'
			return

		if await self.trainUnit():
			return
		

	
	
	
	async def trainUnit(self):
		#make sure we can spend.
		if not self.game.can_spend:
			self.label = 'No spending allowed'
			return
		#get unit to train
		trainee = self.bestTrain()
		if trainee:
			self.game.combinedActions.append(self.unit.train(self.unitCounter.getUnitID(trainee)))
			self.game.can_spend = False
			return True

		
	def resourcesSaved(self):
		if self.game._strat_manager.saving:
			return True
	
		
	#utilities
	
	def canBuild(self, trainee):
		if self.game.can_afford(self.unitCounter.getUnitID(trainee)):
			return True
		
	
	
	def bestTrain(self):
		bestName = None
		bestCount = -1
		bestNeeded = False
		for name, count in self.game._strat_manager.able_army.items():
			#check if its one of our types.
			if name in self.trainList:
				#check if it's needed or not.
				if self.game._strat_manager.check_allowed(name):
					bestNeeded = True
					if self.canBuild(name) and count > bestCount:
						bestName = name
						bestCount = count
		if bestName:
			self.label = "Best {}".format(bestName)
			return bestName
		if bestNeeded:
			self.label = 'need resources'
			return None
				
		#apparently couldn't build anything in the ideal list that is being allowed, check for anything to build.
		#if minerals are backing up, then go ahead and build anything.
		if self.game.minerals > 550:
			bestName = None
			bestCount = -1		
			for name, count in self.game._strat_manager.able_army.items():
				#check if its one of our types.
				if name in self.trainList:
					#check if it's needed or not.
					if self.canBuild(name):
						if count > bestCount:
							bestName = name
							bestCount = count
			if bestName:
				self.label = "2nd {}".format(bestName)
				return bestName
			
		self.label = 'Allowing resources elsewhere'
		return None
	

	def queueStatus(self):
		if self.unit.noqueue:
			self.queued = False
		else:
			self.queued = True		
			
	
	@property
	def inQueue(self) -> bool:
		return self.queued


		
			