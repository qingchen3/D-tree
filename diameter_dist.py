# This python file reproduces results shown in Figure 10a.
# This file takes the html file (download from http://konect.cc/statistics/diam/) as the input
# and calculates the distributions of the distance.

# run this file: "python diameter_dist.py"

from bs4 import BeautifulSoup
import sys
from collections import Counter


if __name__ == "__main__":
    sys.setrecursionlimit(1500000)

    with open("datasets/Diameter.html", 'rb') as fp:
        soup = BeautifulSoup(fp, 'html.parser')

    tds = soup.find_all("td", {"class": "padleft", "align": "right"}, partial=False)
    diameters = []
    for i in range(1, len(tds)):
        s = tds[i].text.rstrip().replace(',', '')
        diameters.append(int(s))

    ordered = sorted(Counter(diameters).items())
    writer = open("./res/diameters_dist.dat", 'w')
    writer.write("range index percentage\n")

    c1 = 0
    c2 = 0
    c3 = 0
    c4 = 0
    c5 = 0
    for d, freq in ordered:
        if d <= 5:
            c1 += freq
        elif 5 < d <= 10:
            c2 += freq
        elif 10 < d <= 16:
            c3 += freq
        elif 16 < d <= 20:
            c4 += freq
        else:
            c5 += freq

    writer.write("1-5 0 %f\n" %(round(100 * c1 / 1324, 2)))
    writer.write("6-10 1 %f\n" %(round(100 * c2 / 1324, 2)))
    writer.write("11-16 2 %f\n" %(round(100 * c3 / 1324, 2)))
    writer.write("17-20 3 %f\n" %(round(100 * c4 / 1324, 2)))
    writer.write("20+ 4 %f\n" %(round(100 * c5 / 1324, 2)))

    writer.flush()
    writer.close()

    print("results saved in res/diameters_dist.dat")
