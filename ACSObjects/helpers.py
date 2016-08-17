import pandas as pd
import time, datetime
from math import radians,cos,sin,sqrt,asin

def convertSeriesGPSTime( TimeOfWeekSec, WeekNum ):
    """
    Convert GPS time (measured in Time-of-Week [seconds] and Week number) to UTC time
    # REF: mavlink/pymavlink/DFReader.py
    # epoch = 86400*(10*365 + (1980-1969)/4 + 1 + 6 - 2)
        return epoch + 86400*7*week + sec - 15

    # Usage:
    # Ex:   TimeOfWeekSec = df['GPS_TimeMS']/1000.
            WeekNum = df['GPS_Week']
            acs.convertSeriesGPSTime( TimeOfWeekSec, WeekNum )

    Returns an object of type 'pandas.tseries.index.DatetimeIndex'
        - Can set the index of a given DataFrame to be this DatetimeIndex by df.index = dtix
    """
    datum = 86400*(10*365 + (1980-1969)/4 + 1 + 6 - 2)
    epoch_time = datum + 86400*7*WeekNum + (TimeOfWeekSec) - 15
    clk_time = pd.to_datetime(epoch_time.values,unit='s')
    clk_time_lcl = clk_time + pd.DateOffset(hours=-7)
    #clk_time_utc = clk_time.tz_localize('UTC')
    #clk_time_lcl = clk_time_utc.tz_convert('US/Pacific')
    #for count in range(len(clk_time_lcl)):
    #    clk_time_lcl[count] = pd.DatetimeIndex[clk_time_lcl[count].replace(tzinfo=None)]
    #clk_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch_time))
    return clk_time_lcl

def convertSingleGPSTime( TimeOfWeekSec, WeekNum ):
    """
    Convert GPS time (measured in Time-of-Week [seconds] and Week number) to UTC time
    # REF: mavlink/pymavlink/DFReader.py
    # epoch = 86400*(10*365 + (1980-1969)/4 + 1 + 6 - 2)
        return epoch + 86400*7*week + sec - 15

    # TODO: include try/catch for index not valid
   """
    datum = 86400*(10*365 + (1980-1969)/4 + 1 + 6 - 2)
    epoch_time = datum + 86400*7*WeekNum + (TimeOfWeekSec) - 15

    clk_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch_time))
    return clk_time

def distance_2GPS( lat1, lon1, lat2, lon2 ):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    # REF: http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2.)**2 + cos(lat1) * cos(lat2) * sin(dlon/2.)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r * 1000        # distance in meters


