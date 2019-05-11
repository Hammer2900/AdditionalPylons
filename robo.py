import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3
from unit_counters import UnitCounter


_debug = False

class Robo:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.label = 'Idle'
		self.queued = False
		self.unitCounter = UnitCounter()
		self.trainList = ['Immortal', 'WarpPrism', 'Colossus', 'Disruptor', 'Observer']
		
		
		
	async def make_decision(self, game, unit):
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)
		self.queueStatus()

		if self.unit.is_idle:
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

		if self.trainUnit():
			return
		
		if self.trainObservers():
			return
		
		
	def trainObservers(self):
		#train observers if under the min.
		if self.game.can_spend and not self.game.under_attack and self.game._strat_manager.army_power > 40 and self.game.units(OBSERVER).amount < 2:
			self.game.combinedActions.append(self.unit.train(OBSERVER))
			self.game.can_spend = False
			return True
		return False

	
	def trainUnit(self):
		#make sure we can spend.
		if not self.game.can_spend:
			self.label = 'No spending allowed'
			return
		#get unit to train
		trainee = self.bestTrain()
		if trainee == 'Observer' and len(self.game.units(OBSERVER)) >= 5:
			return False
		if trainee:
			self.game.combinedActions.append(self.unit.train(self.unitCounter.getUnitID(trainee)))
			self.game.can_spend = False
			return True
		return False

		
	def resourcesSaved(self):
		if self.game._strat_manager.saving:
			return True
	
		
	#utilities
	
	def canBuild(self, trainee):
		if self.game.can_afford(self.unitCounter.getUnitID(trainee)):
			return True
		
	
	
	def bestTrain(self):
		#if it's been at least 7 minutes in the game, make a warpprism if one doesn't exist.
		if self.game.trueGates >= 3 and len(self.game.units.of_type([WARPPRISMPHASING,WARPPRISM])) == 0 and not self.game.already_pending(WARPPRISM):
			return 'WarpPrism'
		
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
		if self.game.minerals > 550 and self.game.vespene > 500:
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
		if self.unit.is_idle:
			self.queued = False
		else:
			self.queued = True		
			
	
	@property
	def inQueue(self) -> bool:
		return self.queued


		
			