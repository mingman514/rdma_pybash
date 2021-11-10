from pybash import bash, bash_return
import sys, time, datetime
import vws_util as vu
from multiprocessing import Process



################################
## Basic Info
################################
server_ip = ''
#base_path = '~/'
save_path = '~/script/test_result_bw'

TESTNAME = 'X3ProETH'
HOST_NAME = bash_return('hostname').decode('utf-8').strip()
TEST_TYPE = ''
TX_DEPTH = 128
MTU = 4096
MSG_SIZE = -1


################################
## Global Variables
################################
Iam = -1
SERVER = 0
CLIENT = 1
# Wait for TF_procs
TF_procs = []
BF_procs = []


def name_generator(test_t=TEST_TYPE, target_size='unknown'):
        return '{}_{}_{}_t{}_m{}_bg{}_s{}'.format(
                TESTNAME, HOST_NAME, test_t, TX_DEPTH, MTU, MSG_SIZE, target_size)

def initialize():
    vu.kill_native_process()
    print('Terminate perf_test Apps')




#def check_jobs():
#    vu.async_wait()
   

#def run_tf(test, option):
#    vu.perf_test(test, option)


def run(test, opt):
    vu.perf_test(test, opt)
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
    ex. python rnic.py 0 10.0.31.2
    """
    Iam = int(sys.argv[1])
    server_ip = sys.argv[2]
  
    test_list = ['wb', 'rb', 'sb']    
    mtu_list = [512, 1024, 2048, 4096]
    tx_depth_list = [1, 2, 4, 128]
    msg_size_list = [1073741824, 1048576]

    """
    Background Flow & Target Flow
    Watch Target Flow Until Ends
    """
    target_list = [1073741824, 1048576, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288]
    initialize()
    total_round = len(test_list) * len(mtu_list) * len(tx_depth_list) * len(msg_size_list) * len(target_list)
    cur_round = 0
    start = time.time()
    for target_s in target_list:
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
                        default_opt = '-F -l 1 --run_infinitely'
                        opt = default_opt
                        opt += ' -m ' + str(MTU)
                        opt += ' -t ' + str(TX_DEPTH)
                        opt += ' -s ' + str(MSG_SIZE)
        
                        f = name_generator(test_t, str(target_s)) + '_bf'
    
                        if Iam == CLIENT:
                            opt += ' {}'.format(server_ip)
                            opt += ' > {}/{}'.format(save_path, f)
    
                        print('Start Background Flow')
                        bf_proc = Process(target=run, args=(test_t, opt))
                        bf_proc.start()
                        
                        ###################
                        ### Target Flow
                        ###################
                        time.sleep(2) # in case of port conflict
                        default_opt = '-F -l 1 --run_infinitely'
                        opt = default_opt
                        opt += ' -m ' + str(MTU)
                        opt += ' -t ' + str(TX_DEPTH)
                        opt += ' -s ' + str(target_s)
                        
                        f = name_generator(test_t, str(target_s))
                        f += '_tf'
    
                        if Iam == CLIENT:
                            opt += ' {}'.format(server_ip)
                            opt += ' > {}/{}'.format(save_path, f)
    
                        print('Start Target Flow')
                        tf_proc = Process(target=run, args=(test_t, opt))
                        tf_proc.start()
                      
                        if msg_size > 104857600 or target_s > 104857600:
                            time.sleep(40)
                        else:
                            time.sleep(20)


    
                        # Sync & Init
                        initialize()
                        vu.synchronize(Iam, server_ip)
        
                        # Status
                        end = time.time()
                        cur_round += 1
                        print('')
                        
                        now = end - start
                        print('[{}]Now Round {}/{} ({}m left)'.format(str(datetime.timedelta(seconds=now)).split('.')[0], cur_round, total_round, round((now/cur_round)*(total_round - cur_round)/60, 2)))
#                        sys.exit(1)

