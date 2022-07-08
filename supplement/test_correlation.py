import numpy as np
from os.path import join

if __name__ == '__main__':

    # to add enron, 'youtube',
    testcases = ['fb', 'wiki', 'dnc', 'messages', 'call',  'tech',  'stackoverflow', 'enron', 'youtube', 'scholar']
    data_folder = '/users/qing/projects/draft-dynamic-connectivity/VLDB/res'
    count = 0
    sum_pearson_correlation_vertices = 0
    sum_pearson_correlation_Sd = 0
    for testcase in testcases:
        vertices_file = join(data_folder, "vertices_%s.csv" % testcase)
        Sd_file = join(data_folder, "Sd_%s.csv" % testcase)
        query_file = join(data_folder, "query_%s.csv" % testcase)

        if testcase in ['fb', 'wiki', 'dnc', 'messages', 'call']:
            m = 6
        elif testcase == 'scholar':
            m = 3
        else:
            m = 4

        Sd_data = []
        [Sd_data.append([]) for i in range(1, m)]
        query_data = []
        [query_data.append([]) for i in range(1, m)]

        query_reader = open(query_file, 'r')
        query_reader.readline()

        Sd_reader = open(Sd_file, 'r')
        Sd_reader.readline()

        for line in Sd_reader.readlines():
            items = line.rstrip().split(',')
            for i in range(1, m):
                Sd_data[i - 1].append(int(items[i]))

        vertices_data = []
        vertices_reader = open(vertices_file, 'r')
        vertices_reader.readline()

        for line in vertices_reader.readlines():
            items = line.rstrip().split(',')
            vertices_data.append(int(items[1]))

        for line in query_reader.readlines():
            items = line.rstrip().split(',')
            for i in range(1, m):
                query_data[i - 1].append(float(items[i]))

        for i in range(1, m):
            r = np.corrcoef(np.array(Sd_data[i - 1]), np.array(query_data[i - 1]))
            sum_pearson_correlation_Sd += r[0, 1]

            r = np.corrcoef(np.array(vertices_data), np.array(query_data[i - 1]))
            sum_pearson_correlation_vertices += r[0, 1]

            count += 1
    print("Average pearson correlation between Sd and query performance: %f." % (sum_pearson_correlation_Sd / count))
    print("Average pearson correlation between # of vertices and query performance: %f."
          % (sum_pearson_correlation_vertices / count))
    print()

    for operation in ['insertion_te', 'insertion_nte', 'deletion_te', 'deletion_nte']:
        sum_pearson_correlation_vertices = 0
        sum_pearson_correlation_Sd = 0
        count = 0
        for testcase in testcases:
            vertices_file = join(data_folder, "vertices_%s.csv" % testcase)
            Sd_file = join(data_folder, "height_%s.csv" % testcase)
            update_file = join(data_folder, "updates/%s_%s.csv" % (testcase, operation))

            if testcase in ['fb', 'wiki', 'dnc', 'messages', 'call']:
                m = 6
            elif testcase == 'scholar':
                m = 3
            else:
                m = 4

            vertices_data = []
            vertices_reader = open(vertices_file, 'r')
            vertices_reader.readline()
            for line in vertices_reader.readlines():
                items = line.rstrip().split(',')
                vertices_data.append(int(items[1]))

            Sd_data = []
            [Sd_data.append([]) for i in range(1, m)]
            Sd_reader = open(Sd_file, 'r')
            Sd_reader.readline()
            for line in Sd_reader.readlines():
                items = line.rstrip().split(',')
                for i in range(1, m):
                    Sd_data[i - 1].append(float(items[i]))

            update_data = []
            [update_data.append([]) for i in range(1, m)]
            update_reader = open(update_file, 'r')
            update_reader.readline()
            for line in update_reader.readlines():
                items = line.rstrip().split(',')
                for i in range(1, m):
                    update_data[i - 1].append(float(items[i]))

            for i in range(1, m):
                r = np.corrcoef(np.array(vertices_data), np.array(update_data[i - 1]))
                sum_pearson_correlation_vertices += r[0, 1]
                count += 1

            for i in range(1, m):
                r = np.corrcoef(np.array(Sd_data[i - 1]), np.array(update_data[i - 1]))
                sum_pearson_correlation_Sd += r[0, 1]

        print("Average pearson correlation between # of vertices and %s: %f."
              % (operation, sum_pearson_correlation_vertices / count))
        print("Average pearson correlation between Sd/V and %s: %f."
              % (operation, sum_pearson_correlation_Sd / count))
        print()

    '''
    Average pearson correlation between # of vertices and insertion_te: 0.621559.
    Average pearson correlation between Sd/V and insertion_te: 0.645742.

    Average pearson correlation between # of vertices and insertion_nte: 0.563328.
    Average pearson correlation between Sd/V and insertion_nte: 0.608772.

    Average pearson correlation between # of vertices and deletion_te: 0.532656.
    Average pearson correlation between Sd/V and deletion_te: 0.576389.

    Average pearson correlation between # of vertices and deletion_nte: 0.440058.
    Average pearson correlation between Sd/V and deletion_nte: 0.519574.
    
    (0.621559 + 0.563328 + 0.532656 + 0.440058) / 4 = 0.53940025, 
    (0.645742 + 0.608772 + 0.576389 + 0.519574) / 4 = 0.58761925 
    '''






