"""
All the steps which needs to be performed before test case execution
must be put in this class.
"""
import sys
import os
from os.path import expanduser
from datetime import datetime
import yaml
import traceback
from lib import logger
from lib.CheckRequirements import CheckRequirements
from robot.libraries.BuiltIn import BuiltIn
from lib.utilities import make_transitions
from lib.Jiralib import Jiralib
from lib.models import test_case
from lib.db_utils import Db_utils
from robot.parsing.model import TestData

class Setup(object):
    """
    Run pre-requisites steps before every test case execution.
    """
    def run(self, depends=None, **kwargs):
        """
        Setup before testcase steps execution.

        Will include message '<tcname> execution stated by sutas' in
        testsuite log so that test suite can be parsed for individual
        testcase log.
        Validates the Hardware and Software requirements.

        - **parameters**, **types**, **return** and **return types**::

        :param kwargs: Key value pair. device name as key and
                       software as value.
        :type kwargs: dictionary
        """
        try:
            logger.warn("\n")
            tcname = BuiltIn().get_variable_value("${TEST NAME}")
            suitename = BuiltIn().get_variable_value("${SUITE NAME}")
            if tcname:
                logger.warn(tcname + " execution started by sutas", console=False)
            else:
                logger.warn(suitename + " execution started by sutas", console=False)
            context = os.environ.__dict__["context"]
            tc_ids = []
            tc_db_ids = []
            tc_id = None
            sutas_id = None
            reporter = None
            assignee = None
            description = None
            testtype_field = None
            testtypelist = []
            robosuitepath = os.environ['robosuitepath']
            suite = TestData(parent=None, source=robosuitepath)
            robotctagids = []
            robotcnames = []
            for testcase in suite.testcase_table:
                robotcnames.append(testcase.name)
                robotctagids.append(testcase.tags.value)
            robotcdict = dict(list(zip(robotcnames,robotctagids)))
            if '-l' in sys.argv:
                testtypelist.append(os.environ['testtype'])
            if ("-j" in sys.argv or '-i' in sys.argv) and context['EnableTestManagement'].lower() == "yes":
                obj = Jiralib(context.get('url'), context.get('username'), context.get('pwd'))
                conn = obj.conn
                fieldmap = {field['name']: field['id'] for field in conn.fields()}
                sutas_id = fieldmap['sutas_id']
                jira_tc_ids = os.environ.__dict__["testids"]
                for i in list(jira_tc_ids.values()):
                    tc_sutas_id = conn.issue(i[0]).raw['fields'][ fieldmap['sutas_id']]
                    for robotcname,tctaglist in list(robotcdict.items()):
                        if tcname:
                            if robotcname.strip() == tcname.strip():
                                tctags = [tag.split('_') for tag in tctaglist]
                                tctaglist = []
                                for tctag in tctags:
                                    tctaglist.extend(tctag)
                                if tc_sutas_id.strip() in tctaglist:
                                    tc_ids.append(i[0])
                if tc_ids:
                    tc_db_ids = []
                    for tc_id in tc_ids:
                        tc_obj = conn.issue(tc_id)
                        tcname = tc_obj.raw['fields']['summary'].split('CLONE - ')[-1]
                        make_transitions(conn, tc_obj)
                        fieldmap = {field['name']: field['id'] for field in conn.fields()}
                        sid = fieldmap['sutas_id']
                        sutas_id = tc_obj.raw['fields'][sid]
                        fields = tc_obj.fields()
                        fix_vers = ','.join([i.name for i in fields.fixVersions])
                        tc_id = tc_obj.key
                        reporter = context.get('username')
                        if fields.assignee:
                            assignee = fields.assignee.name
                        else:
                            assignee = None
                        description = fields.description
                        testtype_field = fieldmap.get('Test Type','')
                        testbuild_field = fieldmap.get('Test Build Type','')
                        testtypes = tc_obj.raw['fields'].get(testtype_field,[])
                        testbuildtypes = tc_obj.raw['fields'].get(testbuild_field,'')
                        if (not testtypes) and (not testbuildtypes):
                            msg = 'testtype field or testbuild type is not defined and None, please add test type in jira for testcase {}'.format(sid)
                            raise Exception(msg)
##                        for testtype in testtypes:
##                            testtypelist.append(testtype['value'])
                        if tcname:
                            if context.get('database').lower() == 'yes':
                                db_util_obj = Db_utils()
                                start_time = datetime.now()
                                tc_data = {'name':tcname, 'ts_id': context.get('ts_db_id'), 'start_time':start_time,}
                                
                                tc_data.update({\
                                    'reporter':reporter, 'assignee':assignee, \
                                    'description':description,\
                                    'tc_id':tc_id, 'sutas_id':sutas_id, 'test_case_type':','.join(testtypelist),'environment':context.get('environment'),
                                    'fix_version':context.get('fix_version_db_id')})
                                if context.get('sprint_number'):
                                    tc_data.update({'sprint_number':context.get('sprint_number')})
                
                                testcase_obj = test_case()
                                tc_db_ids.append(db_util_obj.write(testcase_obj, tc_data))
                                os.environ.__dict__["context"].update({'tc_db_ids':tc_db_ids, 'tc_id':tc_ids, 'start_time':start_time,})
                            os.environ.__dict__["context"].update({'tc_id':tc_ids})
            else:
                if tcname:
                    if context.get('database').lower() == 'yes':
                        db_util_obj = Db_utils()
                        start_time = datetime.now()
                        tc_data = {'name':tcname, 'ts_id': context.get('ts_db_id'), 'start_time':start_time,}
                        tc_data.update({\
                                'reporter':reporter, 'assignee':assignee, \
                                'description':description,\
                                'tc_id':tc_id, 'sutas_id':sutas_id, 'test_case_type':','.join(testtypelist),'environment':context.get('environment'),
                                'fix_version':context.get('fix_version_db_id')})
                        if context.get('sprint_number'):
                            tc_data.update({'sprint_number':context.get('sprint_number')})

                        testcase_obj = test_case()
                        tc_db_ids.append(db_util_obj.write(testcase_obj, tc_data))
                        os.environ.__dict__["context"].update({'tc_db_ids':tc_db_ids, 'tc_id':tc_id, 'start_time':start_time,})
                    os.environ.__dict__["context"].update({'tc_id':tc_ids})
                    import pprint
                    pprint.pprint(os.environ.__dict__["context"])
            dependency = True
            if depends:
                depends = depends.split(',')
                for test in depends:
                    try:
                        if (os.environ.__dict__["TestStatus"][test]).lower() == "fail":
                            dependency = False
                    except KeyError:
                        logger.warn("Testcases are not properly ordered as per dependency.")
                        logger.warn("Sutas will continue execution.")
                if not dependency:
                    msg = "Dependency tests failed hence skipping testcase"
                    logger.error(msg)
                    raise Exception(msg)
            if kwargs and os.environ.get("Configfile"):
                CheckRequirements().get_rqmt(kwargs)
            else:
                logger.warn("\n\nNo requirements is provided for validating Software/Hardware.")
        except Exception as err:
            out = "\n" + traceback.format_exc()
            logger.debug(out)
            raise Exception(err)
