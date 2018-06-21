# -*- coding: utf-8 -*-

import sqlite3
import datetime
import socket
import threading
import queue
import time
import sys

start = datetime.datetime.now()
print(start, "\n")


def TcpConnect(ip, telnet_port=23, ssh_port=22):
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


def update_data_in_database(device_id, old_status, status):
    date_added = datetime.datetime.now()
    """ Для каждого потока требуется свое подключение к базе, нельязя использовать одно подключения,
        которое создано ранее"""

    if status != old_status:
        try:
            con = sqlite3.connect('/home/ilya/collect_config/db.sqlite3',
                                 detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
            print('Connect sucess')
        except sqlite3.Error as e:
            print(e)

        cur = con.cursor()
        cur.execute(
                    'UPDATE collect_configs_device SET status = ?, date_last_change_state = ? WHERE Id = ?',
            (status, date_added, device_id)
                    )
        con.commit()
        print(cur.lastrowid)
        con.close()
    else:
        pass


def check_status_device(work_queue):
    """Device status check"""
    while True:
        # Если заданий нет - закончим цикл
        if work_queue.empty():
            sys.exit()
        # Получаем задание из очереди
        i = work_queue.get()
        print('DEVICE: ', i)
        # из строки вида xx.xx.xx.xx;11;OK получаем массив в котором содержится ip adress, device id, OK
        # разделяя строку по ";"
        data = i.split(";")
        ip = data[0]
        device_id = int(data[1])
        old_status = data[2]
        status = TcpConnect(ip, telnet_port=23, ssh_port=22)
        update_data_in_database(device_id, old_status, status)
        # Сообщаем о выполненном задании
        work_queue.task_done()
        print(u'Очередь: %s завершилась' % i)


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
con.close()


work_queue = queue.Queue()    # Создаем FIFO очередь


for i in res:
    print('\n============== {0} - {1} - {2} - {3} ==================='.format(i[0], i[1], i[10], i[11]))
    ip = i[1]
    device_id = int(i[0])
    old_status = i[11]
    """Заполняем очеред строками, состоящими из  ip, device_id, old_status"""
    work_queue.put('{0};{1};{2}'.format(ip, device_id, old_status))


# Создаем и запускаем потоки, которые будут обслуживать очередь
for i in range(7):
    print(u'Поток', str(i), u'стартовал')
    # print("kolichestvo activnyh potokov: ", threading.activeCount())
    t1 = threading.Thread(target=check_status_device, args=(work_queue,))
    t1.setDaemon(True)
    t1.start()
    time.sleep(0.01)


work_queue.join()  # Ставим блокировку до тех пор пока не будут выполнены все задания

end = datetime.datetime.now()
print('Lead time: '.format(end - start))
