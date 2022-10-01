#!/usr/bin/env python3

import argparse
import random
import string
import csv
import pandas as pd
import sys
import time
import requests
import pycurl
import numpy as np
import base64
from requests.auth import HTTPBasicAuth
from requests.structures import CaseInsensitiveDict
import json
from datetime import datetime
from typing import Union
from tabulate import tabulate

from Timetracker.helper.io import Io
from Timetracker.objects.entity import Entity

TIME_DURATION_UNITS = (
#     ('w', 60*60*24*7),
#     ('d', 60*60*24),
    ('h', 60*60),
    ('m', 60),
    ('s', 1)
)

class Timetracker:

    def __init__(self, day):
        self.day = day
        self.io = Io(day)

    def settings(self):
        # Create file if needed
        settings = self.io.getSettings()

        print("Current settings are:")
        for key in settings:
            print(key + ' : ' + settings[key])

        alterEmail = str(input('Do you wish to alter your MAIL (y/n)?'))
        if alterEmail == 'y':
            newEmail = str(input('Enter new mail: '))
            settings['email'] = newEmail
            
        alterJiraToken = str(input('Do you wish to alter your JIRA TOKEN (y/n)?'))
        if alterJiraToken == 'y':
            newJiraToken = str(input('Enter new jira token: '))
            settings['token_jira'] = newJiraToken
            
        alterTempoToken = str(input('Do you wish to alter your TEMPO TOKEN (y/n)?'))
        if alterTempoToken == 'y':
            newTempoToken = str(input('Enter new tempo token: '))
            settings['token_tempo'] = newTempoToken

        self.io.upsertSettingsJson(settings)

    def printList(self):
        headers = ["ID", "Started", "Ticket", "Duraction", "Comment"]
        arrEntities = self.io.getEntityObjects()
        counter = 0
        totalTimeForTheDay = 0
        if not arrEntities:
            print('No entries found in the file ' + self.io.log_file)

        #data = {}
        data = []

        for entity in arrEntities:
            arrEntity = []
            counter = counter + 1
            strTicket = entity.get_ticket().ljust(17)
            if entity.get_start() > 0 and entity.get_end() == 0:
                duration = self.getCurrentTimestamp() - entity.get_start() + entity.get_time()
                duration = self.getTimeStringBySeconds(duration)
                totalTimeForTheDay += self.getCurrentTimestamp() - entity.get_start() + entity.get_time()
            else:
                duration = self.getTimeStringBySeconds(entity.get_time())
                totalTimeForTheDay += entity.get_time()
            strMessage = '[' + str(counter) + ']'
            strMessage += ' - ' + datetime.fromtimestamp(entity.get_created_at()).strftime("%Y-%m-%d %H:%M:%S")
            strMessage += ' - ' + strTicket + ' - ' + str(duration)

            status = '';
            if (int(entity.get_start()) > 0):
                strMessage += ' - [RUNNING]'
                status = 'running';
            if (int(entity.get_jira_id()) > 0):
                strMessage += ' - [FINISHED]'

            arrDataEntity = [
                str(counter),
                datetime.fromtimestamp(entity.get_created_at()).strftime("%Y-%m-%d %H:%M:%S"),
                strTicket,
                str(duration),
                status,
                str(entity.get_comment())
            ]

            strMessage += ' - ' + str(entity.get_comment())
            #print(strMessage)

            data.append(arrDataEntity)

        #print ("{:<3} {:<20} {:<17} {:<12} {:<50}".format('ID','Start','Ticket','Duration','Comment'))
        #for k, v in data.items():
        #    lang, perc, change, comment = v
        #    print ("{:<3} {:<20} {:<17} {:<12} {:<50}".format(k, lang, perc, change, comment))
        #print('--------------------------------------')
        #print('Current day: ' + self.getTimeStringBySeconds(totalTimeForTheDay))

        print (tabulate(data, headers=["ID", "Start", "Ticket", "Duration", "Status", "Comment"], tablefmt="simple", maxcolwidths=[None, None, None, None, None, 100]))

    def getCurrentTimestamp(self) -> int:
        currentTime = int(time.time())
        return currentTime

    def getTimeStringBySeconds(self, seconds):
        if seconds == 0:
            return '00h 00m 00s'
        parts = []
        for unit, div in TIME_DURATION_UNITS:
            amount, seconds = divmod(int(seconds), div)
            if amount > 0:
                if amount < 10:
                    amount = str('0' + str(amount))
                parts.append('{}{}{}'.format(amount, unit, "" if amount == 1 else ""))
            else:
                parts.append('{}{}{}'.format('00', unit, '' if amount == 1 else ''))
        return ' '.join(parts)

    def startNewEntity(self) -> Entity:
        self.stopAllLogs()
        randomId = self.generateRandomHash()
        currentTime = self.getCurrentTimestamp()
        #print(randomId)
        ticket = str(input('Enter your ticket:'))
        comment = str(input('Enter your comment:'))
        newEntity = Entity(randomId)
        newEntity.set_ticket(ticket)
        newEntity.set_comment(comment)
        newEntity.set_created_at(str(currentTime))
        newEntity.set_start(str(currentTime))

        self.io.writeToFile(newEntity.get_entity_id() + ';' + newEntity.get_ticket() + ';' + newEntity.get_comment() + ';' + str(newEntity.get_created_at()) + ';0;' + str(newEntity.get_start()) + ';0;0;0;0')
        print('New entry created and started')
        return newEntity

    def stopEntity(self, objWorkLog = None):
        if objWorkLog == None:
            objWorkLog = self.selectEntity()

        if self.canUpdate(objWorkLog) == 0:
            print('Can\'t stop this worklog')
            return

        if objWorkLog.get_start() == 0:
            return
        else:
            started_at = int(objWorkLog.get_start())
            stopped_at = int(self.getCurrentTimestamp())
            diff = stopped_at - started_at
            currentTimeRunning = int(objWorkLog.get_time())
            objWorkLog.set_time(diff + currentTimeRunning)
            objWorkLog.set_start(0)
            objWorkLog.set_end(0)
            self.updateEntityByModel(objWorkLog)

    def canUpdate(self, entity) -> bool:
        if entity.get_tempo_id() > 0:
            return 0
        return 1

    def canUpdateTicket(self, entity) -> bool:
        if entity.get_jira_id() > 0:
            return 0
        return 1

    def resumeEntity(self) -> Entity:
        self.stopAllLogs()
        selectedEntity = self.selectEntity()

        if self.canUpdate(selectedEntity) == 0:
            print('Can\'t resume this worklog')
            return selectedEntity

        currentTime = self.getCurrentTimestamp()
        selectedEntity.set_start(currentTime)
        selectedEntity.set_end(0)
        chosenEntity = self.updateEntityByModel(selectedEntity)
        return chosenEntity

    def removeEntity(self):
        objWorkLog = self.selectEntity()

        if self.canUpdate(objWorkLog) == 0:
            print('Can\'t remove this worklog')
            return

        entity_id = objWorkLog.get_entity_id();
        print("Trying to remove entity " + entity_id)

        df = pd.read_csv(self.io.path_to_file, sep=";")

        # 2.
        df_s = df[:5]

        # 3.
        df_s.set_index('entity_id', inplace=True)

        # 4.1.
        df = df_s.drop(str(entity_id))

        df.to_csv(self.io.path_to_file, index=True, sep=";")
        print("Record with ID " + entity_id + " was removed")


    def updateEntityByModel(self, entityModel):
        print(self.io.path_to_file)
        df = pd.read_csv(self.io.path_to_file, index_col="entity_id", sep=";")
        # Set cell value at row 'c' and column 'Age'
        entityId = entityModel.get_entity_id()
        df.loc[entityId, 'ticket'] = entityModel.get_ticket()
        df.loc[entityId, 'comment'] = entityModel.get_comment()
        df.loc[entityId, 'time'] = entityModel.get_time()
        df.loc[entityId, 'start'] = entityModel.get_start()
        df.loc[entityId, 'end'] = entityModel.get_end()
        df.loc[entityId, 'jira_id'] = entityModel.get_jira_id()
        df.loc[entityId, 'tempo_id'] = entityModel.get_tempo_id()
        # Write DataFrame to CSV file
        df.to_csv(self.io.path_to_file, sep=";")
        return entityModel

    def stopAllLogs(self):
        # Get a list of all entities of the specific day
        # Loop over them and stop them if they are running
        objWorkLogs = self.io.getEntityObjects()
        for stopWorklog in objWorkLogs:
            if stopWorklog.get_start() > 0:
                self.stopEntity(stopWorklog)

    def generateRandomHash(self, argLength = 20):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(argLength))

    def loadEntity(self, entityId):
        arrObjects = self.io.getEntityObjects()
        for objEntity in arrObjects:
            if objEntity.get_entity_id() == entityId:
                return objEntity
        return None

    def selectEntity(self):
        arrEntities = self.io.getEntityObjects()
        counter = 0
        references = {}
        if not arrEntities:
            print('No entries found in the file ' + self.io.log_file)
        for entity in arrEntities:
            counter = counter + 1
            strTicket = entity.get_ticket().ljust(18)
            if entity.get_start() > 0 and entity.get_end() == 0:
                duration = self.getCurrentTimestamp() - entity.get_start() + entity.get_time()
                duration = self.getTimeStringBySeconds(duration)
            else:
                duration = self.getTimeStringBySeconds(entity.get_time())
            strMessage = '[' + str(counter) + '] '
            strMessage += ' - ' + datetime.fromtimestamp(entity.get_created_at()).strftime("%Y-%m-%d %H:%M:%S")
            strMessage += ' - ' + strTicket + ' - ' + str(duration)

            if (int(entity.get_start()) > 0):
                strMessage += ' - [RUNNING...]'

            strMessage += ' - ' + str(entity.get_comment())
            print(strMessage)
            references[counter] = entity.get_entity_id()
        chosenId = int(input('Enter your choice:'))
        try:
            chosenEntity = self.loadEntity(references[chosenId])
        except:
            print("Entry " + str(chosenId) + " does not exist")
            sys.exit()
        return chosenEntity

    def selectEntityTypeModel(self):
        # Get OBJECT based on selection in CLI
        objEntity = self.selectEntity()
        return objEntity

    def upsertTicketInEntity(self):
        selectedEntity = self.selectEntityTypeModel()

        if self.canUpdateTicket(selectedEntity) == 0:
            print('Can\'t update the ticket in this worklog. Already sent to JIRA.')
            return

        strTicket = str(input('Enter your JIRA ticket number:'))
        selectedEntity.set_ticket(strTicket)
        self.updateEntityByModel(selectedEntity)
        return selectedEntity

    def upsertCommentInEntity(self):
        selectedEntity = self.selectEntityTypeModel()

        if self.canUpdateTicket(selectedEntity) == 0:
            print('Can\'t update the comment in this worklog. Already sent to JIRA.')
            return

        strMessage = str(input('Enter/Edit your comment:'))
        selectedEntity.set_comment(strMessage)
        self.updateEntityByModel(selectedEntity)
        return selectedEntity

    def addTimeFromEntity(self):
        selectedEntity = self.selectEntityTypeModel()

        if self.canUpdate(selectedEntity) == 0:
            print('Can\'t update this worklog')
            return

        currentTime = self.getCurrentTimestamp()
        intAdd = int(input('Number of minutes to add:')) * 60
        oldTime = selectedEntity.get_time()
        if selectedEntity.get_start() > 0:
            print('You cannot change the time from a worklog which is running...')
            sys.exit()
        newTime = oldTime + intAdd
        selectedEntity.set_time(newTime)
        self.updateEntityByModel(selectedEntity)
        print('The old time was ' + self.getTimeStringBySeconds(oldTime) + '. The updated time is ' + self.getTimeStringBySeconds(newTime))
        return selectedEntity

    def subtractTimeFromEntity(self):
        selectedEntity = self.selectEntityTypeModel()

        if self.canUpdate(selectedEntity) == 0:
            print('Can\'t update this worklog')
            return

        currentTime = self.getCurrentTimestamp()
        intAdd = int(input('Number of minutes to subtract:')) * 60
        oldTime = selectedEntity.get_time()
        if selectedEntity.get_start() > 0:
            print('You cannot change the time from a worklog which is running...')
            sys.exit()
        newTime = oldTime - intAdd
        if newTime < 0:
            print('Your duration would be below 0 which we cannot do... Try again')
            sys.exit()
        selectedEntity.set_time(newTime)
        self.updateEntityByModel(selectedEntity)
        print('The old time was ' + self.getTimeStringBySeconds(oldTime) + '. The updated time is ' + self.getTimeStringBySeconds(newTime))
        return selectedEntity

    def processEntities(self):
        self.io.validateSettings()
        arrEntities = self.io.getEntityObjects()
        tokenJira = self.io.getSettingTokenJira()
        email = self.io.getSettingEmail()

        count = 0
        for entity in arrEntities:
            if entity.get_send() == 1 or entity.get_jira_id() > 0:
                continue

            if entity.get_time() < 60:
                print('Your worklog should be at least 1 minute')
                continue

            print('Start sending to JIRA: ' + entity.get_ticket())
            startedAt = datetime.fromtimestamp(entity.get_created_at()).strftime("%Y-%m-%d")
            startedAt += 'T'
            startedAt += datetime.fromtimestamp(entity.get_created_at()).strftime("%H:%M:%S")
            startedAt += '.000-0000'
            data = {"timeSpentSeconds": entity.get_time(),
                  "comment": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                      {
                        "type": "paragraph",
                        "content": [
                          {
                            "text": entity.get_comment(),
                            "type": "text"
                          }
                        ]
                      }
                    ]
                  },
                  "started": startedAt
                }

            url = 'https://studioemma.atlassian.net/rest/api/3/issue/' + entity.get_ticket() + '/worklog'

            token = email + ':' + tokenJira
            token_bytes = token.encode('ascii')
            base64_bytes = base64.b64encode(token_bytes)
            base64_token = base64_bytes.decode('ascii')

            headers = CaseInsensitiveDict()
            headers["Accept"] = "application/json"
            headers["Authorization"] = "Basic " + base64_token
            headers["Content-Type"] = "application/json"
            resp = requests.post(url, headers=headers, data=json.dumps(data))

            arrData = json.loads(resp.text)
            # print(arrData)
            ticketId = arrData['id']
            print('Sent to JIRA: ' + entity.get_ticket() + ' (ticketID ' + str(ticketId) + ')')

            entity.set_send(1)
            entity.set_jira_id(ticketId)
            self.updateEntityByModel(entity)
            count += 1

        print(str(count) + " worklogs have been send to JIRA")
        print("Start updating worklogs to TEMPO")

        arrEntities = self.io.getEntityObjects()
        arrAttributes = None

        for entity in arrEntities:
            if entity.get_tempo_id() > 0:
                print("Ticket " + entity.get_entity_id() + ' already send to TEMPO')
                continue

            if entity.get_jira_id() == 0:
                print("Ticket " + entity.get_entity_id() + ' not yet send TO JIRA')
                continue

            if arrAttributes == None:
                print("Getting attributes from Tempo")
                arrAttributes = self.getWorkLogPropertyDetails()

            arrSelectedOptions = []
            # print(arrAttributes)

            print("Tempo data for " + entity.get_ticket() + ' > ' + entity.get_comment())

            for attribute in arrAttributes:
                count = 1
                arrOptions = dict()
                for option in attribute['options']:

                    arrOptions[count] = {'key': attribute['key'], 'value': option['key']}
                    print('[' + str(count) + '] ' + option['label'])
                    count += 1

                # print(arrOptions)
                selectedValue = int(input('Select option:'))
                arrSelectedOptions.append(arrOptions[selectedValue])
                # print(attribute)

            # print(arrSelectedOptions)
            tempoId = self.putAttributeOptionsToWorkLog(entity.get_jira_id(), arrSelectedOptions)
            entity.set_tempo_id(tempoId)
            self.updateEntityByModel(entity)

    def getWorkLogPropertyDetails(self):
        email = self.io.getSettingEmail()
        tokenTempo = self.io.getSettingTokenTempo()
        headers = CaseInsensitiveDict()
        headers["Authorization"] = "Bearer " + tokenTempo
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"

        url = 'https://api.tempo.io/core/3/work-attributes';

        attributeDetails = requests.get(url, headers = headers)

        arrResult = json.loads(attributeDetails.text)
        # print(arrResult)

        details = []

        for result in arrResult['results']:
            if not "required" in result.keys():
                continue

            key = result['key']
            label = result['name']
            type = result['type']
            required = result['required']

            if not required == 1:
                continue;

            if not "names" in result:
                continue;

            arrOptions = []
            names = result['names']
            for optionKey in names:
                arrOption = dict()
                #print(optionKey + ' --> ' + names[optionKey])
                arrOption['key'] = optionKey
                arrOption['label'] = names[optionKey]
                arrOptions.append(arrOption)

            arrAdd = dict()
            arrAdd['key'] = key
            arrAdd['label'] = label
            arrAdd['options'] = arrOptions

            details.append(arrAdd)
        return details

    def putAttributeOptionsToWorkLog(self, jiraWorkLogId, putOptions):
        print('Sending ' + str(jiraWorkLogId) + ' to TEMPO')
        #GET INFO FROM TEMPO ABOUT WORKLOG
        email = self.io.getSettingEmail()
        tokenTempo = self.io.getSettingTokenTempo()
        headers = CaseInsensitiveDict()
        headers["Authorization"] = "Bearer " + tokenTempo
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"

        url = 'https://api.tempo.io/core/3/worklogs/jira/' + str(jiraWorkLogId);

        response = requests.get(url, headers = headers)

        decodedResult = json.loads(response.text)

        tempoWorkLogId = decodedResult['tempoWorklogId']

        if not tempoWorkLogId:
            print("Failed to get tempo ID from worklog")
            sys.exit()
        else:
            print("Tempo Worklog ID : " + str(tempoWorkLogId))

        url = 'https://api.tempo.io/core/3/worklogs/' + str(tempoWorkLogId);
        print('URL to post to tempo: ' + url)

        putTempoData = {
            "issueKey": decodedResult['issue']['key'],
            "timeSpentSeconds": decodedResult['timeSpentSeconds'],
            "billableSeconds": decodedResult['timeSpentSeconds'],
            "startDate": decodedResult['startDate'],
            "startTime": decodedResult['startTime'],
            "description": decodedResult['description'],
            "remainingEstimateSeconds": 0,
            "authorAccountId": decodedResult['author']['accountId'],
            "attributes": putOptions
        }

        # print(json.dumps(putTempoData))

        # print('Updating Tempo Ticket: ' + json.dumps(putTempoData))
        headers = CaseInsensitiveDict()
        headers["Authorization"] = "Bearer " + tokenTempo
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        resp = requests.put(url, headers=headers, data=json.dumps(putTempoData))

        print("Worklog updated in TEMPO")
        return tempoWorkLogId
