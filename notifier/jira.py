# Parses JSONs to Jira objects.

class Issue:
    def __init__(self, info):
        self.info = info

    key = property(lambda self: self.info['key'])
    type = property(lambda self: self.info['fields']['issuetype']['name'])
    status = property(lambda self: self.info['fields']['status']['name'])
    summary = property(lambda self: self.info['fields']['summary'])
    assignee = property(lambda self: Assignee(self.info['fields']['assignee']))

    def __str__(self):
        return '%s %s' % (self.key, self.summary)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key


class Assignee:
    def __init__(self, info):
        self.info = info

    key = property(lambda self: self.info['key'])
    name = property(lambda self: self.info['displayName'])
    email = property(lambda self: self.info['emailAddress'])

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key
