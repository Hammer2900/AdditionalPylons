import sc2
from sc2.constants import *

#our own classes
from gateway import Gateway as gwControl
from robo import Robo as rbControl
from stargate import Stargate as sgControl
from nexus import Nexus as nxControl
from cybercore import CyberCore as ccControl
from forge import Forge as fgControl
from twilight import Twilight as tcControl
from robobay import RoboBay as byControl
from fleet import Fleet as fbControl
from archive import Archive as taControl


class BuildingList():

	def __init__(self):
		self.building_objects = {}
		

	async def make_decisions(self, game):
		self.game = game
		for unit in self.game.units():
			obj = self.building_objects.get(unit.tag)
			if obj:
				await obj.make_decision(self.game, unit)

	def getObjectByTag(self, unit_tag):
		if self.building_objects.get(unit_tag):
			return self.building_objects.get(unit_tag)
		return None

	def remove_object(self, unit_tag):
		if self.building_objects.get(unit_tag):
			del self.building_objects[unit_tag]
		
	def load_object(self, unit):
		#print ('Unit Created:', unit.name, unit.tag)
		#check to see if an object already exists for this tag
		if self.getObjectByTag(unit.tag):
			return
		
		if unit.name == 'Gateway':
			obj = gwControl(unit)
			self.building_objects.update({unit.tag:obj})
		elif unit.name == 'RoboticsFacility':
			obj = rbControl(unit)
			self.building_objects.update({unit.tag:obj})				
		elif unit.name == 'Stargate':
			obj = sgControl(unit)
			self.building_objects.update({unit.tag:obj})
		elif unit.name == 'Nexus':
			obj = nxControl(unit)
			self.building_objects.update({unit.tag:obj})
		elif unit.name == 'CyberneticsCore':
			obj = ccControl(unit)
			self.building_objects.update({unit.tag:obj})
		elif unit.name == 'Forge':
			obj = fgControl(unit)
			self.building_objects.update({unit.tag:obj})			
		elif unit.name == 'TwilightCouncil':
			obj = tcControl(unit)
			self.building_objects.update({unit.tag:obj})			
		elif unit.name == 'RoboticsBay':
			obj = byControl(unit)
			self.building_objects.update({unit.tag:obj})				
		elif unit.name == 'FleetBeacon':
			obj =fbControl(unit)
			self.building_objects.update({unit.tag:obj})
		elif unit.name == 'TemplarArchive':
			obj =taControl(unit)
			self.building_objects.update({unit.tag:obj})
						
			
			
		#else:
		# 	print ('Unit Created:', unit.name, unit.tag)
		
	@property
	def workersRequested(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Nexus' and v.needWorkers }
		if len(baselist) > 0:
			return True


	@property
	def underAttack(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Nexus' and v.underAttack }
		if len(baselist) > 0:
			return True

	@property
	def warpgateAvail(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'CyberneticsCore' and v.warpReady }
		if len(baselist) > 0:
			return True

	@property
	def pulseCrystalsAvail(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'FleetBeacon' and v.pulseCrystalsReady }
		if len(baselist) > 0:
			return True

	@property
	def extendedLanceAvail(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'RoboticsBay' and v.lanceReady }
		if len(baselist) > 0:
			return True




