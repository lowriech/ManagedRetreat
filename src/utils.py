from datetime import datetime
import os.path
from os import walk


def get_normal_distribution_mappings(mean, sd, values):
    from torch.distributions import normal
    n = normal.Normal(mean, sd)
    y = dict()
    for i in values:
        y[round(i, 0)] = round(1 - n.cdf(i).item(), 3)
    return y


def get_by_extension(folder, ext):
    for root, dirs, files in walk(folder):
        buffer = []
        for filename in files:
            if filename.endswith(ext):
                buffer.append(filename)
        return buffer


def convert_numeric_to_datetime(time):
    time = str(time)
    return datetime(int(time[0:4]),
                    int(time[4:6]),
                    int(time[6:8]),
                    int(time[8:10]),
                    int(time[10:12]))

# TODO Deprecate in favor of get_by_extension
def get_dotshp_from_shpdir(shpdir):
    for root, dirs, files in walk(shpdir):
        for filename in files:
            if filename.endswith(".shp"):
                print(root)
                return os.path.join(root, filename)