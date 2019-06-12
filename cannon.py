import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.position import Point2, Point3

_debug = False

class Cannon:
	
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
			'Medivac': 40,
			'SCV': 45,
			'SiegeTank': 25,
			'SiegeTankSieged': 25,
			'Battlecruiser': 55,
			'Thor': 40,
			'WidowMine': 30,	
			'WidowMineBurrowed': 50,		
			'Raven': 51,
			#Protoss
			'Carrier': 15,
			'Colossus': 15,
			'Mothership': 20,
			'Phoenix': 5,	
			'VoidRay': 5,
			'Tempest': 10,
			#Zerg
			'Infestor': 30,
			'Ultralisk': 25,
			'BroodLord': 25,
			'Overlord': -100, #no reason to attack them first.
		}		
		
	def make_decision(self, game, unit):
		self.game = game
		self.unit = unit
		self.saved_position = self.unit.position
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

		self.closestEnemies = self.game.getUnitEnemies(self)
		if self.closestEnemies.amount > 0:
			#1 priority is always attack first if we can
			if self.game.attack(self):
				self.label = 'Attacking'
				return #we attacked this step.

		self.label = 'Waiting for Enemies';



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
