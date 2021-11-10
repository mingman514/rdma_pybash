from pybash import bash, bash_return
import sys, time, datetime
import vws_util as vu
from multiprocessing import Process

"""
This test is to figure out if large READ flow affect WRITE Tput flow in the same RNIC.

Note: READ flow and WRITE flow must be hosted by different node,
      and therefore, it is important to save result files in each node respectively.
"""

################################
## Basic Info
################################
server_ip = ''
#base_path = '~/'
save_path = '~/script/test_result'

TESTNAME = 'X6ETH100'
HOST_NAME = bash_return('hostname').decode('utf-8').strip()
TEST_TYPE = ''
TX_DEPTH = 128
MTU = 4096
MSG_SIZE = -1


################################
## Global Variables
################################
Iam = ''
SERVER = 0
CLIENT = 1
# Wait for TF_procs
TF_procs = []
BF_procs = []


def name_generator(test_t=TEST_TYPE):
        return '{}_{}_{}_t{}_m{}_bg{}'.format(
                TESTNAME, HOST_NAME, test_t, TX_DEPTH, MTU, MSG_SIZE)

def initialize():
    vu.kill_native_process()
    print('Terminate perf_test Apps')




#def check_jobs():
#    vu.async_wait()
   

#def run_tf(test, option):
#    vu.perf_test(test, option)


def run(test, opt, core=-1):
    vu.perf_test(test, opt, core)
    #print(test_t, opt)

def supervise(opt):
    #print('Start watching for target process to finish...')
    elapsed = 0
    FLAG = 1
    while FLAG:
        cmds = bash_return('pgrep -a ib_').decode('utf-8').strip()
#        print(cmds)
#        print('find:',opt)
        if opt not in cmds:
            FLAG = 0
            print('Target process finished: {}s'.format(elapsed))
        else:
            time.sleep(1)
            if elapsed % 10 == 0:
                print('Target process working... {}s'.format(elapsed))
            elapsed += 1
            

if __name__ == '__main__':
    """
    usage) python write_read.py [r:read/ w:write] counterpartIP
    ex. python write_read.py r 10.0.31.2  # for client in READ flow
    ex. python write_read.py w 10.0.32.2  # for client in WRITE flow
    """
    Iam = sys.argv[1]
    server_ip = sys.argv[2]
    if Iam != 'r' and Iam != 'w':
        print('MUST use r or w to specify flow type')
        sys.exit(1)
    myip = vu.get_self_ip()
    print('My IP is:',myip)

    test_list = ['rb']
    mtu_list = [512, 1024, 2048, 4096]
    tx_depth_list = [128]
    msg_size_list = [256, 512, 1024, 2048, 4096, 8192, 16384, 1048576, 1073741824]
    #msg_size_list = [256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576, 1073741824]
    #msg_size_list = [4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576, 1073741824]

    """
    Background Flow & Target Flow
    Watch Target Flow Until Ends
    """
    #target_t = 'tput' # 'tput' or 'lat'
    target_list = ['tput', 'lat']
    initialize()
    total_round = len(test_list) * len(mtu_list) * len(tx_depth_list) * len(msg_size_list) * len(target_list)
    cur_round = 0
    start = time.time()
    for target_t in target_list:
        for test_t in test_list:    
            TEST_TYPE = test_t
            
            for mtu in mtu_list:
                MTU = mtu
    
                for tx_depth in tx_depth_list:
                    TX_DEPTH = tx_depth
    
                    for msg_size in msg_size_list:
                        MSG_SIZE = msg_size
    
                        ####################
                        ### Background Flow
                        ####################
                        default_opt = '-F -l 1 --run_infinitely -d mlx5_0'
                        opt = default_opt
                        opt += ' -m ' + str(MTU)
                        opt += ' -t ' + str(TX_DEPTH)
                        opt += ' -s ' + str(MSG_SIZE)
        
                        f = name_generator(test_t) + '_bf'
    
                        if Iam == 'r':
                            opt += ' {}'.format(server_ip)
                            if target_t == 'tput':
                                opt += ' > {}/{}'.format(save_path, f)
    
                        print('Start Background Flow')
                        bf_proc = Process(target=run, args=(test_t, opt, 0))
                        bf_proc.start()
                        
                        ###################
                        ### Target Flow
                        ###################
                        print('Wait for Background Flow Warming Up')
                        tar_test_t = 'wb'
                        if target_t == 'tput':
                            time.sleep(10)  # set enough time to measure bw of background
                            default_opt = '-F -l 64 -s 16 -d mlx5_0 -n 100000000 -Q 1'
                        elif target_t == 'lat':
                            tar_test_t = test_t[0] + 'l'
                            time.sleep(3)  # set enough time to measure bw of background
                            default_opt = '-F -l 1 -s 16 -d mlx5_0 -n 10000000 -t ' + str(TX_DEPTH)
    
                        if msg_size > 104857600: # spare more time for very large msg
                            time.sleep(15)

                        opt = default_opt
                        opt += ' -m ' + str(MTU)
                        
                        
                        f = name_generator(tar_test_t)
                        f += '_tf'
    
                        if Iam == 'w':
                            opt += ' {}'.format(server_ip)
                            opt += ' > {}/{}'.format(save_path, f)
    
                        tf_proc = Process(target=run, args=(tar_test_t, opt, 1))
                        tf_proc.start()
                        
                        ###################
                        ### Supervisor
                        ###################
                        time.sleep(2)
                        opt = opt.split('>')[0].strip()
                        sv_proc = Process(target=supervise, args=(opt,))
                        sv_proc.start()
    
                        sv_proc.join()
    
                        # Sync & Init
                        initialize()
                        if Iam == 'r':
                            vu.synchronize(0, myip)
                        else:
                            vu.synchronize(1, server_ip)

        
                        # Status
                        end = time.time()
                        cur_round += 1

                        now = end - start
                        print('\n--------------------------------')
                        print('[{}]Now Round {}/{} ({}m left)'.format(str(datetime.timedelta(seconds=now)).split('.')[0], cur_round, total_round, round((now/cur_round)*(total_round-cur_round)/60, 0)))

                        print('--------------------------------')

