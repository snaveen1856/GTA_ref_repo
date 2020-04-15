#!/usr/bin/python

#print('hello-world')
import os
import sys

cmd1 = r"sutas user_setup --raisebugs no --jirapwd '' --jira_affect_version '' --jiraenv QA --loglevel info --slack no --slacktoken '' --emailnotifications no --symmetrickey GSS --teamsnotifications no --consolidatedmail no --enabledatabase no --dbpassword '' --dbserverpwd '' --enabletestmanagement no --sprintnumber '' --fixversion '' --tm_project '' --enablepushtestartifacts no --testaritfactsserverpwd '' --jiraproj ''"


os.system(cmd1)
cmd2 = r"sutas execute -s tests/test.robot -c tests/smoke_test_config.yaml"
os.system(cmd2)
