# Written by Hoon Seo, seohoon@mines.edu, with MIT license
# Tested on MacOSX, Pycharm, Python 3.6.4

import csv
import copy

# minmax_info = []
########################### Filling Missing value and adjusting length to 70 starts ###########################

def csv_to_raw():
    with open(r'./data/marketData.csv', 'r') as f:
        raw = []
        csvReader = csv.reader(f)
        for line in csvReader:
            raw.append(line)
    return raw

def raw_to_list(raw):
    list = []
    for i in range(len(raw)):
        if int(raw[i][3]) <= int(raw[i][4]):
            min = int(raw[i][3])
        else:
            min = int(raw[i][4])
        price = []
        volume = []
        for j in range(5, 5 + min):
            splited = raw[i][j].split('@')
            if splited[1] == None or splited[1] == 'None':
                price.append(None)
            else:
                price.append(float(splited[1]))
            if splited[2] == None or splited[2] == 'None':
                volume.append(None)
            else:
                volume.append(float(splited[2]))
        list.append([price, volume])
    return list #(n, 2, 70) price, volume

def get_avg(list, sidx, left=True):
    sum = 0.
    num = 0.
    valid = False
    if left:
        for i in range(sidx):
            if(type(list[i])==type(2.) and list[i]>0.):
                valid = True
                sum = sum + list[i]
                num = num + 1.
        if valid:
            return [num, sum/num]
        else:
            return False
    else:
        for i in range(sidx+1, len(list)):
            if (type(list[i]) == type(2.) and list[i]>0.):
                valid = True
                sum = sum + list[i]
                num = num + 1.
        if valid:
            return [num, sum/num]
        else:
            return False

def fill_missing_value_to_list(list):
    result = []
    for i in range(len(list)):
        if(type(list[i]) == type(2.) and list[i]>0.):
            result.append(list[i])
        else:
            left_avg = get_avg(list, i, True)
            right_avg = get_avg(list, i, False)
            if left_avg != False and right_avg != False:
                result.append((left_avg[0]*left_avg[1]+right_avg[0]*right_avg[1])/(left_avg[0]+right_avg[0]))
            elif left_avg == False and right_avg != False:
                result.append(right_avg[1])
            elif left_avg != False and right_avg == False:
                result.append(left_avg[1])
            else:
                return []
    return result

def apply_filling_missing_value(list, no_e = 70):
    result = []
    for i in range(len(list)):
        row = copy.deepcopy(list[i])
        diff = no_e-len(list[i][0]) #70 - ?
        if diff>0:
            all_True = True
            for j in range(len(list[i])):
                if get_avg(list[i][j], len(list[i][j]), True) == False:
                    all_True = False
            if all_True:
                for j in range(diff):
                    for k in range(len(list[i])):
                        row[k].append(get_avg(list[i][k], len(list[i][k]), True))
        elif diff<0:
            for j in range(-diff):
                for k  in range(len(list[i])):
                    row[k].pop()
        for j in range(len(row)):
            row[j] = copy.deepcopy(fill_missing_value_to_list(row[j]))
        any_not_70 = False
        for j in range(len(row)):
            if len(row[j]) != no_e:
                any_not_70 = True
        if not any_not_70:
            result.append(row)
    return result   #(n, 2, 70) price, volume

# result = apply_filling_missing_value(raw_to_list(csv_to_raw()))
# # result = raw_to_list(csv_to_raw())
# for i in result:
#     print('\n')
#     for j in i:
#         print(j)

########################### Normalization Starts ###########################

def minmax_normalization(data, mmrange = None):
    if mmrange == None:
        mmrange = (0., 1.)
    time = []
    for i in range(70):
        time.append(((i + 1.)/70.))
    result = []
    for i in range(len(data)):
        all_same = False
        row = []
        maxi = 1
        mini = 1
        for j in range(len(data[i])):
            column = []
            maxi = float(max(data[i][j]))
            mini = float(min(data[i][j]))
            if maxi == mini:
                all_same = True
                break
            for k in range(len(data[i][j])):
                column.append(float(data[i][j][k] - mini)*(mmrange[1]-mmrange[0])/(maxi-mini) + mmrange[0])
            row.append(column)
        if not all_same:
            # minmax_info.append([mini, maxi])
            row.append(time)
            result.append(row)
    return result   #(n, 3, 70) price, volume, time

def get_data(mmrange = None):
    if mmrange == None:
        mmrange = (0., 1.)
    return minmax_normalization(apply_filling_missing_value(raw_to_list(csv_to_raw())), mmrange)

# result = get_data()
# for i in range(len(result)):
#     print('\n')
#     for j in range(len(result[i])):
#         print(result[i][j])

########################### Preprocessing for data for prediction ###########################

def sample_to_list(sample, start_min = 0, steps = 10):  #start_min = now - listing_time, start_min >= 0 or = current time just
    list = []
    for i in range(len(sample)):
        splited = sample[i].split('@')
        if splited[1] == None or splited[1] == 'None':
            # list.append([None, float(splited[2]), max(0., (10. - start_min - len(sample) + float(i))/70.)])
            list.append([None, float(splited[2]), (10. + start_min - len(sample) + float(i) + 1.) / 70.])
        elif splited[2] == None or splited[2] == 'None':
            # list.append([float(splited[1]), None, max(0., (10. - start_min - len(sample) + float(i))/70.)])
            list.append([float(splited[1]), None, (10. + start_min - len(sample) + float(i) + 1.) / 70.])
        else:
            # list.append([float(splited[1]), float(splited[2]), max(0., (10. - start_min - len(sample) + float(i))/70.)])
            list.append([float(splited[1]), float(splited[2]), (10. + start_min - len(sample) + float(i) + 1.) / 70.])
    return list #(n, 3) price, volume, time

def get_avg_vertical(list, sidx, feature, up=True):
    sum = 0.
    num = 0.
    valid = False
    if up:
        for i in range(sidx):
            if(type(list[i][feature])==type(2.) and list[i][feature]>0.):
                valid = True
                sum = sum + list[i][feature]
                num = num + 1.
        if valid:
            return [num, sum/num]
        else:
            return False
    else:
        for i in range(sidx+1, len(list)):
            if (type(list[i][feature]) == type(2.) and list[i][feature]>0.):
                valid = True
                sum = sum + list[i][feature]
                num = num + 1.
        if valid:
            return [num, sum/num]
        else:
            return False

def apply_fill_missing_value_to_list_vertical(list):
    result = []
    for i in range(len(list)):
        el = []
        for j in range(len(list[i])): #last index indicates time
            if list[i][j] == None or list[i][j] == 0.:
                up_avg = get_avg_vertical(list, i, j, True)
                down_avg = get_avg_vertical(list, i, j, False)
                if up_avg != False and down_avg != False:
                    el.append((up_avg[0] * up_avg[1] + down_avg[0] * down_avg[1]) / (up_avg[0] + down_avg[0]))
                elif up_avg == False and down_avg != False:
                    el.append(down_avg[1])
                elif up_avg != False and down_avg == False:
                    el.append(up_avg[1])
                else:
                    return []
            else:
                el.append(list[i][j])
        result.append(el)
    return result   #(length = 60, 3) price, volume, time

def recover_minmax_scaler(value, min, max, mmrange=None):
    if mmrange == None:
        mmrange = (-1., 1.)
    return (value - mmrange[0])*(max - min)/(mmrange[1]-mmrange[0]) + min

def minmax_normalization_vertical(list, steps = 10, mmrange = None):
    if mmrange == None:
        mmrange = (-1., 1.)
    # diff = len(list) - steps
    price = []
    volume = []
    result = []
    for i in range(len(list)):
        price.append(list[i][0])
        volume.append(list[i][1])
    price_maxi = float(max(price))
    price_mini = float(min(price))
    volume_maxi = float(max(volume))
    volume_mini = float(min(volume))

    if (price_mini != price_maxi and volume_mini != volume_maxi):
        for i in range(len(list)-steps, len(list)):
            result.append([(list[i][0]-price_mini)*(mmrange[1]-mmrange[0])/(price_maxi-price_mini) + mmrange[0], (list[i][1]-volume_mini)*(mmrange[1]-mmrange[0])/(volume_maxi-volume_mini) + mmrange[0], list[i][2]])
    elif price_mini == price_maxi and volume_mini == volume_maxi:
        for i in range(len(list)-steps, len(list)):
            result.append([0., 0., list[i][2]])
    elif price_mini == price_maxi and volume_mini != volume_maxi:
        for i in range(len(list)-steps, len(list)):
            result.append([0., (list[i][1]-volume_mini)*(mmrange[1]-mmrange[0])/(volume_maxi-volume_mini) + mmrange[0], list[i][2]])
    elif price_mini != price_maxi and volume_mini == volume_maxi:
        for i in range(len(list)-steps, len(list)):
            result.append([(list[i][0]-price_mini)*(mmrange[1]-mmrange[0])/(price_maxi-price_mini) + mmrange[0], 0., list[i][2]])



    # if diff<0:
    #     for i in range(-diff):
    #         # result[:0] = [[get_avg_vertical(result, len(result), 0, True), get_avg_vertical(result, len(result), 1, True), result[-1][2]+1.]]
    #         result.insert(0, [get_avg_vertical(result, len(result), 0, True), get_avg_vertical(result, len(result), 1, True), result[-1][2]+1.])
    # elif diff>0:
    #     for i in range(diff):
    #         result.pop(0)

    return (result, price_maxi, price_mini, volume_maxi, volume_mini, mmrange)   #result = (n = 10, 3) price, volume, time

def get_data_for_prediction(sample, start_min = 0, steps = 10, mmrange = None):
    if mmrange == None:
        mmrange = (-1., 1.)
    return minmax_normalization_vertical(apply_fill_missing_value_to_list_vertical(sample_to_list(sample, start_min = start_min, steps = steps)), steps, mmrange)

