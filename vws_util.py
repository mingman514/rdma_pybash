from pybash import bash, bash_return
import time
import socket

PASSWD = 'aldrn5'

############################################
# Basic
############################################
def get_self_ip():
    ip_list = bash_return('hostname -I').decode('utf-8')
    ip = ip_list.split(' ')

    ip10 = ''
    for _ip in ip:
        if _ip[0:3] == '10.':
            ip10 = _ip
            break

    return ip10

def build_using_sh(cont, filepath):
    # Usage
    # build_using_sh('vws_node1', '/freeflow/vws_freeflow/libvws/build.sh')
    path = '/'.join(filepath.split('/')[:-1])
    filename = filepath.split('/')[-1]
    bash('docker exec {} sh -c "cd {}; ./{}"'.format(cont, path, filename))


def mkdir(path):
    bash('mkdir {}'.format(path))

def test_t_translate(test, core=-1):
    testname = ''
    if test == 'sb':
        testname = 'ib_send_bw'
    elif test == 'sl':
        testname = 'ib_send_lat'
    elif test == 'wb':
        testname = 'ib_write_bw'
    elif test == 'wl':
        testname = 'ib_write_lat'
    elif test == 'rb':
        testname = 'ib_read_bw'
    elif test == 'rl':
        testname = 'ib_read_lat'
    else:
        print('Invalid testing format. (Use one of sb/sl/wb/wl/rb/rl)')
        exit(-1)
    if core >= 0:
        testname = 'sudo taskset -c {} {}'.format(core, testname)
    return testname

def kill_native_process():
    bash('echo {} | sudo -S kill -9 $(pgrep ib_)'.format(PASSWD))

      
def kill_ib():
    bash('echo comnet02 | sudo kill -9 $(top | pgrep ib_send)')
    bash('echo comnet02 | sudo kill -9 $(top | pgrep ib_read)')
    bash('echo comnet02 | sudo kill -9 $(top | pgrep ib_write)')

def async_wait(job):
    print('Waiting for [{}] to finish'.format(job))
    FLAG = 1
    while FLAG:
        try:
            processing = bash_return('pgrep ' + job)
        except:
            FLAG = 0

############################################
# Perf test
############################################
def perf_test(test, option, core=-1):
    """
    ex. ib_send_bw -S 3 -Q 1 -a
        -> perf_test('sb', '-S 3 -Q 1 -a')
    """
    testname = test_t_translate(test, core)
    
    if '10.' in option or '192.' in option:
        print('Client Wait')
        time.sleep(0.5)
    
    option += ' &'
    print('[perf_test] {} {}'.format(testname, option))
    bash('{} {}'.format(testname, option))
    #if '>' in option:
    #    res_path = option.split('> ')[1]
    #    bash('cat {}'.format(res_path))

if __name__ == '__main__':
    replace_line('vws_node1', '/freeflow/vws_freeflow/libvws/libvws.h', 57, '#define TRMQ_POLL_TH 5')
#    restart_router()
#    restart_vwsshm()
#    time.sleep(10)
#    perf_test('vws_node1', 'sb', '-S 3 -Q 1 -a 10.32.0.2')
#    restart_router()
#    restart_vwsshm()

#    build_using_sh('vws_node1', '/freeflow/vws_freeflow/libvws/build.sh')
#    async_wait('vws_node1', 'build.sh')

############################################
# Perf test
############################################
def synchronize(Iam, hostip):
    HOST = hostip
    PORT = 8880

    if Iam == 0:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
    
        client_socket, addr = server_socket.accept()
    
        print('Connected by', addr)

        data = client_socket.recv(10)

        client_socket.sendall('ack'.encode())

        client_socket.close()
        server_socket.close()

    else:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                client_socket.connect((HOST, PORT))
                break
            except:
                time.sleep(0.2)
        client_socket.sendall('ack'.encode())
        data = client_socket.recv(10)
        print('Received', repr(data.decode()))

        client_socket.close()

    print('--------- Sync Completed ------------')


