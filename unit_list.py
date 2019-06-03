import sc2
from sc2.constants import *

#our own classes
from unit_counters import UnitCounter
from warpprism import WarpPrism as wpControl
from immortal import Immortal as imControl
from stalker import Stalker as skControl
from zealot import Zealot as zlControl
from sentry import Sentry as snControl
from adept import Adept as adControl
from colossus import Colossus as coControl
from voidray import VoidRay as vrControl
from tempest import Tempest as tpControl
from phoenix import Phoenix as pxControl
from probe import Probe as pbControl
from shade import Shade as sdControl
from hightemplar import HighTemplar as htControl
from observer import Observer as obControl
from disruptor import Disruptor as dsControl
from disruptor_phased import DisruptorPhased as dpControl
from carrier import Carrier as crControl
from mothership import Mothership as msControl
from archon import Archon as arControl


class UnitList():

	def __init__(self):
		self.unit_objects = {}
		self.unitCounter = UnitCounter()

	def make_decisions(self, game):
		self.game = game
		
		for unit in self.game.units():
			obj = self.unit_objects.get(unit.tag)
			if obj:
				obj.make_decision(self.game, unit)

	def getObjectByTag(self, unit_tag):
		if self.unit_objects.get(unit_tag):
			return self.unit_objects.get(unit_tag)
		return None

	def remove_object(self, unit_tag):
		if self.unit_objects.get(unit_tag):
			unit_obj = self.unit_objects.get(unit_tag)
			#check to see if it's a probe, if so remove it from gathering.
			if unit_obj.unit.name == 'Probe':
				unit_obj.removeGatherer()
			if unit_obj.unit.name == 'DisruptorPhased':
				unit_obj.clearMines()
				unit_obj.clearLurkers()
			#check to see if it's our probe scout, if so create another.
			# if unit_obj.unit.name == 'Probe' and unit_obj.scout:
			# 	#was a scout, create a new one.
			# 	self.assignScout()
			del self.unit_objects[unit_tag]
			
		
	def load_object(self, unit):
		#print ('Unit Created:', unit.name, unit.tag)
		#check to see if an object already exists for this tag
		if self.getObjectByTag(unit.tag):
			return
		
		if unit.name == 'WarpPrism':
			obj = wpControl(unit)
			self.unit_objects.update({unit.tag:obj})
		elif unit.name == 'Immortal':
			obj = imControl(unit)
			self.unit_objects.update({unit.tag:obj})
		elif unit.name == 'Stalker':
			obj = skControl(unit)
			self.unit_objects.update({unit.tag:obj})			
		elif unit.name == 'Zealot':
			obj = zlControl(unit)
			self.unit_objects.update({unit.tag:obj})
		elif unit.name == 'Sentry':
			obj = snControl(unit)
			self.unit_objects.update({unit.tag:obj})
		elif unit.name == 'Adept':
			obj = adControl(unit)
			self.unit_objects.update({unit.tag:obj})				
		elif unit.name == 'Colossus':
			obj = coControl(unit)
			self.unit_objects.update({unit.tag:obj})
		elif unit.name == 'VoidRay':
			obj = vrControl(unit)
			self.unit_objects.update({unit.tag:obj})
		elif unit.name == 'Phoenix':
			obj = pxControl(unit)
			self.unit_objects.update({unit.tag:obj})
		elif unit.name == 'Probe':
			obj = pbControl(unit)
			self.unit_objects.update({unit.tag:obj})
		elif unit.name == 'Tempest':
			obj = tpControl(unit)
			self.unit_objects.update({unit.tag:obj})			
		elif unit.name == 'AdeptPhaseShift':
			obj = sdControl(unit)
			self.unit_objects.update({unit.tag:obj})
		elif unit.name == 'HighTemplar':
			obj = htControl(unit)
			self.unit_objects.update({unit.tag:obj})			
		elif unit.name == 'Observer':
			obj = obControl(unit)
			self.unit_objects.update({unit.tag:obj})			
		elif unit.name == 'Disruptor':
			obj = dsControl(unit)
			self.unit_objects.update({unit.tag:obj})
		elif unit.name == 'DisruptorPhased':
			obj = dpControl(unit)
			self.unit_objects.update({unit.tag:obj})
		elif unit.name == 'Carrier':
			obj = crControl(unit)
			self.unit_objects.update({unit.tag:obj})
		elif unit.name == 'Mothership':
			obj = msControl(unit)
			self.unit_objects.update({unit.tag:obj})
		elif unit.name == 'Archon':
			obj = arControl(unit)
			self.unit_objects.update({unit.tag:obj})			
		# else:
		# 	print ('Unit Created:', unit.name, unit.tag)
		

	def unitPosition(self, ownerUnit):
		if self.unit_objects.get(ownerUnit.tag):
			unit_obj = self.unit_objects.get(ownerUnit.tag)
			return unit_obj.saved_position
		return None		


	def phaseTargets(self):
		phaseList = {k : v for k,v in self.unit_objects.items() if v.unit.name == 'DisruptorPhased' }
		targets = []
		for key, phase in phaseList.items():
			targets.append(phase.currentTarget)
		return targets

	def adeptChaseTarget(self, ownerUnit):
		#get the object by the unit_tag.
		if self.unit_objects.get(ownerUnit.tag):
			unit_obj = self.unit_objects.get(ownerUnit.tag)
			return unit_obj.chasePosition
		return None
		

	def unitDamaged(self, ownerUnit):
		if self.unit_objects.get(ownerUnit.tag):
			unit_obj = self.unit_objects.get(ownerUnit.tag)
			return unit_obj.wasDamaged
		return False		

	def unitHomeTarget(self, ownerUnit):
		#get the object by the unit_tag.
		if self.unit_objects.get(ownerUnit.tag):
			unit_obj = self.unit_objects.get(ownerUnit.tag)
			return unit_obj.homeTarget
		return None

	def unitTarget(self, ownerUnit):
		#get the object by the unit_tag.
		if self.unit_objects.get(ownerUnit.tag):
			unit_obj = self.unit_objects.get(ownerUnit.tag)
			return unit_obj.last_target
		return None
	
	def disruptorBallCancel(self, owner_tag) -> bool:
		ballList = {k : v for k,v in self.unit_objects.items() if v.unit.type_id == DISRUPTORPHASED and v.requestCancel and v.ownerTag == owner_tag}
		if len(ballList) > 0:
			return True		
		return False

	def adeptOrder(self, ownerUnit):
		#get the object by the unit_tag.
		if self.unit_objects.get(ownerUnit.tag):
			unit_obj = self.unit_objects.get(ownerUnit.tag)
			return unit_obj.shadeOrder
		return None

	def assignScout(self):
		#if it's late in the game and we aren't attacking, then don't make a replacement.
		if self.game.defend_only and self.game.time > 360:
			return
		#find a probe to assign as a scout.
		probeList = {k : v for k,v in self.unit_objects.items() if v.unit.name == 'Probe' and not v.collect_only and not v.scout }
		for key, probe in probeList.items():
			probe.becomeScout()
			probe.removeGatherer()
			return
			

	def unitCount(self, unit_name):
		unitList = {k : v for k,v in self.unit_objects.items() if v.unit.name == unit_name }
		return len(unitList)

	def shieldSafe(self, inc_unit):
		#check for other sentries near by with shields that are active.
		shieldingList = {k : v for k,v in self.unit_objects.items() if v.unit.name == 'Sentry' and v.shieldActive and v.unit.distance_to(inc_unit.unit) < 2.5 }
		if len(shieldingList) > 0:
			return False
		return True

	def freeNexusBuilders(self):
		probeList = {k : v for k,v in self.unit_objects.items() if v.unit.name == 'Probe' and v.nexus_builder }
		if len(probeList) > 0:
			for key, probe in probeList.items():
				probe.nexus_builder = False
				probe.nexus_position = None

	@property
	def nexusBuilderAssigned(self) -> bool:
		probeList = {k : v for k,v in self.unit_objects.items() if v.unit.name == 'Probe' and v.nexus_builder }
		if len(probeList) > 0:
			return True
		return False


	@property
	def hallucinationScore(self) -> int:
		hallList = {k : v for k,v in self.unit_objects.items() if v.isHallucination }
		hall_score = 0
		for key, unit_obj in hallList.items():
			hall_score += self.unitCounter.getUnitPower(unit_obj.unit.name)
		return hall_score
		

	def phoenixScouting(self):
		phoenixList = {k : v for k,v in self.unit_objects.items() if v.unit.name == 'Phoenix' and v.isHallucination }
		if len(phoenixList) > 0:
			return True
		return False

	def getGravitonTarget(self, inc_unit):
		phoenixList = {k : v for k,v in self.unit_objects.items() if v.unit.name == 'Phoenix' and v.isBeaming }
		#print (len(phoenixList), inc_unit.unit.name, len(self.unit_objects))
		target = None
		#get the closest.
		mindist = 1000
		for key, phoenix in phoenixList.items():
			#get the distance to th
			if inc_unit.unit.position.to2.distance_to(phoenix.position.to2) < mindist:
				target = phoenix.beam_unit
				mindist = inc_unit.unit.position.to2.distance_to(phoenix.unit.position.to2)
		if mindist < 10:
			return target
		return None


	def getWorkers(self):
		return {k : v for k,v in self.unit_objects.items() if v.unit.name == 'Probe' }.items()


	def friendlyEngagedFighters(self, closestEnemy, friendRange=10):
		#find all the units near the closest Enemy that aren't retreating.
		baselist = {k : v for k,v in self.unit_objects.items() if v.unit.position.to2.distance_to(closestEnemy.position.to2) < friendRange }
		#find out how much DPS we have going on.
		friendDPStoGround = 0
		friendDPStoAir = 0
		friendAirHealth = 0
		friendGroundHealth = 0
		friendTotalDPS = 0
		for k, friendObj in baselist.items():
			if friendObj.unit.is_flying:
				friendAirHealth += friendObj.unit.health + friendObj.unit.shield
			else:
				friendGroundHealth += friendObj.unit.health + friendObj.unit.shield
			friendDPStoGround += friendObj.unit.ground_dps
			friendDPStoAir += friendObj.unit.air_dps
			if friendObj.unit.ground_dps > friendObj.unit.air_dps:
				friendTotalDPS += friendObj.unit.ground_dps
			else:
				friendTotalDPS += friendObj.unit.air_dps

		return [friendDPStoGround, friendDPStoAir, friendAirHealth, friendGroundHealth, friendTotalDPS]		
		

	def friendlyFighters(self, inc_unit, friendRange=10):
		#find all the units near the passed units position that aren't retreating.
		#baselist = {k : v for k,v in self.unit_objects.items() if not v.isRetreating and v.unit.position.to2.distance_to(inc_unit.position.to2) < friendRange }
		baselist = {k : v for k,v in self.unit_objects.items() if v.unit.position.to2.distance_to(inc_unit.position.to2) < friendRange }

		#find out how much DPS we have going on.
		friendDPStoGround = 0
		friendDPStoAir = 0
		friendAirHealth = 0
		friendGroundHealth = 0
		friendTotalDPS = 0
		for k, friendObj in baselist.items():
			if friendObj.unit.is_flying:
				friendAirHealth += friendObj.unit.health + friendObj.unit.shield
			else:
				friendGroundHealth += friendObj.unit.health + friendObj.unit.shield
			friendDPStoGround += friendObj.unit.ground_dps
			friendDPStoAir += friendObj.unit.air_dps
			if friendObj.unit.ground_dps > friendObj.unit.air_dps:
				friendTotalDPS += friendObj.unit.ground_dps
			else:
				friendTotalDPS += friendObj.unit.air_dps

		return [friendDPStoGround, friendDPStoAir, friendAirHealth, friendGroundHealth, friendTotalDPS]




	#properties.
	@property
	def amount(self) -> int:
		return len(self.unit_objects)

		
		

