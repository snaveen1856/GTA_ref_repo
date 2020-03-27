"""
Module for communicating with jira and do operations on it.
"""
from lib.AESCipher import AESCipher as aes
from jira.client import JIRA
from lib import logger
import os
from lib.utilities import get_data_from_yaml


class Jiralib(object):
    """
    Jira Library to interact with jira
    """

    def __init__(self, server, username, pwd):
        """
        Constructor

        - **parameters**, **types**, **return** and **return types**::

            param server: ipaddress of Jira server
            type: string
            param username: Username to login into jira
            type: string
            param pwd: Password to login into jira
            type: string
        """
        try:
            pwd = aes().decrypt(pwd)
        except ValueError:
            logger.warn("Invalid Password is provided".format(pwd))
            raise Exception(pwd)
        self.conn = self.connect_jira(server, username, pwd)

    def find_project_by_name(self, project_name):
        """
        Retuns project_id if  project exists

        - **parameters**, **types**, **return** and **return types**::

            param project_name: Project Name
            type: string
        """
        project = None
        for i in self.conn.projects():
            if i.name == project_name:
                project = i
                break
        if project:
            return project.id
        else:
            logger.warn("no project with name %s" % project_name)
            raise Exception("No Project with Name {} found in jira".format(project_name))

    def find_project_key(self, project_name):
        """

        Returns Project's Key if project exists

        - **parameters**, **types**, **return** and **return types**::

            :param project_name: Project Name
            :return: project's key
        """
        project = None
        for i in self.conn.projects():
            if i.name == project_name:
                project = i
                break
        if project:
            return project.key
        else:
            logger.warn("no project with name %s" % project_name)
            raise Exception("No Project with Name {} found in jira".format(project_name))

    @staticmethod
    def find_project_by_key(conn, project_key):
        """
        Returns Project's Name if project exists

        - **parameters**, **types**, **return** and **return types**::

            :param project_name: Project Key
            :return: project's Name
        """
        project = None
        for i in conn.projects():
            if i.key == project_key:
                project = i
                break
        if project:
            return project.name
        else:
            logger.warn("no project with name %s" % project_key)
            raise Exception("No Project with Key {} found in jira".format(project_key))

    def connect_jira(self, server, username, pwd):
        """
        Creates connection to jira.
        Raises Exception if connection fails.

        - **parameters**, **types**, **return** and **return types**::
            :param server: Jira server 
            :param username: username to login to Jira
            :param pwd: password to login
            :type server: string
            :type username: string
            :type pwd: string
        """
        options = {'server': server}
        try:
            jira = JIRA(options, basic_auth=(username, pwd))
            return jira
        except Exception as err:
            logger.error(err)
            raise Exception(err)

    def raise_issue(self, project_name, affects_version, environment,
                    summary, description, watcher=None, component=None, label=['SUTAS-AUTOMATION'],
                    priority=None, comment=None,
                    issuetype=None, attachments=None):
        """
        Raises issue in jira with all fields provides.

            - **parameters**, **types**, **return** and **return types**::
                :param project_name: Name of the project in which jira issue will be created
                :param affects_version: Build Version in which test suite was run.
                :param environment: Environment in which test suite run like test/dev
                :param summary: Summary of the issue created
                :param description: Description of the issue created.
                :param watcher: Watchers for the issue created
                :param component:
                :param label: Labels could be regression,sanity,smoke,feature,etc.
                :param priority:priority of the issue created
                :param comment: Comments if any for the issue
                :param issuetype: Type of the issue created.
                :param attachments: Log file to be attached for the issue created
        """
        severitydict = {'1': 'S1: Critcical', '2': 'S2: Major',
                        '3': 'S3: Moderate', '4': 'S4: Low', '5': 'S5: Trivial'}
        globfilepath = os.path.join(
            os.path.expanduser('~'), "global_conf.yaml")
        globdata = get_data_from_yaml(globfilepath)
        severity = globdata['Jira']['bugseverity']
        priority = globdata['Jira']['bugpriority']
        try:
            if ((severity == " ") and (priority == " ")):
                raise ValueError
            else:
                issuetype = {'name': 'Bug'}
                fieldmap = {field['name']: field['id'] for field in self.conn.fields()}
                severity_field = fieldmap['Severity']
                hitcount = fieldmap['HitCount']
                affected_version = [{'name': affects_version}]
                comp = [{'name': component}]
                fields = {'project': self.find_project_by_name(project_name),
                          'summary': summary,
                          'description': description,
                          'priority': {'id': priority},
                          severity_field: {'value': severitydict[severity]},
                          'versions': affected_version,
                          'environment': environment,
                          'labels': label,
                          'components': comp,
                          'issuetype': issuetype}
                new_issue = self.conn.create_issue(fields=fields, prefetch=True)
                new_issue.update(fields={fieldmap['HitCount']:1})
                if 'Ticket Source' in fieldmap:
                    new_issue.update(fields = {fieldmap['Ticket Source'] : {'value':'Quality Engineering'}})
                logger.warn('\n\nNew issue "%s" created successfully.\n' % new_issue)
                proj_key = self.find_project_key(project_name)

                '''if (len(new_issue == 0)):
                    logger.warn("'\n\nError in creating new issue.\n")
                else:
                    logger.warn('\n\nNew issue "%s" created successfully.\n' % new_issue)
                    proj_key = self.find_project_key(project_name)'''
                if watcher:
                    users = watcher.split(",")
                    try:
                        for user in users:
                            try:
                                self.conn.add_watcher(new_issue, user)
                            except Exception as err:
                                msg = '{} cannot be added as watcher'.format(user)
                                logger.warn(msg)
                        lead_watch = self.conn.project(proj_key).raw[
                            "lead"]["displayName"]
                        try:
                            self.conn.add_watcher(new_issue, lead_watch)
                        except Exception as err:
                            msg = '{} cannot be added as lead watcher'.format(
                                lead_watch)
                            logger.warn(msg)
                    except KeyError:
                        logger.warn("\nUser not available or No Team lead"
                                    "assigned to project.. Hence could not "
                                    "add watcher\n")
                else:
                    try:
                        watcher = self.conn.project(proj_key).raw[
                            "lead"]["displayName"]
                        if watcher:
                            try:
                                self.conn.add_watcher(new_issue, watcher)
                            except Exception as err:
                                msg = '{} cannot be added as watcher'.format(watcher)
                                logger.warn(msg)
                    except KeyError:
                        logger.warn("\nNo Team Lead assigned to project."
                                    " So, unable to add watcher\n")
                if attachments:
                    try:
                        self.conn.add_attachment(new_issue, attachments)

                    except Exception as err:
                        msg = 'Not able to add attachments {} to the bug raised'.format(attachments,new_issue)
                        logger.warn(msg)
                    except IOError:
                        disp = '{} file not found'.format(attachments)
                        logger.warn(disp)
                if comment:
                    try:
                        self.conn.add_comment(new_issue, comment)
                    except Exception as err:
                        msg = 'Not able to add Comments {} to the bug {} raised'.format(comment,new_issue)
                        logger.warn(msg)
                return new_issue
        except ValueError:
            print("Incorrect argument : Null value not allowed")


    def get_summary(self, project_name):
        """
        Return summaries from all issues in a project

            - **parameters**, **types**, **return** and **return types**::

                :param project_name: project name in jira from which all the issues summaries
        """
        for i in self.conn.projects():
            if i.name == project_name:
                project_name = i.key
                break
        issues = self.conn.search_issues(
            'project= %s ' % str(project_name), maxResults=999999999)
        summaries = []
        issues_keys = []
        for i in issues:
            summaries.append(self.conn.issue(
                i).fields.summary.split("failed with error ")[-1])
            issues_keys.append(self.conn.issue(i).key)
        return summaries, issues_keys, issues

    def get_fields_from_subtasks(self, project, tc_name, ts_id):
        """
        Get configuration, Label and environment fields from test-case sub-task

            - **parameters**, **types**, **return** and **return types**::

                :param project: Jira project
                :param tc_name: test case name
                :return: values of configuration, Label and Environment fields
        """

        # Get all sub-tasks from parent(test suite) issue
        issues = self.conn.search_issues('parent= %s' % str(ts_id),
                                         maxResults=999999999)
        if (len(issues) > 0):
            # Get the sub-task that matches the test case name
            issues_with_tc_name = []
            for issue in issues:
                if tc_name in issue.fields.summary:
                    issues_with_tc_name.append(issue)

            # Get the field values
            for issue in issues_with_tc_name:
                allfields = self.conn.fields()
                namemap = {field['name']: field['id'] for field in allfields}
                if 'Component/s' in namemap:
                    components = issue.raw['fields'][namemap['Component/s']]
                    try:
                        if components == "":
                            raise ValueError
                        else:
                            for comp in components:
                                component = comp.get('name')
                            label = issue.raw['fields'][namemap['Labels']]
                            return component, label

                    except ValueError:
                        print("Incorrect argument : Null value not allowed")
                else:
                    raise Exception("Component/s not found in jira project given {}".format(project))
        else:
            raise Exception("No Subtask found from parent issue")





