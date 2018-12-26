import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.constants import *
from sc2.position import Point2, Point3
from sc2 import Race

'''
Phoenix Info
-----------------
Description: Air Unit
Built From: Stargate
Cost:
	Minerals: 150
	Vespene: 100
	GameSpeed: 25
	Supply: 2
Attributes: Light, Mechanical
Attack 1:
	Targets:	Air
	Damage:	 	5 (+1) (x2)
	DPS:	 	12.7 (+2.5)
	Cooldown:	0.79
	Bonus:	 	+5 vs Light
	Bonus DPS:	+12.7 vs Light
	Range:	 	5 (+2)
Defence:
	Health: 120
	Shield: 60
	Armor: 0 (+1)
Energy: 50 / 200
Sight: 10
Speed: 5.95
Strong against:
    Banshee
    Void Ray
    Mutalisk
Weak against:
    Battlecruiser
    Carrier
    Corruptor
'''
_debug = False

class Phoenix:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'
		self.scout = None
		self.beam_unit = None


	def make_decision(self, game, unit):
		self.saved_position = unit.position #first line always.
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)
		self.bonus_range = 0
		if self.game._science_manager._pulse_crystals_researched:
			self.bonus_range = 2

		
		if self.scout is None:
			if AbilityId.GRAVITONBEAM_GRAVITONBEAM in self.abilities:
				self.scout = False
			else:
				self.scout = True

		if self.scout:
			self.runScout()
		else:
			self.runList()

		if not 'gravitonbeam' in str(self.unit.orders).lower():
			self.beam_unit = None
		else:
			self.label = 'Beaming Debug'


		#debugging info
		if _debug or self.unit.is_selected:
			if self.last_target:
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, self.last_target, (155, 255, 25))
			self.game._client.debug_text_3d(self.label, self.unit.position3d)



	def runScout(self):
		#2 keep safe
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			if self.game.keepSafe(self):
				self.label = 'Retreating'
				return #staying alive

		#8 find the enemy
		if self.game.searchEnemies(self):
			self.label = 'Searching'
			return #looking for targets

		

	def runList(self):
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:		
			#1 priority is always attack first if we can
			#check to see if a phoenix near us is beaming something, if so let's attack it.
			if self.attackBeamed():
				self.label = 'Attacking Beamed'
				return #attacking the beamed unit
			
			if self.game.attack(self, self.bonus_range):
				self.label = 'Attacking'
				return #we attacked this step.
	
			#2 keep safe again.
			if self.game.keepSafe(self):
				if AbilityId.CANCEL_GRAVITONBEAM in self.abilities:
					self.beam_unit = None
					self.game.combinedActions.append(self.unit(AbilityId.CANCEL_GRAVITONBEAM))			
				self.label = 'Retreating Death'
				return #staying alive
	
			#3 priority is to keep our distance from enemies
			if self.game.KeepKiteRange(self, self.bonus_range):
				self.label = 'Kiting'
				return #kiting
	
			#4 check if we can beam someone up.
			if self.gravitonBeam():
				self.label = 'Beaming'
				return

			#look around our range and find the highest target value and move towards it.
			if (not self.game.defend_only or self.game.under_attack) and self.game.moveNearEnemies(self):
				self.label = 'Moving Priority Target'
				return #moving towards a better target.			
			
			
		#if we are in defend mode and we aren't under attack, then go to the defend point.
		if self.game.defend_only and not self.game.under_attack:
			self.game.defend(self)
			self.label = 'Defending'			
			return #defending.

		#move to friendly.
		if self.game.moveToFriendlies(self):
			self.label = 'Moving Friend'
			return #moving to friend.			
		
		#6 move the closest known enemy.
		if self.game.moveToEnemies(self):
			self.label = 'Moving Enemy'
			return #moving to next target.
		
		#7 wait until our shield is at 100%
		if self.unit.shield_percentage < 1:
			self.label = 'Full Regen'
			self.last_target = None	
			return #chillin until healed
			
		#8 find the enemy
		if self.game.searchEnemies(self):
			self.label = 'Searching'
			return #looking for targets

		self.label = 'Idle'

	
	def attackBeamed(self):
		targetEnemy = self.game.unitList.getGravitonTarget(self)
		if targetEnemy:
			self.game.combinedActions.append(self.unit.attack(targetEnemy))
			self.last_action = 'attack'
			self.last_target = Point3((targetEnemy.position3d.x, targetEnemy.position3d.y, (targetEnemy.position3d.z + 1)))

			if self.unit.is_selected or _debug:
				self.game._client.debug_line_out(self.game.unitDebugPos(self.unit), self.game.p3AddZ(targetEnemy.position3d), color=Point3((219, 4, 4)))
			return True
			
		return False
	
	
	def gravitonBeam(self):
		if self.unit.weapon_cooldown == 0 and not self.game.unitList.getGravitonTarget(self):    #make sure we aren't just between something else we could be attacking.
			ok_units = [PROBE, SCV, DRONE, IMMORTAL, MARAUDER, STALKER, REAPER, HELLION, CYCLONE, SIEGETANK, QUEEN, LURKER, INFESTOR, ROACH, RAVAGER, HIGHTEMPLAR, DARKTEMPLAR]
			if AbilityId.GRAVITONBEAM_GRAVITONBEAM in self.abilities:
				friends = self.game.units.filter(lambda x: x.can_attack_air).closer_than(8, self.unit)
				if friends.amount > 1:
				#make sure friendlies are around to attack it.
					closerEnemies = self.closestEnemies.of_type(ok_units).closer_than(8, self.unit)
					if closerEnemies:
						#look around for a unit to lift, giving priority to ones that can attack us.
						if closerEnemies.filter(lambda x: x.can_attack_air).exists:
							#take the one with the most hitpoints.
							target = closerEnemies.filter(lambda x: x.can_attack_air).sorted(lambda x: x.health + x.shield, reverse=True).first
							self.game.combinedActions.append(self.unit(AbilityId.GRAVITONBEAM_GRAVITONBEAM, target))
							self.beam_unit = target
							return True
						else:
							#lift any of them.
							target = closerEnemies.sorted(lambda x: x.health + x.shield, reverse=True).first
							self.game.combinedActions.append(self.unit(AbilityId.GRAVITONBEAM_GRAVITONBEAM, target))
							self.beam_unit = target
							return True				
					elif self.unit.energy > 100 and self.closestEnemies.not_flying.filter(lambda x: not x.is_massive).closer_than(8, self.unit).exists:
						#take the one with the most hitpoints.
						target = self.closestEnemies.not_flying.filter(lambda x: not x.is_massive).closer_than(8, self.unit).sorted(lambda x: x.health + x.shield, reverse=True).first
						self.game.combinedActions.append(self.unit(AbilityId.GRAVITONBEAM_GRAVITONBEAM, target))
						self.beam_unit = target
						return True
		return False
				
	
	
	def checkNewAction(self, action, posx, posy):
		actionStr = (action + '-' + str(posx) + '-' + str(posy))
		if actionStr == self.last_action:
			return False
		self.last_action = actionStr
		return True

	@property
	def position(self) -> Point2:
		return self.saved_position
		
	
	@property
	def isRetreating(self) -> bool:
		return self.retreating
	
	@property
	def isBeaming(self) -> bool:
		if self.beam_unit:
			return True
		return False
	


		
		
		
		
	