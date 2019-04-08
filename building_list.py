import sc2
from sc2.constants import *
from sc2.position import Point2, Point3

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

	async def remove_object(self, unit_tag, game):
		self.game = game
		if self.building_objects.get(unit_tag):
			obj = self.building_objects.get(unit_tag)
			if obj.unit.name == 'Nexus':
				self.game.getDefensivePoint()
				self.game.expPos = await self.game.get_next_expansion()
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
	def underWorkerAllin(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Nexus' and v.underWorkerAllin }
		if len(baselist) > 0:
			return True
		return False
		
	@property
	def workersRequested(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Nexus' and v.needWorkers }
		if len(baselist) > 0:
			return True
		return False

	@property
	def underAttack(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Nexus' and v.underAttack }
		if len(baselist) > 0:
			return True
		return False

	@property
	def warpgateAvail(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'CyberneticsCore' and v.warpReady }
		if len(baselist) > 0:
			return True
		return False

	@property
	def pulseCrystalsAvail(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'FleetBeacon' and v.pulseCrystalsReady }
		if len(baselist) > 0:
			return True
		return False
	
	@property
	def chargeAvail(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Twilight' and v._charge_researched }
		if len(baselist) > 0:
			return True
		return False


	@property
	def extendedLanceAvail(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'RoboticsBay' and v.lanceReady }
		if len(baselist) > 0:
			return True
		return False

	@property
	def gatesQueued(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if (v.unit.name == 'WarpGate' or v.unit.name == 'Gateway') and not v.inQueue }
		if len(baselist) > 0:
			return False
		return True
		
	@property
	def stargatesQueued(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Stargate' and not v.inQueue }
		if len(baselist) > 0:
			return False
		return True
	
	@property
	def robosQueued(self) -> bool:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'RoboticsFacility' and not v.inQueue }
		if len(baselist) > 0:
			return False
		return True
	
	@property
	def allQueued(self) -> bool:
		blist = ['RoboticsFacility', 'Stargate', 'WarpGate', 'Gateway']
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name in blist and not v.inQueue }
		if len(baselist) > 0:
			return False
		return True

	@property
	def pylonsRequested(self) -> int:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Nexus' and v.pylonsRequested > 0 }
		pyr = 0
		for k, unitObj in baselist.items():
			pyr += unitObj.pylonsRequested
		return pyr

	@property
	def cannonsRequested(self) -> int:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Nexus' and v.cannonsRequested > 0 }
		pyr = 0
		for k, unitObj in baselist.items():
			pyr += unitObj.cannonsRequested
		return pyr
	
	@property
	def shieldsRequested(self) -> int:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Nexus' and v.shieldsRequested > 0 }
		pyr = 0
		for k, unitObj in baselist.items():
			pyr += unitObj.shieldsRequested
		return pyr

	@property
	def nextPylonLoc(self) -> Point2:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Nexus' and v.pylonsRequested > 0 }
		for k, unitObj in baselist.items():
			return unitObj.nextPylonPosition

	@property
	def nextFreePylonLoc(self) -> Point2:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Nexus' and v.pylonsRequested == 0 and v.next_pylon_location }
		for k, unitObj in baselist.items():
			return unitObj.nextPylonPosition
		
	@property
	def nextCannonLoc(self) -> Point2:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Nexus' and v.cannonsRequested > 0 }
		for k, unitObj in baselist.items():
			return unitObj.nextCannonPosition

	@property
	def nextShieldLoc(self) -> Point2:
		baselist = {k : v for k,v in self.building_objects.items() if v.unit.name == 'Nexus' and v.shieldsRequested > 0 }
		for k, unitObj in baselist.items():
			return unitObj.nextShieldPosition





