import os
import subprocess


def bash(cmd):
    return os.system(cmd)

def bash_return(cmd):
    return subprocess.check_output(cmd, shell=True)

