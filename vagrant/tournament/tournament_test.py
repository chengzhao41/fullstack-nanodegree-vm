#!/usr/bin/env python
#
# Test cases for tournament.py

from tournament import *

def testDeleteMatches():
    deleteMatches()
    print "1. Old matches can be deleted."


def testDelete():
    deleteMatches()
    deletePlayers()
    print "2. Player records can be deleted."


def testCount():
    deleteMatches()
    deletePlayers()
    c = countPlayers()
    if c == '0':
        raise TypeError(
            "countPlayers() should return numeric zero, not string '0'.")
    if c != 0:
        raise ValueError("After deleting, countPlayers should return zero.")
    print "3. After deleting, countPlayers() returns zero."


def testRegister():
    deleteMatches()
    deletePlayers()
    registerPlayer("Chandra Nalaar")
    c = countPlayers()
    if c != 1:
        raise ValueError(
            "After one player registers, countPlayers() should be 1.")
    print "4. After registering a player, countPlayers() returns 1."
    registerPlayer("Cheng Zhao")
    c = countPlayers()
    if c != 2:
        raise ValueError(
            "After 2 players registers, countPlayers() should be 2.")
    print "4b. After registering 2 players, countPlayers() returns 2."


def testRegisterCountDelete():
    deleteMatches()
    deletePlayers()
    registerPlayer("Markov Chaney")
    registerPlayer("Joe Malik")
    registerPlayer("Mao Tsu-hsi")
    registerPlayer("Atlanta Hope")
    c = countPlayers()
    if c != 4:
        raise ValueError(
            "After registering four players, countPlayers should be 4.")
    deletePlayers()
    c = countPlayers()
    if c != 0:
        raise ValueError("After deleting, countPlayers should return zero.")
    print "5. Players can be registered and deleted."


def testStandingsBeforeMatches():
    deleteMatches()
    deletePlayers()
    registerPlayer("Melpomene Murray")
    registerPlayer("Randy Schwartz")
    standings = playerStandings()
    if len(standings) < 2:
        raise ValueError("Players should appear in playerStandings even before "
                         "they have played any matches.")
    elif len(standings) > 2:
        raise ValueError("Only registered players should appear in standings.")
    if len(standings[0]) != 4:
        raise ValueError("Each playerStandings row should have four columns.")
    [(id1, name1, wins1, matches1), (id2, name2, wins2, matches2)] = standings
    if matches1 != 0 or matches2 != 0 or wins1 != 0 or wins2 != 0:
        raise ValueError(
            "Newly registered players should have no matches or wins.")
    if set([name1, name2]) != set(["Melpomene Murray", "Randy Schwartz"]):
        raise ValueError("Registered players' names should appear in standings, "
                         "even if they have no matches played.")
    print "6. Newly registered players appear in the standings with no matches."


def testReportMatches():
    deleteMatches()
    deletePlayers()
    registerPlayer("Bruno Walton")
    registerPlayer("Boots O'Neal")
    registerPlayer("Cathy Burton")
    registerPlayer("Diane Grant")
    standings = playerStandings()
    [id1, id2, id3, id4] = [row[0] for row in standings]
    reportMatch(id1, id2)
    reportMatch(id3, id4)
    standings = playerStandings()
    for (i, n, w, m) in standings:
        if m != 1:
            raise ValueError("Each player should have one match recorded.")
        if i in (id1, id3) and w != 1:
            raise ValueError("Each match winner should have one win recorded.")
        elif i in (id2, id4) and w != 0:
            raise ValueError("Each match loser should have zero wins recorded.")
    print "7. After a match, players have updated standings."

    reportMatch(id1, id3)
    reportMatch(id2, id4)
    standings = playerStandings()
    for (i, n, w, m) in standings:
        if m != 2:
            raise ValueError("Each player should have 2 match recorded.")
        if i in (id1, ) and w != 2:
            raise ValueError("1 player should have 2 win recorded.")
        elif i in (id2, id3) and w != 1:
            raise ValueError("2 players should have 1 win recorded.")
        elif i in (id4, ) and w != 0:
            raise ValueError("1 player should have 0 wins recorded.")
    print "7b. After a match, players have updated standings."


def testPairings():
    deleteMatches()
    deletePlayers()
    registerPlayer("Twilight Sparkle")
    registerPlayer("Fluttershy")
    registerPlayer("Applejack")
    registerPlayer("Pinkie Pie")
    standings = playerStandings()
    [id1, id2, id3, id4] = [row[0] for row in standings]
    reportMatch(id1, id2)
    reportMatch(id3, id4)
    pairings = swissPairings()
    if len(pairings) != 2:
        raise ValueError(
            "For four players, swissPairings should return two pairs.")
    [(pid1, pname1, pid2, pname2), (pid3, pname3, pid4, pname4)] = pairings
    correct_pairs = set([frozenset([id1, id3]), frozenset([id2, id4])])
    actual_pairs = set([frozenset([pid1, pid2]), frozenset([pid3, pid4])])
    if correct_pairs != actual_pairs:
        raise ValueError(
            "After one match, players with one win should be paired.")
    print "8. After one match, players with one win are paired."


def testReportMatchesWithOddPlayers():
    deleteMatches()
    deletePlayers()
    registerPlayer("Apple Walton")
    registerPlayer("Boots O'Neal")
    registerPlayer("Cathy Burton")
    standings = playerStandings()
    [id1, id2, id3] = [row[0] for row in standings]
    reportMatch(id1, id2)
    reportMatch(id3) # received a bye
    standings = playerStandings()
    for (i, n, w, m) in standings:
        if m != 1:
            raise ValueError("Each player should have one match recorded.")
        if i in (id1, id3) and w != 1:
            raise ValueError("Each match winner should have one win recorded.")
        elif i in (id2,) and w != 0:
            raise ValueError("Each match loser should have zero wins recorded.")
    print "9. After a match, all 3 players have updated standings."

    deleteMatches()
    deletePlayers()
    registerPlayer("Apple Walton")
    registerPlayer("Boots O'Neal")
    registerPlayer("Cathy Burton")
    registerPlayer("Twilight Sparkle")
    registerPlayer("Fluttershy")
    standings = playerStandings()
    [id1, id2, id3, id4, id5] = [row[0] for row in standings]
    reportMatch(id1, id2)
    reportMatch(id3, id4) 
    reportMatch(id5)# received a bye
    standings = playerStandings()
    for (i, n, w, m) in standings:
        if m != 1:
            raise ValueError("Each player should have one match recorded.")
        if i in (id1, id3, id5) and w != 1:
            raise ValueError("Each match winner should have one win recorded.")
        elif i in (id2, id4) and w != 0:
            raise ValueError("Each match loser should have zero wins recorded.")
    print "9b. After a match, all 5 players have updated standings."


def testPairingsWithOddPlayers():
    deleteMatches()
    deletePlayers()
    registerPlayer("Twilight Sparkle")
    registerPlayer("Fluttershy")
    registerPlayer("Applejack")
    registerPlayer("Pinkie Pie")
    registerPlayer("Cheng Zhao")
    standings = playerStandings()
    pairings = swissPairings()

    if len(pairings) != 3:
        raise ValueError(
            "For 5 players, swissPairings should return 3 pairs.")
    [(pid1, pname1, pid2, pname2), (pid3, pname3, pid4, pname4), (pid5, pname5, pid6, pname6)] = pairings
    if pid6 is not None:
    	raise ValueError("1 player should have received a bye")

    reportMatch(pid1, pid2)
    reportMatch(pid3, pid4)
    reportMatch(pid5, pid6)

    standings = playerStandings()
    for (i, n, w, m) in standings:
        if m != 1:
            raise ValueError("Each player should have one match recorded.")
        if i in (pid1, pid3, pid5) and w != 1:
            raise ValueError("Each match winner should have one win recorded.")
        elif i in (pid2, pid4) and w != 0:
            raise ValueError("Each match loser should have zero wins recorded.")
    print "10. After a match, all 5 players have updated standings."


if __name__ == '__main__':
    testDeleteMatches()
    testDelete()
    testCount()
    testRegister()
    testRegisterCountDelete()
    testStandingsBeforeMatches()
    testReportMatches()
    testPairings()
    # my own tests
    testReportMatchesWithOddPlayers()
    testPairingsWithOddPlayers()
    print "Success!  All tests pass!"

    # delete 
    deleteMatches()
    deletePlayers()
