import chess.polyglot
import struct, mmap, os

BookEntryStruct = struct.Struct('>QHfIfI')

class MmapReader(object):
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
        if self.mmap is None:   raise IndexError()
        if key < 0:  key = len(self) + key

        try:
            key, raw_move, weight, learn = ENTRY_STRUCT.unpack_from(self.mmap, key * ENTRY_STRUCT.size)
        except struct.error:
            raise IndexError()

        return Entry(key, raw_move, weight, learn)

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
            mid_key, _, _, _ = ENTRY_STRUCT.unpack_from(self.mmap, mid * ENTRY_STRUCT.size)
            if mid_key < key:
                lo = mid + 1
            else:
                hi = mid

        return lo

    def __contains__(self, entry):
        return any(current == entry for current in self.find_all(entry.key, entry.weight))

    def find_all(self, board, minimum_weight=1, exclude_moves=()):
        """Seeks a specific position and yields corresponding entries."""
        try:
            key = int(board)
            board = None
        except (TypeError, ValueError):
            key = zobrist_hash(board)

        i = self.bisect_key_left(key)
        size = len(self)

        while i < size:
            entry = self[i]
            i += 1

            if entry.key != key:                break
            if entry.weight < minimum_weight:   continue

            if board:                move = entry.move(chess960=board.chess960)
            elif exclude_moves:      move = entry.move()

            if exclude_moves and move in exclude_moves:      continue
            if board and not board.is_legal(move):           continue

            yield entry

    def close(self):
        if self.mmap is not None:   self.mmap.close()
        try:      os.close(self.fd)
        except OSError:     pass

class BookBuilder():
    def __init__(self, mmap_file_path, inmem_thres=10000):
        ''' flush to mmamp if len of inmem is over inmem_thres'''
        self.inmem = {}
        self.inmemthres = inmem_thres
        self.mmap = MmapReader(mmap_file_path)

    def _ismaster(self, elos, thres=2400):
        return elos[0]>=thres and elos[1]>=thres

    def _updres(self, n, perf, res):
        return (n*perf + res) / (n+1)

    def _updstats(self, dm, res, ismaster):
        dm[1] = self._updres(dm[0], dm[1] , res)
        dm[0] += 1
        if ismaster:
            dm[3] = self.updres(dm[2], dm[3], res)
            dm[2] += 1
    
    def upd(self, board, move, res, elos):
        ''' update the book with move and result of the game 
        '''
        h = int(board)
        m = self._pack_move(move)
        ismaster = self._ismaster(elos)
        initstate = [1, res, 1 if ismaster else 0, res if master else 0.5]
        if h in self.inmem:
            d = self.inmem[h]
            if m in d:
                self._updstats(d[m], res, ismaster) ##TODO see if it's update inplace
            else:
                d[m] = initstate
        else:
            self.inmem[h] = {m:initstate}

        if len(self.inmem)>self.inmem_thres:    self._persist()

    def _pack_move(self, m):
        ''' persist move, not following polyglot twisted way'''
        if not chessmove:  return None  ## null move, don't insert to book
        r = (m.to_square << 6) | m.from_square
        return r if m.promotion is None else (m.promotion << 12) | r

    def unpack_move(self, h):
        return chess.Move(h & 0x3f, (h >>6) & 0x3f, (h >>12) & 0x7)

    def _persist(self):
        ''' merge inmem and mmap '''
        logging.info('flush stats from memory into disk {} {}'.format(len(self.inmem), len(self.mmap)))

        # get a distinct set of keys from inmem and mmap, sort by hash,move, then, open a new mmap to write
        # the keys shouldn't occupy too much ram since it's only a list, not dict
        # traverse the existing mmap, merge stats with inmem dict if necessary, then write to mmap
        # rename prev mmap to be .prev, rename new mmap to the main file name, re-open it as read only
        # clear the inmem dict, watch out for memory, it shouldn't grow 

    def __exit__(self, exc_type, exc_value, traceback):
        return self._persist()

'''
struct.pack(struct.Struct(">H"), 
struct.unpack('H', struct.pack('H', 60.12))
ENTRY_STRUCT = struct.Struct(">QHHI")
'''
