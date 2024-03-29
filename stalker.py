import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

'''
Stalker Info
---------------------
Description: Ground Unit
Built From: Gateway
Cost:
	Minerals: 125
	Vaspene: 50
	GameSpeed: 30
	Supply: 2
Attributes: Armored, Mechanical
Attack 1:
	Targets:	Ground / Air
	Damage:	 	13 (+1)
	DPS:	 	9.7 (+0.75)
	Cooldown:	1.34
	Bonus:	 	+5 (+1) vs Armored
	Bonus DPS:	+3.7 (+0.75) vs Armored
	Range:	 	6
Defence:
	Health: 80
	Sheild: 80
	Armor: 1 (+1)
Sight: 10
Speed: 4.13
Cargo Size: 2
Strong against:
    Reaper
    Void Ray
    Mutalisk
Weak against:
    Marauder
    Immortal
    Zergling

'''
_debug = False

class Stalker:
	
	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'
		self.last_health = 0
		self.damaged = False
		self.comeHome = False
		self.homeTarget = None
		self.enemy_target_bonuses = {
			#gets bonus vs armored units.
			#Terran
			'Marauder': 5,
			'Thor': 5,
			'SiegeTank': 25,
			'SiegeTankSieged': 25,			
			'Medivac': 50,
			'SCV': 40,
			'Battlecruiser': 5,
			'Viking': 5,
			'VikingFighter': 5,
			'Cyclone': 5,
			'Liberator': 5,
			'WidowMine': 50,	
			'WidowMineBurrowed': 50,		
			'Raven': 51,
			'Banshee': 20,
			#Protoss
			'Stalker': 5,
			'WarpPrism': 5,
			'Immortal': 5,
			'VoidRay': 5,
			'Tempest': 5,
			'Disruptor': 5,
			'Carrier': 5,
			#Zerg
			'Roach': 5,
			'Infestor': 30,
			'Ultralisk': 5,
			'Overlord': -100, #no reason to attack them first.
			'Overseer': 5,
			'Corruptor': 5,
			'Brood Lord': 5,
		}		
		
	def make_decision(self, game, unit):
		self.game = game
		self.stalker = unit
		self.unit = unit
		self.saved_position = self.unit.position
		self.abilities = self.game.allAbilities.get(self.unit.tag)
		
		self.trackHealth()
		
		self.runList()
	

		#debugging info
		if _debug or self.unit.is_selected:
			if self.last_target:
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, self.last_target, color=Point3((155, 255, 25)))
	
			self.game._client.debug_text_3d(self.label, self.unit.position3d)
		
		
		
		
	def runList(self):
		if not self.unit.is_ready:
			return #warping in		
			#keep safe from effects
		if self.game.effectSafe(self):
			self.label = 'Dodging'
			return #dodging effects.
		
		#check if we need to come home and defend.
		self.comeHome = self.game.checkHome(self)
		
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			
			
			
			#1 priority is always attack first if we can
			if self.game.attack(self):
				self.label = 'Attacking'
				return #we attacked this step.
			
			#check to see if we need to blink out of damage.
			if self.defensiveBlink():
				self.label = 'Defensive Blink'
				return

			#see if we need to evaluate the battle before entering it.
			if self.game.waitForce(self):
			 	self.label = 'Waiting for reinforcements'
			 	return #staying alive

			
			#1a check to see if we are even able to retreat.
			if self.game.canEscape(self):
				#1b priority is to save our butts if we can because we have to stop to attack.
				if self.game.keepSafe(self):
					self.label = 'Retreating Safe'
					return #staying alive
			else:
				#see if we can blink out of it.
				if self.blinkRetreat():
					self.label = 'Blinking'
					return #trying to blink away.

			#2 keep safe again.
			if self.game.keepSafe(self):
				self.label = 'Retreating Death'
				return #staying alive
	
			#3 priority is to keep our distance from enemies
			if self.game.KeepKiteRange(self):
				self.label = 'Kiting'
				return #kiting
			
			#look around our range and find the highest target value and move towards it.
			if (not self.game.defend_only or self.game.under_attack) and self.game.moveNearEnemies(self):
				self.label = 'Moving Priority Target'
				return #moving towards a better target.

			
		
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
						
		#8 find the enemy
		if self.game.searchEnemies(self):
			self.label = 'Searching'
			return #looking for targets


	def offensiveBlink(self, targetEnemy):
		#make sure we can even blink.
		if AbilityId.EFFECT_BLINK_STALKER in self.abilities and self.game.can_afford(EFFECT_BLINK_STALKER):
			#check to see if the target is running away from us.
			useblink = False
			lead_position = self.game.leadTarget(targetEnemy, self)
			#get distance from unit to enemy and distance from unit to lead position.
			enemy_distance = self.unit.distance_to(targetEnemy)
			
			if targetEnemy.movement_speed >= self.unit.movement_speed and enemy_distance < 11 and enemy_distance > 6:
				useblink = True
			elif targetEnemy.movement_speed < self.unit.movement_speed and enemy_distance > 9:
				useblink = True
				
			#check if they are on differnt ground level and blink to them then in the future.
			
			if useblink:
				overall = self.unit.distance_to(lead_position) - enemy_distance
				if overall > 0:
					#unit is running away, blink towards them.
					blinkPoint = self.unit.position.towards(targetEnemy.position, distance=5.5)
					if blinkPoint:
						#check to make sure we aren't about to blink into a bunch of other units who want to kill us.
						possibles = self.closestEnemies.filter(lambda x: x.can_attack_ground and x.distance_to(blinkPoint) <= (x.ground_range + x.radius + self.unit.radius + 1) and self.game.targetFacing(self, x))
						if len(possibles) == 0:
							if self.checkNewAction('blink', blinkPoint[0], blinkPoint[1]):
								self.game.combinedActions.append(self.unit(AbilityId.EFFECT_BLINK_STALKER, blinkPoint))
							self.last_target = blinkPoint.position
							return True
		return False

	def blinkRetreat(self):
		self.retreating = True
		if AbilityId.EFFECT_BLINK_STALKER in self.abilities and self.game.can_afford(EFFECT_BLINK_STALKER):
			retreatPoint = self.game.findGroundRetreatTarget(self.unit, inc_size=6, enemy_radius=10)
			if retreatPoint:
				if self.checkNewAction('blink', retreatPoint[0], retreatPoint[1]):
					self.game.combinedActions.append(self.unit(AbilityId.EFFECT_BLINK_STALKER, retreatPoint))
				self.last_target = retreatPoint.position
				return True
		return False		


	def defensiveBlink(self):
		if self.damaged and self.unit.shield == 0:
			if AbilityId.EFFECT_BLINK_STALKER in self.abilities and self.game.can_afford(EFFECT_BLINK_STALKER):
				retreatPoint = self.game.findGroundRetreatTarget(self.unit, inc_size=6, enemy_radius=10)
				if retreatPoint:
					if self.checkNewAction('blink', retreatPoint[0], retreatPoint[1]):
						self.game.combinedActions.append(self.unit(AbilityId.EFFECT_BLINK_STALKER, retreatPoint))
					self.last_target = retreatPoint.position
					return True
		return False


	def trackHealth(self):
		if (self.unit.health + self.unit.shield) < self.last_health:
			self.damaged = True
		self.last_health = self.unit.health + self.unit.shield


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
	def isHallucination(self) -> bool:
		return False
	
	@property
	def sendHome(self) -> bool:
		return self.comeHome					
