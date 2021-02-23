import copy
import math
import random

import geneticgame

GAME_SIZE = 4
BITS_PER_ITEM = 5

last_ten = [0] * 10
which = 0
totcount = 0

class biggerGame ():
  '''
  Ten rounds.  Each round, each player picks one of their numbers.  Higher one gets 100 points + differential.
  '''

  @staticmethod
  def play (p1, p2, game_parms):
    score = 0
    px = [p1, p2]
    play = [0, 0]
    game_log = " "
    for round in range(10):
        for who in range(2):
            play[who] = px[who][random.randrange(len(px[who]))]
        diff = play[0] - play[1]
        score += math.copysign (20, diff) + diff
    return {'score': score, 'log': game_log}

  @staticmethod
  def decode (internal):
    if 'genes' in internal:
        internal = internal['genes']
    ret = [0] * GAME_SIZE
    for item in range (GAME_SIZE):
        val = 0
        for bit in range (BITS_PER_ITEM):
            val = val * 2 + internal[item * BITS_PER_ITEM + bit]
        if val < 25:
            ret [item] = 1.1 ** val # 1 - 10
        else:
            ret [item] = val - 31.0 # 0 - -6
    return ret

  @staticmethod
  def parms ():
      return {'chrome_length': GAME_SIZE * BITS_PER_ITEM}

class GeneticOverride (geneticgame.GeneticGame):
    def get_chromes (self):
        return self.chromes

    def eval_logger (self, results):
        self.eval_result = results

    def log (self):
        if self.gen % self.parms['eval']['interval'] == 0:
            tot = 0
            for key, ch in self.chromes.items():
                tot += sum (self.game.decode (ch))
            toptot = 0
            for ch in self.get_top(3):
                toptot += sum (self.game.decode (self.chromes[ch]))

            msg = f"G={self.gen}  A={round (tot/len(self.chromes), 2)}  T={round (toptot/3, 2)}  E={round (self.eval_result, 2)}"
            if self.gen % 500 == 0:
                fh = open (f"stats{self.gen}.txt", "a")
                fh.write (msg + '\n')
                fh.close ()
            print (msg)

game = biggerGame()
gg = GeneticOverride (game, {'eval': {'static': 3, 'outputter': "eval_logger", "interval": 10}, 'rounds': 200})
print ('--Lets Go!--')
ret = gg.optimize ()
print ('--Final results--')
print (ret)
