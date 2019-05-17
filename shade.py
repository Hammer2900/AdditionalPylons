import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3


_debug = False

'''
Phase Info
-----------------
Description: Ground Unit
Sight: 4
Speed: 3.5

		#CANCEL_ADEPTSHADEPHASESHIFT
		#CANCEL_ADEPTPHASESHIFT
		#ADEPTPHASESHIFT_ADEPTPHASESHIFT
		#AdeptPhaseShift
'''


class Shade:

	def __init__(self, unit):
		self.tag = unit.tag
		self.unit = unit
		self.saved_position = None
		self.last_action = ''
		self.shade_start = None
		self.owner = None
		self.ownerOrder = None
		self.comeHome = False
		self.homeTarget = None
		self.enemy_target_bonuses = {
			'Medivac': 300,
			'SCV': 100,
			'SiegeTank': 300,
			'Battlecruiser': 350,
			'Carrier': 350,
			'Infestor': 300,
			'BroodLord': 300,
			'WidowMine': 300,
			'Mothership': 600,
			'Viking': 300,
			'VikingFighter': 300,
		}
		
		
	def make_decision(self, game, unit):
		self.saved_position = unit.position #first line always.
		self.game = game
		self.unit = unit
		self.abilities = self.game.allAbilities.get(self.unit.tag)
		self.label = 'Idle'
		if not self.shade_start:
			self.shade_start = self.game.time
			#find our owner adept.
			self.owner = self.find_owner()
	
		self.getOwnerOrder()
		self.runList()

		#debugging info
		if _debug or self.unit.is_selected:
			if self.owner:
				opos = Point3((self.owner.position3d.x, self.owner.position3d.y, (self.owner.position3d.z + 1)))
				spos = Point3((self.unit.position3d.x, self.unit.position3d.y, (self.unit.position3d.z + 1)))
				self.game._client.debug_line_out(spos, opos, color=Point3((155, 255, 25)))
			lb = "{} {}".format(str(self.ownerOrder), self.label)
			self.game._client.debug_text_3d(lb, self.unit.position3d)


	def runList(self):
		self.closestEnemies = self.game.getUnitEnemies(self)

		if self.psionicCancel():
			return # canceled shade.
		
		#5 priority is to move towards enemies not in range.
		if self.moveToEnemies():
			self.label = 'Moving to Enemies'
			return #moving to enemy
		
		if self.searchEnemies():
			self.label = 'Searching for Enemies'
			return #search enemies.
				


	def getOwnerOrder(self):
		#use the owner tag to get the object, then get it's order.
		self.ownerOrder = self.game.unitList.adeptOrder(self.owner)


	def find_owner(self):
		if len(self.game.units(ADEPT)) > 0:
			owner = self.game.units(ADEPT).closest_to(self.unit)
			return owner
		return None
		

	def psionicCancel(self):
		#if the owner order is that we are surrounded, do not cancel unless we are also surrounded.
		if self.ownerOrder == 'Surrounded':
			#print ('owner surrounded')
			if not self.game.checkSurrounded(self):
				#print ('owner saved')
				return False
			#print ('owner not saved')
		
		if self.shade_start:
			#see if it's time to cancel the shift.
			if (self.shade_start + 5.5) < self.game.time:
				#cancel the shift.
				if AbilityId.CANCEL_ADEPTSHADEPHASESHIFT in self.abilities and self.game.can_afford(CANCEL_ADEPTSHADEPHASESHIFT):
					self.game.combinedActions.append(self.unit(AbilityId.CANCEL_ADEPTSHADEPHASESHIFT))
					self.shade_start = None
					return True
		return False
		
		
	def searchEnemies(self):
		#search for enemies
		if self.unit.is_moving:
			return True #moving somewhere already
		searchPos = self.game.getSearchPos(self.unit)
		if self.checkNewAction('move', searchPos[0], searchPos[1]):
			self.game.combinedActions.append(self.unit.move(searchPos))
			return True
		return False
		
	def moveToEnemies(self):
		# move to nearest enemy ground unit/building because no enemy unit is closer than 5
		if self.game.known_enemy_units.exclude_type([ADEPTPHASESHIFT]).not_flying.exists:
			closestEnemy = self.game.known_enemy_units.exclude_type([ADEPTPHASESHIFT]).not_flying.furthest_to(self.unit)
			if self.checkNewAction('move', closestEnemy.position[0], closestEnemy.position[1]):
				self.game.combinedActions.append(self.unit.move(closestEnemy))
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
		return False
	
	@property
	def isSolo(self) -> bool:
		return self.solo

	@property
	def isHallucination(self) -> bool:
		return False
	
	@property
	def sendHome(self) -> bool:
		return self.comeHome	
									
			
	
		

		
		
		
		
	