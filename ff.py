from pprint import pprint
from bs4 import BeautifulSoup
import requests
from splinter import Browser
import os
import json
import re


def addRankingToExperts(expertNames, expertsRankings, playerWithRankings):
	playerName = playerWithRankings[1].strip()
	i = 3
	first = playerWithRankings[i].strip()
	# Skip the injury field if there is one
	if first == 'Q' or first == 'P' or first == 'D' or first == 'O':
		i = 5
	else:
		i = 4
	for expert in expertNames:
		if playerWithRankings[i].strip() == 'NR':
			expertsRankings[expert].append((playerName, float('inf')))
		elif expert == "Avg":
			expertsRankings[expert].append((playerName, float(playerWithRankings[i])))
		else:
			expertsRankings[expert].append((playerName, int(playerWithRankings[i])))
		i += 1

def printRankings(expertRankings):
	for expert in expertRankings.keys():
		if expert != "Avg":
			print(expert + "'s Rankings:")
			for ranking in expertRankings[expert]:
				print(str(ranking[1]) + ". " + ranking[0])
			print()
	print("Average rankings for each player: ")
	for ranking in expertRankings["Avg"]:
		print(ranking[0] + ": " + str(ranking[1]))

def getWeek10Rankings():
	browser = Browser('firefox')
	url = 'http://espn.go.com/fantasy/football/story/_/page/15ranksWeek9QB/fantasy-football-week-9-quarterback-rankings'
	browser.visit(url)

	table_data = browser.html
	soup = BeautifulSoup(table_data, 'lxml')
	headers = soup.find(class_= "tal header").find_all_next('tr')

	expertNames = ["Berry", "Karabell", "Yates", "Cockroft", "Clay", "Avg"]
	expertsRankings = {}
	for expert in expertNames:
		expertsRankings[expert] = []

	for i in headers:
		playerWithRankings = i.get_text(" | ").split("|")
		# (player name, ranking)
		addRankingToExperts(expertNames, expertsRankings, playerWithRankings)

	for expert in expertsRankings.keys():
		expertsRankings[expert].sort(key= lambda tup: tup[1])

	# printRankings(expertsRankings)
	browser.quit()
	return expertsRankings

def getActualRankings():
	browser = Browser('firefox')
	url = 'http://games.espn.go.com/ffl/leaders?&slotCategoryId=0&scoringPeriodId=9&seasonId=2015'
	browser.visit(url)

	table_data = browser.html
	soup = BeautifulSoup(table_data, 'lxml')

	# (player name -> (position rank, fantasy points))
	actualRankings = {}

	headers = soup.find_all(class_= re.compile("^pncPlayerRow"))
	j = 1
	for i in headers:
		playerStats = i.get_text(" | ").split("|")
		# print(playerStats)
		actualRankings[playerStats[0].strip()] = (j, float(playerStats[-1]))
		j += 1
	# print(actualRankings)
	browser.quit()
	return actualRankings

def expertScore(expertRankings, actualRankings):
	# expertRankings: (player name, ranking)
	# actualRankings: (player name -> (position rank, fantasy points))
	# print("expert rankings")
	# print(expertRankings)
	# print("actual rankings: ")
	# print(actualRankings)
	score = 0.0
	processed = []
	for i in range(len(expertRankings)):
		currPlayer = expertRankings[i][0]
		currPlayerExpertRanking = expertRankings[i][1]
		processed.append(currPlayer)
		currPlayerActualRanking = actualRankings[currPlayer][0]
		currPlayerActualPoints = actualRankings[currPlayer][1]
		for j in range(i+1, len(expertRankings)):
			# By nature of the expert rankings being sorted, we know that each player we
			# are comparing to will have a worse ranking than the current one.
			comparePlayer = expertRankings[j][0]
			comparePlayerActualRanking = actualRankings[comparePlayer][0]
			comparePlayerActualPoints = actualRankings[comparePlayer][1]
			# Success
			if currPlayerActualRanking <= comparePlayerActualRanking:
				score += abs(currPlayerActualPoints - comparePlayerActualPoints)**2
			# Failure
			else:
				score -= abs(currPlayerActualPoints - comparePlayerActualPoints)**2
	return score/100.0

def getScoresForExperts(expertsRankings, actualRankings):

	scores = []
	for expert in expertsRankings.keys():
		score = expertScore(expertsRankings[expert], actualRankings)
		scores.append((expert, score))
	return scores

def main():
	expertsRankings = getWeek10Rankings()
	actualRankings = getActualRankings()
	scores = getScoresForExperts(expertsRankings, actualRankings)
	for tup in scores:
		print(tup[0] + " : " + str(tup[1]))

main()


