import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

'''
High Templar Info
-----------------
Attributes: Biological, Light, Psionic
Attack 1:
	Targets: 	Ground
	Damage:		4 (+1)
	DPS:	 	3.2 (+0.8)
	Cooldown:	 	1.25
	Range:	 	6
Defence:
	Hitpoints: 40
	Shield: 40
	Armor: 0 (+1)
Energy: 50 / 200
Sight: 10
Speed: 2.62
Cargo Size: 2
Strong against:
    Marine
    Sentry
    Hydralisk
Weak against:
    Ghost
    Colossus
    Roach
'''

_debug = True

class HighTemplar:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.retreating = False
		self.saved_position = None
		self.last_action = ''
		self.last_target = None
		self.label = 'Idle'
		self.attack_range = 6
		self.comeHome = False
		self.homeTarget = None
		self.enemy_target_bonuses = {
			'SCV': 100,
			'SiegeTank': 300,
			'Infestor': 300,
			'WidowMine': 300,	
		}		

	def make_decision(self, game, unit):
		self.saved_position = unit.position #first line always.
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)
	
		self.runList()
	
		#debugging info
		if _debug or self.unit.is_selected:
			if self.last_target:
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, self.last_target, (155, 255, 25))
			self.game._client.debug_text_3d(self.label, self.unit.position3d)
			

	def runList(self):
		if not self.unit.is_ready:
			return #warping in
		
		if self.morphArchon():
			self.label = 'Morphing'
			return #morphing, do nothing else.

		#keep safe from effects
		if self.game.effectSafe(self):
			self.label = 'Dodging'
			return #dodging effects.	
		
		#check if we need to come home and defend.
		self.comeHome = self.game.checkHome(self)
		

		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			
			#see if we are able to escape if needed.
			if self.game.canEscape(self) and self.game.keepSafe(self):
				self.label = 'Retreating Safe'
				return #staying alive			

			#1 priority is always attack first if we can
			if self.game.attack(self):
				self.label = 'Attacking'
				return #we attacked this step.
	
			#1b aoe if we can.
			if self.psionicStorm():
				self.label = 'Psionic Storm'
				return #draining energy.		
			
			#1c drain energy if we can.
			if self.feedback():
				self.label = 'Feedback'
				return #draining energy.
	
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



	def morphArchon(self):
		#check to see if there are 2 templars present, if so, morph them.
		#MORPH_ARCHON
		if AbilityId.MORPH_ARCHON in self.abilities and self.game.can_afford(MORPH_ARCHON):
			print ('morph found')
			return True
		return False

	def psionicStorm(self):
		aoeTarget = self.game.findAOETarget(self, 9, 1.5)  #range of 9, radius of 1.5
		if aoeTarget:
			if AbilityId.PSISTORM_PSISTORM in self.abilities and self.game.can_afford(PSISTORM_PSISTORM):
				self.game.combinedActions.append(self.unit(AbilityId.PSISTORM_PSISTORM, aoeTarget))
				return True
		return False
		

	def feedback(self):
		#find an enemy in range who also has energy to drain.
		closestEnemy = self.game.findEnergyTarget(self, 9)  #range of 9
		if closestEnemy:
			if AbilityId.FEEDBACK_FEEDBACK in self.abilities and self.game.can_afford(FEEDBACK_FEEDBACK):
				self.game.combinedActions.append(self.unit(AbilityId.FEEDBACK_FEEDBACK, closestEnemy))
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
	def isHallucination(self) -> bool:
		return False
	
	@property
	def sendHome(self) -> bool:
		return self.comeHome	
					
	
		

		
		
		
		
	
		
	