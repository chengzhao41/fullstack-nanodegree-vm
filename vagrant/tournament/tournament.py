#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    conn = psycopg2.connect("dbname=tournament")
    c = conn.cursor()
    c.execute("delete from matches;")
    conn.commit()
    conn.close()
    return 


def deletePlayers():
    """Remove all the player records from the database."""
    conn = psycopg2.connect("dbname=tournament")
    c = conn.cursor()
    c.execute("delete from players;")
    conn.commit()
    conn.close()
    return 


def countPlayers():
    """Returns the number of players currently registered."""
    conn = psycopg2.connect("dbname=tournament")
    c = conn.cursor()
    c.execute("select count(*) from players;")
    numberOfPlayers = c.fetchone()[0]
    conn.close()
    return numberOfPlayers


def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    conn = psycopg2.connect("dbname=tournament")
    c = conn.cursor()
    c.execute("insert into players (name) values (%s);", (name,))
    conn.commit()
    conn.close()
    return 


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        ties: the number of matches the player has tied
        matches: the number of matches the player has played
    """
    conn = psycopg2.connect("dbname=tournament")
    c = conn.cursor()
    c.execute("select id, name, wins, matches from standings;")
    rows = c.fetchall()
    conn.close()
    return rows


def reportMatch(winner, loser=None, tie=False):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost, if it is None, then winner received a bye
      tie: boolean value that indicates if the match was a tie
    """
    conn = psycopg2.connect("dbname=tournament")
    c = conn.cursor()
    if loser is None: 
        c.execute("insert into matches (winner_id) values (%s);", (winner,))
    else:
        c.execute("insert into matches (winner_id, loser_id, tie) values (%s, %s, %s);", (winner, loser, tie))
    conn.commit()
    conn.close()
    return 
 
 
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    If there are an odd number of players, the lowest ranked player who has not
    received a bye, will be set up to get a bye.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    conn = psycopg2.connect("dbname=tournament")
    c = conn.cursor()
    c.execute("select p1_id, p1_name, p2_id, p2_name from pairings where row_number % 2 = 1;")
    rows = c.fetchall()

    if (countPlayers() % 2 == 1):
        c.execute("select id, name from bye_player;")
        result = c.fetchone();
        if (result != ()):
            rows.append((result[0], result[1], None, None))
    conn.close()
    return rows



