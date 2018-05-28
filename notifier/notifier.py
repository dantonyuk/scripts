import smtplib
from email.mime.text import MIMEText
from itertools import groupby
from urllib.parse import urljoin, urlencode
import requests
from jinja2 import Template

from settings import *
from jira import *


ERR_CANNOT_RETRIEVE_ISSUES = 'Can not retrieve issues from Jira. Response is %s %s.'


def retrieve_issues():
    url = urljoin(JIRA_URL, 'rest/api/latest/search')
    resp = requests.get(url, auth=(JIRA_USERNAME, JIRA_PASSWORD), params={'jql': JIRA_QUERY})

    if not resp.ok:
        print(ERR_CANNOT_RETRIEVE_ISSUES % (resp.status_code, resp.reason))
        exit(1)

    return list(map(Issue, resp.json()['issues']))


def notify_assignee(assignee, issues):
    text = Template(EMAIL_BODY).render(
        BROWSE_URL=urljoin(JIRA_URL, 'browse'), ISSUES_URL=urljoin(JIRA_URL, 'issues'),
        assignee=assignee, issues=issues,
        JQL=urlencode({'jql': JIRA_QUERY + ' AND assignee=currentUser()'}))
    recipient = '%s <%s>' % (assignee.name, assignee.email)
    msg = MIMEText(text, EMAIL_TYPE)
    msg['From'] = EMAIL_FROM
    msg['To'] = recipient
    msg['Subject'] = Template(EMAIL_SUBJECT).render(assignee=assignee, issues=issues)
    smtp = smtplib.SMTP(SMTP_SERVER)
    smtp.sendmail(EMAIL_FROM, [recipient], msg.as_string())
    smtp.quit()


def main():
    issues = retrieve_issues()
    for assignee, issues in groupby(issues, Issue.assignee.fget):
        notify_assignee(assignee, list(issues))


if __name__ == "__main__":
    main()
