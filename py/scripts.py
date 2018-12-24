'''
entry points for command lines
'''

from chessutil import *
from book import *


def buildbook_command(bookfile, pgnfile, max_ply=60, min_rating=2100):
    with BookBuilder(bookfile) as bookbuilder:
        ## load multiple pgn if needed
        bookbuilder.load_pgn(pgnfile, maxply=max_ply, minrating=min_rating)

def printbook_command(bookfile):
    with BookReader(bookfile) as b:
        b.print()

    
## TODO
def mergebooks_command(file1, file2, tofile):
    b1 = BookReader(file1)
    b2 = BookReader(file2)

    keymoves = set()
    for e in b1:
        keymoves.add( (e.key, e.raw_move))
    for e in b2:
        keymoves.add( (e.key, e.raw_move))

    with open(tofile, "wb") as f: # write empty file required by mmap
        f.write((len(keymoves) * BookEntryStruct.size) *b'\0')

    flags = os.O_CREAT | os.O_RDWR
    fd = os.open(tofile, flags | os.O_BINARY if hasattr(os, "O_BINARY") else flags)
    bookmmap = mmap.mmap(fd, 0, access=mmap.ACCESS_WRITE)

    i = 0
    for k,m in sorted(keymoves):
        e = b1.find(k, m)
        e2 = b2.find(k, m)
        assert(not(e is None and e2 is None))
        if e and e2:
            nsum = e.n+e2.n
            mnsum = e.mastern+e2.mastern
            e = BookEntry(k, m, nsum, (e.n*e.perf + e2.n*e2.perf)/nsum, mnsum,  0.5 if mnsum == 0 else (e.mastern*e.masterperf + e2.mastern*e2.masterperf)/mnsum)
        elif e is None:
            e = e2
        BookEntryStruct.pack_into(bookmmap, BookEntryStruct.size * i, k, m, e.n, e.perf, e.mastern, e.masterperf)
        i += 1
    os.close(fd)
        
        
if __name__ == '__main__':
    import scriptine
    scriptine.run()
