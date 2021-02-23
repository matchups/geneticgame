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

game = biggerGame()
gg = GeneticOverride (game, {'eval': {'static': 3, "interval": 10}, 'rounds': 200})
print ('--Lets Go!--')
ret = gg.optimize ()
print ('--Final results--')
print (ret)
