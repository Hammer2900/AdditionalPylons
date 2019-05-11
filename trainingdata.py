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
		self.best_win_per = 0
		self.random_choice = True
		self.first_game = False




	def findStrat(self, opp_id, race, map_name):
		#check if this is a new opponent.
		#opp_id = "{}-{}".format(race, str(opp_id))
		if not self.data_dict.get(opp_id):
			#start with strat_id 1.
			self.first_game = True
			return 1
		opp_data = self.data_dict.get(opp_id)
		#print (str(opp_data))
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
		best_strat = 0
		best_winper = 0
		best_losses = 0
		strats = [1,2,3,4,5]
		for key, val in strat_stats.items():
			#print (key, val)
			if key in strats:
				strats.remove(key)
			# else:
			# 	print ('key', key, 'not found')
			# 	print (str(strats))
			winper = (val[0] / (val[0] + val[1])) * 100
			print (key, val, winper)
			if winper > best_winper:
				best_strat = key
				best_winper = winper
				best_losses = val[1]
			#check to see if we have too many.
			if val[0] + val[1] >= 4:
				self.cleanStrat(opp_id, key, map_name)
		self.best_win_per = best_winper
		self.random_choice = False
		
		if best_winper < 100 and len(strats) > 0:
			self.best_win_per = 0
			self.random_choice = True		
			return random.choice(strats)
		if best_strat == 0:
			self.best_win_per = 0
			self.random_choice = True			
			return random.randint(1,5)
		if best_winper < 50:
			#loop all strats have the same amount of losses as the best strat.
			strats = [1,2,3,4,5]
			strats.remove(best_strat)
			try_strats = []
			for strat in strats:
				if strat_stats.get(strat):
					val = strat_stats.get(strat)
					if val[1] < best_losses:
						try_strats.append(strat)
			if len(try_strats) > 0:
				self.random_choice = True
				return random.choice(try_strats)
		return best_strat



#################
#Data Management#
#################

	def cleanStrat(self, opp_id, strat_id, map_name):
		opp_data = [x for x in self.data_dict.get(opp_id) if x[1] == strat_id]
		opp_data = sorted(opp_data, key=itemgetter(0), reverse=True)
		del opp_data[4:]
		#remove existing data for the strat_id and create a new list for the dictionary.
		old_data = self.data_dict.get(opp_id)
		for match in old_data:
			if match[1] != strat_id:
				#not the strat being cleaned, add the match.
				opp_data.append(match)
		self.data_dict.update({opp_id:opp_data})
		#save the results to file.
		self.saveData()
		
		
		
	def removeResult(self, opp_id, match_id, race):
		#opp_id = "{}-{}".format(race, str(opp_id))
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
		#opp_id = "{}-{}".format(race, str(opp_id))
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

	
	def getOppHistory(self, opp_id, race):
		#opp_id = "{}-{}".format(race, str(opp_id))
		return self.opp_units.get(opp_id)
	
	def saveUnitResult(self, opp_id, units, race):
		#opp_id = "{}-{}".format(race, str(opp_id))
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
			with open("data/res.dat", "rb") as fp:
				self.data_dict = pickle.load(fp)
				battles = self.totalDataCount()
				if battles > 20000:
					print ('clearing data')
					self.data_dict.clear()
		except (OSError, IOError) as e:
			self.data_dict = {}
			
		try:
			with open("data/unitRes.dat", "rb") as fp:
				self.opp_units = pickle.load(fp)
		except (OSError, IOError) as e:
			self.opp_units = {}
		

	def saveData(self):
		try:
			with open("data/res.dat", "wb") as fp:
				pickle.dump(self.data_dict, fp)
		except (OSError, IOError) as e:
			print (str(e))
	
########
#Others#
########

	def stratWinPer(self):
		if self.first_game:
			return " I have no opponent data, so this is a good starting point."
		elif self.random_choice:
			return " I need more data, so I'm choosing randomly."
		else:
			return ' I win with it {}% of the time lately.'.format(self.best_win_per)

		

	def totalOppDataCount(self, opp, race):
		#opp = "{}-{}".format(race, str(opp))
		if self.data_dict.get(opp):
			return len(self.data_dict.get(opp))	
		return 0


	def totalDataCount(self):
		total = 0
		for opp, matches in self.data_dict.items():
			total += len(matches)
		return total


