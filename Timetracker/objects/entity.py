#!/usr/bin/env python3

class Entity:
    def __init__(self, entityId = None, ticket = None, comment = None, createdAt = None, time = None, start = None, end = None, send = 0, jira_id = 0, tempo_id = 0):
        self.entity_id = entityId
        self.ticket = ticket
        self.comment = comment
        self.created_at = createdAt
        self.time = time
        self.start = start
        self.end = end
        self.send = send
        self.jira_id = jira_id
        self.tempo_id = tempo_id
    def set_entity_id(self, entity_id):
        self.entity_id = entity_id
    def set_ticket(self, argTicket):
        self.ticket = argTicket
    def set_comment(self, argComment):
        self.comment = argComment
    def set_created_at(self, argCreatedAt):
        self.created_at = argCreatedAt
    def set_time(self, argTime):
        self.time = int(float(argTime))
    def set_start(self, argStart):
        self.start = int(float(argStart))
    def set_end(self, argEnd):
        self.end = int(float(argEnd))
    def set_send(self, argSend):
        self.send = int(float((argSend)))
    def set_jira_id(self, argJiraId):
        self.jira_id = int(float((argJiraId)))
    def set_tempo_id(self, argTempoId):
        self.tempo_id = int(float((argTempoId)))
    def get_entity_id(self):
        return self.entity_id
    def get_ticket(self):
        return self.ticket
    def get_comment(self):
        return self.comment
    def get_created_at(self):
        return int(float(self.created_at))
    def get_time(self):
        return int(float(self.time))
    def get_start(self):
        return int(float(self.start))
    def get_end(self):
        return int(float(self.end))
    def get_send(self):
        return int(float((self.send)))
    def get_jira_id(self):
        return int(float((self.jira_id)))
    def get_tempo_id(self):
        return int(float((self.tempo_id)))
