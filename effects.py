from sc2.constants import *
from sc2 import Race
from sc2.position import Point2, Point3


'''
This class is inherited by the main class
Tracks effects so units can dodge.

'''

class Effects():
		
	def addEffects(self):
		#clear the existing arrays.
		self.dodge_positions = []
		self.air_dodge_positions = []
		self.obs_dodge_positions = []
		#loop effects and parse what we need.
		for effect in self.state.effects:
			if effect.id in [EffectId.RAVAGERCORROSIVEBILECP]:
				for position in effect.positions:
					self.dodge_positions.append([position, 0.5])
					self.air_dodge_positions.append([position, 0.5])
					self.obs_dodge_positions.append([position, 0.5])
			elif effect.id in [EffectId.LURKERMP]:
				for position in effect.positions:
					self.dodge_positions.append([position, 0.5])
			elif effect.id in [EffectId.PSISTORMPERSISTENT]:
				for position in effect.positions:
					self.dodge_positions.append([position, 1.5])
					self.air_dodge_positions.append([position, 1.5])
					self.obs_dodge_positions.append([position, 1.5])
			elif effect.id in [EffectId.SCANNERSWEEP]:
				for position in effect.positions:
					self.obs_dodge_positions.append([position, 13.5])

		if len(self.cached_enemies.of_type([MISSILETURRET,RAVEN,OBSERVER,OVERSEER,PHOTONCANNON,SPORECRAWLER])) > 0:
			for unit in self.cached_enemies.of_type([MISSILETURRET,RAVEN]):
				self.obs_dodge_positions.append([unit.position, 11.5])

		#widow mine tracking
		if self.enemy_race == Race.Terran:
			self.trackWidowmines()

		#lurker tracking
		if self.enemy_race == Race.Zerg:
			self.trackLurkers()

		if len(self.units(DISRUPTORPHASED)) > 0:
			#get their target position and their position
			# targets = self.unitList.phaseTargets()
			# for position in targets:
			# 	if position:
			# 		self.dodge_positions.append([position, 2.5])

			for unit in self.units(DISRUPTORPHASED):
				self.dodge_positions.append([unit.position, 2.5])

		if len(self.cached_enemies.of_type([DISRUPTORPHASED,BANELING])) > 0:
			for unit in self.cached_enemies.of_type([DISRUPTORPHASED,BANELING]):
				self.dodge_positions.append([unit.position, 2.5])

		if len(self.burrowed_mines) > 0:
			for unit_tag, [position, lastseen] in self.burrowed_mines.items():
				self.dodge_positions.append([position, 5.8])
				self.air_dodge_positions.append([position, 5.8])

		# if len(self.burrowed_lurkers) > 0:
		# 	for unit_tag, position in self.burrowed_lurkers.items():
		# 		self.dodge_positions.append([position, 5.5])




	def debugEffects(self):
		#loop effects and add a circle at their position and radius.
		for [position, radius] in self.dodge_positions:
			self._client.debug_sphere_out(self.turn3d(position), radius, Point3((132, 0, 66))) #purple


	def trackLurkers(self):
		if len(self.cached_enemies(LURKERMPBURROWED)) > 0:
			for unit in self.cached_enemies(LURKERMPBURROWED):
				self.burrowed_lurkers.update({unit.tag:unit.position})
		#remove all widowmines from the list.
		if len(self.cached_enemies(LURKERMP)) > 0:
			for unit in self.cached_enemies(LURKERMP):
				self.removeLurker(unit.tag)


	def removeLurker(self, unit_tag):
		if self.burrowed_lurkers.get(unit_tag):
			#found remove it.
			del self.burrowed_lurkers[unit_tag]

	def trackWidowmines(self):
		if len(self.cached_enemies(WIDOWMINEBURROWED )) > 0:
			for unit in self.cached_enemies(WIDOWMINEBURROWED ):
				self.burrowed_mines.update({unit.tag:[unit.position, self.time]})
		#remove all widowmines from the list.
		if len(self.cached_enemies(WIDOWMINE)) > 0:
			for unit in self.cached_enemies(WIDOWMINE):
				self.removeWidowmine(unit.tag)
		#remove expired widowmines from the list.
		if len(self.burrowed_mines) > 0:
			removals = []
			for unit_tag, [position, lastseen] in self.burrowed_mines.items():
				if lastseen < self.time - 10:
					removals.append(unit_tag)
			for unit_tag in removals:
				self.removeWidowmine(unit_tag)


	def removeWidowmine(self, unit_tag):
		if self.burrowed_mines.get(unit_tag):
			#found remove it.
			del self.burrowed_mines[unit_tag]
			
			
			
