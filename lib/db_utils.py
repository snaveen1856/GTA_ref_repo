'''Contains database related query operations'''
import datetime
import os
import paramiko
import sqlalchemy
from lib.models import db_session as db
from lib.utilities import (get_data_from_yaml,
                                 check_diskusage)
from lib import logger
from lib.AESCipher import AESCipher
from lib.WINRM import WINRM

class Db_utils(object):
    """
    To manage daabase operations.

    """

    def __init__(self):
        self.db = db()
        filepath = os.path.join(os.path.expanduser('~'), "user_info.yaml")
        globalfilepath = os.path.join(
            os.path.expanduser('~'), "global_conf.yaml")
        userdata = get_data_from_yaml(filepath)
        glob_data = get_data_from_yaml(globalfilepath)
        self.dbserver = glob_data['Database']['serverip']
        self.username = userdata['Database']['serverusername']
        self.password = AESCipher().decrypt(
            userdata['Database']['serverpassword'])
        self.servertype = glob_data['Database']['serverOStype']

    def check_diskspace(self):
        '''Checks the disks space on database server'''
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(self.dbserver, username=self.username,
                        password=self.password)
        except Exception as err:
            if 'Authentication failed' in err:
                msg = 'Check username and password of Webserver'
                logger.error(msg)
                raise Exception(msg)
            else:
                msg = ""
                logger.error(str(err))
        logger.warn('Checking disk space on database server..')
        if check_diskusage(ssh):
            logger.warn("please check the below url to prune the database "
                        "https://sungardas.sharepoint.com/teams/ProdTeam/"
                        "_layouts/15/WopiFrame.aspx?sourcedoc=%7B0F36181D-55F3"
                        "-4757-BFEE-259F967D76CA%7D&file=High%20Level%20"
                        "Design%20Document%20-%20SUTAS.docx&action=default")

    def write(self, table_obj, table_data):
        """
        Responsible to add data to given table in the database.

        - **parameters**, **types**, **return** and **return types**::

            :param table_obj: data base table obj.
            :type kwargs: db object
            :param table_data: data base table data.
            :type kwargs: dictionary
            :return: table row id
        """
        table_obj.__dict__.update(table_data)
        self.db.add(table_obj)
        self.db.commit()
        self.db.close()

        return table_obj.id

    def get_rows_by_name(self, table, name):
        """
        Responsible to fetch data from given table with search criteria name

        - **parameters**, **types**, **return** and **return types**::
            :param table: data base table obj.
            :type table: data base class
            :param name: name.
            :type name: string
            :return: table row ids
            :rtype: Integer
        """
        rows = self.db.query(table).filter_by(name=name).one_or_none()
        return rows

    def get_id_by_name(self, table, name):
        """
        Responsible to get row id by name

        - **parameters**, **types**, **return** and **return types**::
            :param table: data base table obj.
            :type table: data base class
            :param name: name.
            :type name: string
            :return: table row id
            :rtype: Integer
        """
        ids = self.db.query(table).filter_by(name=name).one_or_none()
        if ids:
            id = ids.id
        else:
            id = None
        return id
    def get_project_name_by_id(self, table, project_id):
        """
            Returns project id for the given project
        """
        ids = self.db.query(table).filter_by(project_id=project_id).one_or_none()
        if ids:
            name = ids.name
        else:
            name = None
        return name

    def chk_bug_id(self, table, id):
        """
        check bug id existed or not

        - **parameters**, **types**, **return** and **return types**::
            :param table: data base table obj.
            :type table: data base class
            :param id: id.
            :type id: integer
            :return: table row id or None
            :rtype: Integer
        """
        ids = self.db.query(table).filter_by(jira_bug_id=id).one_or_none()
        if ids:
            id = ids.id
        else:
            id = None
        return id

    def chk_user_id(self, table, user_id):
        """
         check user id existed or not

         - **parameters**, **types**, **return** and **return types**::
             :param table: data base table obj.
             :type table: data base class
             :param user_id: user_id.
             :type user_id: integer
             :return: table row id or None
             :rtype: Integer
         """
        ids = self.db.query(table).filter_by(user_id=user_id).one_or_none()
        if ids:
            id = ids.id
        else:
            id = None
        return id

    def chk_fix_version(self, table, fix_version):
        """
         checks fix_version existed or not

         - **parameters**, **types**, **return** and **return types**::
             :param table: data base table obj.
             :type table: data base class
             :param fix_version: fix_version.
             :type fix_version: string
             :return: table row id or None
             :rtype: Integer
         """
        ids = self.db.query(table).filter_by(
            fix_version=fix_version).one_or_none()
        if ids:
            id = ids.id
        else:
            id = None
        return id

    def update_status(self, table, row_id, status):
        """
         it updates the test case status in corresponding table

         - **parameters**, **types**, **return** and **return types**::
             :param table: data base table obj.
             :type table: data base class
             :param row_id: row_id.
             :type row_id: integer
             :param status: status of the testcase.
             :type status: string
             :return: True
             :rtype: boolean
         """
        self.db.query(table).filter_by(id=row_id).first().status = status
        self.db.commit()
        self.db.close()
        return True

    def update_data_bulk(self, table, db_id, data):
        """
         it updates the test case data in bulk in corresponding table

         - **parameters**, **types**, **return** and **return types**::
             :param table: data base table obj.
             :type table: data base class
             :param db_id: db_id.
             :type db_id: integer
             :param data: to be modified test case date.
             :type data: dictionary
             :return: True
             :
        """
        try:
            self.db.query(table).filter_by(id=db_id).update(data)
        except sqlalchemy.exc.StatementError as err:
            logger.error(data)
            raise Exception(err)
        except Exception as err:
            logger.warn(err)
            try:
                self.db = db()
                self.db.query(table).filter_by(id=db_id).update(data)
            except Exception as err:
                logger.warn('DB connection failed')
                logger.error(err)
                raise Exception(err)
        self.db.commit()
        self.db.close()
        return True

    def delete_data(self, table):
        '''deletes the records from table
                - **parameters**, **types**, **return** and **return types**::

            :param table_obj: data base table obj.
            :type kwargs: db object

        '''
        prev_time = str(datetime.datetime.now() -
                        datetime.timedelta(days=3 * 365))
        self.db.query(table).filter(table.start_time < prev_time).delete()
        self.db.commit()
        self.db.close()
        return True

    def lock(self):
        '''locks the database by creating a file on db server.'''
        if self.servertype.lower() == 'linux':
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                self.ssh.connect(
                    self.dbserver, username=self.username, password=self.password)
                self.sftp = self.ssh.open_sftp()
                self.sftp.chdir('/tmp/')
                try:
                    self.sftp.stat('/tmp/prune.lock')
                    logger.warn(
                        'pruning is already in progress.. hence skipping the pruning for now.')
                    return False
                except IOError:
                    with open('prune.lock', 'w') as psql:
                        psql.write('pruning is starting...')
                    self.sftp.put('prune.lock', '/tmp/prune.lock')
            except paramiko.SSHException:
                logger.error("Connection Error")
            except Exception:
                return False
            return True
        else:
            self.winrmclient = WINRM(self.dbserver, self.username, self.password)
            try:
                self.winrmclient.connect()
            except:
                logger.error('connection failed')
                raise Exceptioneption('connection failed')
            std_out,std_err,status_code = self.winrmclient.run_cmd('type  C:\\prune.lock')
            if status_code == 0:
                logger.warn(
                        'pruning is already in progress.. hence skipping the pruning for now.')
                return False
            else:
                std_out,std_err,status_code = self.winrmclient.run_cmd('echo datapruning >  C:\\prune.lock')
            return True


    def unlock(self):
        '''Unlocks the dbserver by removing the file.'''
        if self.servertype.lower() == 'linux':
            try:
                self.sftp.remove('/tmp/prune.lock')
                os.remove('prune.lock')
            except IOError:
                self.ssh.close()
            return True
        else:
            std_out,std_err,status_code = self.winrmclient.run_cmd('del  C:\\prune.lock')
            if status_code == 0:
                return True

