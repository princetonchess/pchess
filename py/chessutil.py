
import logging, chess, collections
from chess import pgn,polyglot,uci

def _toint(x): return x if x is None else int(x)
def _toset(x): return x if (x is None or isinstance(x,set)) else set(x)
def _todate(x):return x if x is None else _toint(re.sub('[.-]','', x))

resultmap = {'1-0':1, '0-1':0, '1/2-1/2':0.5}

def gameinfo(game):
    h = {k.lower():v for k,v in game.headers}
    h['result'] = resultmap.get(h.get('result', '1/2-1/2'), 0.5)
    h['elos'] = [_toint(h.get('{}elo'.format(s), None)) for s in ['white','black']]
    h['eventdate'] = _todate(h.get('eventdate', None))
    return h

def traverse_pgn(pgnfile, process_game_func, rethrow=False, **kwargs):
    '''traverse pgn file, for each game, invoke func if it passes the filter'''
    logging.info('traversing file {0}'.format(pgnfile))
    n = 0
    maxply = kwargs.get('maxply')
    minrating = _toint(kwargs.get('minrating'))
    ecos = kwargs.get('ecos')
    nags = kwargs.get('nags')
    players = kwargs.get('player')  ##regex

    with open(pgnfile) as pgn:
        while True:
            try:
                g = chess.pgn.read_game(pgn)
                if g is None: break
                n += 1
                if n % 1000 == 0: logging.info("scanned {0} games".format(n))
                
                if maxply and n>maxply: break

                process_game_func(g)

            except IndexError as e:
                logging.info('out of index error {0}'.format(str(e)))
                if rethrow: raise
                
        logging.info('traversed {0} games'.format(n))
