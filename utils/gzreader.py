import gzip
import json
from os import listdir
from os.path import isfile, join
from _collections import defaultdict


def order(a, b):
    if a < b:
        return a, b
    else:
        return b, a


def get_gzip_filenames(path):
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    return onlyfiles


if __name__ == "__main__":
    input_path = "/Users/qing/Downloads/scholar/"
    filenames = get_gzip_filenames(input_path)
    output_path = "/Users/qing/Downloads/scholar/output"
    print("there are %d files" % len(filenames))
    # writer = open("scholar", 'w')
    min_year = 2022
    max_year = 100
    c = 0
    for file in filenames:
        if 'gz' not in file:
            continue
        f = gzip.open(file, "rb")
        edges_by_years = defaultdict(list)
        content = f.readlines()
        for line in content:
            json_obj = json.loads(line)
            authors_list = json_obj["authors"]
            if json_obj["year"] == None:
                continue
            year = int(json_obj["year"])
            min_year = min(min_year, year)
            max_year = max(max_year, year)
            ids_set = set()
            for author in authors_list:
                for item in author['ids']:
                    ids_set.add(int(item))
            if len(ids_set) > 1:
                ids_list = list(ids_set)
                for i in range(0, len(ids_list)):
                    for j in range(i + 1, len(ids_list)):
                        u = ids_list[i]
                        v = ids_list[j]
                        if u == v:
                            continue
                        (u, v) = order(u, v)
                        # edges.append([u, v, year])
                        edges_by_years[year].append([u, v, year])
                        # writer.write("%d %d %d\n" % (u, v, year))
        # output edges in one file
        for key in edges_by_years.keys():
            writer = open(join(output_path, key, 'a'))
            for u, v, year in edges_by_years[key]:
                writer.write("%d %d %d\n" %(u, v, year))
            writer.flush()
            writer.close()
        c += 1
        print("finish parsing the file :", file, ". So far parsed %d files in total." % c)
    print(min_year, max_year)
        # writer.flush()
    # writer.close()
# json_str = json_bytes.decode('utf-8')
# print(len(json_str))
# data = json.loads(json_str)
# print(data[0])
