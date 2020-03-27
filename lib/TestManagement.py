# -*- coding: utf-8 -*-
"""
File is responsible for managing the test cases in JIRA.
"""
import  os
from os.path import expanduser
import sys
import  yaml
from lib import logger
from lib.IntConfig import notify
from lib.utilities import get_data_from_yaml
from lib.exceptions import UserException
from robot.parsing.model import TestData


class TestManagement(object):
    """
    Testcase management in JIRA
    """

    @staticmethod
    def _format_slack_str(test_case, summ, ids):
        """
        Internal funtion is used for formating the data in partialy tabular form
        param: test_case: Test case object
        param: summ: list contains all the summaries of not planned or not automated testcases
        param: ids: list contains all the test case ids of not planned or not automated testcases
        """
        if test_case and summ and  ids:
            slack_str = " "
            tc_name_len = max(len(line) for line in summ)
            length = tc_name_len / 3
            tc_id_len = len(test_case.key)
            if tc_id_len >= 12:
                tc_id_len = tc_id_len
            else:
                tc_id_len = 12
            pattren = '{:<'+str(tc_id_len)+'} | {:<'+str(tc_name_len)+'}'
            line = ' ' + (length + tc_name_len + tc_id_len) * '-' + ' '
            slack_str = slack_str + line + '\n'
            header = pattren.format('Test Case ID', 'Test Case Name') + '\n'
            slack_str = slack_str + header
            for tc_id, tc_name in  zip(ids, summ):
                slack_str = slack_str + line + '\n'
                slack_str = slack_str + pattren.format(tc_id, tc_name.strip()) + '\n'
            slack_str = slack_str + line + '\n'
            return slack_str
        else:
            return ""

    @staticmethod
    def get_test_case_tags(conn, ts_id,testtype,rerun=None,type='failed'):
        """
        param: conn: jira connection object
        param: ts_id: test suite id
        """
        globfilepath = os.path.join(os.path.expanduser('~'), "global_conf.yaml")
        globdata = get_data_from_yaml(globfilepath)
        enable_test_mgt = True
        if 'EnableTestManagement' not in globdata or globdata.get('EnableTestManagement','no').lower() == "no":
            enable_test_mgt = False
        # fetching test cases from given master test suite.
        if ',' in ts_id:
            test_cases = []
            ts_id = ts_id.split(',')
            for parent in ts_id:
                cases = conn.search_issues('parent=' + parent,startAt=0, maxResults=100)
                cases_b = conn.search_issues('parent=' + parent,startAt=100, maxResults=100)
                cases.extend(cases_b)
                test_cases.extend(cases)
        else:
            test_cases = []
            test_cases = conn.search_issues('parent=' + ts_id, startAt=0, maxResults=100)
            test_cases_b = conn.search_issues('parent=' + ts_id, startAt=100, maxResults=100)
            test_cases.extend(test_cases_b)
        if not test_cases:
            raise Exception("No Testcases found to clone for the given Suite {}".format(ts_id))
        fieldmap = {field['name']: field['id'] for field in conn.fields()}
        os.environ.__dict__['fieldmap'] = {}
        os.environ.__dict__['fieldmap'].update(fieldmap)
        #sutas_id and Automated are customfields added fro sutas framework, \
        # so we don't get these fields dirctly with issue object.
        sutas_id_field = fieldmap['sutas_id']
        try:
            auto_field = fieldmap['Automated?']
        except KeyError:
            auto_field = fieldmap['Automated']
        not_planned = '\n Below mentioned test cases are  in "not planned"' \
            'state hence not running them.\n'
        not_automated = "\n Below mentioned test cases has Automated field" \
            "as 'No' hence not running them.\n"
        np_summ = []
        na_summ = []
        np_id = []
        na_id = []
        tc_list = []
        tc_data = {}
        to_be_cloned_test_cases = []
        np_slack_str = ''
        na_slack_str = ''
        #checking wheather automated and sutas_id fields are existed or not
        if auto_field and sutas_id_field:
            # if test case marked as not planed or it is not automatable, those kind \
            # of test cases will be ignored
            for test_case in test_cases:
                if test_case.fields().status.name.lower() == 'not planned':
                    np_summ.append(test_case.fields().summary.encode('utf-8'))
                    np_id.append(test_case.key)
                elif test_case.raw['fields'][auto_field] == None:
                    na_summ.append(test_case.fields().summary.encode('utf-8'))
                    na_id.append(test_case.key)
                elif test_case.fields().status.name.lower() != 'not planned' and \
                     test_case.raw['fields'][auto_field][0]['value'].lower() == 'yes':
                    if test_case.raw['fields'][sutas_id_field]:
                        tc_list.append(test_case.raw['fields'][sutas_id_field])
                        to_be_cloned_test_cases.append(test_case)
                #sending not planned and not aumatable testcase list as notification through slack
                np_slack_str = TestManagement._format_slack_str(test_case, np_summ, np_id)
                na_slack_str = TestManagement._format_slack_str(test_case, na_summ, na_id)
            if np_slack_str:
                notify.message(not_planned)
                notify.message(np_slack_str)
            if na_slack_str:
                logger.info(not_automated)
                logger.info(na_slack_str)
                #notify.message(not_automated)
                #notify.message(na_slack_str)
            if tc_list:
                logger.info("Testcases which are automated and updated with sutas_id in jira {}".format(tc_list))
                #It will filter test cases based on the conifiguration provided by user in user_configuration file
                #for test_type and sprint_no
                robosuitepath = os.environ['robosuitepath']
                suite = TestData(parent=None, source=robosuitepath)
                robotctagids = []
                robotcnames = []
                for testcase in suite.testcase_table:
                    robotcnames.append(testcase.name.lower())
                    robotctagids.append(testcase.tags.value)
                robotcdict = dict(list(zip(robotcnames,robotctagids)))
                if '-t' in sys.argv:
                    to_be_cloned_test_cases = []
                    tcnames = os.environ['testnames'].lower().split(',')
                    for tc in tcnames:
                        if tc in robotcnames:
                            for jira_tc in tc_list:
                                if jira_tc in robotcdict[tc]:
                                    tcid = jira_tc
                                    to_be_cloned_test_cases.append(conn.issue(tcid))
                        else:
                            raise Exception("Robot file doesn't contain tc {} Mentioned".format(tc))
                else:
                    to_be_cloned_test_cases = TestManagement.filter_tcs(conn,to_be_cloned_test_cases,testtype)
                if not to_be_cloned_test_cases:
                    raise Exception("Not found any testcase to clone for the given suite with given configuration")
                final_tcs = []
                for test_case in to_be_cloned_test_cases:
                    if not rerun:
                        for robotctagid in robotctagids:
                            if robotctagid:
                                if test_case.raw['fields'][sutas_id_field] in robotctagid:
                                    final_tcs.append(test_case.raw['fields'][sutas_id_field])
                                    continue
                    else:
                        if test_case.fields().status.name.lower() == 'failed' and type=='failed':
                            final_tcs.append(test_case.raw['fields'][sutas_id_field])
                        elif test_case.fields().status.name.lower() == 'skipped' and type=='skipped':
                            final_tcs.append(test_case.raw['fields'][sutas_id_field])
                tc_list = list(set(final_tcs))
                tags = 'OR'.join(tc_list)
                logger.info(tags)
            else:
                raise UserException("Make sure fields 'sutas_id' and " \
                            "'Automated' must be there in every test case")
        if not tags:
            raise UserException("No test cases found in provided test suite : ", ts_id)
        issue_obj = None
        if isinstance(ts_id,list):
            os.environ['multiplesuiteids'] = ','.join(ts_id)
            iss_obj = conn.issue(ts_id[-1])
        else:
            iss_obj = conn.issue(ts_id)
        #checking testmanagent enabled or not in configuration files
        if enable_test_mgt:
            if iss_obj:
                if not rerun:
                    #clning the test suite and its test cases from Master test suite
                    clone_testcases = [conn.issue(tc) for tc in tc_list]
                    issue_obj = TestManagement.clone_test_suite(\
                        conn, iss_obj, clone_testcases, testtype)
                    logger.warn("cloned test suite id : " + issue_obj.key)
                    notify.message("cloned test suite id : " + issue_obj.key)
                else:
                    issue_obj = iss_obj
                    logger.warn("Rerunning test suite of id : " + issue_obj.key)
                    notify.message("Rerunning test suite of id : " + issue_obj.key)
                ts_id = issue_obj.id
                # fetching test cases from cloned test suite.
                test_cases = conn.search_issues('parent=' + ts_id)
                for test_case in test_cases:
                    tc_data[test_case.raw['fields'][sutas_id_field]] = \
                        (test_case.key, test_case.fields().summary)
                    if issue_obj.fields().status.name.upper() in ['TODO','TO DO'] and not rerun:
                        for test_case in test_cases:
                            if test_case.raw['fields'][sutas_id_field]:
                                status = test_case.fields().status.name.lower()
                                if status in ['test in progress','running',\
                                                'passed', 'failed', 'skipped', 'blocked']:
                                    raise Exception("Test case already executed, Before \
                                                    executing a test case make sure\
                                                    status in todo or ready to run state.")
                            else:
                                raise Exception("Make sure 'sutas_id' field updateed \
                                                            with test case ID")
                            transitions = conn.transitions(ts_id)
                            #moving test suite to running state
                            for transition in transitions:
                                if transition['name'].lower() in ['run','suite in progress']:
                                    conn.transition_issue(ts_id, str(transition['id']))

                    elif issue_obj.fields().status.name.lower() in ['running', 'suite in progress']:
                        if not rerun:
                            raise Exception("Test suite won't run because it is in Running state,\
                                            If you want to run test suit then clone the master \
                                            suite and provide cloned test suite id")
                    elif issue_obj.fields().status.name.lower() in ['done','completed']:
                        if not rerun:
                            raise Exception("Test suite won't run because it is in Completed state, \
                            If you want to run test suit then clone the master suite and \
                            provide cloned test suite id")
                    os.environ.__dict__["testids"] =  {}
                    os.environ.__dict__["testids"].update(tc_data)
            else:
                raise Exception("No test suite found with provided test suite id :", ts_id)
        else:
            issue_obj = iss_obj
        return tags, issue_obj

    @staticmethod
    def _update_status_jira(tc_ids, resultslist, j_conn, new_issue, error=None):
        """
        Update the status of test case in JIRA

        - **parameters**, **types**, **return** and **return types**::

            :param tc_id: Test case id to update the status
            :param result(str): status of a test case in this case it is Pass or Fail
            :param j_conn: JIRA connection object.
            :param new_issue: raised bug id in case of test failed to
                              link the bug id to test case
            :type: tc_id: string
            :type: result: string
            :type: j_conn: object
            :type: new_issue: string
        """
        for count,tc_id in enumerate(tc_ids):
            try:
                result = resultslist[count]
                #issue object
                issue = j_conn.issue(tc_id)
                if new_issue:
                    try:
                        j_conn.create_issue_link('blocked by', issue, new_issue)
                    except Exception as err:
                        logger.warn(err)
                        logger.warn("Not able to link the bug {} to testcase {}".format(new_issue,tc_id))
            except Exception as err:
                raise Exception(err)
                #raise Exception('No issues found with this test case id', tc_id)
            status = issue.fields().status
            transitions = j_conn.transitions(tc_id)
            if status.name.lower() in ['test in progress','running']:
                for transition in transitions:
                    if not transition['name'].lower().find(result.lower()):
                        #making transitions to what ever result comes in
                        j_conn.transition_issue(issue.key, str(transition['id']))
            if result.lower() == "skip" and error:
                #adding eeror message to the issue as a comment
                j_conn.add_comment(issue, str(error))
        return

    @staticmethod
    def get_actual_tc_id(tc_name, result, j_conn, robo_file, new_issue=None, error=None):
        """
            Function will pull the test case tags(so called test case ids) by using
            tc_name provided in this function and then find the actual test case id
            esxists in JIRA that are stored in testids environmental variable file.
            after finding the actual test case id to be complete..?
            provided in this function

            - **parameters**, **types**, **return** and **return types**::

                :param tc_name: Test case name
                :param result(str): status of a test case in this case it is Pass or Fail
                :param j_conn: JIRA connection object.
                :param robo_file: robot file full path
                :param new_issue: raised bug id in case of test failed to link the
                bug id to test case.
                :type tc_name: string
                :type result: string
                :type: j_conn: object
                :type: robo_file: string
                :type:  new_issue: string

        """
        jira_tc_ids = os.environ.__dict__["testids"]
        robosuitepath = os.environ['robosuitepath']
        suite = TestData(parent=None, source=robosuitepath)
        robotctagids = []
        robotcnames = []
        for testcase in suite.testcase_table:
            robotcnames.append(testcase.name)
            robotctagids.append(testcase.tags.value)
        robotcdict = dict(list(zip(robotcnames,robotctagids)))
        actual_tc_ids = []
        for tag in jira_tc_ids:
            if tag in robotcdict[tc_name]:
                actual_tc_ids.append(jira_tc_ids[tag][0])
        if actual_tc_ids and result:
            if len(actual_tc_ids) > 1:
                new_issue = None
            TestManagement._update_status_jira(actual_tc_ids, result, j_conn, new_issue, error=error)

    @staticmethod
    def _clone_test_case(j_conn, cloned_ts_obj, a_test_cases, testtype):
        """
        Responsible for clone the test cases which are present in master test suite
        :param j_conn: JIRA connection object.
        :param ts_name: cloned test suite jira object
        returns sucess or exception
        """
        fieldmap = {field['name']: field['id'] for field in j_conn.fields()}
        testtype_field = fieldmap.get('Test Type')
        testbuildtype = fieldmap.get('Test Build Type')
        try:
            auto_field = fieldmap['Automated?']
        except KeyError:
            auto_field = fieldmap['Automated']
        expected_result = fieldmap.get('Expected Result')
        preconditions = fieldmap.get('Preconditions')
        sutas_id = fieldmap.get('sutas_id')
        try:
            actual_result = fieldmap['Actual result']
        except KeyError:
            actual_result = fieldmap['Actual Result']
        globfilepath = os.path.join(os.path.expanduser('~'), "global_conf.yaml")
        globdata = get_data_from_yaml(globfilepath)
        project = globdata.get('TM_Project')
        fixversion = globdata.get('fix_version')
        logger.warn(str(len(a_test_cases)) + ' tests are cloning from master suite id')
        for test_case in a_test_cases:
            data2 = {}
            for field_name in test_case.raw['fields']:
                data2[field_name] = test_case.raw['fields'][field_name]
            final_fix = []            
            if data2['fixVersions']:
                fix_v_list = [f['name'] for f in data2['fixVersions']]
                jra = j_conn.project(project)
                versions = j_conn.project_versions(jra)
                versions = [v.name for v in reversed(versions)]
                if fixversion not in versions:
                    try:
                        fix = j_conn.create_version(name=fixversion, project=project)
                        fixversion = fix.name
                    except:
                        msg = 'Unable to create version {}'.format(fixversion)
                        logger.warn(msg)
                        fixversion = None
                fix_v_list = []
                fix_v_list.append(fixversion)
                for i in fix_v_list:
                    final_fix.append({'name':i})
            tc_f = test_case.fields()
            tc_fields = {\
                'project':{'key':project},
                'summary':'CLONE - ' + tc_f.summary,
                'description':tc_f.description,
                'issuetype':{'name':tc_f.issuetype.name},
                auto_field:[{"value":str(data2[auto_field][0]['value'])}],
                'parent':{'id':cloned_ts_obj.id,}}
            tc_jira_fields = {'priority':'priority','labels':'labels',
                              'fixVersions':'fixVersions',
                              'components':'components',
                              expected_result:'expected_result',
                              preconditions:'preconditions',
                              sutas_id:'sutas_id',
                              testtype_field:'testtype_field',
                              testbuildtype:'testbuildtype'}
            for field,fieldname in list(tc_jira_fields.items()):
                if field:
                    tc_fields[field]= data2[field]
                else:
                    logger.warn("Field {} doesn't exist for the jira TestCase {}".format(fieldname,test_case.key))
                #testbuildtype: data2[testbuildtype]
                #actual_result:data2[actual_result],
            #adding environment field
            tc_fields['environment']=globdata['environment']
            #creating a issue as part of cloning
            new_issue = j_conn.create_issue(fields=tc_fields)
            logger.warn(data2[sutas_id] + '-->' + new_issue.key + ':' + 'CLONE - ' + ' '.join(tc_f.summary.split())) 
            if data2['fixVersions']:
                if final_fix:
                    new_issue.update(fields={"fixVersions":final_fix})
    @staticmethod
    def filter_tcs(conn,test_cases,test_type):
        """
        Responsible for filtering the test cases with provided sprint
        number and test type in master test suite.
        :param a_test_cases: list of test cases other than not planned state
        and 'Automated' field value is yes.
        returns filtered test cases.
        """
        globfilepath = os.path.join(os.path.expanduser('~'), "global_conf.yaml")
        globdata = get_data_from_yaml(globfilepath)
        fieldmap = {field['name']: field['id'] for field in conn.fields()}
        sprint_number = ''
        #test_type = ''
        tbc_tcs = []
        sprint_number = globdata.get('sprint_number', None)
        #test_type = globdata.get('test_type', None)
        robosuitepath = os.environ['robosuitepath']
        suite = TestData(parent=None, source=robosuitepath)
        robotctagids = []
        for testcase in suite.testcase_table:
            robotctagids.append(testcase.tags.value)
        testtype_field = fieldmap.get('Test Type')
        testbuildtype_field = fieldmap.get('Test Build Type')
        sprint_field = fieldmap.get('Sprint')
        for test_case in test_cases:
            if test_type:
                #jira_labels = [val.lower().strip() for val in test_case.fields().labels]
                jira_labels = []
                testtype_fields = test_case.raw['fields'].get(testtype_field,None)
                testbuildtype_fields = test_case.raw['fields'].get(testbuildtype_field,None)
                if testtype_field in test_case.raw['fields']:
                    jira_labels = ([val['value'].strip() for val in testtype_fields] if testtype_fields is not None else [])
                if testbuildtype_field in test_case.raw['fields'] and testbuildtype_fields:
                    jira_labels.append(testbuildtype_fields['value'])
                if jira_labels:
                    if 'and' in test_type:
                        labels = [val.strip() for val in test_type.split('and')]
                        count = 0
                        for jira_label in jira_labels:
                            if jira_label in labels:
                                count += 1
                        if count == len(labels):
                            tbc_tcs.append(test_case)
                    elif (',' in test_type or 'or' in test_type):
                        if ',' in test_type :
                            labels = [val.strip() for val in test_type.split(',')]
                        else:
                            labels = [val.strip() for val in test_type.split('or')]
                        for jira_label in jira_labels:
                            if jira_label in labels:
                                tbc_tcs.append(test_case)
                                break
                    elif  jira_labels and test_type.strip() in jira_labels:
                        tbc_tcs.append(test_case)
                else:
                    logger.warn("Test types are not defined for the testcase {} in jira.Please Mention them.".format(test_case))
    
        if tbc_tcs:
            tbc_tcs = list(set(tbc_tcs))
        else:
            if test_type:
                if 'and' in test_type:
                    test_types = ','.join(test_type.split('and'))
                    raise Exception('Master suite doesnot contain testcases with mentioned labels {} together'.format(test_types))
                if 'or' in test_type:
                    test_types = ','.join(test_type.split('or'))
                    raise Exception('Master suite doesnot contain testcases with any of mentioned labels {}'.format(test_types))
                if ',' in test_type:
                    test_types = ','.join(test_type.split(','))
                    raise Exception('Master suite doesnot contain testcases with any of mentioned labels {}'.format(test_types))
                else:
                    raise Exception('Master suite doesnot contain testcases with the mentioned label {}'.format(test_type))
            else:
                tbc_tcs = test_cases
        filteredtcids = []
        for robotctagid in robotctagids:
            if not robotctagid:
                continue
            robotctagid = [tag for tag in robotctagid]
            count = 0
            for tbc_tc in tbc_tcs:
                if tbc_tc.key in robotctagid:
                    if test_type:
                        if 'and' in test_type:
                            test_types = test_type.split('and')
                            for t_type in test_types:
                                if t_type in robotctagid:
                                    count += 1
                            if count == len(test_types):
                                filteredtcids.append(tbc_tc)
                        if 'or' in test_type or ',' in test_type:
                            if 'or' in test_type:
                                test_types = test_type.split('or')
                            if ',' in test_type:
                                test_types = test_type.split(',')
                            for t_type in test_types:
                                if t_type in robotctagid:
                                    filteredtcids.append(tbc_tc)
                        else:
                            if test_type in robotctagid:
                                filteredtcids.append(tbc_tc)
                    else:
                        return tbc_tcs
        return filteredtcids
    
    @staticmethod
    def clone_test_suite(j_conn, master_ts_obj, a_test_cases, testtype):
        """
        Responsible for clone the test from master test suite
        :param j_conn: JIRA connection object.
        :param master_ts_obj: test suite jira object
        :param a_test_cases: list of test cases to be cloned.
        returns cloned test suite jira object
        """
        fieldmap = {field['name']: field['id'] for field in j_conn.fields()}
        master_suite_ids = os.environ.get('multiplesuiteids',None)
        if master_suite_ids:
            master_suite_ids = master_suite_ids.split(',')
        if a_test_cases:
            ts_f = master_ts_obj.fields()
            globfilepath = os.path.join(os.path.expanduser('~'), "global_conf.yaml")
            globdata = get_data_from_yaml(globfilepath)
            project = globdata['TM_Project']
            fixversion = globdata['fix_version']
            sprint_name = globdata['sprint_number']
            sprint_id = TestManagement.get_sprint_id(j_conn,sprint_name)
            sprint_field = fieldmap.get('Sprint')  
            data = {}
            for field_name in master_ts_obj.raw['fields']:
                data[field_name] = master_ts_obj.raw['fields'][field_name]
            final_fix = []
            if data['fixVersions']:
                fix_v_list = [f['name'] for f in data['fixVersions']]
                jra = j_conn.project(project)
                versions = j_conn.project_versions(jra)
                versions = [v.name for v in reversed(versions)]
                if fixversion not in versions:
                    try:
                        fix = j_conn.create_version(name=fixversion, project=project)
                        fixversion = fix.name
                    except:
                        msg = 'Unable to create version {}'.format(fixversion)
                        logger.warn(msg)
                        fixversion = None
                fix_v_list.pop()
                fix_v_list.append(fixversion)
                for i in fix_v_list:
                    if i==fixversion:
                        final_fix.append({'name':i})            
            ts_fields = {
                'project':{'key':project},
                'summary':'CLONE - ' + ts_f.summary,
                'description':ts_f.description,
                'issuetype':{'name':ts_f.issuetype.name},
                'labels':data['labels'],
                'fixVersions':final_fix}
            if master_suite_ids:
                ts_fields['summary'] = 'CLONE - ' + '_'.join(master_suite_ids)
            cloned_ts_obj = j_conn.create_issue(fields=ts_fields)
            if sprint_id:
                cloned_ts_obj.update(fields={sprint_field:sprint_id})
            else:
                logger.warn("Sprint {} not fount in jira project {} or not associated to any board".format(sprint_name, project))
            if master_suite_ids:
                for master_suite_id in master_suite_ids:
                    master_ts_obj = j_conn.issue(master_suite_id)
                    j_conn.create_issue_link('clones', cloned_ts_obj, master_ts_obj)
                    j_conn.create_issue_link('is cloned by', master_ts_obj, cloned_ts_obj)
            else:
                j_conn.create_issue_link('clones', cloned_ts_obj, master_ts_obj)
                j_conn.create_issue_link('is cloned by', master_ts_obj, cloned_ts_obj)
            TestManagement._clone_test_case(j_conn, cloned_ts_obj, \
                                            a_test_cases, testtype)
            return cloned_ts_obj
        else:
            raise Exception("No test cases found in master suite with \
            provided configuration in global conf file")
    @staticmethod
    def get_sprint_id(j_conn, sprint_name=None):
        with open(os.path.join(expanduser('~'),'testenvdata.yaml'),'r') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        boards_list = data['Boards']
        for board in j_conn.boards():
            if board.name in boards_list:
                sprints = j_conn.sprints(board.id)
                for sprint in sprints:
                    if sprint.name == sprint_name:
                        return sprint.id    
