#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import sqlite3
import re
from pysnmp.entity.rfc3413.oneliner import cmdgen
import datetime
import threading
import queue
import time
import sys


path_to_db = r"/home/admin/collect_config/db.sqlite3"
start = datetime.datetime.now()
print("\n========================================\r\n"
      "{0}\r\n"
      "===========================================\n".format(start))


def get_extensive_info_device(vendor, sysDescr, community, ip):
    """Функция для получения серийного номера, типа шасси, хостнэйма по snmp"""
    if vendor == "Cisco" or vendor == "cisco":
        chassis = re.findall(r'\(\w+-', str(sysDescr))[0][1:-1]
        cmdGen = cmdgen.CommandGenerator()
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
            cmdgen.CommunityData(community),
            cmdgen.UdpTransportTarget((ip, 161)), '1.3.6.1.2.1.47.1.1.1.1.11.1', '1.3.6.1.2.1.1.5.0')
        # print("extensive info: \nip = {0}, community = {1}, \nvarBinds = {2}".format(ip, community, varBinds))
        if len(varBinds[0][1]) != 0:
            SN = varBinds[0][1]
        else:
            SN = "Unknow"
        if len(varBinds[1][1]) != 0:
            hostname = varBinds[1][1]
        else:
            hostname = "Unknow"
    elif vendor == "Linux" or vendor == "linux":
        chassis = "Unknow"
        SN = "Unknow"
        cmdGen = cmdgen.CommandGenerator()
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
            cmdgen.CommunityData(community),
            cmdgen.UdpTransportTarget((ip, 161)), '1.3.6.1.2.1.1.5.0')
        if len(varBinds[0][1]) != 0:
            hostname = varBinds[0][1]
        else:
            hostname = "Unknow"
    elif vendor == "Juniper" or vendor == "juniper":
        cmdGen = cmdgen.CommandGenerator()
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
            cmdgen.CommunityData(community),
            cmdgen.UdpTransportTarget((ip, 161)), '1.3.6.1.2.1.1.5.0', '1.3.6.1.4.1.2636.3.1.2.0',
            '1.3.6.1.4.1.2636.3.1.3.0')
        if len(varBinds[0][1]) != 0:
            hostname = varBinds[0][1]
        else:
            hostname = "Unknow"
        if len(varBinds[1][1]) != 0:
            chassis = varBinds[1][1]
        else:
            chassis = "Unknow"
        if len(varBinds[2][1]) != 0:
            SN = varBinds[2][1]
        else:
            SN = "Unknow"
    else:
        chassis = "Unknow"
        hostname = "Unknow"
        SN = "Unknow"
    return chassis, SN, hostname


def get_full_name_OS(vendor, sysDescr):
    """ Функция для получения версии ПО из системного дискрипшена"""
    if vendor == "Cisco" or vendor == "cisco":
        full_os = re.findall(r'\(\w+-\w+-\w+\), Version \d+.\w+\(\w+\)\w*', str(sysDescr))[0]
    elif vendor == "Linux" or vendor == "linux":
        full_os = re.findall(r'\d+.\d+.\d+-\d+-\w+.*', str(sysDescr))[0]
    elif vendor == "Juniper" or vendor == "Juniper":
        full_os = re.findall(r'\d+.\d+X\d+-\w+.\d+', str(sysDescr))[0]
    else:
        full_os = "Unknow"
    return full_os


def get_snmp_DevInfo(work_queue):
    """get system description deviice"""
    while True:
        # Если заданий нет - закончим цикл
        if work_queue.empty():
            sys.exit()
        # Получаем задание из очереди
        i = work_queue.get()
        # print('DEVICE: ', i)
        # из строки вида xx.xx.xx.xx;public;11 получаем массив в котором содержится ip adress, community, device id
        #  разделяя строку по ";"
        data = i.split(";")
        ip = data[0]
        community = data[1]
        device_id = data[2]
        cmdGen = cmdgen.CommandGenerator()
        # print('community, ip = ' + str(community) + ' ' + str(ip) + '\r')
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.nextCmd(
            cmdgen.CommunityData(community),
            cmdgen.UdpTransportTarget((ip, 161)), '.1.3.6.1.2.1.1.1', '.1.3.6.1.2.1.1.5')
        # print("\nGet snmp \r")
        if len(varBinds) == 0:
            vendor = "Unknown"
            full_os = "Unknown"
            chassis = "Unknown"
            SN = "Unknown"
            hostname = "Unknown"
        elif len(varBinds) != 1:
            vendor = "Unknown"
            full_os = "Unknown"
            chassis = "Unknown"
            SN = "Unknown"
            hostname = "Unknown"
        else:
            if re.search(r"[Cc]isco|[Ll]inux|[Jj]uniper", str(varBinds[0][0][1])) is not None:
                vendor = re.search(r"[Cc]isco|[Ll]inux|[Jj]uniper", str(varBinds[0][0][1])).group(0)
                sysDescr = varBinds[0][0][1]
                full_os = get_full_name_OS(vendor, sysDescr)
                chassis, SN, hostname = get_extensive_info_device(vendor, sysDescr, community, ip)
            else:
                vendor = "Unknown"
                full_os = "Unknown"
                chassis = "Unknown"
                SN = "Unknown"
                hostname = "Unknown"
        # print("vendor = {0} \nfull_OS = {1} \nchassis = {2} \nSN = {3}"
            # "\nhostname = {4}".format(vendor, full_os, chassis, SN, hostname))

        """ Для каждого потока требуется свое подключение к базе, нельязя использовать одно подключения,
        которое создано ранее"""
        try:
            con = sqlite3.connect(path_to_db, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
            # print('Connect sucess')
        except sqlite3.Error as e:
            print("Error connect to DB: {0}".format(e))

        cur = con.cursor()
        cur.execute('UPDATE collect_configs_device SET vendor_or_OS = ?, soft_version= ?, model = ?, sn = ?, hostname =? WHERE Id = ?',
        (str(vendor), str(full_os), str(chassis), str(SN), str(hostname), str(device_id)))
        con.commit()
        con.close()
        # Сообщаем о выполненном задании
        work_queue.task_done()
        # print(u'Очередь: %s завершилась' % i)


try:
    con = sqlite3.connect(path_to_db, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    # print('Connect to DB sucess')
except sqlite3.Error as e:
    print("Error connect to DB: {0}".format(e))


cur = con.cursor()
cur.execute('SELECT * FROM collect_configs_device WHERE status = "OK"')
res = cur.fetchall()
# print(res)
con.close()
work_queue = queue.Queue() # Создаем FIFO очередь


for i in res:
    print('\r============== {0} - {1} - {2} - {3}==================='.format(i[0], i[1], i[8], i[10]))
    # print(i[0], i[1], i[8], i[10])
    community = i[8]
    ip = i[1]
    device_id = int(i[0])
    vendor_or_os = i[10]
    status = i[11]
    """Заполняем очеред строками, состоящими из  ip, community, device_id"""
    work_queue.put('{0};{1};{2}'.format(ip, community, device_id))



# Создаем и запускаем потоки, которые будут обслуживать очередь
for i in range(7):
    # print(u'Поток', str(i), u'стартовал')
    # print("kolichestvo activnyh potokov: ", threading.activeCount())
    t1 = threading.Thread(target=get_snmp_DevInfo, args=(work_queue,))
    t1.setDaemon(True)
    t1.start()
    time.sleep(0.1)


work_queue.join()  # Ставим блокировку до тех пор пока не будут выполнены все задания

end = datetime.datetime.now()
print("Lead time: {0}".format(end-start))
