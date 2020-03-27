'''Compares benchmark values with exec values and calculates performance.'''
import os
import yaml
from robot.result import ExecutionResult
from robot import utils
from lib import logger
from lib.mapmetrics import mapmetrics


def process_file(inpath, outpath, items='suite-test-keyword'):
    '''Creates the metrics file.

    - **parameters**, **types**, **return** and **return types**::
            :param inpath: output.xml file location
            :param outpath: perf.txt file location
            :type inpath: string
            :type outpath: string

    '''
    #parses the output.xml and creates stats.
    suite = ExecutionResult(inpath).suite
    #create metrics file in outpath location.
    metricsfile = open(outpath, 'wb')
    #writes the data into the file.
    metricsfile.write('NAME'.rjust(40) + ' | ' + 'TYPE'.rjust(10) + ' | ' + 'STATUS'.rjust(
        10) + ' | ' + 'ELAPSED'.rjust(25) + ' | ' + 'ELAPSED SECS'.rjust(10) + '\n')
    #processes the suite and writes the stats to metricsfile.
    process_suite(suite, metricsfile, items.lower())
    #closes the metricsfile object.
    metricsfile.close()


def process_suite(suite, fileobj, items, level=0):
    '''Process the suite tags.

    - **parameters**, **types**, **return** and **return types**::
            :param suite: testsuite
            :param fileobj: file object
            :param items: items to be parsed
            :type suite: string
            :type fileobj: object
            :type items: string

    '''
    #validates the items and process it.
    if 'suite' in items:
        #processes suite
        process_item(suite, fileobj, level, 'Suite')
    if 'keyword' in items:
        #process the keywords.
        for keyword in suite.keywords:
            process_keyword(keyword, fileobj, level + 1)
    for subsuite in suite.suites:
        #process the subsuite.
        process_suite(subsuite, fileobj, items, level + 1)
    for test in suite.tests:
        #process the tests in a test suite.
        process_test(test, fileobj, items, level + 1)


def process_test(test, fileobj, items, level):
    '''Process the testcase tags.

    - **parameters**, **types**, **return** and **return types**::
            :param test: testcase
            :param fileobj: file object
            :param items: items to be parsed
            :type suite: string
            :type fileobj: object
            :type items: string

    '''
    #process a testcase.
    if 'test' in items:
        process_item(test, fileobj, level, 'Test', 'suite' not in items)
    if 'keyword' in items:
        #process a keyword.
        for keyword in test.keywords:
            process_keyword(keyword, fileobj, level + 1)


def process_keyword(keyword, fileobj, level):
    '''Process the keyword.

    - **parameters**, **types**, **return** and **return types**::
            :param keyword: keyword
            :param fileobj: file object
            :param items: items to be parsed
            :type suite: string
            :type fileobj: object
            :type items: string
    '''
    if keyword is None:
        return
    #process keyword.
    process_item(keyword, fileobj, level, keyword.type.capitalize())
    for subkw in keyword.keywords:
        process_keyword(subkw, fileobj, level + 1)


def process_item(item, fileobj, level, item_type, long_name=False):
    '''Process an item and calculates the time.

    - **parameters**, **types**, **return** and **return types**::
            :param item: keyword
            :param fileobj: file object
            :param level: items to be parsed
            :param item_type: item type; test,suite,keyword
            :type item: string
            :type fileobj: object
            :type level: string

    '''
    #creates indent.
    indent = '' if level == 0 else ('|  ' * (level - 1) + '|- ')
    #Encodes the string to utf-8
    name = (item.longname if long_name else item.name).encode('UTF-8')
    #finds the elapsed time in secs.
    elapsed = utils.elapsed_time_to_string(item.elapsedtime)
    fileobj.write(name.rjust(40) + ' | ' + (item_type).rjust(10) + ' | ' + item.status.rjust(10) + ' | ' + str(elapsed).rjust(25) + ' | '
                  + str(item.elapsedtime / 1000.0).rjust(10) + '\n')


def getdatafromfile(filepath):
    '''Get data from perf.txt file returns dictionary.

    - **parameters**, **types**, **return** and **return types**::
            :param filepath: perf.txt file location
            :type arg: string
            :return: Returns input values as dictionary
            :rtype: dictionary

    '''
    #opens perf.txt file
    with open(filepath, 'r') as tfile:
        data = tfile.read()
    #converts the data in to list of items with no titles.
    data = data.strip().split('\n')[1:]
    metrics = {}
    #process the each item and creates a dict with type as key.
    #suite,test,keyword & type and time are values in a list
    for item in data:
        suitemetrics = []
        item = item.strip().split('|')
        if item[1].strip() in metrics:
            value = metrics[item[1].strip()]
            value.append(item[0].strip() + ',' +
                         item[2].strip() + ',' + item[-1].strip())
            metrics[item[1].strip()] = value
        else:
            suitemetrics.append(
                item[0].strip() + ',' + item[2].strip() + ',' + item[-1].strip())
            metrics[item[1].strip()] = suitemetrics
    return metrics


def findmaxvaluesfrombenchmark(benchmarkdata):
    '''Finds the max response times from benchmark times.

    - **parameters**, **types**, **return** and **return types**::
            :param benchmarkdata: benchmarkdata
            :type benchmarkdata: dictionary
            :return: Returns input values as dictionary
            :rtype: dictionary

    '''
    benchmark = {}
    #reads the dictionary adn finds the maximum value of times 
    #associated with same type and name.
    for keys, values in list(benchmarkdata.items()):
        maxlist = []
        for value in values:
            value = value.split(',')
            if value[0] in benchmark:
                values = [benchmark[value[0]]]
                values.append(value[-1])
                benchmark[value[0]] = max(values)
            else:
                benchmark[value[0]] = value[-1]

    return benchmark


def perfcompare(outputxmlfile, benchmarkfile, output_dir):
    '''Compares the metrics data with benchmark data and creates perf.txt.

    - **parameters**, **types**, **return** and **return types**::
            :param outputxmlfile: output.xml file location
            :param benchmarkfile: perf.txt file location
            :param output_dir: output dir location
            :type outputxmlfile: string
            :type benchmarkfile: string
            :type output_dir: string

    '''
    metricsfile = os.path.join(output_dir, 'metricsfile.txt')
    #process the output.xml file and creates metrics file.
    process_file(outputxmlfile, metricsfile)
    #reads the data from metrics file and creates a dcitionary.
    metdata = getdatafromfile(metricsfile)
    #reads the values from benchmark.yaml.
    with open(benchmarkfile) as bench:
        benchmarkdata = yaml.load(bench, Loader=yaml.FullLoader)
    #writes data in to perf.txt file.
    perffile = open(os.path.join(output_dir, 'perf.txt'), 'w')
    msg = 'NAME'.rjust(30) + ' | ' \
        + 'TYPE'.rjust(10) + ' | ' \
        + 'STATUS'.rjust(10) + ' | ' \
        + 'ExecTime(s)'.rjust(12) + ' | ' \
        + 'Benchmark Time'.rjust(15) + ' | ' \
        + 'Comments' + '\n'
    perffile.write(130 * '=' + '\n')
    #create first item with titles in the file
    perffile.write(msg)
    perffile.write(130 * '=' + '\n')
    #reads the metdata dict and iterates over the values which contains
    #test/suite/keyword name, type and times.
    for metkey, metvalues in list(metdata.items()):
        for metvalue in metvalues:
            metvalue = metvalue.split(',')
            #creates an item with name, type, status and execution time
            msg = metvalue[0].rjust(30) + ' | ' + metkey.rjust(10) + ' | ' + metvalue[
                1].rjust(10) + ' | ' + metvalue[-1].rjust(12) + ' | '
            #iterates over benchmarkdata.
            for benchkey, benchvalue in list(benchmarkdata.items()):
                #if benchmark key equals to metricsdata key then adds msg 
                #to benchmark value
                if benchkey == metvalue[0]:
                    msg += benchvalue.rjust(15) + ' | '
                    #compares the benchmark value with metrics execution times
                    if float(benchvalue) > float(metvalue[-1]):
                        msg += 'Performance Improved.\n'
                        logger.info(benchkey + ' performance improved.')
                    elif float(benchvalue) < float(metvalue[-1]):
                        msg += 'Performance Degraded.\n'
                        logger.info(benchkey + ' performance degraded.')
                    else:
                        msg += 'No Change in Performance.\n'
            #if the metrics key is not in benchmark data keys
            else:
                if metvalue[0] not in list(benchmarkdata.keys()):
                    msg += 'Not Requested'.rjust(15) + ' | ' + 'No Comments.\n'
            #writes the message to perf.txt file
            perffile.write(msg)
    #closes the file object
    perffile.close()
    #maps the metrics data to part of test.
    mapmetrics(os.path.join(output_dir, 'perf.txt'),
                     os.path.join(output_dir, 'output.xml'))
    msg = "Check {} for performance related info.".format(
        os.path.join(output_dir, 'perf.txt'))
    #prints the location of performance related info file to the user.
    logger.info(msg)
