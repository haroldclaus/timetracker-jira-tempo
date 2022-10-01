#!/usr/bin/env python3

import argparse
import random
import string
import os
import json
import sys
from os.path import exists
import csv
import pandas as pd
import time,datetime
from pathlib import Path

from Timetracker.objects.entity import Entity

class Io:
    def __init__(self, day = None):
        if day == None:
            e = datetime.datetime.now()
            s = "-"
            arrDay = [str(e.year), str(e.month), str(e.day)]
            day = s.join(arrDay)
            self.day = day
        else:
            self.day = day

        self.log_folder = str(Path.home()) + "/Timetracker/"
        self.log_file = "tt-" + day + ".csv"
        self.settings_file = "settings.json"
        self.path_to_file = self.log_folder + self.log_file
        self.path_to_settings_file = self.log_folder + self.settings_file
        self.createCsvIfNotExists()
        self.createSettingsIfNotExists()
        #print(self.log_file)
        #sys.exit()

    def createCsvIfNotExists(self):
        # Check whether the specified path exists or not
        isExist = os.path.exists(self.log_folder)

        # If it doesn't exists, create it
        if not isExist:
          # Create a new directory because it does not exist
          os.makedirs(self.log_folder)
          print("The new directory is created! Dir: " + self.log_folder)

        file_exists = exists(self.path_to_file)
        if not file_exists:
            self.createCsv()

    def getSettings(self):
        with open(self.path_to_settings_file) as settings_json_file:
            settings = json.load(settings_json_file)
            return settings

    def getSetting(self, key):
        settings = self.getSettings()
        return settings[key]

    def getSettingEmail(self):
        settings = self.getSettings()
        return settings['email']

    def getSettingTokenJira(self):
        settings = self.getSettings()
        return settings['token_jira']

    def getSettingTokenTempo(self):
        settings = self.getSettings()
        return settings['token_tempo']


    def validateSettings(self):
        settings = self.getSettings()
        for key in settings:
            if settings[key] == '':
                print("Settings are incomplete. Please run the 'tt settings' command to fullfil the configuration.")
                sys.exit()

    def createSettingsIfNotExists(self):
        config_file_exists = exists(self.path_to_settings_file)
        if not config_file_exists:
            basicSettingsData = {
                'email' : '',
                'token_jira' : '',
                'token_tempo' : ''
            }
            self.upsertSettingsJson(basicSettingsData)

    def createCsv(self):
        file = open(self.path_to_file,'a+')
        message = "entity_id;ticket;comment;created_at;time;start;end;send;jira_id;tempo_id"
        file.write(str(message) + "\n")
        file.close()
        print("New worklog has been created: " + self.path_to_file)

    def upsertSettingsJson(self, settingsData):
        file = open(self.path_to_settings_file,'w')

        settingsDataStr = json.dumps(settingsData)
        file.write(str(settingsDataStr))
        file.close()
        print("Settings file created/updated")

    def getLogFile(self):
        return self.log_file;

    def setLogFile(self, strLogFile):
        self.log_file = strLogFile

    def getEntityObjects(self, filePath = None):
        if not filePath:
            filePath = self.path_to_file
        arrEntityModels = []
        intCount = 0

        logFile = self.path_to_file
        #print("Logfile path: " + logFile)

        with open(filePath, newline='') as csvfile:
            spamReader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row in spamReader:
                intCount += 1
                if intCount == 1:
                    continue
                parsedEntity = Entity()
                parsedEntity.set_entity_id(row[0])
                parsedEntity.set_ticket(row[1])
                parsedEntity.set_comment(row[2])
                parsedEntity.set_created_at(row[3])
                parsedEntity.set_time(row[4])
                parsedEntity.set_start(row[5])
                parsedEntity.set_end(row[6])
                parsedEntity.set_send(row[7])
                parsedEntity.set_jira_id(row[8])
                parsedEntity.set_tempo_id(row[9])
                arrEntityModels.append(parsedEntity)
        return arrEntityModels

    def writeToFile(self, message):
        f = open(self.path_to_file, "a")
        f.write(str(message) + "\n")
        f.close()
