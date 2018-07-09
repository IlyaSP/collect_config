#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import pexpect
import time
import hashlib
import datetime
import sqlite3
import socket
import threading
import queue
import sys

SSH_NEWKEY = r'Are you sure you want to continue connecting \(yes/no\)\?'
error_authen = "Permission denied"
error = "Error"

path_to_db = r"/home/admin/collect_config/db.sqlite3"
start = datetime.datetime.now()
print("\n========================================\r\n"
      "{0}\r\n"
      "===========================================\n".format(start))


def connect_to_DB(path_to_db):
    try:
        con = sqlite3.connect(path_to_db, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

    except sqlite3.Error as e:
        print("Error connect to DB: {0}".format(e))
    return con


def TcpConnect(ip, hostname, telnet_port=23, ssh_port=22):
    """Check availability telnet or ssh"""
    # print("Start check available device port 22-23")
    session = socket.socket()
    session.settimeout(2)
    result = session.connect_ex((ip, ssh_port))
    session.close()
    # print("Result connect SSH {0}".format(result))
    if result == 0:
        # print('protocol SSH')
        protocol = 'SSH'
    else:
        session = socket.socket()
        session.settimeout(2)
        result = session.connect_ex((ip, telnet_port))
        session.close()
        # print("Result connect Telnet {0}".format(result))
        if result == 0:
            # print('protocol telnet')
            protocol = 'Telnet'
        else:
            print('Device {0} - {1} unreachable'.format(ip, hostname))
            protocol = 'Unknown'
    return protocol


def collect_config_cisco(ip, user, password, enable_pass, protocol, hostname):
    if protocol == "SSH":
        # print("Connect to {0} - {1}".format(hostname, ip))
        ssh = pexpect.spawn("ssh {0}@{1}".format(user, ip))
        ssh.timeout = 15
        i = ssh.expect([pexpect.TIMEOUT, SSH_NEWKEY, "[Pp]assword:", pexpect.EOF])
        if i == 0:
            print("TIMEOUT to {0} - {1}".format(ip, hostname))
            return error
        elif i == 1:
            print("accept key ssh for {0} - {1}".format(ip, hostname))
            ssh.sendline("yes")
            ssh.expect("[Pp]assword:")
            ssh.sendline(password)
        elif i == 2:
            ssh.sendline(password)
        elif i == 3:
            print("EOF Error for {0} - {1}".format(ip, hostname))
            return error

        time.sleep(0.1)
        i = ssh.expect(["#", ">", "[Pp]assword:", error_authen])
        if i == 0:
            ssh.sendline("terminal len 0")
            ssh.expect("#")
            time.sleep(0.1)
            ssh.sendline("show running-config")
            time.sleep(0.1)
            ssh.expect("#")
            config = ssh.before.decode("utf-8")
            return config
        elif i == 1:
            ssh.sendline("enable")
            time.sleep(0.1)
            ssh.expect("[Pp]assword:")
            ssh.sendline(enable_pass)
            ii = ssh.expect(["#", "[Pp]assword:"])
            if ii == 0:
                ssh.sendline("terminal len 0")
                ssh.expect("#")
                time.sleep(0.1)
                ssh.sendline("show running-config")
                time.sleep(0.1)
                ssh.expect("#")
                config = ssh.before.decode("utf-8")
                return config
            else:
                print("Bad enable password for {0} - {1}".format(ip, hostname))
                return error
        elif i == 2:
            print("Bad login or password for {0} - {1}".format(ip, hostname))
            return error

    elif protocol == "Telnet":
        # print("Connect to {0} - {1}".format(hostname, ip))
        telnet = pexpect.spawn("telnet {0}".format(ip))
        telnet.timeout = 15
        i = telnet.expect([pexpect.TIMEOUT, "[Uu]sername:", pexpect.EOF])
        if i == 0:
            print("TIMEOUT to {0} - {1}".format(ip, hostname))
            return error
        elif i == 1:
            telnet.sendline(user)
            telnet.expect("[Pp]assword:")
            telnet.sendline(password)
        elif i == 2:
            print("EOF Error for {0} - {1}".format(ip, hostname))
            return error

        time.sleep(0.1)
        i = telnet.expect(["#", ">", r"% Login invalid", error_authen])
        if i == 0:
            telnet.sendline("terminal len 0")
            telnet.expect("#")
            # print(ssh.before.decode("utf-8"), ssh.after.decode("utf-8"))
            time.sleep(0.1)
            telnet.sendline("show running-config")
            time.sleep(0.1)
            telnet.expect("#")
            config = telnet.before.decode("utf-8")
            return config
        elif i == 1:
            telnet.sendline("enable")
            time.sleep(0.1)
            telnet.expect("[Pp]assword:")
            telnet.sendline(enable_pass)
            ii = telnet.expect(["#", "[Pp]assword:"])
            if ii == 0:
                telnet.sendline("terminal len 0")
                telnet.expect("#")
                time.sleep(0.1)
                telnet.sendline("show running-config")
                time.sleep(0.1)
                telnet.expect("#")
                config = telnet.before.decode("utf-8")
                return config
            else:
                print("Bad enable password for {0} - {1}".format(ip, hostname))
                return error
        elif i == 2:
            print("Bad login or password for {0} - {1}".format(ip, hostname))
            return error


def collect_config_juniper(ip, user, password, protocol, hostname):
    if protocol == "SSH":
        # print("Connect to {0} - {1}".format(hostname, ip))
        ssh = pexpect.spawn("ssh {0}@{1}".format(user, ip))
        ssh.timeout = 15
        i = ssh.expect([pexpect.TIMEOUT, SSH_NEWKEY, "[Pp]assword:", pexpect.EOF])
        if i == 0:
            print("TIMEOUT to {0} - {1}".format(ip, hostname))
            return error
        elif i == 1:
            print("accept key ssh for {0} - {1}".format(ip, hostname))
            ssh.sendline("yes")
            ssh.expect("[Pp]assword:")
            ssh.sendline(password)
        elif i == 2:
            ssh.sendline(password)
        elif i == 3:
            print("EOF Error for {0} - {1}".format(ip, hostname))
            return error

        time.sleep(1)
        ssh.sendline("\n")
        i = ssh.expect(["%", ">", "[Pp]assword:"])
        if i == 0:
            ssh.sendline("cli")
            ssh.expect(">")
            # print(ssh.before.decode("utf-8"), ssh.after.decode("utf-8"))
            ssh.sendline("set cli screen-length 0")
            time.sleep(0.1)
            ssh.expect(">")
            ssh.sendline("show configuration")
            time.sleep(0.1)
            ssh.expect(">")
            config = ssh.before.decode("utf-8")
            return config
        elif i == 1:
            ssh.sendline("set cli screen-length 0")
            time.sleep(0.1)
            ssh.expect(">")
            ssh.sendline("show configuration")
            time.sleep(0.1)
            ssh.expect(">")
            config = ssh.before.decode("utf-8")
            return config
        elif i == 2:
            print("Bad login or password for {0} - {1}".format(ip, hostname))
            return error


def get_hash_config(config):
    hash_new = hashlib.sha256(config.encode('ascii')).hexdigest()
    return hash_new


def get_oldhash_current_number_configs(device_id, path_to_db):
     con = connect_to_DB(path_to_db)
     cur = con.cursor()
     cur.execute('SELECT id, hash_config, date_added FROM collect_configs_config '
                           'WHERE device_id = ? ORDER BY date_added DESC', (str(device_id),))
     configs = cur.fetchall()
     cur.close()
     con.close()
     return configs


def insert_config_db(device_id, hash_new, config, ip, hostname):
    con = connect_to_DB(path_to_db)
    cur = con.cursor()
    date_added = datetime.datetime.now()
    param = (config, hash_new, date_added, str(device_id))
    cur.execute('INSERT INTO collect_configs_config(config, hash_config, date_added, device_id) VALUES (?, ?, ?, ?)',
                param)

    cur.close()
    con.commit()
    con.close()
    msg = "= Config for {0} - {1} has been added =".format(hostname, ip)
    print(msg)
    return msg


def update_config_db(config, id_string, hash_new, ip, hostname):
    con = connect_to_DB(path_to_db)
    cur = con.cursor()
    date_added = datetime.datetime.now()
    cur.execute('UPDATE collect_configs_config SET config = ?, hash_config = ?, date_added = ? WHERE Id = ?',
                (config, hash_new, date_added, id_string))
    cur.close()
    con.commit()
    con.close()
    msg = "= Config for {0} - {1} has been updated =".format(hostname, ip)
    print(msg)
    return msg


def get_config(work_queue):
    while True:
        # Если заданий нет - закончим цикл
        if work_queue.empty():
            sys.exit()
        # Получаем задание из очереди
        i = work_queue.get()
        # print('DEVICE: ', i)
        #  разделяя строку по ";"
        data = i.split(";")
        device_id = data[0]
        ip = data[1]
        user = data[2]
        password = data[3]
        enable_pass = data[4]
        vendor = data[5]
        max_configs = int(data[6])
        hostname = data[7]
        protocol = TcpConnect(ip, hostname, telnet_port=23, ssh_port=22)
        if vendor == "Cisco":
            config = collect_config_cisco(ip, user, password, enable_pass, protocol, hostname)
        elif vendor == "Juniper":
            config = collect_config_juniper(ip, user, password, protocol, hostname)
        hash_new = get_hash_config(config)
        configs = get_oldhash_current_number_configs(device_id, path_to_db)
        if len(configs) > 0:
            hash_old = configs[0][1]
        else:
            pass
        if len(configs) == 0:
            print("Device {0} - {1} has no configuration".format(hostname, ip))
            insert_config_db(device_id, hash_new, config, ip, hostname)
        elif len(configs) < max_configs:
            if hash_new == hash_old:
                print("Config device {0} - {1} was not change".format(hostname, ip))
            else:
                insert_config_db(device_id, hash_new, config, ip, hostname)
        elif len(configs) == max_configs:
            if hash_new == hash_old:
                print("Config device {0} - {1} was not change".format(hostname, ip))
            else:
                id_string = configs[len(configs) - 1][0]
                update_config_db(config, id_string, hash_new, ip, hostname)
        else:
            print("The number of configurations for {0} - {1} exceeds the limit in {2} configurations".format(hostname, ip,
                                                                                                          max_configs))
        # Сообщаем о выполненном задании
        work_queue.task_done()
        # print(u'Очередь: %s завершилась' % i)


con = connect_to_DB(path_to_db)
cur = con.cursor()
cur.execute('SELECT id, ip, username, password, enable_pass, vendor_or_os, max_number_cofigs, hostname '
            'FROM collect_configs_device WHERE status = "OK" AND vendor_or_OS '
            'IN ("Cisco", "Juniper", "cisco", "juniper")')
res = cur.fetchall()
cur.close()
con.close()

print("Number of devices: {0}".format(len(res)))
work_queue = queue.Queue() # Создаем FIFO очередь
for i in res:
    # print(i)
    device_id = i[0]
    ip = i[1]
    user = i[2]
    password = i[3]
    enable_pass = i[4]
    vendor = i[5]
    max_configs = int(i[6])
    hostname = i[7]
    """Заполняем очеред строками, состоящими из  device_id, ip, user, password, enable_pass, vendor, max_config, 
    hostname"""
    work_queue.put('{0};{1};{2};{3};{4};{5};{6};{7}'.format(device_id, ip, user, password, enable_pass, vendor,
                                                            max_configs, hostname))

# Создаем и запускаем потоки, которые будут обслуживать очередь
for i in range(47):
    t1 = threading.Thread(target=get_config, args=(work_queue,))
    t1.setDaemon(True)
    t1.start()
    time.sleep(0.01)


work_queue.join()  # Ставим блокировку до тех пор пока не будут выполнены все задания


end = datetime.datetime.now()
print("Lead time: {0}".format(end - start))