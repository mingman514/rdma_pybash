from pybash import bash, bash_return
import sys, time, datetime
import vws_util as vu
from multiprocessing import Process



################################
## Basic Info
################################
server_ip = ''
#base_path = '~/'
save_path = '~/script/test_result'

TESTNAME = 'X5'
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
            print('Target process finished')
        else:
            time.sleep(1)
            print('Target process working... {}s'.format(elapsed))
            elapsed += 1
            

if __name__ == '__main__':
    """
    ex. python rnic.py 0 10.0.31.2
    """
    Iam = int(sys.argv[1])
    server_ip = sys.argv[2]
  
    test_list = ['sb', 'rb', 'wb']    
    mtu_list = [512, 1024, 2048, 4096]
    tx_depth_list = [1, 2, 128]
    msg_size_list = [256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 1048576, 1073741824]

    """
    Background Flow & Target Flow
    Watch Target Flow Until Ends
    """
    target_t = 'tput' # 'tput' or 'lat'
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
    #                    print('bf name: ', f)
    
                        if Iam == CLIENT and target_t == 'tput':
                            opt += ' {}'.format(server_ip)
                            opt += ' > {}/{}'.format(save_path, f)
    
                        print('Start Background Flow')
                        bf_proc = Process(target=run, args=(test_t, opt))
                        bf_proc.start()
                        
                        ###################
                        ### Target Flow
                        ###################
                        print('Wait for Background Flow Warming Up')
                        if target_t == 'tput':
                            time.sleep(10)  # set enough time to measure bw of background
                            default_opt = '-F -l 64 -s 16 -d mlx5_0 -n 100000000'
                        elif target_t == 'lat':
                            time.sleep(3)  # set enough time to measure bw of background
                            default_opt = '-F -l 1 -s 16 -d mlx5_0 -n 10000000 -t ' + str(TX_DEPTH)
    
                        opt = default_opt
                        opt += ' -m ' + str(MTU)
                        
                        f = name_generator(test_t) if target_t == 'tput' else name_generator(test_t[0]+'l')
                        f += '_tf'
    #                    print('tf name: ', f)
    
                        if Iam == CLIENT:
                            opt += ' {}'.format(server_ip)
                            opt += ' > {}/{}'.format(save_path, f)
    
                        tf_proc = Process(target=run, args=(test_t, opt))
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
                        vu.synchronize(Iam, server_ip)
        
                        # Status
                        end = time.time()
                        cur_round += 1
                        print('[{}]Now Round {}/{} ({}m left)'.format(str(datetime.timedelta(seconds=(end-start))).split('.')[0], cur_round, total_round, round((total_round-cur_round)*1.5), 2))

