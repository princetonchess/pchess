'''
entry points for command lines
'''

from chessutil import *
from book import *


def buildbook_command(pgnfile, maxply=60, min_mastern=10, sideline_tolerance=0.15):
    pass
    
## TODO
def mergebooks_command(file1, file2, tofile):
    b1 = BookReader(file1)
    b2 = BookReader(file2)
    fd = os.open(tofile, os.O_WRONLY | os.O_BINARY if hasattr(os, "O_BINARY") else os.O_RDONLY)
    mmap = mmap.mmap(self.fd, 0, access=mmap.ACCESS_WRITE)
    
        
if __name__ == '__main__':
    import scriptine
    scriptine.run()
