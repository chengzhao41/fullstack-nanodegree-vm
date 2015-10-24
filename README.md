README for tournament

There should be 3 files:
	1) tournament.sql: used for creating the database, tables, and views
	2) tournmanet.py: the python methods for running a tournamnet
	3) tournament_test.py: unit tests for making sure that everyone works

Requirements:
- have python installed
- have postgres installed

Instructions:

1) Installing the database
	a) Navigate to folder containing "tournament.sql" 
	b) run psql
	c) run "\i tournament.sql"

2) Running the python program
	a) Naivgate to folder containing "tournament.py"
	b) run python
	c) run "from tournament import *"
	d) now run the methods that you wish


Bonus features:
	1) Able to handle odd number of players
	2) Prevents rematches between players
	3) Support games where a draw is possible