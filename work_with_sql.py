#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import sqlite3
from pysnmp.entity.rfc3413.oneliner import cmdgen
import datetime


path_to_db = r"/home/admin/collect_config/db.sqlite3"
start = datetime.datetime.now()
print("\n========================================\r\n"
      "{0}\r\n"
      "===========================================\n".format(start))


try:
    con = sqlite3.connect(path_to_db, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    # print('Connect sucess')
    # print(con)

except sqlite3.Error as e:
    print("Error connect to DB: {0}".format(e))

cur = con.cursor()
cur.execute('''select * from sqlite_master''')
l = cur.fetchall()


def get_snmp_linux(community, ip):
    """get information snmp for linux"""
    # print("Get snmp for linux\n")
    cmdGen = cmdgen.CommandGenerator()
    # print('community, ip = ' + str(community) + ' ' + str(ip))
    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((ip, 161)), '1.3.6.1.4.1.2021.10.1.3.1',
        '1.3.6.1.4.1.2021.10.1.3.2')

    # print('varBind= ' + str(varBinds) + '\n')
    if varBinds == []:
        s = [0, 0]
    else:
        s = []
        for i in varBinds:
            a = str(i)
            # print(a.find(r'No Such'))
            if a.find('No Such') == -1:
                s.append(int(float(a[a.find('=') + 2:]) * 100))
            else:
                s.append(0)
    return (s)


def get_snmp_Cisco(community, ip):
    """get information snmp for Cisco"""
    # print("Get snmp for Cisco\n")
    cmdGen = cmdgen.CommandGenerator()
    # print('community, ip = ' + str(community) + ' ' + str(ip))
    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((ip, 161)), '1.3.6.1.4.1.9.2.1.57.0 ', '1.3.6.1.4.1.9.2.1.58.0')
    if varBinds == []:
        s = [0, 0]
    else:
        s = []
        for i in varBinds:
            # print(i)
            a = str(i)
            if a.find('No Such ') == -1:
                s.append(int(a[a.find('=') + 2:]))
            else:
                s.append(0)
        # print('s = ' + str(s))

    # print('s = ' + str(s))
    return (s)


def get_snmp_juniper(community, ip):
    """get information snmp for Juniper"""
    # print("Get snmp for Juniper\n")
    cmdGen = cmdgen.CommandGenerator()
    # print('community, ip = ' + str(community) + ' ' + str(ip))
    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((ip, 161)), '.1.3.6.1.4.1.2636.3.1.13.1.8.9.1.0.0',
        '.1.3.6.1.4.1.2636.3.1.13.1.8.9.1.0.0')
    if varBinds == []:
        s = [0, 0]
    else:
        s = []
        for i in varBinds:
            # print(i)
            a = str(i)
            if a.find('No Such ') == -1:
                s.append(int(a[a.find('=') + 2:]))
            else:
                s.append(0)
        # print('s = ' + str(s))

    # print('s = ' + str(s))
    return (s)


def insert_data_databese(load_1m, load_5m):
    date_added = datetime.datetime.now()
    # print('date_added', date_added)
    params = (load_1m, load_5m, date_added, device_id)
    cur.execute(
        'INSERT INTO collect_configs_statisticsdevice(cpu_utilization_1min, cpu_utilization_5min, date_added, device_id) VALUES (?, ?, ?, ?)',
        params)
    con.commit()
    # print(cur.lastrowid)


def update_data_in_database(id_string, load_1m, load_5m):
    date_added = datetime.datetime.now()
    cur.execute(
        'UPDATE collect_configs_statisticsdevice SET cpu_utilization_1min = ?, cpu_utilization_5min = ?,'
        ' date_added = ? WHERE Id = ?',
        (load_1m, load_5m, date_added, id_string)
    )
    con.commit()


cur.execute('SELECT * FROM collect_configs_device WHERE status = "OK"')
res = cur.fetchall()
# print(res)
print("Number of devices: {0}".format(len(res)))
for i in res:
    # print(i[0], i[1], i[8], i[10])
    community = i[8]
    ip = i[1]
    device_id = int(i[0])
    vendor_or_OS = i[10]
    old_status = i[11]
    # print(' -- = {0} =---= {1} =--- Status = {2}= --'.format(str(vendor_or_OS), str(ip), str(old_status)))
    if vendor_or_OS == 'Linux':
        # print('- device_id = {0}; ip = {1}; Vendor ={2} ---'.format(str(device_id), str(ip), str(vendor_or_OS)))
        cur.execute('SELECT * FROM collect_configs_statisticsdevice WHERE device_id = ? ORDER BY date_added DESC',
                    (str(device_id),))
        l = cur.fetchall()
        # print("+++++++ sum string for device = {0} +++++++++".format(len(l)))
        if len(l) < 2:
            # print('-----------------l < 2----------------------------------')
            load_1m, load_5m = get_snmp_linux(community, ip)
            # print('load_1m = ' + str(load_1m), load_5m)
            insert_data_databese(load_1m, load_5m)
            # print('------------------- END l < 2 ---------------------------------------')
            print("====== Data for {0} was added =======".format(ip))
        else:
            # print('------------------- l > 2 -------------------------------------------')
            delta = datetime.datetime.strptime(l[0][4], "%Y-%m-%d %H:%M:%S.%f") - datetime.datetime.strptime(
                l[len(l) - 1][4], "%Y-%m-%d %H:%M:%S.%f")
            # print("---------------------- Delta in seconds = {0}--------------------".format(delta.total_seconds()))
            if delta.total_seconds() >= 7200:
                # print('-------------- Time is up -------------------')
                id_string = int(l[len(l) - 1][0])
                 #print('------ Id string for update: {0} ---------------'.format(str(id_string)))
                load_1m, load_5m = get_snmp_linux(community, ip)
                update_data_in_database(id_string, load_1m, load_5m)
                # print('--------------------- END l > 2(Time is up) -------------------------------------')
                print("====== Data for {0} was updated =======".format(ip))
            else:
                # print('---------------------------- The time has not yet expired -----------------------')
                load_1m, load_5m = get_snmp_linux(community, ip)
                insert_data_databese(load_1m, load_5m)
                # print('----------------- END (The time has not yet expired)-----------------------------')
                print("====== Data for {0} was added =======".format(ip))
    elif vendor_or_OS == 'Cisco':
        # print('- device_id = {0}; ip = {1}; Vendor ={2} ---'.format(str(device_id), str(ip), str(vendor_or_OS)))
        cur.execute('SELECT * FROM collect_configs_statisticsdevice WHERE device_id = ? ORDER BY date_added DESC',
                    (str(device_id),))
        l = cur.fetchall()
        # print("+++++++ sum string for device = {0} +++++++++".format(len(l)))
        if len(l) < 2:
            # print('-----------------l < 2----------------------------------')
            load_1m, load_5m = get_snmp_Cisco(community, ip)
            # print('load_1m = ' + str(load_1m), load_5m)
            insert_data_databese(load_1m, load_5m)
            # print('------------------- END l < 2 ---------------------------------------')
            print("====== Data for {0} was added =======".format(ip))
        else:
            # print('------------------- l > 2 -------------------------------------------')
            delta = datetime.datetime.strptime(l[0][4], "%Y-%m-%d %H:%M:%S.%f") - datetime.datetime.strptime(
                l[len(l) - 1][4], "%Y-%m-%d %H:%M:%S.%f")
            # print("---------------------- Delta in seconds = {0}--------------------".format(delta.total_seconds()))
            if delta.total_seconds() >= 7200:
                # print('-------------- Time is up -------------------')
                id_string = int(l[len(l) - 1][0])
                # print('------ Id string for update: {0} ---------------'.format(str(id_string)))
                load_1m, load_5m = get_snmp_Cisco(community, ip)
                update_data_in_database(id_string, load_1m, load_5m)
                # print('--------------------- END l > 2(Time is up) -------------------------------------')
                print("====== Data for {0} was updated =======".format(ip))
            else:
                # print('---------------------------- The time has not yet expired -----------------------')
                load_1m, load_5m = get_snmp_Cisco(community, ip)
                insert_data_databese(load_1m, load_5m)
                # print('----------------- END (The time has not yet expired)-----------------------------')
                print("====== Data for {0} was added =======".format(ip))
    elif vendor_or_OS == 'Juniper':
        # print('- device_id = {0}; ip = {1}; Vendor ={2} ---'.format(str(device_id), str(ip), str(vendor_or_OS)))
        cur.execute('SELECT * FROM collect_configs_statisticsdevice WHERE device_id = ? ORDER BY date_added DESC',
                    (str(device_id),))
        l = cur.fetchall()
        # print("+++++++ sum string for device = {0} +++++++++".format(len(l)))
        if len(l) < 2:
            # print('-----------------l < 2----------------------------------')
            load_1m, load_5m = get_snmp_juniper(community, ip)
            # print('load_1m = ' + str(load_1m), load_5m)
            insert_data_databese(load_1m, load_5m)
            # print('------------------- END l < 2 ---------------------------------------')
            print("====== Data for {0} was added =======".format(ip))
        else:
            # print('------------------- l > 2 -------------------------------------------')
            delta = datetime.datetime.strptime(l[0][4], "%Y-%m-%d %H:%M:%S.%f") - datetime.datetime.strptime(
                l[len(l) - 1][4], "%Y-%m-%d %H:%M:%S.%f")
            # print("---------------------- Delta in seconds = {0}--------------------".format(delta.total_seconds()))
            if delta.total_seconds() >= 7200:
                # print('-------------- Time is up -------------------')
                id_string = int(l[len(l) - 1][0])
                # print('------ Id string for update: {0} ---------------'.format(str(id_string)))
                load_1m, load_5m = get_snmp_juniper(community, ip)
                update_data_in_database(id_string, load_1m, load_5m)
                # print('--------------------- END l > 2(Time is up) -------------------------------------')
                print("====== Data for {0} was updated =======".format(ip))
            else:
                # print('---------------------------- The time has not yet expired -----------------------')
                load_1m, load_5m = get_snmp_juniper(community, ip)
                insert_data_databese(load_1m, load_5m)
                # print('----------------- END (The time has not yet expired)-----------------------------')
                print("====== Data for {0} was added =======".format(ip))
cur.close()
con.close()

end = datetime.datetime.now()
print("Lead time: {0}".format(end-start))
