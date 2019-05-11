import random
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
'''
This class carried out build orders previously, variables left in case for now.

'''

_print_unit_training = False

class Trainer:

	def __init__(self):
		self.allow_voidrays = False
		self.allow_tempests = False
		self.allow_phoenix = False
		self.allow_zealots = False
		self.allow_stalkers = False
		self.allow_immortals = False
		self.allow_warpprisms = False
		self.allow_sentrys = False
		self.allow_observers = False
		self.allow_colossus = False
		self.allow_adepts = False
		self.allow_hightemplars = False
		self.allow_disruptors = False
		self.allow_carriers = False
		self.allow_mothership = False
	
	async def train_all(self, game):
		self.game = game

