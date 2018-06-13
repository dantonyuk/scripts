import argparse
import smtplib
from email.mime.text import MIMEText
from itertools import groupby
from urllib.parse import urljoin, urlencode
import requests
from jinja2 import Template

from settings import *
from jira import *


ERR_CANNOT_RETRIEVE_ISSUES = 'Can not retrieve issues from Jira. Response is %s %s.'


def retrieve_issues(query):
    url = urljoin(JIRA_URL, 'rest/api/latest/search')
    resp = requests.get(url, auth=(JIRA_USERNAME, JIRA_PASSWORD), params={'jql': query})

    if not resp.ok:
        print(ERR_CANNOT_RETRIEVE_ISSUES % (resp.status_code, resp.reason))
        exit(1)

    return list(map(Issue, resp.json()['issues']))


def notify_assignee(assignee, issues):
    if EXCLUDE_RECIPIENTS is not None and assignee.email.lower() in EXCLUDE_RECIPIENTS:
        return
    if INCLUDE_RECIPIENTS is not None and assignee.email.lower() not in INCLUDE_RECIPIENTS:
        return

    text = Template(EMAIL_BODY).render(
        BROWSE_URL=urljoin(JIRA_URL, 'browse'), ISSUES_URL=urljoin(JIRA_URL, 'issues'),
        assignee=assignee, issues=issues,
        JQL=urlencode({'jql': JIRA_QUERY + ' AND assignee=currentUser()'}))

    recipient = '%s <%s>' % (assignee.name, assignee.email)
    recipients = [recipient]

    msg = MIMEText(text, EMAIL_TYPE)
    msg['From'] = EMAIL_FROM
    msg['To'] = recipient
    if EMAIL_CC is not None:
        msg['Cc'] = EMAIL_CC
        recipients = recipients + [EMAIL_CC]
    msg['Subject'] = Template(EMAIL_SUBJECT).render(assignee=assignee, issues=issues)
    smtp = smtplib.SMTP(SMTP_SERVER)
    smtp.sendmail(EMAIL_FROM, recipients, msg.as_string())
    smtp.quit()


def main():
    parser = argparse.ArgumentParser(description='Notify developers about unclosed issues.')
    parser.add_argument('-q', '--query', default='')
    args = parser.parse_args()
    query = (args.query is not None) and args.query or JIRA_QUERY

    issues = retrieve_issues(query)
    for assignee, issues in groupby(issues, Issue.assignee.fget):
        notify_assignee(assignee, list(issues))


if __name__ == "__main__":
    main()
