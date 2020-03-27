import os
from os.path import expanduser
from lib import logger
from lib.utilities import get_data_from_yaml
from lib.AESCipher import AESCipher as aes
from sqlalchemy import (Column, DateTime,
     Integer, BIGINT, String, Float, ForeignKey, func, TIMESTAMP)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from sqlalchemy.types import PickleType

Base = declarative_base()


class test_execution(Base):
    __tablename__ = 'test_execution'
    id = Column(BIGINT, primary_key=True, unique = True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    cpu_time = Column(Float)
    os_type = Column(String(100))
    hostname = Column(String(50))
    host_ip = Column(String(50))
    memory_usage = Column(Float(50))
    io_time = Column(Float(50))

class projects(Base):
    __tablename__ = 'projects'
    id = Column(BIGINT, primary_key=True, unique = True)
    project_id = Column(String(50), unique = True)
    name = Column(String(50))
    project_lead_jira_id = Column(String(50))

class test_suite(Base):
    __tablename__ = 'test_suite'
    id = Column(BIGINT, primary_key=True, unique = True)
    ts_id = Column(String(500))
    master_ts_id = Column(String(500))
    run_id = Column(Integer, ForeignKey('test_execution.id'))
    name = Column(String(500))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String(50))
    project_id = Column(Integer, ForeignKey('projects.id'))
    description = Column(String(2500))
    test_suite_type = Column(String(50))

class users(Base):
    __tablename__ = 'users'
    id = Column(BIGINT, primary_key=True, unique = True)
    user_id = Column(String(50), unique = True)
    name = Column(String(50))
    project_id = Column(Integer, ForeignKey('projects.id'))
    jira_id = Column(String(50))
    email_id = Column(String(100))
    slack_id = Column(String(100))
    teams_url = Column(String(255))


class bugs(Base):
    __tablename__ = 'bugs'
    id = Column(BIGINT, primary_key=True, unique = True)
    jira_bug_id = Column(String(32), unique = True)
    type = Column(Integer, ForeignKey('bug_type.id'))
    status = Column(Integer, ForeignKey('issue_status.id'))
    bugpriority = Column(String(100))
    bugseverity = Column(String(100))
    affects_version = Column(String(100))

class fix_version(Base):
    __tablename__ = 'fix_version'
    id = Column(BIGINT, primary_key=True, unique = True)
    fix_version = Column(String(50))
    release_date = Column(DateTime)
    description = Column(String(1000))

class test_case(Base):
    __tablename__ = 'test_case'
    id = Column(BIGINT, primary_key=True, unique = True)
    tc_id =  Column(String(50))
    name = Column(String(1000))
    description = Column(String(1000))
    ts_id = Column(Integer, ForeignKey('test_suite.id'))
    sutas_id = Column(String(50))
    reporter = Column(String(50))
    assignee = Column(String(50))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    result = Column(String(50))
    status = Column(Integer, ForeignKey('issue_status.id'))
    reason_for_failure = Column(String(500))
    log_path = Column(String(255))
    bug_id = Column(Integer, ForeignKey('bugs.id'))
    fix_version = Column(Integer, ForeignKey('fix_version.id'))
    release_no = Column(String(50))
    build_no = Column(String(50))
    hitcount = Column(Integer)
    test_case_type = Column(String(50))
    environment = Column(String(100))
    sprint_number = Column(String(100))
    
class issue_status(Base):
    __tablename__ = 'issue_status'
    id = Column(BIGINT, primary_key=True, unique = True)
    name = Column(String(100))

class bug_type(Base):
    __tablename__ = 'bug_type'
    id = Column(BIGINT, primary_key=True, unique = True)
    name = Column(String(500))

def db_session():
    filepath = os.path.join(expanduser('~'), "user_info.yaml")
    globalfilepath = os.path.join(expanduser('~'), "global_conf.yaml")
    glob_data = get_data_from_yaml(globalfilepath)
    user_data = get_data_from_yaml(filepath)
    if glob_data and glob_data.get('EnableDatabase'):
        if glob_data.get('Database'):
            db_name = glob_data['Database'].get('database_name')
            serverip = glob_data['Database'].get('serverip')
        if user_data and user_data.get('Database'):
            user_name = user_data['Database'].get('username')
            pwd = user_data['Database'].get('pwd')
            #decrypting the password
            db_pwd = aes().decrypt(pwd)
        DATABASE_URL = 'postgresql+psycopg2://'+user_name+':%s'%(db_pwd)+'@'+serverip+'/'+db_name
        #DATABASE_URL = DATABASE_URL.encode('utf-8').strip()
    else:
        DATABASE_URL = None
    session = None
    if DATABASE_URL:
        #creating engine
        engine = create_engine(DATABASE_URL)
        session = sessionmaker(expire_on_commit=False)
        session.configure(bind = engine)
        #creates tables
        Base.metadata.create_all(engine)
        #session object
        session = session()
    return session
