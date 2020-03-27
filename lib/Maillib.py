"""
Email library for sending mail notifications while running test suites through SUTAS
"""
import os
import sys
from os.path import expanduser
import re
import smtplib
import datetime
import time
from tabulate import tabulate
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from smtplib import SMTPRecipientsRefused
from smtplib import SMTPSenderRefused
from lib.MailExceptions import MailConnectionException
from lib.MailExceptions import MailRecipientsException
from lib.MailExceptions import MailSocketAccessDeniedException
from lib.utilities import get_data_from_yaml
from lib import logger
from robot.rebot import rebot_cli


class Maillib(object):
    """
    Sends mail notifications while running test suite
    if user wishes to get notifications
    """
    def __init__(self, recipients):
        """
        Creates connection to smtp mail server

            - **parameters**, **types**, **return** and **return types**::

                param recipients: List of recipients
                param type: list
        """
        self.recipients = recipients
        self.sender = 'sutas@sungardas.com'
        globalfilepath = os.path.join(expanduser('~'), "global_conf.yaml")
        self.glob_data = get_data_from_yaml(globalfilepath)
        if not self.recipients:
            raise MailRecipientsException
        try:
            smtpip = self.glob_data["Email"]["smtpip"]
            smtpport = self.glob_data["Email"]["smtpport"]
            self.mailconn = smtplib.SMTP(smtpip, int(smtpport))
        except Exception as e:
            if 'errno' in dir(e):
                if e.errno == 10060:
                    raise MailConnectionException(
                        'Mail connection is not established check smtp ip or port')
                if e.errno == 10013:
                    raise MailSocketAccessDeniedException('An attempt was made'
                                                          'to access a socket '
                                                          'in a way forbidden '
                                                          'by its access '
                                                          'permissions')
                else:
                    raise
            else:
                raise

    def send_mail(self, subject):
        """
        Sends mail to user provided recipients list in user_info file.

        - **parameters**, **types**, **return** and **return types**::

            param subject: mail subject line
            param type: String
        """
        sutasfolder = os.path.join(os.path.expanduser('~'), "Sutas_Logs")
        consolidated_report = "Consolidated_report" + time.strftime("%Y%b%d_%H%M%S") + ".html"
        consolidated_log = "Consolidated_log" + time.strftime("%Y%b%d_%H%M%S") + ".html"
        os.environ['consolidated_report'] = os.path.join(sutasfolder,consolidated_report)
        os.environ['consolidated_log'] = os.path.join(sutasfolder,consolidated_log)
        env_details = self.glob_data['environment']
        hashh = "######################################"
        rebotargs = ["--report", os.path.join(sutasfolder, consolidated_report),
                     "--log", os.path.join(sutasfolder, consolidated_log)]
        body = ""
        if 'envandteninfo' in os.environ:
            headerdata = 'Test run status executed in environment: ' + \
                os.environ['envandteninfo'].upper(
                ) + ' \n' + + + len('Test run status executed in environment') * '=' + '\n'
        else:
            headerdata = 'Test run status executed in environment: ' + env_details.upper() + \
                ' \n' + + + \
                len('Test run status executed in environment') * '=' + '\n'
        tsdict = {}
        suitelogpaths = os.path.join(sutasfolder, "suitelogpaths")
        # reading lines from suitelogpaths file. This file contains all the
        # tessuitelog file paths which are executed by SUTAS. we will be
        # reading this file only when consolidatedemail is yes in
        # global_conf file.
        with open(suitelogpaths, "r") as paths:
            data = paths.read().strip().splitlines()
        # Looping through each line of data. Each line the testsuitelog path
        suiteresult = ''
        for tslogpath in data:
            if os.path.isfile(tslogpath):
                # getting testsuite log path from testsuitelog file path.
                tspath = os.path.dirname(tslogpath)
                # getting tesuite name from testsuitelog file path.
                tsname = os.path.basename(tslogpath).split(
                    str(datetime.datetime.now().year))[0]
                # getting the mailfile path which is created in IntConfig.py file
                # using testsuite path and testsuite name
                testlog = os.path.join(tspath, tsname)
                # reading all the notification data from mailfile
                with open(testlog, "r") as logdata:
                    tsdata = logdata.read()
                # appending ouput.xml file to rebotargs for consolidated html
                # files
                if os.path.isfile(os.path.join(tspath, 'output.xml')):
                    rebotargs.append(os.path.join(tspath, 'output.xml'))
                else:
                    rebotargs = []
                pattern = re.compile(
                    r'\d{1,3}\sPass,\s\d{1,3}\sSkip,\s\d{1,3}\sFail')
                # Email notification contains summary like how many pass,fail and
                # skipped. getting the summary using re.
                summary = ''
                report_found = True
                if tsdata:
                    try:
                        if not pattern.findall(tsdata):
                            logger.error("HTML report not generated as test execution is incomplete or not yet started")
                            report_found = False
                        summary = "\t" + pattern.findall(tsdata)[0]
                        if not suiteresult:
                            suiteresult = re.findall(r'\d{1,5}',summary)
                        else:
                            suiteresult2 = re.findall(r'\d{1,5}',summary)
                            suiteresult2 = [int(count) for count in suiteresult2]
                            suiteresult = [int(count) for count in suiteresult]
                            suiteresult = [str(sum(vals)) for vals in zip(suiteresult2,suiteresult)]
                        os.environ['suiteresult'] = ','.join(suiteresult)
                        mailsummary = summary
                        mailsummary = '{} Pass, {} Skip, {} Fail'.format(suiteresult[0],suiteresult[1],suiteresult[2])
                    except IndexError:
                        mailsummary = '0 Pass, 0 Skip, 0 Fail(No tests are executed)'
                else:
                    mailsummary = ' failed before executing the suite'
                tab = tabulate([[tsname, summary]])
                headerdata += "\n" + tab.split("\n")[1] + "\n"
                body = body + hashh + '\n' + '\t\t' + tsname + \
                    '\n' + hashh + '\n' + str(tsdata) + '\n'
                os.remove(testlog)
        if self.glob_data['Consolidatedmail'] == 'yes':
            try:
                # using rebot_cli method of robot framework, clubbing multiple
                # output.xml file in to one xml file and produces consolidated
                # log.html and reports.html files.
                if not rebotargs:
                    logger.error("SUTAS is not attaching Consolidated log to the mail.")
                else:
                    rebot_cli(rebotargs)
            except SystemExit:
                pass
            except Exception as e:
                raise
        body = headerdata + "\n" + body

        try:
            if self.recipients:
                msg = MIMEMultipart()
                end_time = datetime.datetime.now()
                start_time = datetime.datetime.strptime(
                    os.environ['start_time'], "%Y-%m-%d %H:%M:%S.%f")
                timedelta = end_time - start_time
                timeinsec = timedelta.total_seconds()
                elapsedhrs = int(timeinsec / 3600)
                elapsedmins = int((timeinsec / 60) - (elapsedhrs * 60))
                elapsedsecs = int(
                    timeinsec - (elapsedhrs * 3600) - (elapsedmins * 60))
                elapsedtime = str(
                    elapsedhrs) + 'Hr, ' + str(elapsedmins) + 'Min, ' + str(elapsedsecs) + 'Secs '
                if 'envandteninfo' in os.environ:
                    if '-l' in sys.argv:
                        subject = sys.argv[sys.argv.index('-l')+1]
                        subject = subject.upper()
                    subject = os.environ['envandteninfo'].upper()
                else:
                    subject = subject.capitalize() + " results against " + env_details.upper() + \
                        ' environment: ' + mailsummary + ' Elapsed Time: ' + elapsedtime
                msg['From'] = self.sender
                msg['To'] = self.recipients
                self.recipients = self.recipients.split(',')
                msg['Subject'] = subject
                tspath = os.path.dirname(data[0])
                # attaching log.html, report.html and perf.txt file to email.
                for out in ['log.html', 'report.html', 'perf.txt']:
                    if out == 'perf.txt':
                        attfile = os.path.join(tspath, out)
                        if not os.path.isfile(attfile):
                            continue
                    elif self.glob_data['Consolidatedmail'] == 'yes':
                        if 'report' in out:
                            attfile = os.environ['consolidated_report']
                        if 'log' in out:
                            attfile = os.environ['consolidated_log']
                    else:
                        attfile = os.path.join(tspath, out)
                    if report_found:
                        try:
                            attachment = open(attfile, "rb")
                            attobj = MIMEBase('application', 'octet-stream')
                            attobj.set_payload((attachment).read())
                            encoders.encode_base64(attobj)
                            attfile = attfile.replace(re.findall('\d{4}\w{3}\d{2}_\d{6}',attfile)[0],'')
                            attobj.add_header(
                                'Content-Disposition',
                                "attachment; filename= %s"
                                % os.path.basename(attfile))
                            msg.attach(attobj)
                        except IOError:
                            disp = '{} file not found'.format(attfile)
                            logger.warn(disp)
                            attachment = None
                if self.glob_data.get('send_mail_only_if_failed','no')== 'yes':
                    testsuiteresult = os.environ['suiteresult']
                    passed, skipped, failed = re.findall(r'\d{1,3}', testsuiteresult)
                    if int(failed)+int(skipped)==0:
                        logger.warn("SUTAS is not sending MailNotifications since no tests are failed")
                        return
                msg.attach(MIMEText(body, 'plain'))
                text = msg.as_string()
                self.mailconn.sendmail(self.sender, self.recipients, text)
            else:
                raise MailRecipientsException
        except SMTPSenderRefused:
            if self.glob_data.get('Consolidatedmail','no') == 'yes':
                if self.glob_data.get('EnableTestArtifacts','no') == 'yes':
                    logslink1 = 'https://' + self.glob_data['TestArtifact'][
                        'serverip'] + r'/sutas-logs/' + os.environ['consolidated_log']
                    logslink2 = 'https://' + self.glob_data['TestArtifact'][
                        'serverip'] + r'/sutas-logs/' + os.environ['consolidated_report']
                    body = body + '\n' + 'Logs location in the apache server is provided below\n' + logslink1
                    body = body + '\n' + logslink2
            msg2 = MIMEMultipart()
            msg2['From'] = self.sender
            msg2['To'] = ','.join(self.recipients)
            msg2['Subject'] = subject
            msg2.attach(MIMEText(body, 'plain'))
            text = msg2.as_string()
            try:
                self.mailconn.sendmail(self.sender, self.recipients, text)
            except SMTPRecipientsRefused as err:
                logger.info(err)
                logger.info("No connectivity to smtp.")
        except MailRecipientsException as err:
            logger.warn(err.message)
        except SMTPRecipientsRefused as err:
            logger.warn(err)
            logger.warn("No connectivity to smtp.")

    def send_mail_when_failed(self, body):
        try:
            if self.recipients:
                msg = MIMEMultipart()
                msg['From'] = self.sender
                msg['To'] = self.recipients
                self.recipients = self.recipients.split(',')
                msg['Subject'] = "SUTAS Execution Terminated"
                msg['X-Priority'] = '2'
                hashh = "######################################"
                line = "="*len(hashh)
                space = " "*len(hashh)
                body = line + '\n' + os.environ['cmd'] + '\n' + line + '\n' + space + '\n' + body
                msg.attach(MIMEText(body, 'plain'))
                text = msg.as_string()
                self.mailconn.sendmail(self.sender, self.recipients, text)
        except MailRecipientsException as err:
            logger.warn(err.message)
        except SMTPRecipientsRefused as err:
            logger.warn(err)
            logger.warn("No connectivity to smtp.")

    def close_connection(self):
        """
            Closes the email connection
        """
        self.mailconn.quit()
