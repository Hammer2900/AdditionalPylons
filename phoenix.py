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
		self.beam_unit = None
		self.base_searched = False
		self.beam_move_target = None
		self.bonus_range = 0
		self.is_hallucination = None
		self.comeHome = False
		self.homeTarget = None
		self.enemy_target_bonuses = {
			#gets bonus vs light units.
			#Terran
			'Medivac': 40,
			'Raven': 41,
			'Banshee': 10,
			#Protoss
			'Phoenix': 5,
			'Observer': 10,
			#Zerg
			'Mutalisk': 5,
			'Overlord': -100, #no reason to attack them first.
		}		


	def make_decision(self, game, unit):
		self.saved_position = unit.position #first line always.
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)
		self.bonus_range = 0
		self.beam_move_target = None
		if self.game.buildingList.pulseCrystalsAvail:
			self.bonus_range = 2
			
		if self.is_hallucination is None:
			if AbilityId.GRAVITONBEAM_GRAVITONBEAM in self.abilities:
				self.is_hallucination = False
			else:
				self.is_hallucination = True

		if self.is_hallucination:
			self.runScout()
		else:
			self.runList()

		if not 'gravitonbeam' in str(self.unit.orders).lower():
			self.beam_unit = None

		#debugging info
		if _debug or self.unit.is_selected:
			if self.last_target:
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, self.last_target, color=Point3((155, 255, 25)))
			self.game._client.debug_text_3d(self.label, self.unit.position3d)



	def runScout(self):
		#2 keep safe
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			if self.game.keepSafe(self):
				self.label = 'Retreating'
				return #staying alive

		#8 find the enemy
		if self.searchEnemies():
			self.label = 'Searching'
			return #looking for targets

		

	def runList(self):

		#enemies around us mode.
		if self.game.effectSafe(self):
			self.label = 'Dodging'
			return #dodging effects.
		
		#check if we need to come home and defend.
		self.comeHome = self.game.checkHome(self)

		
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
				# if AbilityId.CANCEL_GRAVITONBEAM in self.abilities:
				# 	self.beam_unit = None
				# 	self.game.combinedActions.append(self.unit(AbilityId.CANCEL_GRAVITONBEAM))			
				self.label = 'Retreating Death'
				return #staying alive
	
			#3 priority is to keep our distance from enemies
			if self.game.KeepKiteRange(self, self.bonus_range):
				self.label = 'Kiting'
				return #kiting
	
			#look around our range and find the highest target value and move towards it.
			if (not self.game.defend_only or self.game.under_attack) and self.game.moveNearEnemies(self):
				self.label = 'Moving Priority Target'
				return #moving towards a better target.			

			#4 check if we can beam someone up.
			# if self.gravitonBeam():
			# 	self.label = 'Beaming'
			# 	return
			
			
		#if we are in defend mode and we aren't under attack, then go to the defend point.
		if self.game.defend_only and not self.game.under_attack:
			self.game.defend(self)
			self.label = 'Defending'			
			return #defending.
		
		#move to rally point before attacking:
		if self.game.moveRally and not self.game.under_attack:
			self.game.rally(self)
			self.label = 'Rallying'
			return #moving to rally
		
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
		
		if self.closestEnemies.amount == 0:
			#8 find the enemy
			if self.game.searchEnemies(self):
				self.label = 'Searching'
				return #looking for targets
		else:
			#see if gravbeam is up, if so, find a target to get with it.
			if self.gravTarget():
				self.label = 'Moving Grav'
				return

		self.label = 'Idle'

	def gravTarget(self):
		if AbilityId.GRAVITONBEAM_GRAVITONBEAM in self.abilities:
			pickup_target = None
			
			ok_units = [PROBE, SCV, DRONE, IMMORTAL, MARAUDER, STALKER, REAPER, HELLION, CYCLONE, SIEGETANK, QUEEN, LURKER, INFESTOR, ROACH, RAVAGER, HIGHTEMPLAR, DARKTEMPLAR]
			pickables = self.closestEnemies.of_type(ok_units)
			if len(pickables) > 0:
				#look around for a unit to lift, giving priority to ones that can attack us.
				if len(pickables.filter(lambda x: x.can_attack_air)) > 0:
					#take the one with the most hitpoints.
					pickup_target = pickables.filter(lambda x: x.can_attack_air).sorted(lambda x: x.health + x.shield, reverse=True).first
				else:
					#lift any of them.
					pickup_target = pickables.sorted(lambda x: x.health + x.shield, reverse=True).first
			elif self.unit.energy > 100 and len(self.closestEnemies.filter(lambda x: not x.is_structure and not x.is_flying and not x.is_massive)) > 0:
				#pick up the one closest to us.
				pickup_target = self.closestEnemies.filter(lambda x: not x.is_flying and not x.is_massive).sorted(lambda x: x.health + x.shield, reverse=True).first
			if pickup_target:
				#check to see if we are in range to pickup, otherwise move to it.
				if self.unit.distance_to(pickup_target) > 4:
					if self.checkNewAction('move', pickup_target.position[0], pickup_target.position[1]):
						self.game.combinedActions.append(self.unit.move(self.game.leadTarget(pickup_target, self)))
					self.beam_move_target = pickup_target
					return True
				else:
					self.game.combinedActions.append(self.unit(AbilityId.GRAVITONBEAM_GRAVITONBEAM, pickup_target))
					self.beam_unit = pickup_target
					return True				
			
		return False

	def searchEnemies(self):
		#search for enemies
		if self.unit.is_moving:
			return True #moving somewhere already
		#go to the enemy base first.
		startPos = random.choice(self.game.enemy_start_locations)
		if self.unit.distance_to(startPos) > 10 and not self.base_searched:
			self.game.combinedActions.append(self.unit.move(startPos))
			self.last_target = Point3((startPos.position.x, startPos.position.y, self.game.getHeight(startPos.position)))
			return True
		else:
			self.base_searched = True
				
		searchPos = self.game.getSearchPos(self.unit)
		if self.checkNewAction('move', searchPos[0], searchPos[1]):
			self.game.combinedActions.append(self.unit.move(searchPos))
			self.last_target = Point3((searchPos.position.x, searchPos.position.y, self.game.getHeight(searchPos.position)))
		return True
	
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
				friends = self.game.units.filter(lambda x: x.can_attack_air).closer_than(3, self.unit)
				if friends.amount > 1:
				#make sure friendlies are around to attack it.
					closerEnemies = self.closestEnemies.of_type(ok_units).closer_than(4, self.unit)
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
					elif self.unit.energy > 100 and self.closestEnemies.not_flying.filter(lambda x: not x.is_massive).closer_than(4, self.unit).exists:
						#take the one with the most hitpoints.
						target = self.closestEnemies.not_flying.filter(lambda x: not x.is_massive).closer_than(8, self.unit).sorted(lambda x: x.health + x.shield, reverse=True).first
						self.game.combinedActions.append(self.unit(AbilityId.GRAVITONBEAM_GRAVITONBEAM, target))
						self.beam_unit = target
						return True
		return False
					
	
	def getTargetBonus(self, targetName):
		if self.enemy_target_bonuses.get(targetName):
			return self.enemy_target_bonuses.get(targetName)
		else:
			return 0	
	
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
	
	@property
	def isMovingBeamTarget(self) -> bool:
		if self.beam_move_target:
			return True
		return False

	@property
	def isHallucination(self) -> bool:
		if self.is_hallucination:
			return True
		return False
	
	@property
	def sendHome(self) -> bool:
		return self.comeHome	
		
		
		
		
	