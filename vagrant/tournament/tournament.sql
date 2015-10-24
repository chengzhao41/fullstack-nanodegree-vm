-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.


-- creating database and connecting to it
drop database tournament;
create database tournament;
\c tournament;

-- create tables

-- table of players
create table players 
(id serial primary key,
name varchar(50) not null 
);

-- table of matches
-- if loser_id is Null then winner received a bye
create table matches 
(id serial primary key,
winner_id integer references players(id) not null,
loser_id integer references players(id),
tie boolean DEFAULT false
);

-- view that shows the standings sorted by number of wins
create view standings 
	as select p.id as id, p.name as name, count(w.winner_id) as wins,
	count(w.id) + count(t.id) + count(l.id) as matches,
	row_number() over (order by count(w.winner_id) desc) as rank
	from players as p 
	left join matches as w on p.id = w.winner_id and w.tie = false
	left join matches as t on (p.id = t.loser_id or p.id = t.winner_id) and t.tie = true
	left join matches as l on p.id = l.loser_id and l.tie = false
	group by p.id
	order by wins desc;

-- view that shows all possible pairings, not including duplicates
create view all_pairings
	as select p1.id as p1_id, p1.name as p1_name, 
	p2.id as p2_id, p2.name as p2_name,
	row_number() over (order by p1.rank, p2.rank) as order
	from standings as p1, standings as p2
	where p1.rank < p2.rank;

-- view that shows all pairings of players who have not played in a match yet
create view all_new_pairings
	as select p1_id, p1_name, p2_id, p2_name, 
	row_number() over (partition by p1_id order by all_pairings.order) as pairings,
	all_pairings.order as order
	from all_pairings 
	left join matches as m1
	on all_pairings.p1_id = m1.winner_id and all_pairings.p2_id = m1.loser_id
	left join matches as m2
	on all_pairings.p2_id = m2.winner_id and all_pairings.p1_id = m2.loser_id
	where m1.id is null and m2.id is null
	order by all_pairings.order;

-- view that shows pairings of players with their next ranked players
create view pairings
	as select p1_id, p1_name, p2_id, p2_name,
	row_number() over (order by p.order) as row_number
	from all_new_pairings as p
	where p.pairings = 1;

-- view that shows the next player that should receive a bye
-- this is the player who is ranked last who has not yet received a bye
create view bye_player
	as select sq.id, s.name
	from (
	select s.id as id
	from standings as s
	except
	select m.winner_id as id
	from matches as m
	where m.loser_id is null) as sq
	join standings as s on sq.id = s.id
	order by s.rank desc
	limit 1;


\q