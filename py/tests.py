from book import *
from chessutil import *
import unittest, collections
import pdb

class testUtil(unittest.TestCase):
    def setUp(self):
        self._init_counts()

    def _init_counts(self):
        self.ngames = 0
        self.nmoves = 0
        self.nlines = 0  ## variations

    def _go_over_game(self, game, **kwargs):
        maxply = kwargs.get('maxply', 10000000)
        self.ngames +=1
        lines = []
        currentline = []
        nodestack = collections.deque([game])
        while nodestack:
            node = nodestack.pop()
            if not currentline or node in currentline[-1].variations:
                if len(currentline)<=maxply: 
                    currentline.append(node)
                else:
                    continue
            else:
                lines.append(currentline)
                currentline=[node] ## start of a new line
            for i in node.variations:
                nodestack.append(i)
        lines.append(currentline)
        ##pdb.set_trace()
        for l in lines:
            self.nmoves += len(l)

        self.nlines += len(lines)

    def test_traverse_pgn_base(self):
        self._init_counts()
        traverse_pgn('testdata/c02.pgn', self._go_over_game, False)
        self.assertEqual(self.ngames, 3)
        self.assertEqual(self.nlines, 3)
        self.assertEqual(self.nmoves, 139+90+204 + self.ngames) # total number of plys + ngames(startpos)

    def test_traverse_pgn_filter_rating(self):
        self._init_counts()
        traverse_pgn('testdata/c02.pgn', self._go_over_game, False, minrating=2400)
        self.assertEqual(self.ngames, 1)
        self.assertEqual(self.nlines, 1)
        self.assertEqual(self.nmoves, 204 + self.ngames) # total number of plys + ngames(startpos)

    def test_traverse_pgn_filter_maxply(self):
        self._init_counts()
        traverse_pgn('testdata/c02.pgn', self._go_over_game, False, maxply=20)
        self.assertEqual(self.ngames, 3)
        self.assertEqual(self.nlines, 3)
        self.assertEqual(self.nmoves, 60 + self.ngames) # total number of plys + ngames(startpos)

    def test_traverse_pgn_filter_eco(self):
        self._init_counts()
        traverse_pgn('testdata/test.pgn', self._go_over_game, False, ecos={'C42', 'D37'})
        self.assertEqual(self.ngames, 2)


class TestBook(unittest.TestCase):
    bookpath = '/tmp/testbook.bin'
    startpos_key = chess.polyglot.zobrist_hash(chess.Board())

    def setUp(self):
        self._loadpgn_to_book()

    def _go_over_game(self, game, **kwargs):
        maxply = kwargs.get('maxply', 60)
        node = game
        gi = gameinfo(game)
        i = 0
        while node.variations:
            nextnode = node.variations[0]
            if i <= maxply:
                self.bookbuilder.upd(node.board(), nextnode.move, gi['result'], gi['elos'])
            node = nextnode
            i += 1

    def _loadpgn_to_book(self):
        if os.path.exists(self.bookpath):  os.remove(self.bookpath)
        self.bookbuilder = BookBuilder(self.bookpath)
        traverse_pgn('testdata/c02.pgn', self._go_over_game, False, maxply=10)
        self.bookbuilder.persist()
        
    def test_book_base(self):
        book = BookReader(self.bookpath)
        for e in book:
            print(e)

        self.assertTrue('FoO'.isupper())

if __name__ == '__main__':
    unittest.main()
