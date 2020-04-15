#!/bin/sh

pushd /sutas
sutas user_setup --raisebugs no --jirapwd '' --jira_affect_version '' --jiraenv QA --loglevel info --slack no --slacktoken '' --emailnotifications no --symmetrickey GSS --teamsnotifications no --consolidatedmail no --enabledatabase no --dbpassword '' --dbserverpwd '' --enabletestmanagement no --sprintnumber '' --fixversion '' --tm_project '' --enablepushtestartifacts no --testaritfactsserverpwd '' --jiraproj ''
sutas execute -s tests/test.robot -c tests/smoke_test_config.yaml
popd > /dev/null
# sutas run command
while true; do sleep 1000; done

