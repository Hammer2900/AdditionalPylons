from sc2.constants import *
import random



class UnitCounter:
	
	def __init__(self):
		
		self.unitCosts = {
			'Zealot': 2,
			'Stalker': 2,
			'Adept': 2,
			'Sentry': 2,
			'Immortal': 4,
			'WarpPrism': 2,
			'VoidRay': 4,
			'Phoenix': 2,
			'Colossus': 6,
			'Tempest': 5,
			'Carrier': 6,
			'HighTemplar': 2,
			'Disruptor': 3, 
			'DarkTemplar': 2,
			'Observer': 1,
			'Mothership': 8
		}
		
		#current power = supply * tier
		self.unitPower = {
			#zerg
			'Overlord': 0.01,
			'Baneling': 0.55,
			'Zergling': 0.30,
			'Hydralisk': 5,
			'Mutalisk': 5,
			'Ultralisk': 18,
			'Roach': 3,
			'Infestor': 5,
			'Queen': 2,
			'Overseer': 0.5,
			'Ravager': 3,
			'Lurker': 4,
			'Corruptor': 5,
			'Viper': 9,
			'BroodLord': 12,
			'SpineCrawler': 6,
			'SporeCrawler': 6,
			
			#protoss
			'Zealot': 2,
			'Stalker': 4,
			'Adept': 4,
			'Sentry': 4,
			'Immortal': 12,
			'WarpPrism': 1,
			'VoidRay': 12,
			'Phoenix': 4,
			'Colossus': 24,
			'Tempest': 24,
			'HighTemplar': 8,
			'Disruptor': 12, 
			'DarkTemplar': 8,
			'Observer': 2,
			'Archon': 20,
			'PhotonCannon': 6,
			'Oracle': 9,
			'Carrier': 18,
			'Mothership': 32,
			
			#terran
			'CommandCenter': 0.1,
			'PlanetaryFortress': 10,
			'Marine': 1.25,
			'Reaper': 1,
			'Marauder': 4,
			'Ghost':  6,
			'Hellion': 4,
			'WidowMine': 4,
			'Cyclone': 6,
			'SiegeTank': 9,
			'Thor': 18,
			'Viking': 6,
			'VikingFighter': 8,
			'VikingAssault': 8,
			'Medivac': 1,
			'Liberator': 9,
			'Raven': 8,
			'Banshee': 12,
			'Battlecruiser': 24,
			'MissileTurret': 6

			
			
		}
		
		
		self.supportTable = {
			'Sentry': ['Ground', 20],
			'WarpPrism': ['GroundSupply', 32]
		}
		

		
		self.counterTable = {
			#zerg counters
			'SpineCrawler': [
				[['Immortal', 0.5], ['Zealot', 0.25]],
				[['Stalker', 1]],
				[['Zealot', 1]],
			],
			'SporeCrawler': [
				[['Zealot', 1]],
			],			
			'Overlord': [
				[['Stalker', 0.01]]
				],
			'Baneling': [
				[['Colossus', 0.1], ['Stalker', 0.5], ['Zealot', 0.25]],
				[['Stalker', 1], ['Zealot', 0.25]],
				],
			'Zergling': [			
				[['Colossus', 0.25], ['Zealot', 0.1]],
				[['Zealot', 0.5]],
				],
			'Hydralisk': [
				[['Colossus', 0.25], ['Sentry', 0.25], ['Zealot', 0.5]],
				[['Immortal', 0.25],['Sentry', 0.5], ['Zealot', 0.25]],				
				[['Stalker', 1],['Sentry', 0.5], ['Zealot', 0.25]],
				[['Zealot', 2]],
				],			
			'Mutalisk': [
				[['Phoenix', 1]],
				[['Stalker', 2], ['Zealot', 0.25]],
				],
			'Ultralisk': [				
				[['VoidRay', 1], ['Immortal', 2], ['Zealot', 2]],
				[['VoidRay', 1], ['Zealot', 2]],
				[['Immortal', 2], ['Zealot', 2]],
				[['Stalker', 2], ['Zealot', 2]],
				],
			'Roach': [
				[['Colossus', 0.25], ['Immortal', 0.5], ['Zealot', 0.5]],
				[['Immortal', 0.5], ['Zealot', 0.5]],
				[['Stalker', 1.5], ['Zealot', 0.5]],
				[['Zealot', 2]],
				],
			'Infestor': [
				[['Stalker', 1],['Zealot', 0.5]],
				],
			'Queen': [
				[['Stalker', 1],['Zealot', 0.5]],
				[['Zealot', 1]],
				],
			'Overseer': [
				[['Stalker', 1]],
				],
			'Ravager': [
				[['Immortal', 0.5],['Zealot', 0.5]],
				],
			'Lurker': [
				[['Observer', 0.25], ['Disruptor', 0.25], ['Immortal', 0.5], ['Zealot', 0.25]],
				[['Observer', 0.25], ['Immortal', 0.5], ['Zealot', 0.25]],
				],
			'Corruptor': [
				[['VoidRay', 1], ['Zealot', 0.25]],
				[['Stalker', 1], ['Zealot', 0.25]],
				],
			'Viper': [
				[['Phoenix', 1], ['Zealot', 0.25]],
				[['Stalker', 1], ['Zealot', 0.25]],
				],
			'BroodLord': [
				[['VoidRay', 1]],
				[['Stalker', 3]],
				],
			
			#protoss counters
			'Zealot': [
				[['Adept', 1], ['Zealot', 0.25]],
				[['Zealot', 1]],
				],
			'Stalker': [
				[['Immortal', 0.75], ['Sentry', 0.25], ['Zealot', 0.25]],
				[['Stalker', 1], ['Sentry', 0.25], ['Zealot', 0.25]],
				[['Zealot', 2]],
				],
			'Adept': [
				[['Stalker', 1], ['Sentry', 0.25], ['Zealot', 0.25]],
				[['Zealot', 2]],
				],
			'Sentry': [
				[['Stalker', 1], ['Zealot', 0.25]],
				[['Zealot', 2]],
				],
			'Immortal': [
				[['VoidRay', 1], ['Sentry', 0.25], ['Zealot', 2]],
				[['Zealot', 3], ['Sentry', 0.25]],
				[['Zealot', 3]],
				],
			'WarpPrism': [
				[['Phoenix', 0.5]],
				[['Stalker', 1]],
				],
			'VoidRay': [
				[['Phoenix', 1]],
				[['Stalker', 3]],
				],
			'Oracle': [
				[['Phoenix', 1]],
				[['Stalker', 3]],
				],
			'Carrier': [
				[['Tempest', 3]],
				[['Stalker', 8], ['Sentry', 3]],
				],
			'Phoenix': [
				[['Stalker', 2]],
				],
			'Colossus': [
				[['VoidRay', 2], ['Immortal', 1], ['Phoenix', 1], ['Sentry', 1], ['Zealot', 1]],
				[['VoidRay', 2], ['Phoenix', 0.5], ['Zealot', 3]],
				[['Immortal', 1], ['Sentry', 1], ['Zealot', 4]],
				[['Stalker', 6],['Zealot', 5], ['Sentry', 1]],
				[['Zealot', 12]],
				],
			'Tempest': [
				[['Tempest', 1], ['Stalker', 1]],
				[['Phoenix', 2],['Stalker', 2]],
				[['Stalker', 4]],
				],
			'HighTemplar': [
				[['Immortal', 1], ['Sentry', 0.5]],
				[['Stalker', 2], ['Zealot', 1], ['Sentry', 0.5]],
				[['Zealot', 4]],
				],
			'Disruptor': [
				[['Immortal', 1], ['Zealot', 0.25]],
				[['Stalker', 2]],
				[['Zealot', 4]],
				],
			'DarkTemplar': [
				[['Observer', 2], ['Stalker', 2], ['Zealot', 0.25]],
				],
			'Archon': [
				[['Immortal', 1], ['Sentry', 0.5], ['Zealot', 0.25]],
				[['Stalker', 2], ['Zealot', 1], ['Sentry', 0.5]],
				[['Zealot', 4]],
				],
			'Observer': [
				[['Observer', 0.01]],
				],
			'PhotonCannon': [
				[['Immortal', .5], ['Sentry', 0.25], ['Zealot', 0.05]],
				[['Stalker', 2], ['Sentry', 0.25]],
				[['Zealot', 3]],
				],
			'Mothership': [
				[['Tempest', 5]],
				[['Stalker', 10], ['Sentry', 4]],
			],

			#terran counters
			'CommandCenter':[
				[['Sentry', 0.05], ['Tempest', 1], ['Disruptor', 0.05], ['Observer', 1]],
				[['Stalker', 0.02],['Sentry', 0.01]],
				],
			'PlanetaryFortress':[
				[['Tempest', 1]],
				[['Immortal', 2], ['Sentry', 0.05], ['Zealot', 1]],	
				[['Zealot', 3], ['Sentry', 0.05]],
				],
			'Marine': [
				[['Colossus', 0.25]],
				[['Stalker', 1], ['Sentry', 0.05]],
				[['Zealot', 2]],
				],
			'Reaper': [
				[['Stalker', 2]],
				],
			'Marauder': [
				[['Tempest', 1]],
				[['VoidRay', 1]],
				[['Immortal', 1], ['Sentry', 0.25], ['Zealot', 0.25]],
				[['Zealot', 1], ['Sentry', 0.25]],
				[['Zealot', 2]],
				],
			'Ghost':  [
				[['Colossus', 0.5], ['Tempest', 0.5], ['Observer', 0.25]],
				[['Stalker', 1], ['Observer', 0.25]],
				],
			'Hellion': [
				[['Colossus', 0.5], ['Zealot', 0.2], ['Stalker', 0.1]],
				[['Stalker', 1.5]],
				[['Zealot', 1]]
				],
			'WidowMine': [
				[['Tempest', 1], ['Disruptor', 0.05], ['Observer', 1], ['Zealot', 0.5] ],
				[['Stalker', 0.5], ['Observer', 1]],
				],
			'Cyclone': [
				[['Tempest', 1], ['Sentry', 0.5], ['Zealot', 0.25]],
				[['Stalker', 1], ['Sentry', 0.5], ['Zealot', 0.25]],
				[['Zealot', 1]],
				],
			'SiegeTank': [
				[['Tempest', 1], ['Zealot', 2]],
				[['Stalker', 1], ['Sentry', 0.5], ['Zealot', 0.25]],
				[['Zealot', 2]],
				],
			'Thor': [
				[['Immortal', 1],['Sentry', 0.5], ['Zealot', 0.5]],
				[['Stalker', 1], ['Sentry', 0.5], ['Zealot', 0.5]],
				[['Zealot', 4]],
				],
			'Viking': [
				[['Tempest', 1], ['Zealot', 0.25]],
				[['Stalker', 1], ['Sentry', 0.5], ['Zealot', 0.25]],
				],
			'Medivac': [
				[['Phoenix', 1]],
				[['Stalker', 1]],
				],
			'Liberator': [
				[['Tempest', 1], ['Zealot', 0.25]],
				[['Phoenix', 1], ['Zealot', 0.25]],
				[['Stalker', 2], ['Zealot', 0.25]],
				],
			'Raven': [
				[['Tempest', 1], ['Zealot', 0.25]],
				[['Phoenix', 1], ['Stalker', 1], ['Zealot', 0.25]],
				[['Stalker', 2], ['Zealot', 0.25]],
				],
			'Banshee': [
				[['Phoenix', 1], ['Observer', 2]],
				[['Stalker', 1], ['Observer', 2]],
				],
			'Battlecruiser': [
				[['Tempest', 3], ['Stalker', 1], ['Sentry', 0.25]],
#				[['VoidRay', 2.5], ['Phoenix', 0.5]],
				[['Stalker', 4], ['Sentry', 0.25]]
				],
			'VikingFighter': [
				[['Tempest', 1], ['Zealot', 0.25]],
				[['Stalker', 1], ['Sentry', 0.5], ['Zealot', 0.25]],
				],
			'VikingAssault': [
				[['Tempest', 1], ['Zealot', 0.25]],
				[['Stalker', 1], ['Sentry', 0.5], ['Zealot', 0.25]],
				],
			'MissileTurret': [
				[['Immortal', 0.1], ['Zealot', 0.25]],
				[['Stalker', 1],['Zealot', 2]],
				],

		}	
		
		
		self.cargoSize = {
			'Zealot': 2,
			'Stalker': 2,
			'Adept': 2,
			'Sentry': 2,
			'Immortal': 4,
			'Colossus': 8,
			'HighTemplar':2,
			'DarkTemplar': 2,
			'Disruptor': 4
		}
		
		self.unitTrainers = {
			'Zealot': 'Gateway',
			'Stalker': 'Gateway',
			'Adept': 'Gateway',
			'Sentry': 'Gateway',
			'Immortal': 'RoboticsFacility',
			'WarpPrism': 'RoboticsFacility',
			'VoidRay': 'Stargate',
			'Phoenix': 'Stargate',
			'Colossus': 'RoboticsFacility',
			'Tempest': 'Stargate',
			'Carrier': 'Stargate',
			'HighTemplar': 'Gateway',
			'Disruptor': 'RoboticsFacility', 
			'DarkTemplar': 'Gateway',
			'Observer': 'RoboticsFacility',
			'Mothership': 'Nexus'
		}

		self.unitOpArea = {
			'Zealot': 'Ground',
			'Stalker': 'Ground',
			'Adept': 'Ground',
			'Sentry': 'Ground',
			'Immortal': 'Ground',
			'WarpPrism': 'Air',
			'VoidRay': 'Air',
			'Phoenix': 'Air',
			'Colossus': 'Ground',
			'Tempest': 'Air',
			'Carrier': 'Air',
			'HighTemplar': 'Ground',
			'Disruptor': 'Ground', 
			'DarkTemplar': 'Ground',
			'Observer': 'Air',
			'Mothership': 'Air'
		}
		
		self.unitReqs = {
			'Zealot': ['Gateway'],
			'Stalker': ['Gateway', 'CyberneticsCore'],
			'Adept': ['Gateway', 'CyberneticsCore'],
			'Sentry': ['Gateway', 'CyberneticsCore'],
			'Immortal': ['Gateway', 'CyberneticsCore', 'RoboticsFacility'],
			'WarpPrism': ['Gateway', 'CyberneticsCore', 'RoboticsFacility'],
			'VoidRay': ['Gateway', 'CyberneticsCore', 'Stargate'],
			'Phoenix': ['Gateway', 'CyberneticsCore', 'Stargate'],
			'Colossus': ['Gateway', 'CyberneticsCore', 'RoboticsFacility', 'RoboticsBay'],
			'Tempest': ['Gateway', 'CyberneticsCore', 'Stargate', 'FleetBeacon'],
			'Mothership': ['Gateway', 'CyberneticsCore', 'Stargate', 'FleetBeacon'],
			'Carrier': ['Gateway', 'CyberneticsCore', 'Stargate', 'FleetBeacon'],
			'HighTemplar': ['Gateway', 'CyberneticsCore', 'TwilightCouncil', 'TemplarArchive'],
			'Disruptor': ['Gateway', 'CyberneticsCore', 'RoboticsFacility', 'RoboticsBay'],
			'DarkTemplar': ['Gateway', 'CyberneticsCore', 'TwilightCouncil', 'DarkShrine'],
			'Observer': ['Gateway', 'CyberneticsCore', 'RoboticsFacility']
		}
		
		self.nameCross = {
			'Gateway': GATEWAY,
			'CyberneticsCore': CYBERNETICSCORE,
			'RoboticsFacility': ROBOTICSFACILITY,
			'RoboticsBay': ROBOTICSBAY,
			'Stargate': STARGATE,
			'FleetBeacon': FLEETBEACON,
			'TwilightCouncil': TWILIGHTCOUNCIL,
			'TemplarArchive': TEMPLARARCHIVE,
			'DarkShrine': DARKSHRINE,
			'Zealot': ZEALOT,
			'Stalker': STALKER,
			'Adept': ADEPT,
			'Sentry': SENTRY,
			'Immortal': IMMORTAL,
			'WarpPrism': WARPPRISM,
			'VoidRay': VOIDRAY,
			'Phoenix': PHOENIX,
			'Colossus': COLOSSUS,
			'Tempest': TEMPEST,
			'HighTemplar': HIGHTEMPLAR,
			'Disruptor': DISRUPTOR,
			'DarkTemplar': DARKTEMPLAR,
			'Observer': OBSERVER,
			'Carrier': CARRIER,
			'Mothership': MOTHERSHIP
		}
		
		self.warpAbilities = {
			'Zealot': WARPGATETRAIN_ZEALOT,
			'Stalker': WARPGATETRAIN_STALKER,
			'Adept': TRAINWARP_ADEPT,
			'Sentry': WARPGATETRAIN_SENTRY,
			'HighTemplar': WARPGATETRAIN_HIGHTEMPLAR,
		}
		
		
		self.intro_sayings = [
#			'May the RNG be in your favor and bring you lots of joy. (happy)',
#			'(glhf)',
#			'To make bots practical, flaws must be removed. To make bots endearing, flaws must be added.',
#			'Artificial intelligence is no match for natural stupidity. (nerd)',
			'Hello, my name is AdditionalPylons. You killed my previous version, prepare to die!',
			]	

		self.loss_sayings = [
#			'My IQ came back negative. (surprised)',
#			'If I only had a brain (speechless)',
#			'Roses are #FF0000, violets are #0000FF, all my base are belong to you. (kiss)',
			'But I have people skills! (angry)',
			"Ah, I see you have the machine that goes ping! (surprised)",
			"Come and see the violence inherent in the system. Help! Help! I'm being repressed! (speechless)",
			]

		self.s1_complete = [
			'I used to think I was indecisive, but now I am not so sure. (thinking)',
			'Life is short, smile while you still have all your teeth. (happy)',
			]		

		self.s1_fail = [
#			'People say nothing is impossible, but I do nothing every day. (sleepy)',
			'Everyone has a plan until they get punched in the mouth. (zipped)',
#			'It would be nice to spend resources on buildings and units, but right now they are desperately needed for more pylons.',
			"You're killin' me, Smalls. (angry)",
			]		



	def getLossSaying(self):
		return random.choice(self.loss_sayings)

	def getIntroSaying(self):
		return random.choice(self.intro_sayings)

	def getUnitID(self, name):
		return self.nameCross.get(name)

	def getCounterUnits(self, enemy):
		return self.counterTable.get(enemy)
	
	def getUnitReqs(self, unit):
		return self.unitReqs.get(unit)
	
	def getUnitTrainer(self, unit):
		return self.unitTrainers.get(unit)

	def getUnitCost(self, unit):
		return self.unitCosts.get(unit)
			
	def getUnitPower(self, unit):
		return self.unitPower.get(unit)

	def getSupportReq(self, unit):
		return self.supportTable.get(unit)
	
	def getUnitOpArea(self, unit):
		return self.unitOpArea.get(unit)
	
	def getUnitCargo(self, unit):
		return self.cargoSize.get(unit)

	def getWarpAbility(self, name):
		return self.warpAbilities.get(name)	

	def gets1successSaying(self):
		return random.choice(self.s1_complete)	
	
	def gets1failSaying(self):
		return random.choice(self.s1_fail)	