from sc2.constants import *
import random



class UnitCounter:
	
	def __init__(self):
		
		#current power = supply * tier
		self.unitPower = {
			#zerg
			'Overlord': 0.01,
			'Baneling': 0.55,
			'Zergling': 0.35,
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
			'Marine': 1,
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
				[['Immortal', 0.5]],
				[['Stalker', 1]],
				[['Zealot', 1]],
			],
			'SporeCrawler': [
				[['Zealot', 1]],
			],			
			'Overlord': [
				[['Phoenix', 0.25]],
				[['Stalker', 0.01]]
				],
			'Baneling': [
				[['HighTemplar', 1]],
				[['Disruptor', 0.1], ['Colossus', 0.1], ['Stalker', 0.5]],
				[['Stalker', 1]],
				],
			'Zergling': [
				[['HighTemplar', 0.5],  ['Zealot', 0.5]],				
				[['Zealot', 0.5]],
				],
			'Hydralisk': [
				[['Colossus', 0.25], ['Carrier', 0.25], ['Zealot', 0.5]],
				[['Colossus', 0.25],['Zealot', 0.5]],				
				[['Stalker', 1],['Zealot', 0.5]],
				],
			'Mutalisk': [
				[['Carrier', 0.25], ['Phoenix', 0.75], ['HighTemplar', 0.5]],
				[['Phoenix', 1]],
				[['Stalker', 1]],
				],
			'Ultralisk': [				
				[['VoidRay', 1], ['Immortal', 1],['Archon', 1]],
				[['Immortal', 2]],
				[['Stalker', 2], ['Zealot', 2]],
				],
			'Roach': [
				[['Carrier', 0.25], ['Immortal', 0.5], ['Zealot', 0.5]],
				[['Immortal', 0.5], ['Zealot', 0.5]],
				[['Stalker', 1.5], ['Zealot', 0.5]],
				],
			'Infestor': [
				[['HighTemplar', 1]],
				[['Stalker', 1],['Zealot', 0.5]],
				],
			'Queen': [
				[['Zealot', 1]],
				],
			'Overseer': [
				[['Phoenix', 0.5], ['Stalker', 0.5]],
				],
			'Ravager': [
				[['Immortal', 0.5],['Zealot', 0.5]],
				],
			'Lurker': [
				[['Observer', 0.25], ['Disruptor', 0.25]],
				[['Observer', 0.25], ['Immortal', 0.5]],
				],
			'Corruptor': [
				[['VoidRay', 1], ['Phoenix', 0.5], ['Tempest', 0.1]],
				[['Stalker', 1]],
				],
			'Viper': [
				[['HighTemplar', 1]],
				[['Stalker', 1]],
				],
			'BroodLord': [
				[['Tempest', 1]],
				[['Stalker', 3],['VoidRay', 1]],
				],
			
			#protoss counters
			'Zealot': [
				[['Colossus', 0.1], ['Adept', 0.8]],
				[['Adept', 1]],
				[['Zealot', 1]],
				],
			'Stalker': [
				[['Immortal', 0.75], ['Zealot', 1],['Stalker', 1]],
				[['Zealot', 1],['Stalker', 1]],
				],
			'Adept': [
				[['Stalker', 1]],
				[['Zealot', 2]],
				],
			'Sentry': [
				[['Stalker', 1]],
				[['Zealot', 2]],
				],
			'Immortal': [
				[['Carrier', 0.25], ['Sentry', 0.25]],
				[['VoidRay', 1], ['Sentry', 0.25]],
				[['Zealot', 4]],
				],
			'WarpPrism': [
				[['Phoenix', 0.5]],
				[['Stalker', 3]],
				],
			'VoidRay': [
				[['Phoenix', 1]],
				[['Stalker', 3]],
				],
			'Oracle': [
				[['Phoenix', 0.5]],
				[['Stalker', 3]],
				],
			'Carrier': [
				[['Tempest', 1.5], ['VoidRay', 2],['Phoenix', 1]],
				[['Stalker', 2], ['VoidRay', 2],['Phoenix', 1]],
				[['Stalker', 3]],
				],
			'Phoenix': [
				[['Phoenix', 1]],
				[['Stalker', 1]],
				],
			'Colossus': [
				[['Carrier', 0.25], ['Immortal', 0.5], ['Phoenix', 0.5]],
				[['VoidRay', 1.5]],
				[['Immortal', 1],['Zealot', 2]],
				[['Stalker', 2],['Zealot', 2]],
				],
			'Tempest': [
				[['VoidRay', 2], ['Phoenix', 1]],
				[['Stalker', 3]],
				],
			'HighTemplar': [
				[['HighTemplar', 1],['Zealot', 0.5]],
				[['Colossus', 0.5], ['Zealot', 0.5]],
				[['Stalker', 1], ['Zealot', 2]],
				],
			'Disruptor': [
				[['VoidRay', 1]],
				[['Immortal', 1]],
				[['Stalker', 2]],
				[['Zealot', 1],['Stalker', 2]],
				],
			'DarkTemplar': [
				[['Observer', 0.5], ['Stalker', 0.5]],
				],
			'Archon': [
				[['VoidRay', 1]],
				[['Immortal', 2]],
				[['Stalker', 3]],
				[['Zealot', 4]],
				],
			'Observer': [
				[['Observer', 0.5], ['Phoenix', 0.5]],
				[['Observer', 0.5], ['Stalker', 0.5]],
				],
			'PhotonCannon': [
				[['Immortal', 1]],
				[['Stalker', 2]],
				[['Zealot', 3]],
				],
			'Mothership': [
				[['VoidRay', 5]],
				[['Stalker', 3]],
			],

			#terran counters
			'CommandCenter':[
				[['Phoenix', 0.2], ['Zealot', 1]],
				[['Stalker', 0.2], ['Zealot', 1]],
				],
			'Marine': [
				[['Colossus', 0.1], ['Stalker', 0.5], ['Sentry', 0.05]],
				[['Stalker', 1], ['Sentry', 0.05]],
				[['Zealot', 2]],
				],
			'Reaper': [
				[['Tempest', 1]],
				[['VoidRay', 0.5]],
				[['Stalker', 1]],
				[['Zealot', 2]],
				],
			'Marauder': [
				[['Tempest', 1]],
				[['VoidRay', 1]],
				[['Immortal', 1], ['Sentry', 0.25]],
				[['Zealot', 1], ['Sentry', 0.25]],
				[['Zealot', 2]],
				],
			'Ghost':  [
				[['Phoenix', 1], ['Observer', 0.25]],
				[['Stalker', 1], ['Observer', 0.25]],
				],
			'Hellion': [
				[['Carrier', 1]],
				[['VoidRay', 1]],
				[['Stalker', 1.5], ['Zealot', 1]],
				],
			'WidowMine': [
				[['Tempest', 1], ['Observer', 0.25]],
				[['VoidRay', 1], ['Observer', 0.25]],
				[['Stalker', 0.5], ['Observer', 0.25]],
				],
			'Cyclone': [
				[['Immortal', 1]],
				[['VoidRay', 1]],
				[['Stalker', 0.5], ['Zealot', 0.5]],
				],
			'SiegeTank': [
				[['VoidRay', 1], ['Immortal', 1]],
				[['Immortal', 1], ['Zealot', 0.5]],
				[['Zealot', 2]],
				],
			'Thor': [
				[['VoidRay', 1]],
				[['Immortal', 1], ['Zealot', 2]],
				[['Stalker', 1], ['Zealot', 2]],
				],
			'Viking': [
				[['Tempest', 1]],
				[['VoidRay', 1]],
				[['HighTemplar', 1]],
				[['Stalker', 1]],
				],
			'Medivac': [
				[['HighTemplar', 1],['Stalker', 1]],
				[['Tempest', 1], ['Phoenix', 1]],
				[['Stalker', 1]],
				],
			'Liberator': [
				[['Tempest', 1], ['Phoenix', 1]],
				[['VoidRay', 1]],
				[['Stalker', 2]],
				],
			'Raven': [
				[['HighTemplar', 1],['Phoenix', 1]],
				[['HighTemplar', 1], ['Phoenix', 1]],
				[['Stalker', 2], ['Phoenix', 1]],
				],
			'Banshee': [
				[['Phoenix', 1], ['Observer', 0.5]],
				[['Stalker', 2], ['Observer', 0.5]],
				],
			'Battlecruiser': [
				[['Tempest', 1.5], ['Phoenix', 0.5]],
				[['VoidRay', 2.5], ['Phoenix', 0.5]],
				[['Stalker', 4]]
				],
			'VikingFighter': [
				[['Tempest', 1]],
				[['VoidRay', 1]],
				[['HighTemplar', 1]],
				[['Stalker', 2]],
				],
			'VikingAssault': [
				[['Tempest', 1]],
				[['VoidRay', 1]],
				[['HighTemplar', 1]],
				[['Stalker', 2]],
				],
			'MissileTurret': [
				[['Immortal', 0.1]],
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
		
		
		self.intro_sayings = [
			'May the RNG be in your favor and bring you lots of joy',
			'gl',
			'Artificial intelligence is no match for natural stupidity.',
			'Have fun storming the castle!',
			]	

		self.loss_sayings = [
			'My IQ came back negative.',
			'Roses are #FF0000, violets are #0000FF, all my base are belong to you.',
			'Tis but a scratch.',
			'Everyone has a plan until they get punched in the mouth.',
			'gg',
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
			
	def getUnitPower(self, unit):
		return self.unitPower.get(unit)

	def getSupportReq(self, unit):
		return self.supportTable.get(unit)
	
	def getUnitOpArea(self, unit):
		return self.unitOpArea.get(unit)
	
	def getUnitCargo(self, unit):
		return self.cargoSize.get(unit)
	
	
	
