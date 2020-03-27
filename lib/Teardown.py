"""
All the steps which needs to be performed after test case execution
must be put in this class.
"""
import datetime
import re
import os,sys
import yaml
import traceback
from os import path, getcwd
from robot.libraries.BuiltIn import BuiltIn
from lib.splitlog import get_individual_log
from lib import logger
from lib.ParseAndRaiseBug import ParseAndRaiseBug
from lib.TestManagement import TestManagement
from lib.Jiralib import Jiralib
from lib.models import test_case, bugs, fix_version, issue_status, bug_type
from lib.db_utils import Db_utils
from lib.IntConfig import notify
from lib.TestArtifact import TestArtifact


class Teardown(object):
    """
    Run steps after every test case execution.
    """
    def run(self):  
        """
        This method will add test case status in to global_conf file.
        """
        tc_data = {}
        end_time = datetime.datetime.now()
        result = None
        tc_status_db_id = None
        att = None
        fix_version_db_id = None
        msg = None
        tc_db_id = None
        error_msg = None
        new_issue = None
        try:
            tcname = BuiltIn().get_variable_value("${TEST NAME}")
            tcstatus = BuiltIn().get_variable_value("${TEST STATUS}")
            testresultlist = BuiltIn().get_variable_value("${outlist}")
            suitename = BuiltIn().get_variable_value("${SUITE NAME}")
            suitestatus = BuiltIn().get_variable_value("${SUITE STATUS}")
            prevtestmessage = BuiltIn().get_variable_value("${PREV TEST MESSAGE}")
            context = os.environ.__dict__["context"]
            raise_bugs = context.get('Raise_Bugs')            
            if suitestatus == 'FAIL' and not tcstatus and 'Parent' in prevtestmessage:
                new_issue = None
                error_msg = BuiltIn().get_variable_value("${SUITE MESSAGE}")
                if raise_bugs == 'yes' and error_msg and 'skipping' not in error_msg:
                    obj = Jiralib(context.get('url'), context.get('username'), context.get('pwd'))
                    keyword = error_msg.split('\n')[0]
                    tcname = 'Test Suite' + suitename
                    att = get_individual_log(suitename)
                    conn = obj.conn
                    parse_obj = ParseAndRaiseBug(\
                        context.get('url'), context.get('username'),\
                        context.get('pwd'), context.get('proj'), \
                        context.get('affects_version'), context.get('environment'), \
                        context.get('watcher'), context.get('ts_id'), \
                        context.get('outputdir'), context.get('robo_file'), \
                        context.get('tc_management'))
                    error_msg = ''.join(error_msg.split('\n')[:2])
                    new_issue = parse_obj.parse(suitename, tcname, keyword, error_msg, att, raise_bugs)
                    if context.get('tc_management') is True:
                        conn.create_issue_link('is blocked by', context.get('ts_id'), new_issue)
            elif suitestatus == 'FAIL' and not tcstatus:
                att = get_individual_log(suitename)
            else:
                if not testresultlist:
                    if "TestStatus" in os.environ.__dict__:
                        os.environ.__dict__["TestStatus"][tcname] = tcstatus
                    else:
                        os.environ.__dict__["TestStatus"] = {tcname:tcstatus}
                    sutas_id = ''
                    clone_id = ''
                    if "testids" in os.environ.__dict__:
                        for tckey,clonetc in list(os.environ.__dict__["testids"].items()):
                            if tcname == os.environ.__dict__["testids"][tckey][1].split('CLONE - ')[1]:
                                sutas_id = tckey
                                clone_id = os.environ.__dict__["testids"][tckey][0]
                    msg = BuiltIn().get_variable_value("${TEST MESSAGE}")
                    if tcstatus == 'FAIL':
                        logger.error(msg)
                        if ":" in msg:
                            msg = msg.split(":")[1]
                        if "skipping" in msg.lower():
                            result = "SKIP"
                        else:
                            result = "FAIL"
                        smsg = "*{} --> {}* --> {}* --> {}*".format(tcname, sutas_id, clone_id, result)
                        notify.message("%s\n\terror_msg: %s" %(smsg, msg.strip()))
                    else:
                        result = "PASS"
                        smsg = "*{} --> {}* --> {}* --> PASS*".format(tcname,sutas_id,clone_id)
                        notify.message(smsg)
                    tcstatus = result
                    if not suitestatus:                
                        att = get_individual_log(tcname)
                        logger.warn(att)
                        file_pointer = open(att, "r")
                        data = file_pointer.read()
                        file_pointer.seek(0)
            ##            kws = re.findall(r"(ERROR)+\s+(\w+:)+\s+(\w.*)+\s+", data)
                        error_msg = None 
                        for line in file_pointer:
                            kws = re.findall(r"(ERROR)+\s+(\w+:)+\s+(\w.*)", line)
                            if kws:
                                break
                        strng = ""
                        for line in file_pointer:
                            date = datetime.date.today().strftime('%Y-%m-%d')
                            if date in line:
                                break
                            else:
                                strng +=line
                         
                            k = list(kws[0])
                            kws = [k]
                            kws[0][2] = kws[0][2] + " " + strng
                        keyword = ''
                        if kws:
                            keyword = kws[0][1]
                            error_msg = kws[0][2]
                        else:
                            error_msg = re.findall(r"(ERROR)+\s+(.*)", data)
                            if error_msg:
                                error_msg = error_msg[0][1]
                    else:
                        att = None
                    if raise_bugs.lower() == 'yes' and error_msg and 'skipping' not in error_msg and tcstatus=='FAIL':
                        obj = Jiralib(context.get('url'), context.get('username'), context.get('pwd'))
                        conn = obj.conn
                        parse_obj = ParseAndRaiseBug(\
                                                context.get('url'), context.get('username'),\
                                                context.get('pwd'), context.get('proj'), \
                                                context.get('affects_version'), context.get('environment'), \
                                                context.get('watcher'), context.get('ts_id'), \
                                                context.get('outputdir'), context.get('robo_file'), \
                                                context.get('tc_management'))
                        suite_name = BuiltIn().get_variable_value("${SUITE NAME}")
                        new_issue = parse_obj.parse(suite_name, tcname, keyword, error_msg, att, raise_bugs)                    
                else:
                    for count,testresult in enumerate(testresultlist):
                        tc_id = context.get('tc_id')[count]
                        tcstatus = testresult[0]
                        keyword = None
                        try:
                            error_msg = testresult[1]
                        except IndexError:
                            error_msg = None
                        if raise_bugs.lower() == 'yes' and error_msg and 'skipping' not in error_msg and tcstatus=='FAIL':
                            obj = Jiralib(context.get('url'), context.get('username'), context.get('pwd'))
                            conn = obj.conn
                            parse_obj = ParseAndRaiseBug(\
                                                    context.get('url'), context.get('username'),\
                                                    context.get('pwd'), context.get('proj'), \
                                                    context.get('affects_version'), context.get('environment'), \
                                                    context.get('watcher'), context.get('ts_id'), \
                                                    context.get('outputdir'), context.get('robo_file'), \
                                                    context.get('tc_management'))
                            suite_name = BuiltIn().get_variable_value("${SUITE NAME}")
                            new_issue = parse_obj.parse(suite_name, tcname, keyword, error_msg, att, raise_bugs)
                            if context.get('tc_management') is True:
                                conn.create_issue_link('is blocked by', tc_id, new_issue)                    
                fix_version_db_id = None
                end_time = datetime.datetime.now()
                tc_status = []
                if context.get('database').lower() == 'yes':
                    db_util_obj = Db_utils()
                if context.get('tc_management') and tcname:
                    obj = Jiralib(context.get('url'), context.get('username'), context.get('pwd'))
                    conn = obj.conn
                    if testresultlist:
                        tc_status = [status[0] for count,status in enumerate(testresultlist)]
                    else:
                        tc_status.append(tcstatus)                    
                    TestManagement.get_actual_tc_id(tcname, tc_status, obj.conn, \
                                                    context.get('robo_file'), new_issue, error = error_msg)
                    tc_ids = context.get('tc_id')
                    tc_obj = conn.issue(tc_ids[0])
                    jira_tc_status = tc_obj.fields().status.name
                    if context.get('database').lower() == 'yes':
                        fix_versions = tc_obj.fields().fixVersions
                        if fix_versions:
                            fix_ver = fix_versions[-1]
                            fix_ver_data = {'fix_version': fix_ver.name,}
                            descr = fix_ver.__dict__.get('description')
                            release_date = fix_ver.__dict__.get('releaseDate')
                            if descr:
                                fix_ver_data.update({'description': descr,})
                            if release_date:
                                release_date = datetime.datetime.strptime(release_date, "%Y-%m-%d").date()
                                fix_ver_data.update({'release_date': release_date,})
                            fix_version_db_id = db_util_obj.chk_fix_version(fix_version, fix_ver.name)
                            if not fix_version_db_id:
                                fix_ver_obj = fix_version()
                                fix_version_db_id = db_util_obj.write(fix_ver_obj, fix_ver_data)
                    if context.get('database').lower() == 'yes' and tcname:
                        tc_status_db_id = db_util_obj.get_id_by_name(issue_status, jira_tc_status)
                        if not tc_status_db_id:
                            tc_status_data = {'name': jira_tc_status}
                            tc_table_obj = issue_status()
                            tc_status_db_id = db_util_obj.write(tc_table_obj, tc_status_data)
                    flag = True                    
                    for count,tc_id in enumerate(tc_ids):
                        tc_obj = conn.issue(tc_id)
                        jira_tc_status = tc_obj.fields().status.name
                        if context.get('database').lower() == 'yes':
                            fix_versions = tc_obj.fields().fixVersions
                            if fix_versions:
                                fix_ver = fix_versions[-1]
                                fix_ver_data = {'fix_version': fix_ver.name,}
                                descr = fix_ver.__dict__.get('description')
                                release_date = fix_ver.__dict__.get('releaseDate')
                                if descr:
                                    fix_ver_data.update({'description': descr,})
                                if release_date:
                                    release_date = datetime.datetime.strptime(release_date, "%Y-%m-%d").date()
                                    fix_ver_data.update({'release_date': release_date,})
                                fix_version_db_id = db_util_obj.chk_fix_version(fix_version, fix_ver.name)
                                if not fix_version_db_id:
                                    fix_ver_obj = fix_version()
                                    fix_version_db_id = db_util_obj.write(fix_ver_obj, fix_ver_data)
                        if context.get('database').lower() == 'yes' and tcname:
                            tc_status_db_id = db_util_obj.get_id_by_name(issue_status, jira_tc_status)
                            if not tc_status_db_id:
                                tc_status_data = {'name': jira_tc_status}
                                tc_table_obj = issue_status()
                                tc_status_db_id = db_util_obj.write(tc_table_obj, tc_status_data)
                        if new_issue and context.get('database').lower() == 'yes':
                            fieldmap = {field['name']: field['id'] for field in conn.fields()}
                            hit_count = fieldmap['HitCount']
                            hit_count = new_issue.raw['fields'][hit_count]
                            hit_count = int(hit_count)
                            bug_data = {}
                            bug_db_id = db_util_obj.chk_bug_id(bugs, new_issue.key)
                            status = new_issue.fields().status.name
                            status_db_id = db_util_obj.get_id_by_name(issue_status, status)
                            bugpriority = context.get('bugpriority')
                            bugseverity = context.get('bugseverity')
                            bugpriorities = {'0':None,'1':'Critcical','2':'High','3':'Medium','4':'Low','5':'Trivial'}
                            bugseverities = {'0':None,'1':'Critcical','2':'Major','3':'Moderate','4':'Low','5':'Trivial'}
                            if bugpriority not in bugpriorities:
                                bugpriority = '0'
                            if bugpriority not in bugseverities:
                                bugseverity = '0'
                            if not status_db_id:
                                status_data = {'name': status}
                                table_obj = issue_status()
                                status_db_id = db_util_obj.write(table_obj, status_data)
                            if bug_db_id:
                                if hit_count > 1 and status == 'Reopened':
                                    tc_data.update({'hitcount': hit_count})
                                    bug_typ = 'reopen'
                                elif hit_count > 1:
                                    bug_typ = 'exist'
                                    tc_data.update({'hitcount': hit_count})
                                bug_typ_db_id = db_util_obj.get_id_by_name(bug_type, bug_typ)
                                if not bug_typ_db_id:
                                    bug_typ = {'name': bug_typ}
                                    table_obj = bug_type()
                                    bug_typ_db_id = db_util_obj.write(table_obj, bug_typ)
                                bug_data.update({'type': bug_typ_db_id, 'status': status_db_id,'bugpriority':bugpriorities[bugpriority],
                                                 'bugseverity':bugseverities[bugseverity],'affects_version':context.get('affects_version')})
                                logger.info("BugData:{}".format(bug_data),console=False)
                                db_util_obj.update_data_bulk(bugs, bug_db_id, bug_data)
                                tc_data.update({'bug_id': bug_db_id})
                            else:
                                if hit_count > 1 and status == 'Reopened':
                                    bug_typ = 'reopen'
                                    bug_data.update({'jira_bug_id': new_issue.key})
                                    tc_data.update({'hitcount': hit_count})
                                elif hit_count > 1:
                                    bug_typ = 'exist'
                                    bug_data.update({'jira_bug_id': new_issue.key})
                                    tc_data.update({'hitcount': hit_count})
                                else:
                                    bug_typ = 'new'
                                    bug_data.update({'jira_bug_id': new_issue.key})
                                    tc_data.update({'hitcount': hit_count})
                                bug_typ_db_id = db_util_obj.get_id_by_name(bug_type, bug_typ)
                                if not bug_typ_db_id:
                                    bug_typ = {'name': bug_typ}
                                    table_obj = bug_type()
                                    bug_typ_db_id = db_util_obj.write(table_obj, bug_typ)
                                bug_data.update({'type': bug_typ_db_id, 'status': status_db_id,'bugpriority':bugpriorities[bugpriority],
                                                 'bugseverity':bugseverities[bugseverity],'affects_version':context.get('affects_version')})
                                bug_obj = bugs()
                                logger.info("BugData:{}".format(bug_data),console=False)
                                bug_db_id = db_util_obj.write(bug_obj, bug_data)
                            tc_data.update({'bug_id': bug_db_id,})
                            error_msgs = []
                            if testresultlist:
                                for testresults in testresultlist:
                                    try:
                                        msg = testresults[1]
                                    except IndexError:
                                        #msg = None
                                        pass
                                    finally:
                                        error_msgs.append(msg)
                            else:
                                error_msgs.append(msg)
                            if context.get('database').lower() == 'yes':
                                tc_data.update( {'end_time':end_time,'result':tc_status[count], 'status':tc_status_db_id, \
                                                'log_path': att, 'reason_for_failure': error_msgs[count], \
                                                'fix_version':fix_version_db_id,'environment':context.get('environment')})
                                tc_db_ids = context.get('tc_db_ids')
                                logger.info("TCData:{}".format(tc_data),console=False)
                                db_util_obj.update_data_bulk(test_case, tc_db_ids[count], tc_data)
                                flag = False                   
                    else:
                        if flag:
                            error_msgs = None
                            tc_status = 'PASS'                                
                            if context.get('database').lower() == 'yes':
                                tc_data.update( {'end_time':end_time,'result':result, 'status':tc_status_db_id, \
                                                 'log_path': att, 'reason_for_failure': error_msgs, \
                                                 'fix_version':fix_version_db_id,'environment':context.get('environment')})
                                tc_db_ids = context.get('tc_db_ids')
                                logger.info("TCData:{}".format(tc_data),console=False)
                                db_util_obj.update_data_bulk(test_case, tc_db_ids[0], tc_data)
                else:
                    if context.get('database').lower() == 'yes' and tcname:
                        db_util_obj = Db_utils()
                        tc_data.update( {'end_time':end_time,'result':result, 'status':tc_status_db_id, \
                                                 'log_path': att, 'reason_for_failure': msg, \
                                                 'fix_version':fix_version_db_id,'environment':context.get('environment')})
                        tc_db_ids = context.get('tc_db_ids')
                        logger.info("TCData:{}".format(tc_data),console=False)
                        db_util_obj.update_data_bulk(test_case, tc_db_ids[0], tc_data)

        except Exception as err:
            logger.error(str(err))
            out = "\n" + traceback.format_exc()
            logger.warn(out)
            raise err
        finally:
            art_obj= TestArtifact(att)
            art_obj.check_diskspace()
            att = art_obj.push_artifacts()

