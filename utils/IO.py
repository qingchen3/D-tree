from pathlib import Path
from prettytable import PrettyTable
import collections
from tempfile import NamedTemporaryFile
import shutil
import csv
from pathlib import Path
import os


def setup(testcase, start_timestamp, end_timestamp):

    # setup surviving time for different datasets
    survival_time = 1296000 # by default, 14 days

    if testcase in ['dblp', 'scholar']:
        survival_time = 5  # 5 years
    elif testcase == 'osmswitzerland':
        survival_time = 1

    # First, set up test_num, the number of tests of performance are conducted
    # Second, calculate test_query_frequency = (t_e - t_s) / test_num.
    # that is how frequent we test queries performance.
    # For example, test_query_frequency = 1000000, we test every 1000000 seconds.
    if testcase in ['dblp', 'scholar']:
        test_query_frequency = 1  # run performance test once per year
        test_query_num = end_timestamp - start_timestamp + survival_time  # from year 1980 to year 2021
    else:
        test_query_num = 100  # select 100 test point, calculate the frequency of testing
        test_query_frequency = (end_timestamp - start_timestamp + 2 * survival_time) // test_query_num

    test_points = []
    for i in range(1, test_query_num + 1):
        test_points.append(start_timestamp + i * test_query_frequency)

    if testcase == 'scholar':
        test_points.append(2028)

    '''
    # set up the header for output file
    query_writer = open("res/query_%s.dat" % (testcase), 'w')
    Sd_writer = open("res/Sd_%s.dat" % (testcase), 'w')

    if testcase in ['fb', 'wiki', 'dnc', 'messages', 'call']: # small graphs
        query_writer.write("ts Dtree nDtree HK ET opt\n")
        Sd_writer.write("ts Dtree nDtree HK ET opt\n")
    else:  # large graphs
        query_writer.write("ts Dtree nDtree HK\n")
        Sd_writer.write("ts Dtree nDtree HK\n")
        if not Path("res/insertion_te.csv").is_file():
            insertion_te_writer = open("res/insertion_te.csv", 'w')
            insertion_te_writer.write("Graph,index,DTree,nDTree,HK\n")
            insertion_te_writer.write("tech,0,0,0,0\n")
            insertion_te_writer.write("enron,1,0,0,0\n")
            insertion_te_writer.write("stackoverflow,2,0,0,0\n")
            insertion_te_writer.write("youtube,3,0,0,0\n")
            insertion_te_writer.write("dblp,4,0,0,0\n")
            insertion_te_writer.write("scholar,5,0,0,0\n")
            insertion_te_writer.write("yahoo,6,0,0,0\n")
            insertion_te_writer.flush()
            insertion_te_writer.close()

        if not Path("res/insertion_nte.csv").is_file():
            insertion_nte_writer = open("res/insertion_nte.csv", 'w')
            insertion_nte_writer.write("Graph,index,DTree,nDTree,HK\n")
            insertion_nte_writer.write("tech,0,0,0,0\n")
            insertion_nte_writer.write("enron,1,0,0,0\n")
            insertion_nte_writer.write("stackoverflow,2,0,0,0\n")
            insertion_nte_writer.write("youtube,3,0,0,0\n")
            insertion_nte_writer.write("dblp,4,0,0,0\n")
            insertion_nte_writer.write("scholar,5,0,0,0\n")
            insertion_nte_writer.write("yahoo,6,0,0,0\n")
            insertion_nte_writer.flush()
            insertion_nte_writer.close()

        if not Path("res/deletion_te.csv").is_file():
            deletion_te_writer = open("res/deletion_te.csv", 'w')
            deletion_te_writer.write("Graph,index,DTree,nDTree,HK\n")
            deletion_te_writer.write("tech,0,0,0,0\n")
            deletion_te_writer.write("enron,1,0,0,0\n")
            deletion_te_writer.write("stackoverflow,2,0,0,0\n")
            deletion_te_writer.write("youtube,3,0,0,0\n")
            deletion_te_writer.write("dblp,4,0,0,0\n")
            deletion_te_writer.write("scholar,5,0,0,0\n")
            deletion_te_writer.write("yahoo,6,0,0,0\n")
            deletion_te_writer.flush()
            deletion_te_writer.close()

        if not Path("res/deletion_nte.csv").is_file():
            deletion_nte_writer = open("res/deletion_nte.csv", 'w')
            deletion_nte_writer.write("Graph,index,DTree,nDTree,HK\n")
            deletion_nte_writer.write("tech,0,0,0,0\n")
            deletion_nte_writer.write("enron,1,0,0,0\n")
            deletion_nte_writer.write("stackoverflow,2,0,0,0\n")
            deletion_nte_writer.write("youtube,3,0,0,0\n")
            deletion_nte_writer.write("dblp,4,0,0,0\n")
            deletion_nte_writer.write("scholar,5,0,0,0\n")
            deletion_nte_writer.write("yahoo,6,0,0,0\n")
            deletion_nte_writer.flush()
            deletion_nte_writer.close()
    
        '''
    #return survival_time, test_points, query_writer, Sd_writer
    return survival_time, test_points


def output_average_dist_by_method(data, num, testcase, method):
    """
    :param data: accumulated distances of k snapshots
    :param num: number of snapshots
    :param testcase: graph
    :param isSmallGraph: whether or not current graph is small graph
    :return: outputing distributions of average distances to files
    """
    if method not in ['Dtree', 'nDtree', 'HK', 'ET', 'opt']:
        raise ValueError('unknown method')

    p = "res/dist/%s" %testcase
    if not os.path.exists(p):
        os.makedirs(p, exist_ok = True)

    writer = open("%s/%s.dat" % (p, method), 'w')
    writer.write("d freq\n")

    temp = collections.OrderedDict(sorted(data.items()))

    for d, value in temp.items():
        if value // num > 0:
            writer.write("%d %d\n" % (d, value // num))
    writer.flush()
    writer.close()


def output_average_dist(data, num, testcase, isSmallGraph):
    """
    :param data: accumulated distances of k snapshots
    :param num: number of snapshots
    :param testcase: graph
    :param isSmallGraph: whether or not current graph is small graph
    :return: outputing distributions of average distances to files
    """

    Dtree_dist_data = data[0]
    temp = collections.OrderedDict(sorted(Dtree_dist_data.items()))
    writer = open("res/dist/%s/Dtree.dat" % testcase, 'w')
    writer.write("d freq\n")
    for d, value in temp.items():
        if value // num > 0:
            writer.write("%d %d\n" % (d, value // num))
    writer.flush()
    writer.close()

    nDtree_dist_data = data[1]
    temp = collections.OrderedDict(sorted(nDtree_dist_data.items()))
    writer = open("res/dist/%s/nDtree.dat" % testcase, 'w')
    writer.write("d freq\n")
    for d, value in temp.items():
        if value // num > 0:
            writer.write("%d %d\n" % (d, value // num))
    writer.flush()
    writer.close()

    HK_dist_data = data[2]
    temp = collections.OrderedDict(sorted(HK_dist_data.items()))
    writer = open("res/dist/%s/HK.dat" % testcase, 'w')
    writer.write("d freq\n")
    for d, value in temp.items():
        if value // num > 0:
            writer.write("%d %d\n" % (d, value // num))
    writer.flush()
    writer.close()

    if isSmallGraph:
        ET_dist_data = data[3]
        temp = collections.OrderedDict(sorted(ET_dist_data.items()))
        writer = open("res/dist/%s/ET.dat" % testcase, 'w')
        writer.write("d freq\n")
        for d, value in temp.items():
            if value // num > 0:
                writer.write("%d %d\n" % (d, value // num))
        writer.flush()
        writer.close()

        opt_dist_data = data[4]
        temp = collections.OrderedDict(sorted(opt_dist_data.items()))
        writer = open("res/dist/%s/opt.dat" % testcase, 'w')
        writer.write("d freq\n")
        for d, value in temp.items():
            if value // num > 0:
                writer.write("%d %d\n" % (d, value // num))
        writer.flush()
        writer.close()


# full output of maintainence
def output2file(data, insertion_writer, deletion_writer):
    Dtree_res = data[0]
    nDtree_res = data[1]
    HK_res = data[2]
    if len(data) == 3:
        insertion_writer.write("%d %f %f %d %f %f %d %f %f "
                               "%d %f %f %d %f %f %d %f %f\n"
                               % (Dtree_res.in_te_count,
                                  Dtree_res.in_te_time,
                                  Dtree_res.in_te_time / (Dtree_res.in_te_count + 0.00001),
                                  nDtree_res.in_te_count,
                                  nDtree_res.in_te_time,
                                  nDtree_res.in_te_time / (nDtree_res.in_te_count + 0.00001),
                                  HK_res.in_te_count,
                                  HK_res.in_te_time,
                                  HK_res.in_te_time / (HK_res.in_te_count + 0.00001),
                                  Dtree_res.in_nte_count,
                                  Dtree_res.in_nte_time,
                                  Dtree_res.in_nte_time / (Dtree_res.in_nte_count + 0.00001),
                                  nDtree_res.in_nte_count,
                                  nDtree_res.in_nte_time,
                                  nDtree_res.in_nte_time / (nDtree_res.in_nte_count + 0.00001),
                                  HK_res.in_nte_count,
                                  HK_res.in_nte_time,
                                  HK_res.in_nte_time / (HK_res.in_nte_count + 0.00001)))
        insertion_writer.flush()

        deletion_writer.write("%d %f %f %d %f %f %d %f %f "
                              "%d %f %f %d %f %f %d %f %f \n"
                              % (Dtree_res.de_te_count,
                                 Dtree_res.de_te_time,
                                 Dtree_res.de_te_time / (Dtree_res.de_te_count + 0.00001),
                                 nDtree_res.de_te_count,
                                 nDtree_res.de_te_time,
                                 nDtree_res.de_te_time / (nDtree_res.de_te_count + 0.00001),
                                 HK_res.de_te_count,
                                 HK_res.de_te_time,
                                 HK_res.de_te_time / (HK_res.de_te_count + 0.00001),
                                 Dtree_res.de_nte_count,
                                 Dtree_res.de_nte_time,
                                 Dtree_res.de_nte_time / (Dtree_res.de_nte_count + 0.00001),
                                 nDtree_res.de_nte_count,
                                 nDtree_res.de_nte_time,
                                 nDtree_res.de_nte_time / (nDtree_res.de_nte_count + 0.00001),
                                 HK_res.de_nte_count,
                                 HK_res.de_nte_time,
                                 HK_res.de_nte_time / (HK_res.de_nte_count + 0.00001)))
        deletion_writer.flush()
    else:
        ET_res = data[3]
        opt_res = data[4]
        insertion_writer.write("%d %f %f %d %f %f %d %f %f %d %f %f %d %f %f "
                               "%d %f %f %d %f %f %d %f %f %d %f %f %d %f %f\n"
                               % (Dtree_res.in_te_count,
                                  Dtree_res.in_te_time,
                                  Dtree_res.in_te_time / (Dtree_res.in_te_count + 0.00001),
                                  nDtree_res.in_te_count,
                                  nDtree_res.in_te_time,
                                  nDtree_res.in_te_time / (nDtree_res.in_te_count + 0.00001),
                                  ET_res.in_te_count,
                                  ET_res.in_te_time,
                                  ET_res.in_te_time / (ET_res.in_te_count + 0.00001),
                                  HK_res.in_te_count,
                                  HK_res.in_te_time,
                                  HK_res.in_te_time / (HK_res.in_te_count + 0.00001),
                                  opt_res.in_te_count,
                                  opt_res.in_te_time,
                                  opt_res.in_te_time / (opt_res.in_te_count + 0.00001),
                                  Dtree_res.in_nte_count,
                                  Dtree_res.in_nte_time,
                                  Dtree_res.in_nte_time / (Dtree_res.in_nte_count + 0.00001),
                                  nDtree_res.in_nte_count,
                                  nDtree_res.in_nte_time,
                                  nDtree_res.in_nte_time / (nDtree_res.in_nte_count + 0.00001),
                                  ET_res.in_nte_count,
                                  ET_res.in_nte_time,
                                  ET_res.in_nte_time / (ET_res.in_nte_count + 0.00001),
                                  HK_res.in_nte_count,
                                  HK_res.in_nte_time,
                                  HK_res.in_nte_time / (ET_res.in_nte_count + 0.00001),
                                  opt_res.in_nte_count,
                                  opt_res.in_nte_time,
                                  opt_res.in_nte_time / (opt_res.in_nte_count + 0.00001)))
        insertion_writer.flush()

        deletion_writer.write("%d %f %f %d %f %f %d %f %f %d %f %f %d %f %f "
                               "%d %f %f %d %f %f %d %f %f %d %f %f %d %f %f\n"
                              % (Dtree_res.de_te_count,
                                 Dtree_res.de_te_time,
                                 Dtree_res.de_te_time / (Dtree_res.de_te_count + 0.00001),
                                 nDtree_res.de_te_count,
                                 nDtree_res.de_te_time,
                                 nDtree_res.de_te_time / (nDtree_res.de_te_count + 0.00001),
                                 ET_res.de_te_count,
                                 ET_res.de_te_time,
                                 ET_res.de_te_time / (ET_res.de_te_count + 0.00001),
                                 HK_res.de_te_count,
                                 HK_res.de_te_time,
                                 HK_res.de_te_time / (HK_res.de_te_count + 0.00001),
                                 opt_res.de_te_count,
                                 opt_res.de_te_time,
                                 opt_res.de_te_time / (opt_res.de_te_count + 0.00001),
                                 Dtree_res.de_nte_count,
                                 Dtree_res.de_nte_time,
                                 Dtree_res.de_nte_time / (Dtree_res.de_nte_count + 0.00001),
                                 nDtree_res.de_nte_count,
                                 nDtree_res.de_nte_time,
                                 nDtree_res.de_nte_time / (nDtree_res.de_nte_count + 0.00001),
                                 ET_res.de_nte_count,
                                 ET_res.de_nte_time,
                                 ET_res.de_nte_time / (ET_res.de_nte_count + 0.00001),
                                 HK_res.de_nte_count,
                                 HK_res.de_nte_time,
                                 HK_res.de_nte_time / (HK_res.de_nte_count + 0.00001),
                                 opt_res.de_nte_count,
                                 opt_res.de_nte_time,
                                 opt_res.de_nte_time / (opt_res.de_nte_count + 0.00001)))
        deletion_writer.flush()


def printRes(operation, data):
    t = PrettyTable(['operation', 'Data structure', 'count', 'time'])
    for items in data:
        if len(items) < 4:
            t.add_row([operation, items[0], items[1], items[2]])
        else:
            t.add_row([operation, items[0], items[1], items[2]])
    print(t)


def update_res_vertices_edges(testcase, result_type, data):
    if result_type == 'vertices':  # update result of query performance
        filename = 'res/vertices_%s.csv'%testcase
    elif result_type == 'edges':  # update result of Sd
        filename = 'res/edges_%s.csv' % testcase
    else:
        raise ValueError('unknown result type')

    if not Path(filename).exists():
        writer = open(filename, 'w')
        writer.write('ts,num\n')
        writer.flush()
        writer.close()

    assert Path(filename).exists()

    tempfile = NamedTemporaryFile('w+t', newline = '', delete = False)
    current_time, res = data
    with open(filename, 'r', newline = '') as csvFile, tempfile:
        reader = csv.reader(csvFile, delimiter = ',', quotechar = '"')
        writer = csv.writer(tempfile, delimiter = ',', quotechar = '"')

        latest_time = -1
        for row in reader:
            if row[0] == 'ts':
                writer.writerow(row)
                continue
            elif int(row[0]) == current_time:
                writer.writerow(data)
            else:
                writer.writerow(row)
            latest_time = int(row[0])
        if latest_time < current_time:
            writer.writerow(data)

    shutil.move(tempfile.name, filename)


def update_res_query_Sd(testcase, result_type, data, method):
    # data is in the form: [current, query_time]
    if method == 'Dtree':
        index = 1
    elif method == 'nDtree':
        index = 2
    elif method == 'HK':
        index = 3
    elif method == 'ET':
        index = 4
    elif method == 'opt':
        index = 5
    else:
        raise ValueError('unknown method')

    if result_type == 'query':  # update result of query performance
        filename = 'res/query_%s.csv'%testcase
    elif result_type == 'Sd':  # update result of Sd
        filename = 'res/Sd_%s.csv' % testcase
    else:
        raise ValueError('unknown result type')

    if testcase in ['fb', 'wiki', 'dnc', 'messages', 'call']:
        is_small_graph = True
    else:
        is_small_graph = False

    if not Path(filename).exists():
        writer = open(filename, 'w')
        if is_small_graph:
            writer.write('ts,Dtree,nDtree,HK,ET,opt\n')
        else:
            writer.write('ts,Dtree,nDtree,HK\n')
        writer.flush()
        writer.close()

    assert Path(filename).exists()

    tempfile = NamedTemporaryFile('w+t', newline = '', delete = False)
    current_time, res = data
    with open(filename, 'r', newline = '') as csvFile, tempfile:
        reader = csv.reader(csvFile, delimiter = ',', quotechar = '"')
        writer = csv.writer(tempfile, delimiter = ',', quotechar = '"')

        latest_time = -1
        for row in reader:
            if row[0] == 'ts':
                writer.writerow(row)
                continue
            elif int(row[0]) == current_time:
                items = []
                for i in range(len(row)):
                    items.append(row[i])
                items[index] = res
                writer.writerow(items)
            else:
                writer.writerow(row)
            latest_time = int(row[0])
        if latest_time < current_time:
            if is_small_graph:
                items = [current_time, 0, 0, 0, 0, 0]
            else:
                items = [current_time, 0, 0, 0]
            items[index] = res
            writer.writerow(items)

    shutil.move(tempfile.name, filename)


def update_average_distance(testcase, data, method):
    # data is in the form: [current, query_time]
    if method == 'Dtree':
        index = 1
    elif method == 'nDtree':
        index = 2
    elif method == 'HK':
        index = 3
    elif method == 'ET':
        index = 4
    elif method == 'opt':
        index = 5
    else:
        raise ValueError('unknown method')

    if not os.path.exists('./res'):
        os.makedirs('./res', exist_ok = True)

    if testcase in ['fb', 'wiki', 'dnc', 'messages', 'call']:
        is_small_graph = True
    else:
        is_small_graph = False

    filename = './res/height_%s.csv'%testcase
    if not Path(filename).exists():
        writer = open(filename, 'w')
        if is_small_graph:
            writer.write('ts,Dtree,nDtree,HK,ET,opt\n')
        else:
            writer.write('ts,Dtree,nDtree,HK\n')
        writer.flush()
        writer.close()

    assert Path(filename).exists()

    tempfile = NamedTemporaryFile('w+t', newline = '', delete = False)
    current_time, res = data
    with open(filename, 'r', newline = '') as csvFile, tempfile:
        reader = csv.reader(csvFile, delimiter = ',', quotechar = '"')
        writer = csv.writer(tempfile, delimiter = ',', quotechar = '"')

        latest_time = -1
        for row in reader:
            if row[0] == 'ts':
                writer.writerow(row)
                continue
            elif int(row[0]) == current_time:
                items = []
                for i in range(len(row)):
                    items.append(row[i])
                items[index] = res
                writer.writerow(items)
            else:
                writer.writerow(row)
            latest_time = int(row[0])
        if latest_time < current_time:
            if is_small_graph:
                items = [current_time, 0, 0, 0, 0, 0]
            else:
                items = [current_time, 0, 0, 0]
            items[index] = res
            writer.writerow(items)

    shutil.move(tempfile.name, filename)


def update_average_runtime(testcase, type, data, method):
    # data is in the form: [current, query_time]
    if method == 'Dtree':
        index = 1
    elif method == 'nDtree':
        index = 2
    elif method == 'HK':
        index = 3
    elif method == 'ET':
        index = 4
    elif method == 'opt':
        index = 5
    else:
        raise ValueError('unknown method')

    if not os.path.exists('./res/updates'):
        os.makedirs('./res/updates', exist_ok = True)

    if testcase in ['fb', 'wiki', 'dnc', 'messages', 'call']:
        is_small_graph = True
    else:
        is_small_graph = False

    if type == "insertion_te":
        filename = './res/updates/%s_insertion_te.csv'%testcase
    elif type == "insertion_nte":
        filename = './res/updates/%s_insertion_nte.csv' % testcase
    elif type == "deletion_te":
        filename = './res/updates/%s_deletion_te.csv' % testcase
    elif type == "deletion_nte":
        filename = './res/updates/%s_deletion_nte.csv' % testcase
    else:
        raise ValueError('unknown parameters')

    if not Path(filename).exists():
        writer = open(filename, 'w')
        if is_small_graph:
            writer.write('ts,Dtree,nDtree,HK,ET,opt\n')
        else:
            writer.write('ts,Dtree,nDtree,HK\n')
        writer.flush()
        writer.close()

    assert Path(filename).exists()

    tempfile = NamedTemporaryFile('w+t', newline = '', delete = False)
    current_time, res = data
    with open(filename, 'r', newline = '') as csvFile, tempfile:
        reader = csv.reader(csvFile, delimiter = ',', quotechar = '"')
        writer = csv.writer(tempfile, delimiter = ',', quotechar = '"')

        latest_time = -1
        for row in reader:
            if row[0] == 'ts':
                writer.writerow(row)
                continue
            elif int(row[0]) == current_time:
                items = []
                for i in range(len(row)):
                    items.append(row[i])
                items[index] = res
                writer.writerow(items)
            else:
                writer.writerow(row)
            latest_time = int(row[0])
        if latest_time < current_time:
            if is_small_graph:
                items = [current_time, 0, 0, 0, 0, 0]
            else:
                items = [current_time, 0, 0, 0]
            items[index] = res
            writer.writerow(items)

    shutil.move(tempfile.name, filename)


def update_average_uneven_size_beta(testcase, type, data, method):
    # data is in the form: [current, query_time]
    if method == 'Dtree':
        index = 1
    elif method == 'nDtree':
        index = 2
    elif method == 'HK':
        index = 3
    elif method == 'ET':
        index = 4
    elif method == 'opt':
        index = 5
    else:
        raise ValueError('unknown method')

    if not os.path.exists('./res'):
        os.makedirs('./res', exist_ok = True)

    if testcase in ['fb', 'wiki', 'dnc', 'messages', 'call']:
        is_small_graph = True
    else:
        is_small_graph = False
    if type == "uneven":
        filename = './res/uneven_%s.csv'%testcase
    else:
        filename = './res/beta_%s.csv' % testcase

    if not Path(filename).exists():
        writer = open(filename, 'w')
        if is_small_graph:
            writer.write('ts,Dtree,nDtree,HK,ET,opt\n')
        else:
            writer.write('ts,Dtree,nDtree,HK\n')
        writer.flush()
        writer.close()

    assert Path(filename).exists()

    tempfile = NamedTemporaryFile('w+t', newline = '', delete = False)
    current_time, res = data
    with open(filename, 'r', newline = '') as csvFile, tempfile:
        reader = csv.reader(csvFile, delimiter = ',', quotechar = '"')
        writer = csv.writer(tempfile, delimiter = ',', quotechar = '"')

        latest_time = -1
        for row in reader:
            if row[0] == 'ts':
                writer.writerow(row)
                continue
            elif int(row[0]) == current_time:
                items = []
                for i in range(len(row)):
                    items.append(row[i])
                items[index] = res
                writer.writerow(items)
            else:
                writer.writerow(row)
            latest_time = int(row[0])
        if latest_time < current_time:
            if is_small_graph:
                items = [current_time, 0, 0, 0, 0, 0]
            else:
                items = [current_time, 0, 0, 0]
            items[index] = res
            writer.writerow(items)

    shutil.move(tempfile.name, filename)


def update_maintanence(testcase, data, method):
    files = ['res/insertion_te.csv', 'res/insertion_nte.csv', 'res/deletion_te.csv', 'res/deletion_nte.csv']
    if testcase not in ['wiki', 'messages', 'dnc', 'call', 'fb',
                        'tech', 'enron', 'stackoverflow', 'youtube', 'dblp',  'scholar']:
        raise ValueError(" testcase not in ['wiki', 'messages', 'dnc', 'call', 'fb', "
                         "'tech', 'enron', 'stackoverflow', 'youtube', 'dblp',  'scholar']")

    if method not in ['Dtree', 'nDtree', 'HK', 'ET', 'opt']:
        raise ValueError("method not in ['Dtree', 'nDtree', 'HK', 'ET', 'opt']")

    labels = {'wiki': 'WI', 'messages': 'MS', 'dnc': 'DNC', 'call': 'CA', 'fb': 'FB',
             'tech': 'Tech', 'enron': 'EN', 'stackoverflow': 'ST', 'youtube': 'YT', 'scholar': 'SC'}
    testcase_ = labels[testcase]

    method_index = {'Dtree': 1, 'nDtree': 2, 'HK': 3, 'ET': 4, 'opt': 5}
    idx = method_index[method]
    for filename in files:
        if not Path(filename).exists():
            writer = open(filename, 'w')
            writer.write('Graph,DTree,nDTree,HK,ET,opt\n')
            writer.write("DNC,0,0,0,0,0\nCA,0,0,0,0,0\n"
                         "MS,0,0,0,0,0\nWI,0,0,0,0,0\n"
                         "FB,0,0,0,0,0\nTech,0,0,0,0,0\n"
                         "EN,0,0,0,0,0\nST,0,0,0,0,0\n"
                         "YT,0,0,0,0,0\nSC,0,0,0,0,0\n")
            writer.flush()
            writer.close()

        tempfile = NamedTemporaryFile('w+t', newline = '', delete = False)
        with open(filename, 'r', newline = '') as csvFile, tempfile:
            reader = csv.reader(csvFile, delimiter = ',', quotechar = '"')
            writer = csv.writer(tempfile, delimiter = ',', quotechar = '"')
            for row in reader:
                case = row[0]
                if case != testcase_:
                    writer.writerow(row)
                else:
                    items = []
                    for k in range(len(row)):
                        items.append(row[k])
                    if "insertion_te" in filename:
                        items[idx] = data.in_te_time / (data.in_te_count + 0.00001)
                    elif "insertion_nte" in filename:
                        items[idx] = data.in_nte_time / (data.in_nte_count + 0.00001)
                    elif "deletion_te" in filename:
                        items[idx] = (data.de_te_time / (data.de_te_count + 0.00001))
                    elif "deletion_nte" in filename:
                        items[idx] = (data.de_nte_time / (data.de_nte_count + 0.00001))
                    writer.writerow(items)
        shutil.move(tempfile.name, filename)


def updateRes(testcase, data):
    files = ['res/insertion_te.csv', 'res/insertion_nte.csv', 'res/deletion_te.csv', 'res/deletion_nte.csv']
    Dtree_res = data[0]
    nDtree_res = data[1]
    HK_res = data[2]
    if len(data) > 3:
        ET_res = data[3]
        opt_res = data[4]

    for filename in files:
        tempfile = NamedTemporaryFile('w+t', newline = '', delete = False)
        with open(filename, 'r', newline = '') as csvFile, tempfile:
            reader = csv.reader(csvFile, delimiter = ',', quotechar = '"')
            writer = csv.writer(tempfile, delimiter = ',', quotechar = '"')
            for row in reader:
                if row[0] == testcase:
                    items = []
                    if "insertion_te" in filename:
                        items.append(row[0])
                        items.append(row[1])
                        items.append(Dtree_res.in_te_time / (Dtree_res.in_te_count + 0.00001))
                        items.append(nDtree_res.in_te_time / (nDtree_res.in_te_count + 0.00001))
                        items.append(HK_res.in_te_time / (HK_res.in_te_count + 0.00001))
                        if len(data) > 3:
                            items.append(ET_res.in_te_time / (ET_res.in_te_count + 0.00001))
                            items.append(opt_res.in_te_time / (opt_res.in_te_count + 0.00001))
                    elif "insertion_nte" in filename:
                        items.append(row[0])
                        items.append(row[1])
                        items.append(Dtree_res.in_nte_time / (Dtree_res.in_nte_count + 0.00001))
                        items.append(nDtree_res.in_nte_time / (nDtree_res.in_nte_count + 0.00001))
                        items.append(HK_res.in_nte_time / (HK_res.in_nte_count + 0.00001))
                        if len(data) > 3:
                            items.append(ET_res.in_nte_time / (ET_res.in_nte_count + 0.00001))
                            items.append(opt_res.in_nte_time / (opt_res.in_nte_count + 0.00001))
                    elif "deletion_te" in filename:
                        items.append(row[0])
                        items.append(row[1])
                        items.append(Dtree_res.de_te_time / (Dtree_res.de_te_count + 0.00001))
                        items.append(nDtree_res.de_te_time / (nDtree_res.de_te_count + 0.00001))
                        items.append(HK_res.de_te_time / (HK_res.de_te_count + 0.00001))
                        if len(data) > 3:
                            items.append(ET_res.de_te_time / (ET_res.de_te_count + 0.00001))
                            items.append(opt_res.de_te_time / (opt_res.de_te_count + 0.00001))
                    elif "deletion_nte" in filename:
                        items.append(row[0])
                        items.append(row[1])
                        items.append(Dtree_res.de_nte_time / (Dtree_res.de_nte_count + 0.00001))
                        items.append(nDtree_res.de_nte_time / (nDtree_res.de_nte_count + 0.00001))
                        items.append(HK_res.de_nte_time / (HK_res.de_nte_count + 0.00001))
                        if len(data) > 3:
                            items.append(ET_res.de_nte_time / (ET_res.de_nte_count + 0.00001))
                            items.append(opt_res.de_nte_time / (opt_res.de_nte_count + 0.00001))

                    print(items)
                    writer.writerow(items)
                else:
                    print(row)
                    writer.writerow(row)
        shutil.move(tempfile.name, filename)


def copyRes(current_res, pre_res):
    pre_res.in_nte_count = current_res.in_nte_count
    pre_res.in_nte_time = current_res.in_nte_time
    pre_res.in_te_count = current_res.in_te_count
    pre_res.in_te_time = current_res.in_te_time
    pre_res.de_nte_count = current_res.de_nte_count
    pre_res.de_nte_time = current_res.de_nte_time
    pre_res.de_te_count = current_res.de_te_count
    pre_res.de_te_time = current_res.de_te_time
