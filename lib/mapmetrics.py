'''Maps performance details with part of test field'''
from collections import OrderedDict
from bs4 import BeautifulSoup

def getsuiteinfo(outputxml):
    '''Parses the output.xml file and returnd dictionary with suite,tests,keywords info.

    - **parameters**, **types**, **return** and **return types**::
            :param outputxml: output.xml file location
            :type arg: string
            :return: Returns input values as dictionary
            :rtype: dictionary

    '''
    #Reads the ouput.xml.
    with open(outputxml, 'r') as xml:
        data = xml.read()
    #Creates an object which contains all xml tags
    soup = BeautifulSoup(data)
    #Get values of robot suite tags name value.
    suitename = soup.robot.suite.attrs[-1][-1]
    #Finds test tag in the whole xml file
    testcases = soup.findAll('test')
    testslist = []
    #creates an ordered dictionary.
    testsdict = OrderedDict()
    #Iterates over testcases object.
    for testcase in testcases:
        #Get the testcase tags name value and appends to testslist.
        testslist.append(testcase.attrs[-1][-1])
        #Finds keywords in a testcase. 
        keywords = testcase.findAll('kw')
        keywordlist = []
        for keyword in keywords:
            #Get the keyword tags name value and appends to keywordlist.
            keywordlist.append(keyword.attrs[0][-1])
        #creates a dictonary with testcases and respective keywords in a list.
        testsdict[testcase.attrs[-1][-1]] = keywordlist
    #creates an odered dictionary
    suitedict = OrderedDict()
    #Adds the suitename as key and values are testcases dictionary.
    suitedict[suitename] = testsdict
    return suitedict


def mapmetrics(perffile, outputxml):
    '''Maps the perf.txt contents with part of test.

    - **parameters**, **types**, **return** and **return types**::
            :param outputxml: output.xml file location
            :param perffile: perf.txt file location
            :type perffile: string
            :type outputxml: string
            :return: string of mapped data with testcase
            :rtype: string

    '''
    #Read perf.txt
    with open(perffile, 'r') as perf:
        data = perf.read()
    data = data.strip().split('\n')[3:]
    #dict with suite,tests and keyword info.
    suiteinfo = getsuiteinfo(outputxml)
    flag = True
    count = 0
    mdata = data
    for item in data:
        item = item.split('|')
        #if type is test or suite insert testname & suite in 
        #part of test column
        if item[1].strip() == "Test" or item[1].strip() == "Suite":
            index = data.index('|'.join(item))
            item.insert(1, item[0].rstrip())
            mdata[index] = "|".join(item)
    flag = None
    for item in data:
        item = item.split('|')
        for tests in list(suiteinfo.values()):
            if flag:
                testslist = flag
            else:
                testslist = list(tests.keys())
            for test in testslist:
                #if type is keyword then update part of test column with test.
                if item[1].strip() == "Kw" and count < len(tests[test]) and item[0].strip().split('BuiltIn.')[-1] in tests[test]:
                    count += 1
                    index = data.index('|'.join(item))
                    item.insert(1, test.rjust(30))
                    mdata[index] = "|".join(item)
                    if count >= len(tests[test]):
                        testslist.pop(0)
                        flag = testslist
                        count = 0
                    break
    #if type is setup or teardown then update part of test column with test name.
    def settear(ktype):
        '''maps setup and teardown methods with the testcase name'''
        for tests in list(suiteinfo.values()):
            for test in tests:
                for item in data:
                    item = item.split('|')
                    if item[1].strip() == ktype and item[0].strip().split('.Run')[0] in tests[test]:
                        index = data.index('|'.join(item))
                        item.insert(1, test.rjust(30))
                        mdata[index] = "|".join(item)
                        break

    settear('Teardown')
    settear('Setup')
    msg = 'Name'.rjust(30) + ' | ' \
        + 'Part of Test'.rjust(29) + '| ' \
        + 'Type'.rjust(10) + ' | ' \
        + 'Exec Status'.rjust(10) + '| ' \
        + 'Exec Time(s)'.rjust(12) + ' | ' \
        + 'Benchmark Time'.rjust(15) + ' | ' \
        + 'Comments' + '\n'
    #write data in to the perf.txt file.
    with open(perffile, 'w') as perf:
        perf.write(160 * '=' + '\n')
        perf.write(msg)
        perf.write(160 * '=' + '\n')
        perf.write('\n'.join(data))

    return '\n'.join(data)
