import pickle
import random
from operator import itemgetter

'''
Saves the result and data to find better strats that work.

{opp_id: [[match_id, strat_id, result, race],]}

'''

class TrainingData:
	
	
	def __init__(self):
		self.data_dict = {}
		self.opp_units = {}
		#load the pickle data.
		self.loadData()
		self.strat_count = 6

	def findStrat(self, opp_id, race, map_name):
		#check if this is a new opponent.
		if not self.data_dict.get(opp_id):
			#check for the best overall strat for this map and race.
			best_id = self.bestMapRaceStrat(map_name, race)
			if best_id:
				return best_id
			#check for the best overall strat for this map.
			best_id = self.bestMapStrat(map_name)
			if best_id:
				return best_id			
			#check for the best overall strat for this race.
			best_id = self.bestRaceStrat(race)
			if best_id:
				return best_id			
			#check for the best overall strat.
			best_id = self.bestOverallStrat()
			if best_id:
				return best_id			
			#well, it seems the database is completely empty, random time.
			return random.randint(1, (self.strat_count - 1))
		
		#check based on the opp_id and map_name to see if we can get a strat_id.
		optimal_id = self.bestOppMapStrat(opp_id, map_name)
		if optimal_id:
			return optimal_id
		
		#if we have never played on this map before, find the best strat we can find for this opponent in general.
		gen_id = self.bestOppStrat(opp_id)
		if gen_id:
			return gen_id
		
		#if we still don't have a match, then it's just because we haven't won.   Just pick a random one.
		return random.randint(1, (self.strat_count - 1))
	

###############
#Strat Lookups#
###############
	
	def bestRaceStrat(self, race):
		strat_stats = {}
		for opp_id, matches in self.data_dict.items():
			for match in matches:			
				#opp_id : match_id, strat_id, result, race, map
				if strat_stats.get(match[1]) and match[3] == race:
					#add to the results.
					ss = strat_stats.get(match[1])
					wins = ss[0]
					losses = ss[1]
					if match[2] == 'w':
						wins += 1
					else:
						losses += 1
					#update the strat stats.
					strat_stats.update({match[1]:[wins, losses]})
				elif match[3] == race:
					wins = 0
					losses = 0
					if match[2] == 'w':
						wins += 1
					else:
						losses += 1				
					strat_stats.update({match[1]:[wins, losses]})

		#get the win% of the strats and choose the best.
		#if the best win% is below 50%, then make sure we have tried all strats.
		if len(strat_stats) > 0:		
			best_win = -1
			best_strat = 0
			available_strats = list(range(1, self.strat_count))
			for strat_id, results in strat_stats.items():
				winper = results[0] / (results[0] + results[1])
				#print ('1 map tried', strat_id, winper, results[0], results[1])
				available_strats.remove(strat_id)
				if winper > best_win:
					best_strat = strat_id
					best_win = winper
			if best_win < .50 and len(available_strats) > 0:
				return random.choice(available_strats)
			if best_win == 0:
				return None
			return best_strat
		return None
	
	def bestMapRaceStrat(self, map_name, race):
		strat_stats = {}
		for opp_id, matches in self.data_dict.items():
			for match in matches:
				#opp_id : match_id, strat_id, result, race, map
				if strat_stats.get(match[1]) and match[3] == race and match[4] == map_name:
					#add to the results.
					ss = strat_stats.get(match[1])
					wins = ss[0]
					losses = ss[1]
					if match[2] == 'w':
						wins += 1
					else:
						losses += 1
					#update the strat stats.
					strat_stats.update({match[1]:[wins, losses]})
				elif match[3] == race and match[4] == map_name:
					wins = 0
					losses = 0
					if match[2] == 'w':
						wins += 1
					else:
						losses += 1				
					strat_stats.update({match[1]:[wins, losses]})	
		if len(strat_stats) > 0:
			#get the win% of the strats and choose the best.
			#if the best win% is below 50%, then make sure we have tried all strats.
			best_win = -1
			best_strat = 0
			available_strats = list(range(1, self.strat_count))
			for strat_id, results in strat_stats.items():
				winper = results[0] / (results[0] + results[1])
				#print ('1 map tried', strat_id, winper, results[0], results[1])
				available_strats.remove(strat_id)
				if winper > best_win:
					best_strat = strat_id
					best_win = winper
			if best_win < .50 and len(available_strats) > 0:
				return random.choice(available_strats)
			if best_win == 0:
				return None
			return best_strat
		return None

	def bestOverallStrat(self):
		strat_stats = {}
		for opp_id, matches in self.data_dict.items():
			for match in matches:
				#opp_id : match_id, strat_id, result, race, map
				if strat_stats.get(match[1]):
					#add to the results.
					ss = strat_stats.get(match[1])
					wins = ss[0]
					losses = ss[1]
					if match[2] == 'w':
						wins += 1
					else:
						losses += 1
					#update the strat stats.
					strat_stats.update({match[1]:[wins, losses]})
				else:
					wins = 0
					losses = 0
					if match[2] == 'w':
						wins += 1
					else:
						losses += 1				
					strat_stats.update({match[1]:[wins, losses]})
		if len(strat_stats) > 0:
			#get the win% of the strats and choose the best.
			#if the best win% is below 50%, then make sure we have tried all strats.
			best_win = -1
			best_strat = 0
			available_strats = list(range(1, self.strat_count))
			for strat_id, results in strat_stats.items():
				winper = results[0] / (results[0] + results[1])
				#print ('over tried', strat_id, winper, results[0], results[1])
				available_strats.remove(strat_id)
				if winper > best_win:
					best_strat = strat_id
					best_win = winper
			if best_win < .50 and len(available_strats) > 0:
				return random.choice(available_strats)
			if best_win == 0:
				return None
			return best_strat
		return None

	def bestMapStrat(self, map_name):
		strat_stats = {}
		for opp_id, matches in self.data_dict.items():
			for match in matches:			
				#opp_id : match_id, strat_id, result, race, map
				if strat_stats.get(match[1]) and match[4] == map_name:
					#add to the results.
					ss = strat_stats.get(match[1])
					wins = ss[0]
					losses = ss[1]
					if match[2] == 'w':
						wins += 1
					else:
						losses += 1
					#update the strat stats.
					strat_stats.update({match[1]:[wins, losses]})
				elif match[4] == map_name:
					wins = 0
					losses = 0
					if match[2] == 'w':
						wins += 1
					else:
						losses += 1				
					strat_stats.update({match[1]:[wins, losses]})
		if len(strat_stats) > 0:
			#get the win% of the strats and choose the best.
			#if the best win% is below 50%, then make sure we have tried all strats.
			best_win = -1
			best_strat = 0
			available_strats = list(range(1, self.strat_count))
			for strat_id, results in strat_stats.items():
				winper = results[0] / (results[0] + results[1])
				#print ('1 map tried', strat_id, winper, results[0], results[1])
				available_strats.remove(strat_id)
				if winper > best_win:
					best_strat = strat_id
					best_win = winper
			if best_win < .50 and len(available_strats) > 0:
				return random.choice(available_strats)
			if best_win == 0:
				return None
			return best_strat
		return None
		
	def bestOppMapStrat(self, opp_id, map_name):
		opp_data = self.data_dict.get(opp_id)
		strat_stats = {}
		for match in opp_data:
			#match_id, strat_id, result, race, map
			
			if strat_stats.get(match[1]) and match[4] == map_name:
				#add to the results.
				ss = strat_stats.get(match[1])
				wins = ss[0]
				losses = ss[1]
				if match[2] == 'w':
					wins += 1
				else:
					losses += 1
				#update the strat stats.
				strat_stats.update({match[1]:[wins, losses]})
			elif match[4] == map_name:
				wins = 0
				losses = 0
				if match[2] == 'w':
					wins += 1
				else:
					losses += 1				
				strat_stats.update({match[1]:[wins, losses]})
		#get the win% of the strats and choose the best.
		#if the best win% is below 50%, then make sure we have tried all strats.
		if len(strat_stats) > 0:		
			best_win = -1
			best_strat = 0
			available_strats = list(range(1, self.strat_count))
			for strat_id, results in strat_stats.items():
				winper = results[0] / (results[0] + results[1])
				if results[0] + results[1] > 2:
					self.cleanStrat(opp_id, strat_id, map_name)
				#print ('opp map tried', strat_id, winper, results[0], results[1])
				available_strats.remove(strat_id)
				if winper > best_win:
					best_strat = strat_id
					best_win = winper
			if best_win < .50 and len(available_strats) > 0:
				return random.choice(available_strats)
			if best_win == 0:
				return None
			return best_strat
		return None
				
	def bestOppStrat(self, opp_id):
		#this opponent has a history, lets find the best strat
		opp_data = self.data_dict.get(opp_id)
		strat_stats = {}
		for match in opp_data:
			#match_id, strat_id, result, race, map
			if strat_stats.get(match[1]):
				#add to the results.
				ss = strat_stats.get(match[1])
				wins = ss[0]
				losses = ss[1]
				if match[2] == 'w':
					wins += 1
				else:
					losses += 1
				#update the strat stats.
				strat_stats.update({match[1]:[wins, losses]})
			else:
				wins = 0
				losses = 0
				if match[2] == 'w':
					wins += 1
				else:
					losses += 1				
				strat_stats.update({match[1]:[wins, losses]})
		if len(strat_stats) > 0:				
			#get the win% of the strats and choose the best.
			#if the best win% is below 50%, then make sure we have tried all strats.
			best_win = -1
			best_strat = 0
			available_strats = list(range(1, self.strat_count))
			for strat_id, results in strat_stats.items():
				winper = results[0] / (results[0] + results[1])
				#print ('opp nomap tried', strat_id, winper, results[0], results[1])
				available_strats.remove(strat_id)
				if winper > best_win:
					best_strat = strat_id
					best_win = winper
			if best_win < .50 and len(available_strats) > 0:
				return random.choice(available_strats)
			if best_win == 0:
				return None
			return best_strat
		return None
	

#################
#Data Management#
#################

	def cleanStrat(self, opp_id, strat_id, map_name):
		#get the list of match_ids of the opponenet and only keep the most recent 10 matches.
		#opp_data = self.data_dict.get(opp_id)
		opp_data = [x for x in self.data_dict.get(opp_id) if x[1] == strat_id and x[4] == map_name]
		opp_data = sorted(opp_data, key=itemgetter(0), reverse=True)
		del opp_data[9:]
		#remove existing data for the strat_id and create a new list for the dictionary.
		old_data = self.data_dict.get(opp_id)
		for match in old_data:
			if match[1] != strat_id:
				#not the strat being cleaned, add the match.
				opp_data.append(match)
		self.data_dict.update({opp_id:opp_data})
		#save the results to file.
		self.saveData()

	def removeResult(self, opp_id, match_id):
		#remove the match from the list and save.
		if not self.data_dict.get(opp_id):
			print ('ut oh, where is the match?')
			return
		#opp_data = self.data_dict.get(opp_id)
		opp_data = [x for x in self.data_dict.get(opp_id) if not x[0] == match_id]
		self.data_dict.update({opp_id:opp_data})
		#save the results to file.
		self.saveData()			

	def saveResult(self, opp_id, strat_id, result, match_id, race, map_name):
		if not self.data_dict.get(opp_id):
			#this is a new opponent, add the entry to the dictionary.
			self.data_dict.update({opp_id: [[match_id, strat_id, result, race, map_name]]})
		else:
			#existing opponent, update the dictionary.
			opp_data = self.data_dict.get(opp_id)
			opp_data.append([match_id, strat_id, result, race, map_name])
			self.data_dict.update({opp_id:opp_data})
		#save the results to file.
		self.saveData()		
	
	def getOppHistory(self, opp_id):
		return self.opp_units.get(opp_id)
	
	def saveUnitResult(self, opp_id, units):
		#only saving the last games units, so always just overwrite the previous.
		self.opp_units.update({opp_id:units})
		#now save it.
		self.saveUnitsData()
		
		
	
#################
#File Management#
#################


	def saveUnitsData(self):
		with open("data/unitRes.dat", "wb") as fp:
			pickle.dump(self.opp_units, fp)		

	def loadData(self):
		try:
			with open("data/res2.dat", "rb") as fp:
				self.data_dict = pickle.load(fp)
		except (OSError, IOError) as e:
			self.data_dict = {}
			
		try:
			with open("data/unitRes.dat", "rb") as fp:
				self.opp_units = pickle.load(fp)
		except (OSError, IOError) as e:
			self.opp_units = {}
			

	def saveData(self):
		try:
			with open("data/res2.dat", "wb") as fp:
				pickle.dump(self.data_dict, fp)
		except (OSError, IOError) as e:
			print (str(e))
	
########
#Others#
########
	def totalOppDataCount(self, opp):
		if self.data_dict.get(opp):
			return len(self.data_dict.get(opp))	
		return 0


	def totalDataCount(self):
		total = 0
		for opp, matches in self.data_dict.items():
			total += len(matches)
		return total


