import requests
import smtplib
from email.mime.text import MIMEText
from itertools import groupby
from urllib.parse import urljoin, urlencode
from jinja2 import Template
from settings import *

### Classes

class Issue:
    def __init__(self, info):
        self.info = info

    key = property(lambda self: self.info['key'])
    type = property(lambda self: self.info['fields']['issuetype']['name'])
    status = property(lambda self: self.info['fields']['status']['name'])
    summary = property(lambda self: self.info['fields']['summary'])
    assignee = property(lambda self: Assignee(self.info['fields']['assignee']))


class Assignee:
    def __init__(self, info):
        self.info = info

    key = property(lambda self: self.info['key'])
    name = property(lambda self: self.info['displayName'])
    email = property(lambda self: self.info['emailAddress'])

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key

### Handling

def retrieve_issues():
    url = urljoin(URL, 'rest/api/latest/search')
    resp = requests.get(url, auth=(USERNAME, PASSWORD), params={'jql': QUERY})

    if not resp.ok:
        print('Can not retrieve issues from Jira. Response is %s %s.' % (resp.status_code, resp.reason))
        exit(1)

    return list(map(Issue, resp.json()['issues']))


def notify_assignee(assignee, issues):
    text = Template(TEMPLATE).render(
            BROWSE_URL=urljoin(URL, 'browse'), ISSUES_URL=urljoin(URL, 'issues'),
            assignee=assignee, issues=issues,
            JQL=urlencode({'jql': QUERY + ' AND assignee=currentUser()'}))
    to = '%s <%s>' % (assignee.name, assignee.email)
    msg = MIMEText(text, TEXT_TYPE)
    msg['From'] = FROM
    msg['To'] = to
    msg['Subject'] = Template(SUBJECT).render(assignee=assignee, issues=issues)
    smtp = smtplib.SMTP(SMTP_SERVER)
    smtp.sendmail(FROM, [to], msg.as_string())
    smtp.quit()


def main():
    issues = retrieve_issues()
    for assignee, issues in groupby(issues, Issue.assignee.fget):
        notify_assignee(assignee, list(issues))


if __name__ == "__main__":
    main()
