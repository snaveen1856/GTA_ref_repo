import mock
from mock import Mock, MagicMock    
import os
import yaml
from os.path import expanduser
import pprint
from lib.TestManagement import TestManagement
from lib.ParseAndRaiseBug import ParseAndRaiseBug
from lib.utilities import get_data_from_yaml
from _pytest.monkeypatch import MonkeyPatch
import pytest
from lib import logger



class DictDotLookup(object):
    """
    Creates objects that behave much like a dictionaries, but allow nested
    key access using object '.' (dot) lookups.
    """
    def __init__(self, d):
        for k in d:
            if isinstance(d[k], dict):
                self.__dict__[k] = DictDotLookup(d[k])
            elif isinstance(d[k], (list, tuple)):
                l = []
                for v in d[k]:
                    if isinstance(v, dict):
                        l.append(DictDotLookup(v))
                    else:
                        l.append(v)
                self.__dict__[k] = l
            else:
                self.__dict__[k] = d[k]

    def __getitem__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

    def __iter__(self):
        return iter(list(self.__dict__.keys()))

    def __repr__(self):
        return pprint.pformat(self.__dict__)


def setUp(self):
    globfilepath = os.path.join(os.getcwd(), "global_conf.yaml")
    self.globdata = get_data_from_yaml(globfilepath)



@pytest.fixture
def jconn():
    j_conn = mock.MagicMock()
    return j_conn

@pytest.fixture
def master_ts_obj():
    master_ts_obj = mock.MagicMock()
    return master_ts_obj

@pytest.fixture
def issue_tc():
    issue = mock.MagicMock()
    return issue

def test_clonetestsuite(jconn,master_ts_obj):
    monkeypatch = MonkeyPatch()
    print("\nChecking the code flow of Cloning TestSuite")
    def get_cwd(*args, **kwargs):
        return os.getcwd()
    class clone_tc(object):
        def __call__(self,*args, **kwargs):
            return {"mock_key": "mock_response"}
    monkeypatch.setattr(os.path, "expanduser", get_cwd, raising=True)
    monkeypatch.setattr(TestManagement,"_clone_test_case",clone_tc())
    class v1(object):
        name = 'Version1'
    class v2(object):
        name = 'Version2'
    class fix(object):
        name = 'DaiyExecution'
    os.environ['multiplesuiteids'] = ''
    a_test_cases = ['t1','t2']
    with open('unit_tests_data.yaml','r') as f:
        data = yaml.load(f,Loader=yaml.FullLoader)
    master_ts_data = data['ts_data']
    master_ts_data['versions']=[v1,v2]
    master_ts_fields = {'fields':master_ts_data}
    #To access Dictionary using dot notation DictDotLookup can be used
    data = DictDotLookup(master_ts_data)
    master_ts_obj.fields.return_value = data
    testtype = 'Smoke'
    #To let MagicMock behave like a dictionary
    master_ts_obj.raw.__getitem__.side_effect = master_ts_fields.__getitem__
    master_ts_obj.raw.__iter__.side_effect = master_ts_fields.__iter__
    jconn.project_versions.return_value = [v1,v2]
    jconn.create_version.return_value = fix
    jconn.create_issue.return_value = 'ts_obj'
    jconn._clone_test_case.return_value = 'Test case Created in jira'
    #Intention is to check the code flow of Clone Test Suite
    return_value = TestManagement.clone_test_suite(jconn, master_ts_obj, a_test_cases, testtype)
    assert 'ts_obj' == return_value

def test_update_jira(jconn,issue_tc):
    print("\nChecking the code flow for Updating TestCase Status in Jira")
    tc_ids = ['TM-6433']
    resultslist = ['FAIL']
    new_issue = "<JIRA Issue: key=u'HAR-460', id=u'19223'>"
    fields = {'status':{'name':'Running'}}
    fields = DictDotLookup(fields)
    jconn.issue.return_value = issue_tc
    issue_tc.fields.return_value = fields
    transitions = [{'name':'Passed','id':'1'},
                   {'name':'Failed','id':'2'},
                   {'name':'Skipped','id':'3'},
                   {'name':'Blocked','id':'4'}]
    jconn.transitions.return_value = transitions
    error = 'Raising custom exception for testing'
    TestManagement._update_status_jira(tc_ids, resultslist, jconn, new_issue, error=None)



def test_clonetestcase(jconn):
    def get_cwd(*args, **kwargs):
        return os.getcwd()
    monkeypatch = MonkeyPatch()
    monkeypatch.setattr(os.path, "expanduser", get_cwd, raising=True)
    class cloned_ts_obj(object):
        id = 'TM-7000'
    class v1(object):
        name = 'Version1'
    class v2(object):
        name = 'Version2'
    def update():
        pass
    class fix(object):
        name = 'DaiyExecution'
    class new_issue(object):
        key='TM-7001'
        @classmethod
        def update(cls,fields=None):
            pass
    print(new_issue)
    os.environ['multiplesuiteids'] = ''
    a_test_cases = ['t1','t2']
    master_tc_obj = mock.MagicMock()
    with open('unit_tests_data.yaml','r') as f:
        data = yaml.load(f,Loader=yaml.FullLoader)
    fields = data['project_fields']
    jconn.fields.return_value  = fields
    master_tc_data = data['tc_data']
    master_tc_data['versions']=[v1,v2]
    master_tc_fields = {'fields':master_tc_data}
    #To access Dictionary using dot notation DictDotLookup can be used
    data = DictDotLookup(master_tc_data)
    master_tc_obj.fields.return_value = data
    a_test_cases = [master_tc_obj]
    os.path.expanduser.return_value = os.getcwd()
    testtype = 'Smoke'
    #To let MagicMock behave like a dictionary
    master_tc_obj.raw.__getitem__.side_effect = master_tc_fields.__getitem__
    master_tc_obj.raw.__iter__.side_effect = master_tc_fields.__iter__
    jconn.project_versions.return_value = [v1,v2]
    jconn.create_version.return_value = fix
    jconn.create_issue.return_value = new_issue
    print("\nChecking the code flow of Clone TestCase")
    return_value = TestManagement._clone_test_case(jconn, cloned_ts_obj, a_test_cases, testtype)

def test_filter_tcs(jconn):
    def get_cwd(*args, **kwargs):
        return os.getcwd()
    monkeypatch = MonkeyPatch()
    monkeypatch.setattr(os.path, "expanduser", get_cwd, raising=True)
    os.environ['robosuitepath'] = os.path.join(os.getcwd(),'smoketestsuite.robot')
    test_cases = ['t1','t2']
    test_type = 'Smoke'
    master_tc_obj = mock.MagicMock()
    class v1(object):
        name = 'Version1'
    class v2(object):
        name = 'Version2'
    with open('unit_tests_data.yaml','r') as f:
        data = yaml.load(f,Loader=yaml.FullLoader)
    fields = data['project_fields']
    master_tc_data = data['tc_data']
    master_tc_data['versions']=[v1,v2]
    master_tc_fields = {'fields':master_tc_data}
    jconn.fields.return_value  = fields
    fieldmap = {field['name']: field['id'] for field in jconn.fields()}
    os.environ.__dict__['fieldmap'] = {}
    os.environ.__dict__['fieldmap'].update(fieldmap)
    #To access Dictionary using dot notation DictDotLookup can be used
    data = DictDotLookup(master_tc_data)
    master_tc_obj.fields.return_value = data
    test_cases = [master_tc_obj]
    master_tc_obj.raw.__getitem__.side_effect = master_tc_fields.__getitem__
    master_tc_obj.raw.__iter__.side_effect = master_tc_fields.__iter__



def test_validate_duplicate_issues(jconn):
    def get_cwd(*args, **kwargs):
        return os.getcwd()
    monkeypatch = MonkeyPatch()
    monkeypatch.setattr(os.path, "expanduser", get_cwd, raising=True)
    global_conf_path = os.path.join(os.getcwd(),'global_conf.yaml')
    user_info_conf_path = os.path.join(os.getcwd(),'user_info.yaml')
    glob_data = get_data_from_yaml(global_conf_path)
    user_data = get_data_from_yaml(user_info_conf_path)
    url = glob_data.get("Jira").get("url")
    username = user_data.get("Jira").get("username")
    password = user_data.get("Jira").get("password")
    project = glob_data.get("Jira").get("project")
    affects_version = glob_data.get("Jira").get("affects_version")
    env = user_data.get("env")
    watcher = user_data.get("Jira").get("watcher")
    pid = ''
    outputfile = ''
    with open('unit_tests_data.yaml','r') as f:
        data = yaml.load(f,Loader=yaml.FullLoader)
    pobj = ParseAndRaiseBug(url, username, password, project, affects_version,
                 env, watcher, pid, outputfile, robo_file=None, tc_management = None)
    tc_name = "Test1"
    msg = "SUTAS issue"
    att = outputfile
    summaries = ["SUTAS issue","test2 failed"]
    issue_keys = ["SUTAS-1","SUTAS-2"]
    issobj1 = mock.MagicMock()
    issobj2 = mock.MagicMock()
    issues = [issobj1,issobj2]
    for issue in issues:
        issue.fields.status.name.lower.return_value = 'done'
    fields = data['project_fields']
    jconn.conn.fields.return_value = fields
    jconn.get_summary.return_value  = summaries, issue_keys, issues
    pobj.validate_duplicate_issue(msg, jconn, att, tc_name)
    pass


def test_chkstats(jconn):
    global_conf_path = os.path.join(os.getcwd(),'global_conf.yaml')
    user_info_conf_path = os.path.join(os.getcwd(),'user_info.yaml')
    glob_data = get_data_from_yaml(global_conf_path)
    user_data = get_data_from_yaml(user_info_conf_path)
    url = glob_data.get("Jira").get("url")
    username = user_data.get("Jira").get("username")
    password = user_data.get("Jira").get("password")
    project = glob_data.get("Jira").get("project")
    affects_version = glob_data.get("Jira").get("affects_version")
    env = user_data.get("env")
    watcher = user_data.get("Jira").get("watcher")
    pid = ''
    outputfile = os.getcwd()
    with open('unit_tests_data.yaml','r') as f:
        data = yaml.load(f,Loader=yaml.FullLoader)
    pobj = ParseAndRaiseBug(url, username, password, project, affects_version,
                 env, watcher, pid, outputfile, robo_file=None, tc_management = None)
    pobj.chk_stats(outputfile)
