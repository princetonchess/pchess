import chess.polyglot
import struct, mmap, os, collections, logging
from chessutil import *
import pdb
BookEntryStruct = struct.Struct('>QHIfIf')

class BookEntry(collections.namedtuple("BookEntry", "key raw_move n perf mastern masterperf")):
    """An entry from a Polyglot opening book."""
    __slots__ = ()
    def move(self):
        promotion = (self.raw_move >>12) & 0x7
        return chess.Move(self.raw_move & 0x3f, (self.raw_move >>6) & 0x3f, promotion if promotion else None)
    def __str__(self):
        return '{}: {} - n:{} {} mastern:{} {}'.format(self.key, self.move(), self.n, self.perf, self.mastern, self.masterperf)

class BookReader(object):
    def __init__(self, filename):
        try:
            self.fd = os.open(filename, os.O_RDONLY | os.O_BINARY if hasattr(os, "O_BINARY") else os.O_RDONLY)
            self.mmap = mmap.mmap(self.fd, 0, access=mmap.ACCESS_READ)
        except (ValueError, mmap.error):
            self.mmap = None

    def __enter__(self):  return self
    def __exit__(self, exc_type, exc_value, traceback):   return self.close()
    def __len__(self): return 0 if self.mmap is None else self.mmap.size() // BookEntryStruct.size

    def __getitem__(self, key):
        if self.mmap is None:  raise IndexError()
        if key < 0:  key = len(self) + key
        try:
            key, raw_move, n, perf, mastern, masterperf = BookEntryStruct.unpack_from(self.mmap, key * BookEntryStruct.size)
        except struct.error:
            raise IndexError()

        return BookEntry(key, raw_move, n, perf, mastern, masterperf)

    def __iter__(self):
        i = 0
        size = len(self)
        while i < size:
            yield self[i]
            i += 1

    def bisect_key_left(self, key):
        lo = 0
        hi = len(self)
        while lo < hi:
            mid = (lo + hi) // 2
            mid_key, _, _, _, _, _ = BookEntryStruct.unpack_from(self.mmap, mid * BookEntryStruct.size)
            if mid_key < key:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def find_all(self, board):
        """with hash key, Seeks a specific position and yields corresponding entries."""
        try:
            key = int(board)
        except (TypeError, ValueError):
            key = chess.polyglot.zobrist_hash(board)

        i = self.bisect_key_left(key)
        #pdb.set_trace()
        size = len(self)

        while i < size:
            entry = self[i]
            i += 1
            if entry.key != key:                   
                break
            if board and board.is_legal(entry.move()): 
                yield entry

    def close(self):
        if self.mmap is not None:   self.mmap.close()
        try:      os.close(self.fd)
        except OSError:     pass


class BookBuilder():
    def __init__(self, filename):
        self.inmem = {}
        if os.path.exists('filename'):   raise 'file exists {}'.format(filename)
        self.filename = filename
        self.nentries = 0

    def load_pgn(self, pgnfile, **kwargs):
        traverse_pgn(pgnfile, self.go_over_game, False, **kwargs)
        
    def go_over_game(self, game, **kwargs):
        maxply = kwargs.get('maxply', 60)
        node = game
        gi = gameinfo(game)
        i = 0
        while node.variations:
            nextnode = node.variations[0]
            if i <= maxply:
                self.upd(node.board(), nextnode.move, gi['result'], gi['elos'])
            node = nextnode
            i += 1
        
    def upd(self, board, move, res, elos):
        ''' update the book with move and result of the game 
        '''
        h = chess.polyglot.zobrist_hash(board)
        m = self._pack_move(move)
        ismaster = self._ismaster(board, elos)
        initstate = [1, res, 1 if ismaster else 0, res if ismaster else 0.5]
        if h in self.inmem:
            d = self.inmem[h]
            if m in d:
                self._updstats(d[m], res, ismaster) ##TODO see if it's update inplace
            else:
                d[m] = initstate
                self.nentries +=1
        else:
            self.inmem[h] = {m:initstate}
            self.nentries +=1

    def _ismaster(self, board, elos, thres=2400):
        return elos[0]>=thres if board.turn else elos[1]>=thres

    def _updres(self, n, perf, res):
        return (n*perf + res) / (n+1)

    def _updstats(self, dm, res, ismaster):
        dm[1] = self._updres(dm[0], dm[1] , res)
        dm[0] += 1
        if ismaster:
            dm[3] = self._updres(dm[2], dm[3], res)
            dm[2] += 1

    def _pack_move(self, m):
        ''' persist move, not following polyglot twisted way'''
        if not m:  return None  ## null move, don't insert to book
        r = (m.to_square << 6) | m.from_square
        return r if m.promotion is None else (m.promotion << 12) | r

    def persist(self):
        ''' merge inmem and mmap '''
        logging.info('flush stats from memory into disk {}'.format(self.nentries))
        with open(self.filename, "wb") as f: # write empty file required by mmap
            f.write((self.nentries * BookEntryStruct.size) *b'\0')

        flags = os.O_CREAT | os.O_RDWR
        self.fd = os.open(self.filename, flags | os.O_BINARY if hasattr(os, "O_BINARY") else flags)
        self.mmap = mmap.mmap(self.fd, 0, access=mmap.ACCESS_WRITE)

        i = 0
        for k in sorted(self.inmem):
            for m,entry in self.inmem[k].items():
                n, perf, mastern, masterperf = entry
                BookEntryStruct.pack_into(self.mmap, BookEntryStruct.size * i, k, m, n, float(perf), mastern, float(masterperf))
                i += 1
        os.close(self.fd)

    def __exit__(self, exc_type, exc_value, traceback):
        return self.persist()


