from optparse import OptionParser
from chessutil import *

p = OptionParser(usage="usage: %prog [options]")
p.add_option('-r','--repertoire',dest='repertoire',  metavar='REPERTOIRE', default = 'd:/newchess/opening/repertoire/test.pgn')
p.add_option('-o','--out'       ,dest='out', metavar='OUT', default = 'd:/newchess/opening/training/kidblack.pgn')
p.add_option('-d','--debug'     ,dest='debug', metavar='DEBUG', default = False)
opts, args = p.parse_args()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(threadName)s %(message)s')

def lineToGame(line):
    ''' with list of game nodes'''
    if line:
        game = pgn.Game()
        game.setup(line[0].board())
        node = game
        for n in line[1:]:
            node.add_variation(n.move)
            node = node.variations[0]
        return game

def gentraining(game):
    seenpos = {}
    ## traverse each variations, keep pushing to lines
    ## the goal is to create a bunch of lines, starting with a node that hasn't seen beforeXB
    lines = []
    currentline = []
    nodestack = collections.deque([game])
    while nodestack:
        node = nodestack.pop()
        if not currentline or node in currentline[-1].variations:
            currentline.append(node)
        else:
            lines.append(currentline)
            currentline=[node] ## start of a new line
        for i in node.variations:
            nodestack.append(i)
    lines.append(currentline)
    logging.info('generated {} training lines'.format(len(lines)))
    pn = 0
    with open(opts.out, 'w') as outfile:
        for l in lines:
            g = lineToGame(l)
            if g:
                pn +=1
                outfile.write('{}\n\n'.format(g))
                logging.info('printed {} lines'.format(pn))

if __name__ == "__main__":
    traverse_pgn(opts.repertoire, gentraining, opts.debug)
