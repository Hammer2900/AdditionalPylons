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
		
		#current power based on = Min costs + (Gas Costs * 2)
		self.unitPower = {
			#zerg
			'Overlord': 0.001,
			'Baneling': 100,
			'Zergling': 25,
			'ZerglingBurrowed': 25,
			'Hydralisk': 200,
			'HydraliskBurrowed': 200,
			'Mutalisk': 300,
			'Ultralisk': 700,
			'Roach': 125,
			'RoachBurrowed': 125,
			'Infestor': 400,
			'Queen': 150,
			'Overseer': 0.001,
			'Ravager': 300,
#			'Lurker': 450,
			'LurkerMP': 450,
			'LurkerMPBurrowed': 450,
			'Corruptor': 350,
			'Viper': 500,
			'BroodLord': 800,
			'SpineCrawler': 100,
			'SpineCrawlerUprooted': 100,
			'SporeCrawler': 75,
			'SporeCrawlerUprooted': 75,
			'OverlordTransport': 0.001,
			'InfestorTerran': 5,
			'ChangelingZealot': 5,
			'InfestedTerransEgg': 5,
			'Broodling': 4,
			'Drone': 50,
			'Extractor': 0.001,
			'Hatchery': 0.001,
			'Egg': 0.001,
			'Larva': 0.001,
			'CreepTumor': 0.001,
			'CreepTumorBurrowed': 0.001,
			'SCV': 0.001,

			
			#protoss
			'Zealot': 100,
			'Stalker': 225,
			'Adept': 150,
			'Sentry': 120,
			'Immortal': 475,
			'WarpPrism': 0.001,
			'WarpPrismPhasing': 0.001,
			'VoidRay': 550,
			'Phoenix': 350,
			'Colossus': 700,
			'Tempest': 600,
			'HighTemplar': 350,
			'Disruptor': 450, 
			'DarkTemplar': 375,
			'Observer': 0.001,
			'Archon': 700,
			'PhotonCannon': 150,
			'Oracle': 450,
			'Carrier': 850,
			'Mothership': 1200,
						
			#terran
			'CommandCenter': 0.001,
			'Bunker': 350,
			'PlanetaryFortress': 850,
			'Marine': 50,
			'Reaper': 150,
			'Marauder': 150,
			'Ghost':  375,
			'Hellion': 100,
			'HellionTank': 100,
			'WidowMineBurrowed': 125,
			'WidowMine': 125,
			'Cyclone': 350,
			'SiegeTank': 400,
			'SiegeTankSieged': 400,
			'Thor': 700,
			'Viking': 300,
			'VikingFighter': 300,
			'VikingAssault': 300,
			'Medivac': 300,
			'Liberator': 450,
			'LiberatorAG': 450,
			'Raven': 500,
			'Banshee': 350,
			'Battlecruiser': 1000,
			'MissileTurret': 100,
			'AutoTurret': 5,
			'KD8Charge': 0.001,

		}
		
		self.supportTable = {
			'Sentry': ['Ground', 20],
			'WarpPrism': ['GroundSupply', 32]
		}
		
		self.counterTable = {
			#zerg counters
			'SpineCrawler': [
				[['Immortal', 0.15]],
				[['Stalker', 0.55]],
				[['Zealot', 1]],
			],
			'SpineCrawlerUprooted': [
				[['Immortal', 0.15]],
				[['Stalker', 0.55]],
				[['Zealot', 1]],
			],
			'SporeCrawler': [
				[['Zealot', 0.01]],
			],
			'SporeCrawlerUprooted': [
				[['Zealot', 0.01]],
			],					
			'Overlord': [
				[['Sentry', 0.01]]
				],
			'OverlordTransport': [
				[['Phoenix', 1]]
				],
			'Baneling': [
				[['Stalker', 0.5]],
				[['Stalker', 1]],
				],
			'Zergling': [			
#				[['HighTemplar', 0.25], ['Zealot', 0.25], ['Adept', 0.25]],
				[['Colossus', 0.05], ['Zealot', 0.25], ['Adept', 0.25]],
				[['Adept', 0.25], ['Zealot', 0.25]],				
				[['Zealot', 0.5]],
				],
			'ZerglingBurrowed': [			
#				[['HighTemplar', 0.25], ['Zealot', 0.25], ['Adept', 0.25]],
				[['Colossus', 0.05], ['Zealot', 0.25], ['Adept', 0.25]],
				[['Adept', 0.25], ['Zealot', 0.25]],				
				[['Zealot', 0.5]],
				],
			'Hydralisk': [
				[['Colossus', 0.1], ['Sentry', 0.05], ['Zealot', 0.5]],
				[['Immortal', 0.25],['Sentry', 0.05], ['Zealot', 0.25]],				
				[['Stalker', 1],['Sentry', 0.5], ['Zealot', 0.25]],
				[['Zealot', 2]],
				],
			'HydraliskBurrowed': [
				[['Colossus', 0.1], ['Sentry', 0.05], ['Zealot', 0.5]],
				[['Immortal', 0.25],['Sentry', 0.05], ['Zealot', 0.25]],				
				[['Stalker', 1],['Sentry', 0.5], ['Zealot', 0.25]],
				[['Zealot', 2]],
				],
			'Mutalisk': [
				[['Phoenix', 0.66]],
				[['Stalker', 2], ['Zealot', 0.25]],
				],
			'Ultralisk': [				
				[['VoidRay', 1], ['Immortal', 2], ['Zealot', 2]],
				[['VoidRay', 1], ['Zealot', 2]],
				[['Immortal', 2], ['Zealot', 2]],
				[['Stalker', 2], ['Zealot', 2]],
				],
			'Roach': [
				[['Immortal', 0.33]],
				[['Stalker', 1.5], ['Zealot', 0.5]],
				[['Zealot', 2]],
				],
			'RoachBurrowed': [
				[['Immortal', 0.33]],
				[['Stalker', 1.5], ['Zealot', 0.5]],
				[['Zealot', 2]],
				],
			'Infestor': [
				[['Disruptor', 0.2]],
				[['Stalker', 1],['Zealot', 0.5]],
				],
			'Queen': [
				[['Stalker', 1]],
				[['Zealot', 1]],
				],
			'Overseer': [
				[['Phoenix', 1]],
				[['Stalker', 1]],
				],
			'Ravager': [
				[['Immortal', 0.33]],
				],
			'LurkerMP': [
				[['Observer', 0.25], ['Disruptor', 0.15]],
				[['Observer', 0.25], ['Immortal', 0.5]],
				],
			'LurkerMPBurrowed': [
				[['Observer', 0.25], ['Disruptor', 0.15]],
				[['Observer', 0.25], ['Immortal', 0.5]],
				],			
			'Corruptor': [
				[['VoidRay', 1]],
				[['Stalker', 1], ['Zealot', 0.25]],
				],
			'Viper': [
				[['Phoenix', 1]],
				[['Stalker', 1], ['Zealot', 0.25]],
				],
			'BroodLord': [
				[['VoidRay', 1]],
				[['Stalker', 3]],
				],
			
			#protoss counters
			'Zealot': [
				[['Adept', 0.75]],
				[['Zealot', 1]],
				],
			'Stalker': [
				[['Immortal', 0.25], ['Stalker', 0.5], ['Sentry', 0.05]],
				[['Stalker', 1], ['Sentry', 0.05]],
				[['Zealot', 2]],
				],
			'Adept': [
				[['Stalker', 0.75], ['Sentry', 0.05]],
				[['Zealot', 1.25]],
				],
			'Sentry': [
				# add observers to spot hallucinations once the client gives us the information :)
				[['Stalker', 0.75]],
				[['Zealot', 1]],
				],
			'Immortal': [
				[['Zealot', 3], ['Sentry', 0.05]],
				[['Zealot', 4]],
				],
			'WarpPrism': [
				[['Phoenix', 0.25]],
				[['Stalker', 0.75]],
				],
			'VoidRay': [
				[['Phoenix', 1]],
				[['Stalker', 2]],
				],
			'Oracle': [
				[['Phoenix', 1]],
				[['Stalker', 2]],
				],
			'Carrier': [
				[['Tempest', 2]],
				[['Stalker', 5]],
				],
			'Phoenix': [
				[['Stalker', 2]],
				],
			'Colossus': [
				[['Immortal', 1], ['Phoenix', 2]],
				[['Stalker', 6],['Zealot', 5]],
				[['Zealot', 12]],
				],
			'Tempest': [
				[['Tempest', 1], ['Stalker', 0.25], ['Observer', 0.2]],
				[['Phoenix', 2],['Stalker', 2]],
				[['Stalker', 4]],
				],
			'HighTemplar': [
				[['Immortal', 1]],
				[['Stalker', 2], ['Zealot', 1]],
				[['Zealot', 4]],
				],
			'Disruptor': [
				[['VoidRay', 1]],
				[['Stalker', 2]],
				[['Zealot', 4]],
				],
			'DarkTemplar': [
				[['Observer', 0.5], ['Stalker', 0.5]],
				[['Stalker', 0.5]],
				[['Observer', 0.5]],
				],
			'Archon': [
				[['Immortal', 1]],
				[['Stalker', 2]],
				[['Zealot', 4]],
				],
			'Observer': [
				[['Observer', 0.01]],
				],
			'PhotonCannon': [
				[['Immortal', .25], ['Stalker', 0.5], ['Sentry', 0.05]],
				[['Stalker', 2], ['Sentry', 0.05]],
				[['Zealot', 3]],
				],
			'Mothership': [
				[['Tempest', 5], ['Observer', 1]],
				[['Tempest', 5]],
				[['Stalker', 10], ['Observer', 1]],
				[['Stalker', 10]],
			],

			#terran counters
			'CommandCenter':[
				[['Stalker', 0.01]],
				],
			'Bunker':[
				[['Stalker', 0.01]],
				],
			'PlanetaryFortress':[
				[['Immortal', 2], ['Sentry', 0.05], ['Zealot', 1]],	
				[['Zealot', 3], ['Sentry', 0.05]],
				],
			'Marine': [
				[['Colossus', 0.15], ['Stalker', .5], ['Sentry', 0.05]],
				[['Stalker', 1], ['Sentry', 0.05]],
				[['Zealot', 1]],
				],
			'Reaper': [
				[['Stalker', 0.5]],
				],
			'Marauder': [
				[['Tempest', 1]],
				[['Zealot', 1], ['Sentry', 0.05]],
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
			'HellionTank': [
				[['Colossus', 0.5], ['Zealot', 0.2], ['Stalker', 0.1]],
				[['Stalker', 1.5]],
				[['Zealot', 1]]
				],
			'WidowMineBurrowed': [
				[['Disruptor', 0.1], ['Observer', 0.15]],
				[['Stalker', 0.5], ['Observer', 0.15]],
				],
			'WidowMine': [
				[['Disruptor', 0.1], ['Observer', 0.15]],
				[['Stalker', 0.5], ['Observer', 0.15]],
				],
			'Cyclone': [
				[['Immortal', 0.5], ['Sentry', 0.05]],
				[['Stalker', 1], ['Sentry', 0.05]],
				[['Zealot', 1]],
				],
			'SiegeTankSieged': [
				[['Tempest', 1]],
				[['Stalker', 1]],
				[['Zealot', 2]],
				],			
			'SiegeTank': [
				[['Tempest', 1]],
				[['Stalker', 1]],
				[['Zealot', 2]],
				],
			'Thor': [
				[['Immortal', 1.5]],
				[['Stalker', 2]],
				[['Zealot', 4]],
				],
			'Viking': [
				[['Tempest', 0.4]],
				[['Stalker', 1]],
				],
			'Medivac': [
				[['Tempest', 1]],
#				[['Phoenix', 2]],
				[['Stalker', 1]],
				],
			'LiberatorAG': [
				[['Tempest', 1]],
				[['Phoenix', 2]],
				[['Stalker', 2]],
				],
			'Liberator': [
				[['Tempest', 1]],
				[['Phoenix', 2]],
				[['Stalker', 2]],
				],
			'Raven': [
				[['Tempest', 1]],
				[['Phoenix', 1]],
				[['Stalker', 1]],
				],
			'Banshee': [
				[['Stalker', 1], ['Observer', 0.25]],
				],
			'Battlecruiser': [
				[['Tempest', 3], ['Stalker', 1]],
				[['Stalker', 4]]
				],
			'VikingFighter': [
				[['Tempest', 0.4]],
				[['Stalker', 1]],
				],
			'VikingAssault': [
				[['Tempest', 0.4]],
				[['Stalker', 1]],
				],
			'MissileTurret': [
				[['Sentry', 0.01]],
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
			'May the RNG be in your favor and bring you lots of joy. (happy)',
			'(glhf)',
			'Artificial intelligence is no match for natural stupidity. (nerd)',
			]	

		self.loss_sayings = [
			'My IQ came back negative. (surprised)',
			'If I only had a brain (speechless)',
			'Roses are #FF0000, violets are #0000FF, all my base are belong to you. (kiss)',
			'But I have people skills! (angry)',
			"Ah, I see you have the machine that goes ping! (surprised)",
			"Come and see the violence inherent in the system. Help! Help! I'm being repressed! (speechless)",
			]

		self.s1_complete = [
			# 'I used to think I was indecisive, but now I am not so sure. (thinking)',
			# 'Life is short, smile while you still have all your teeth. (happy)',
			"Starting stage completed, moving to gamestate mode",
			]		

		self.s1_fail = [
#			'People say nothing is impossible, but I do nothing every day. (sleepy)',
#			'Everyone has a plan until they get punched in the mouth. (zipped)',
#			'It would be nice to spend resources on buildings and units, but right now they are desperately needed for more pylons.',
#			"You're killin' me, Smalls. (angry)",
			"Starting stage failed, moving to gamestate mode",
			]		

		self.intro_descriptions = {
			1 : 'one base',
			2 : 'one base rush defense',
			3 : "two bases",	
			4 : 'two bases rush defense',	
			5 : '3 greedy bases',
		}


	def getIntroDescription(self, intro_id):
		return self.intro_descriptions.get(intro_id)

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