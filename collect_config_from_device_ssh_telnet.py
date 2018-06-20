import sqlite3
import re
import netsnmp
from pysnmp.entity.rfc3413.oneliner import cmdgen
import datetime
import time
import socket
import telnetlib
import paramiko
import hashlib

try:
    con = sqlite3.connect('/home/ilya/collect_config/db.sqlite3', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    print('Connect sucess')
    print(con)

except sqlite3.Error as e:
    print(e)

def TelnetConnectCisco(ip, user, password, enable_pass):
    '''Connect Connection on port 23. Configuration collection'''
    t = telnetlib.Telnet(ip)
    res_u = t.expect([b"Username:"], timeout=3)
    if res_u[0] == 0:
        t.write(user.encode('ascii') + b"\n")
        time.sleep(3)
        res_p = t.expect([b'Password:'], timeout=3)
        if res_p[0] == 0:
            t.write(password.encode('ascii') + b"\n")
            time.sleep(3)
            res_p_inc = t.expect(([b'\r\n% Login invalid']), timeout=3)
            if res_p_inc[0] == -1:
                t.write(b"\n")
                res_en = t.expect([b'>'], timeout=1)
                if res_en[0] == 0:
                    t.write(b'enable \n')
                    t.write(enable_pass.encode('ascii') + b'\n')
                    time.sleep(3)
                    res_en = t.expect([b'#'], timeout=3)
                    if res_en[0] == 0:
                        t.write(b'terminal length 0\n')
                        t.write(b'show run \n')
                        time.sleep(11)
                        t.write(b'exit \n')
                        time.sleep(3)
                        a = t.read_very_eager().decode('utf-8')
                        if a.find('!\r\n!\r\nend') == -1:
                            print('The configuration is incomplete')
                            msg = ' Device:' + ip + ' configuration is incomplete' + '\n'
                            conf, h = ' ', ' '

                        else:
                            print('end conf: ' + str(a.find('!\r\n!\r\nend')))
                            conf = a[a.find('terminal len 0') + 17:a.find('!\r\n!\r\nend') + 9]
                            h = hashlib.sha256(conf.encode('ascii')).hexdigest()
                            print('Configuration saved')
                            msg = ' Device:' + ip + ' configuration saved' + '\n'

                    else:
                        print("Enable password incorrect")
                        msg = ' The device:' + ip + ' enable password is incorrect' + '\n'
                        conf, h = ' ', ' '

                else:
                    t.write(b'\n')
                    t.write(b'terminal length 0\n')
                    t.write(b'show run \n')
                    time.sleep(11)
                    t.write(b'exit \n')
                    time.sleep(3)
                    a = t.read_very_eager().decode('utf-8')
                    if a.find('!\r\n!\r\nend') == -1:
                        print('The configuration is incomplete')
                        msg = ' Device:' + ip + ' configuration is incomplete' + '\n'
                        conf, h = ' ', ' '

                    else:
                        print('end conf: ' + str(a.find('!\r\n!\r\nend')))
                        conf = a[a.find('terminal length 0') + 17:a.find('!\r\n!\r\nend') + 9]
                        conf = a[a.find('terminal len 0') + 17:a.find('!\r\n!\r\nend') + 9]
                        h = hashlib.sha256(conf.encode('ascii')).hexdigest()
                        print('Configuration saved')
                        msg = ' Device:' + ip + ' configuration saved' + '\n'

            else:
                print('Login or password incorrect')
                msg = 'Invalid device:' + ip + ' password' + '\n'
                conf, h = ' ', ' '

    else:
        print('Unknow device')
        msg = ' Device:' + ip + ' is unknow' + '\n'
        conf, h = ' ', ' '

    # print(conf)
    t.close()
    return conf, h, msg


def SSHConnectCisco(ip, user, password, enable_pass):
    '''Connect Connection on port 22. Configuration collection'''


    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username = user, password = password, timeout=10)
        time.sleep(1)
        ssh = client.invoke_shell()
        time.sleep(1)
        console_output = ssh.recv(100)
        string = re.search(r'>', console_output.decode('utf-8'))
        if string != None:
            ssh.send('enable' + '\n')
            ssh.send(enable_pass + '\n')
            time.sleep(1)
            console_output = ssh.recv(100).decode('utf-8')
            if re.search(r'#', console_output) != None:
                ssh.send('terminal length 0' + '\n')
                ssh.send('show run' + '\n')
                time.sleep(11)
                ssh.send('exit' + '\n')
                config_output = ssh.recv(20000).decode('utf-8')
                if config_output.find('!\r\n!\r\nend') == -1:
                    print('The configuration is incomplete')
                    msg = ' Device:' + ip + ' configuration is incomplete' + '\n'
                    config, h = ' ', ' '
                else:
                    print('end conf: ' + str(config_output.find('!\r\n!\r\nend')))
                    config = config_output[config_output.find('terminal length 0') + 17:config_output.find('!\r\n!\r\nend') + 9]
                    h = hashlib.sha256(config.encode('ascii')).hexdigest()
                    print('Configuration saved')
                    msg = ' Device:' + ip + ' configuration saved' + '\n'
            else:
                print('Enable password incorrect')
                msg = ' The device:' + ip + ' enable password is incorrect' + '\n'
                config, h = ' ', ' '
        else:
            ssh.send('terminal length 0' + '\n')
            ssh.send('show run' + '\n')
            time.sleep(11)
            ssh.send('exit' + '\n')
            config_output = ssh.recv(20000).decode('utf-8')
            if config_output.find('!\r\n!\r\nend') == -1:
                print('The configuration is incomplete')
                msg = ' Device:' + ip + ' configuration is incomplete' + '\n'
                config, h = ' ', ' '
            else:
                print('end conf: ' + str(config_output.find('!\r\n!\r\nend')))
                config = config_output[config_output.find('terminal length 0') + 17:config_output.find('!\r\n!\r\nend') + 9]
                h = hashlib.sha256(config.encode('ascii')).hexdigest()
                print('Configuration saved')
                msg = ' Device:' + ip + ' configuration saved' + '\n'

    except paramiko.ssh_exception.AuthenticationException as e:
        print(e)
        msg = str(e) + str(ip) + '\n'
        config, h = ' ', ' '

    client.close()
    print(config)
    return config, h, msg


def TcpConnect(ip, username, password, enable_pass, telnet_port = 23, ssh_port = 22, timeout = 10):
    """Check availability telnet or ssh"""
    session = socket.socket()
    session.settimeout(3)
    result = session.connect_ex((ip, ssh_port))
    session.close()
    print(result)
    if result == 0:
        print('SSH')
        config, h, msg = SSHConnectCisco(ip=ip, user=username, password=password, enable_pass=enable_pass)
    else:
        session = socket.socket()
        session.settimeout(3)
        result = session.connect_ex((ip, telnet_port))
        session.close()
        print(result)
        if result == 0:
            print('Telnet')
            config ,h, msg = TelnetConnectCisco(ip=ip, user=username, password=password, enable_pass=enable_pass)
        else:
            print('Device unreachable')
            config, h = ' ', ' '
            msg = ' Device:' + ip + '  is not available' + '\n'
            #with open('logfile.txt', 'a') as f:
                #now = datetime.datetime.now()
                #date = now.strftime("%d.%m.%Y %I:%M %p")
                #f.write(date + ' Device:' + ip + '  is not available' + '\n')

    return config, h, msg


cur = con.cursor()
cur.execute('''select * from sqlite_master''')
	
cur.execute('SELECT * FROM collect_configs_device')
res = cur.fetchall()
for i in res:
    vendor_or_OS = i[10]
    if vendor_or_OS == 'Cisco':
        status = i[11]
        #print('status = ' + str(status))
        if status == 'OK':
            device_id = i[0]
            ip = i[1]
            hostname = i[2]
            username = i[5]
            password = i[6]
            enable_pass = i[7]
            max_number_cofigs = i[12]
            print('\n#------------------------------------------------------------')
            print('Start collect config device ' + str(ip) + ' ' + str(hostname))
            config, hash, msg = (TcpConnect(ip, username, password, enable_pass))
            print(msg)
            print(hash)
            cur.execute('SELECT * FROM collect_configs_config WHERE device_id = ? ORDER BY date_added DESC',
                        (str(device_id),))
            res_conf = cur.fetchall()
            total_configs = len(res_conf)
            print('Total configs for device = ' + str(total_configs))
            hash_old = res_conf[0][2]
            date_old = res_conf[0][3]
            print(hash_old)
            print(date_old)
            if hash == hash_old:
                print('Configuration did not change\n')
                continue
            else:
                print('The configuration has been changed\n')
            if total_configs >= int(max_number_cofigs):
                print("Maximum number of configurations exceeded")
                print("Configuration saved on "+ res_conf[total_configs - 1][3] + " with id configuration " + str(res_conf[total_configs - 1][0]) +
                      " will be deleted\n")
                id_config = res_conf[total_configs - 1][0]
                try:
                    date_update = datetime.datetime.now()
                    cur.execute(
                        'UPDATE collect_configs_config SET config = ?, hash_config = ?, date_added = ? WHERE Id = ?', (config, hash, date_update, id_config))
                    con.commit()
                    print('Configuration is stored in the database')
                except sqlite3.Error as e:
                    con.rollback()
                    print(e)


            else:
                try:
                    date_added = datetime.datetime.now()
                    params = (config, hash, date_added, device_id)
                    cur.execute(
                        'INSERT INTO collect_configs_config(config, hash_config, date_added, device_id) VALUES (?, ?, ?, ?)',
                        params)
                    con.commit()
                    print('Configuration is stored in the database')
                except sqlite3.Error as e:
                    con.rollback()
                    print(e)
                #print('Configuration is stored in the database')

        else:
            ip = i[1]
            hostname = i[2]
            print('\n#------------------------------------------------------------')
            print('Device ' +  str(ip)+ ' ' + str(hostname) + ' unreachable')


cur.close()
con.close()