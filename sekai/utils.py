import os
from colorama import init

init()

def getTermWidth():
    return os.get_terminal_size()[0]

def clear_lines(n):
    for _ in range(n):
        print('\033[1A[\033[2K', end='\r')

def clearConsole():
    command = 'clear'
    if os.name in ('nt', 'dos'):
        command = 'cls'
    os.system(command)
