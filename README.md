# AdditionalPylons
Starcraft 2 Bot written in python using the python-sc2 API.   Uses intelligence gathered to build a response with units to counter the known enemy units. 

Currently competes on the [Starcraft 2 AI ladder](http://sc2ai.net/)

## Prerequisites
* Python3.7
* [python-sc2](https://github.com/Dentosal/python-sc2) - SC2 API

##additionalpylons.py Settings
###### \_debug
Setting this to true is required for any debugging to show up.   If set to False, all other debug settings should also be set to False, as they will eat up extra resources when true.

###### \_debug_economy
Shows the intel along with the demands needed for units.

###### \_debug_positions
Shows the position of some set buildings.

###### \_debug_score
Shows the score of the units around a selected unit.   Creates a sleep timeout as well and will slow the game to a stop when many units are being scored.

###### \_debug_counters
Shows the enemy intel along with the raw amount of counters to train in response.

###### \_debug_effects
Shows the position and radius of some effects.

###### \_debug_combat
Draws lines to see what the units are targeting, as well as giving their current action in text.   If \_debug is true, any unit(s) selected will have this turned on for them, even if this is false.

###### \_local_ladder
Prints opp_id to stdout at the start of the match.  Can be used to debug other prints following, but won't be useful in most cases. 

###### \_use_data
Determines if the bot saves opponent data to learn the best strategy and preseed intel.

###### \_test_strat_id
Force an opening strategy to use(Currently 1-5).   Set to 0 to turn off.


## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
