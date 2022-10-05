from datetime import datetime, timedelta
from math import mean

def open_outfile_inf(data):
    csv_open = False
    count = 0
    while csv_open == False:
        try:
            csv = open("out_{}.csv".format(count), 'x')
            csv_open = True
        except FileExistsError:
            count += 1

def open_outfile():
    file_isopen = False
    while not file_isopen:
        outfile_name = input("file name? (.csv) ")
        try:
            outfile = open("{}.csv".format(outfile_name), 'x')
            file_isopen = True
            outfile.close()
        except FileExistsError:
            append = input("file exists. append to existing file? [y/n] ")
            if append == 'y' or append == 'Y':
                outfile = open("{}.csv".format(outfile_name), 'a')
                file_isopen = True
            else:
                print("please enter a new filename, or ctl+c to quit")
        except KeyboardInterrupt:
            exit()
    return outfile

def read_csv_log_data(logfile, num_thermocouples, start_timestamp, end_timestamp):
    temp_data = []
    print("parsing thermocouple data...")
    line_count=0
    total_lines=0
    for line in logfile:
        total_lines +=1
    logfile.seek(0)
    for line in logfile:
        print("{}%".format(round((line_count/(total_lines-1))*100, 1)), end='\r')
        line_count += 1
        points = line.split(',')
        try:
            year_time = points[0] + '_' + points[1]
        except IndexError:
            print("couldn't parse timestamp on line {}".format(line_count))
        try:
            timestamp = datetime.strptime(year_time, "%Y-%m-%d_%I:%M:%S %p") #data is in 12h clock
        except ValueError:
            try:
                timestamp = datetime.strptime(year_time, "%Y-%m-%d_%H:%M:%S") #data is 24h clock
            except ValueError:
                print("couldn't parse date/time from thermocouple log. got: {}".format(year_time))
                exit()
        if timestamp > start_timestamp and timestamp < end_timestamp:
        #if True:
            temp_data_point = [timestamp]
            for i in range(0, num_thermocouples):
                t = float(points[i+2])
                temp_data_point.append(t)
            temp_data.append(temp_data_point)
    print('\nfound {} data points'.format(len(temp_data)))
    return temp_data

def match_time(time1, time2, tol):
    tolerance = timedelta(minutes = tol)
    if (time2 < time1 + tolerance) and (time2 > time1 - tolerance):
            return True
    else:
        return False    

def correlate_data(loss_data, temp_data, temp_range):
    print("correlating by time...")
    line_count= 0
    total_lines= len(temp_data)
    correlated_data = {}
    temp_interval = 15
    for temp_data_point in temp_data: #outer loop is temp data, since there are less entries.
        print("{}%".format(round((line_count/(total_lines-1))*100, 1)), end='\r')
        line_count += 1
        time_index = datetime.strftime(temp_data_point[0], "%d_%H:%M:%S")
        correlated_data[time_index] = []
        for loss_data_point in loss_data:
            if match_time(temp_data_point[0], loss_data_point[0], temp_interval):
                temp_avg = round(mean(temp_data_point[1:]), 1)
                if temp_avg >= temp_range[0] and temp_avg <= temp_range[1]:
                    correlated_point = (temp_avg, loss_data_point[1], loss_data_point[2])
                    correlated_data[time_index].append(correlated_point)
    print('\nmatched {} data points'.format(len(correlated_data)))                
    return correlated_data