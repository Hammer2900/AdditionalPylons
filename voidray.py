import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

'''
Void Ray Info
-----------------
Description: Large Air Unit
Built From: Stargate
Cost:
	Minerals: 250
	Vespene: 150
	GameSpeed: 43
	Supply: 4
Attributes: Armored, Mechanical
Attack 1:
	Targets:	Ground / Air
	Damage:	 	6 (+1)
	DPS:	 	16.8 (+2.8)
	Cooldown:	0.36 s
	Bonus:	 	+4 vs Armored
				+10 vs Armored (Prismatic Alignment)
	Bonus DPS:	 +11.2 vs Armored
				+28 vs Armored (Prismatic Alignment)
	Range:	 	6
Defence:
	Health: 150
	Shield: 100
	Armor: 0 (+1)
Sight: 10
Speed: 3.5 (-1.4 with Prismatic Alignment)
Strong against:
    Corruptor
    Battlecruiser
    Tempest
Weak against:
    Viking
    Phoenix
    Mutalisk
'''
_debug = False

class VoidRay:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'
		self.last_attack_start = 0
		self.is_hallucination = None
		self.comeHome = False
		self.homeTarget = None
		self.enemy_target_bonuses = {
			#gets bonus vs armored units.
			#Terran
			'Marauder': 10,
			'Thor': 5,
			'SiegeTank': 25,
			'SiegeTankSieged': 25,			
			'Medivac': 30,
			'SCV': 40,
			'Battlecruiser': 5,
			'Viking': 5,
			'VikingFighter': 5,
			'Cyclone': 5,
			'Liberator': 5,
			'WidowMine': 30,	
			'WidowMineBurrowed': 50,		
			'Raven': 25,
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
		self.saved_position = unit.position #first line always.
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)
		
		if self.is_hallucination is None:
			self.check_hallucination()
		
		if self.is_hallucination:
			self.runHallList()
		else:
			self.runList()
		
		#debugging info
		if _debug or self.unit.is_selected:
			if self.last_target:
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, self.last_target, color=Point3((155, 255, 25)))
			self.game._client.debug_text_3d(self.label, self.unit.position3d)

	def runList(self):

		#enemies around us mode.
		if self.game.effectSafe(self):
			self.label = 'Dodging'
			return #dodging effects.
		
		#check if we need to come home and defend.
		self.comeHome = self.game.checkHome(self)


		#get all the enemies around us.
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:

			#see if we are able to escape if needed.
			if self.game.canEscape(self) and self.game.keepSafe(self):
				self.cancelPrismatic()
				self.label = 'Retreating Safe'
				return #staying alive
			
			# if (self.last_attack_start + 1.305) > self.game.time:
			# 	self.label = 'Continued Attacking'
			# 	return #still attacking.

			#1 priority is always attack first if we can
			if self.game.attack(self):
				self.last_attack_start = self.game.time
				self.label = 'Attacking'
				return #we attacked this step.
	
			#1b see if we need to buff up our dps for target.
			if self.armorDPSBuff():
				self.label = 'Buffing'
				return #activating buff.
	
			#2 keep safe again.
			if self.game.keepSafe(self):
				self.cancelPrismatic()				
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


	def runHallList(self):
		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			#look around our range and find the highest target value and move towards it.
			if self.moveNearEnemies(self):
				self.label = 'Hall Moving Priority Target'
				return #moving towards a better target.			
			return #moving to friend.
					
		#6 move the closest known enemy.
		if self.game.moveToEnemies(self):
			self.label = 'Hall Moving Enemy'
			return #moving to next target.
					
		#8 find the enemy
		if self.game.searchEnemies(self):
			self.label = 'Hall Searching'
			return #looking for targets

		self.label = 'Idle'		

	def check_hallucination(self):
		#if a robo is near us, then likely not a hallucination.
		if len(self.game.units(STARGATE)) == 0:
			self.is_hallucination = True
			return
		
		#robo exist in game, see if it's closer than 4 distance away.
		if self.game.units(STARGATE).closer_than(4, self.unit):
			self.is_hallucination = False
			return
		else:
			self.is_hallucination = True
			return
		self.is_hallucination = False


	def moveNearEnemies(self, unit_obj):
		if not self.closestEnemies:
			return False  # no enemies to move to
		
		#find the center of enemies and move to it to draw fire.
		targetPoint = self.game.findDrawFireTarget(self, 10)
		
		if targetPoint:
			if self.checkNewAction('move', targetPoint.position.x, targetPoint.position.y):
				self.game.combinedActions.append(self.unit.move(targetPoint.position))
			return True
		return False

	def cancelPrismatic(self):
		if AbilityId.VOIDRAYSWARMDAMAGEBOOSTCANCEL_CANCEL in self.abilities and self.game.can_afford(VOIDRAYSWARMDAMAGEBOOSTCANCEL_CANCEL):
			self.game.combinedActions.append(self.unit(AbilityId.VOIDRAYSWARMDAMAGEBOOSTCANCEL_CANCEL))
			return True
				
	def armorDPSBuff(self):
		targetEnemy = self.game.findBestTarget(self)
		if targetEnemy:
			if targetEnemy.is_armored:
				if AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT in self.abilities and self.game.can_afford(EFFECT_VOIDRAYPRISMATICALIGNMENT):
					self.game.combinedActions.append(self.unit(AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT))
					return True


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
		if self.is_hallucination:
			return True
		return False
	
	@property
	def sendHome(self) -> bool:
		return self.comeHome	
		
		
	


		
		
		
		
	