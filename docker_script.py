#!/usr/bin/python
from jinja2 import Template

#sutas_dict = {'raisebugs':'yes','jiraurl':'url','jirapwd':'xxx','jirausr':'xxx','jiraaffectversion':'version','jiraenv':'env','jirawatcher':'yes','loglevel':'yes','slack':'No'}

sutas_dict= {"jiraurl": "https://github.com/srikanth0327", "Teams": "No", "raisebugs": "yes"}
tm = Template(open('srikanth_docker').read())

file = tm.render(sutas_dict)

print(file)

doc = open('Dockerfile','w')
doc.write(file)
