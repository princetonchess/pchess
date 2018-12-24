
import logging, chess, collections, re
from chess import pgn,polyglot,uci
import pdb

def _toint(x): return x if x is None else int(x)
def _toset(x): return x if (x is None or isinstance(x,set)) else set(x)
def _todate(x):return x if x is None else _toint(re.sub('[.-]','', x))

resultmap = {'1-0':1, '0-1':0, '1/2-1/2':0.5}

def gameinfo(game):
    h = {k.lower():v for k,v in game.headers.items()}
    h['result'] = resultmap.get(h.get('result', '1/2-1/2'), 0.5)
    h['elos'] = [_toint(h.get('{}elo'.format(s), None)) for s in ['white','black']]
    h['eventdate'] = _todate(h.get('eventdate', None))
    return h

def traverse_pgn(pgnfile, process_game_func, rethrow=False, **kwargs):
    logging.info('traversing file {0}'.format(pgnfile))
    with open(pgnfile) as pgn:
        minrating = _toint(kwargs.get('minrating'))
        ecos = kwargs.get('ecos')
        nags = kwargs.get('nags')
        playerspat = kwargs.get('player')  ##regex
        if playerspat and not '*' in playerspat: playerspat = '.*{}.*'.format(playerspat)
        playersre = re.compile(playerspat, re.IGNORECASE) if playerspat else None
        n = 0
        while True:
            try:
                g = chess.pgn.read_game(pgn)
                if g is None: break
                gi = gameinfo(g)

                n += 1
                if n % 1000 == 0: logging.info("scanned {0} games".format(n))
                
                if minrating:
                    elos = gi.get('elos', None)
                    if elos is None: continue
                    if any([elo is None or elo<minrating for elo in elos]): continue
                if ecos:
                    eco = gi.get('eco', None)
                    if (eco is None) or (not eco in ecos): continue

                if playersre and not (playersre.match(gi.get('white', '')) or 
                                      playersre.match(gi.get('black', ''))):
                    continue

                process_game_func(g, **kwargs)

            except IndexError as e:
                logging.info('out of index error {0}'.format(str(e)))
                if rethrow: raise
        logging.info('finished traversed {0} games'.format(n))
