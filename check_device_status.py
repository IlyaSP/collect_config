# -*- coding: utf-8 -*-

import sqlite3
import datetime
import socket
import telnetlib
import paramiko

start = datetime.datetime.now()
print(start, "\n")

def TcpConnect(ip, telnet_port=23, ssh_port=22, timeout=10):
    """Check availability telnet or ssh"""
    print("Start check available device port22-23")
    session = socket.socket()
    session.settimeout(3)
    result = session.connect_ex((ip, ssh_port))
    session.close()
    print(result)
    if result == 0:
        print('Start SSH')
        status = 'OK'
    else:
        session = socket.socket()
        session.settimeout(3)
        result = session.connect_ex((ip, telnet_port))
        session.close()
        print(result)
        if result == 0:
            print('Start Telnet')
            status = 'OK'
        else:
            print('Device unreachable')
            status = 'Unreachable'
    return status


try:
    con = sqlite3.connect('/home/ilya/collect_config/db.sqlite3',
                          detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    print('Connect sucess')
    print(con)

except sqlite3.Error as e:
    print(e)

cur = con.cursor()
cur.execute('SELECT * FROM collect_configs_device')
res = cur.fetchall()

for i in res:
    print('\n============== {0} - {1} - {2} - {3} ==================='.format(i[0], i[1], i[10], i[11]))

