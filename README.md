# AdditionalPylons
Starcraft 2 Bot written in python using the python-sc2 API.   Uses intelligence gathered to build a response with units to counter the known enemy units. 

Currently competes on the [Starcraft 2 AI ladder](http://sc2ai.net/)

## Prerequisites
* Python3.7
* [python-sc2](https://github.com/Dentosal/python-sc2) - SC2 API

## config.ini Settings

#### [Debug]
###### debug
Setting this to true is required for any debugging to show up.   If set to False, all other debug settings should also be set to False, as they will eat up extra resources when true.

###### debug_economy
Shows the intel along with the demands needed for units.

###### debug_positions
Shows the position of some set buildings.

###### debug_score
Shows the score of the units around a selected unit.   Creates a sleep timeout as well and will slow the game to a stop when many units are being scored.

###### debug_counters
Shows the enemy intel along with the raw amount of counters to train in response.

###### debug_effects
Shows the position and radius of some effects.

###### debug_combat
Draws lines to see what the units are targeting, as well as giving their current action in text.   If \_debug is true, any unit(s) selected will have this turned on for them, even if this is false.

###### local_ladder
Prints opp_id to stdout at the start of the match.  Can be used to debug other prints following, but won't be useful in most cases. 

#### [Strategy]
###### use_data
Determines if the bot saves opponent data to learn the best strategy and preseed intel.

###### test_strat_id
Force an opening strategy to use(Currently 1-5) when data is on.   Set to 0 to turn off.

###### zerg_race_strat_id
Opening strat that will be used against Zerg bots when data is off.

###### protoss_race_strat_id
Opening strat that will be used against Protoss bots when data is off.

###### terran_race_strat_id
Opening strat that will be used against Terran bots when data is off.

## unit_counters.py
###### self.unitPower 
Contains the power score used to determine attack and defend.

###### self.counterTable
This table controls how the bot will behave overall. 

The top "row" in this array below is considered to be the ideal counter.   If the building requirements are met to build all the units in the row, it will build those counters.   If the building requirements aren't met, then it will go down to the next entry in the array until it finds a complete row it is able to build.

```python
'Colossus': [
	[['Immortal', 1], ['Phoenix', 2]],
	[['Stalker', 6], ['Zealot', 5]],
	[['Zealot', 12]],
	],
```
In this example, even if you have a Stargate built, it will not build any Phoenix until it also has a Robotics Factory.   All the requirments of the row must be met.  However, if you add the following row, it will build the Phoenix.

```python
'Colossus': [
	[['Immortal', 1], ['Phoenix', 2]],
	[['Stalker', 6], ['Zealot', 5], ['Phoenix', 2]],
	[['Stalker', 6], ['Zealot', 5]],
	[['Zealot', 12]],
	],
```
And if desired, the following would build both Immortals and Phoenix before both requirements are met.

```python
'Colossus': [
	[['Immortal', 1], ['Phoenix', 2]],
	[['Stalker', 2], ['Immortal', 1]],
	[['Stalker', 2], ['Zealot', 2], ['Phoenix', 2]],
	[['Stalker', 6], ['Zealot', 5]],
	[['Zealot', 12]],
	],
```

The values are how many to build in response to 1 unit.  When only 1 unit is needed in response to larger numbers, just use a decimal value.   The following table would build 1 Colossus for every 10 Marines. 

```python
'Marine': [
	[['Colossus', 0.10]],
	],
```

The bot will automatically change it's build order to accommodate any changes made here.  For example, if the counters for all the units were changed to be just Stalkers, then the bot would automatically build a Cybernetics Core, Mass Warpgates along with a Twilight Council the blink upgrade.   Then you have a mass Blink Stalker bot.   Change them all to Tempest and it will build everything needed and you'll have a mass Tempest bot.  No other changes needed.


## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
