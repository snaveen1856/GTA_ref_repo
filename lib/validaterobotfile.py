"""
Parses the robot file and get testcase order.
Also gets dependency information of each testcase and checks if
testcases are in proper order with respect to dependency.
"""
import sys
from lib import logger
from lib.IntConfig import notify

class DependencyException(Exception):
    """
    This is a exception class which will be raised when there
    is issue with dependencies.
    """
class IncorrectRobotfile(Exception):
    """
    Raised when incorrect robotfile is provided.
    """

class ValidateRobotFile(object):
    """
    Class to validate robot file.

    - **parameters**, **types**, **return** and **return types**::

        :param robofile: Full path of robot file
        :type robofile: string
    """
    def __init__(self, robofile):
        """
        ValidateRobotFile constructor.

        - **parameters**, **types**, **return** and **return types**::

        :param robofile: Full path of robot file
        :type robofile: string

        """
        self.robofile = robofile
        self.dependency = []
        self.tcorder = []
        isrobotfile = False
        try:
            with open(self.robofile, "r") as robo:
                # reading data from robot file
                data = robo.readlines()
                self.data = data
                # checking if provided correct robot file and removing all
                # the lines till "*** Test Cases ***" from self.data. After
                # below script is executed self.data will have only testcases 
                # information in it.
                if data:
                    while True:
                        if self.data:
                            if "*** Test Cases ***" in data[0]:
                                self.data.pop(self.data.index(data[0]))
                                isrobotfile = True
                                break
                            else:
                                self.data.pop(self.data.index(data[0]))
                        else:
                            break
            if not isrobotfile:
                msg = ("Incorrect robofile is provided."
                       "Provided robotfile doesn't contain any testcases.")
                logger.error(msg)
                notify.message(msg)             
                raise IncorrectRobotfile(msg)
        except IOError as err:
            msg = "Error while opening robot file. Error is %s" %err.message
            logger.error(msg)
            notify.message(msg)
            raise IOError(err)
        except IncorrectRobotfile as err:
            msg = ("Incorrect robofile is provided."
                   "Provided robotfile doesn't contain any testcases.")
            logger.error(msg)
            notify.message(msg)           
            raise IncorrectRobotfile(msg)

    def _get_tcorder(self):
        """
        This will parse robofile and stores tcnames in order.   
        """
        for num, line in enumerate(self.data, 0):
            if not line.startswith("    "):
                if line != "\n":
                    self.tcorder.append(line.strip("\n"))

    def _check_dependency(self, tcname, depends):
        """
        This Method will check if the testcases are in proper
        order with respect to dependencies.

        If they are not in proper order then this method will
        raise exception.
        """
        tcindex = self.tcorder.index(tcname)
        dependsindex = []
        for i in depends:
            dependsindex.append(self.tcorder.index(i))
        for i in dependsindex:
            if tcindex < i:
                msg = "%s must be ordered after %s\n" %(tcname, self.tcorder[i])
                self.dependency.append(msg)

    def validate_testdata(self):
        """
        This method will parse robofile and gets depends value from each
        testcase and check if they are in order or not.
        """
        self._get_tcorder()
        for line in self.data:
            if not line.startswith("    "):
                tcname = line.strip("\n")
                continue
            if "[Setup]" in line:
                if "depends" in line:
                    line = line.strip("\n").split("depends")[1][1:]
                    depends = line.split()[0].split(',')
                    self._check_dependency(tcname, depends)

        if self.dependency:
            msg = "Test cases are not in proper dependency order.\n"
            for i in self.dependency:
                msg = msg + i
            logger.warn(msg, console=False)
            notify.message(msg)
            raise DependencyException(msg)
        else:
            msg = "Testcases are in correct dependency order."
            logger.warn(msg)
            notify.message(msg)          


