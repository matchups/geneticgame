import random

import geneticgame

GAME_SIZE = 14

class GOPSGame ():
  '''
  The game contains 14 rounds of picking a number 1-14 without replacement and each player bidding one
  of their cards labeled 1-14.  The higher card bet gets the specified number of points; split in
  case of a tie.
  A strategy consists of for each number 1-14, three possible cards to bid, with weights for each, and
  an indication of what to do if that card is not available.  The encoding is as follows for each card:
  4 bits for the possible cards to bid, with 0 meaning lowest available and 15 as highest
  2 bits for the weights (interpreted as 1, 2, 3, 5)
  2 bits for the fallback (next lowest, next highest, a different card, and closest)
  So there are 14 x 3 x 8 = 336 total bits.
  '''
  @staticmethod
  def play (p1, p2, game_parms):
    ret = 0
    cards = [[True] * GAME_SIZE] * 2
    strats = [p1, p2]
    targets = random.sample(range(GAME_SIZE), k=GAME_SIZE)
    for round in range (GAME_SIZE):
        target = targets[round]
        for who in (0, 1):
            info = strats[who][target]
            picker = info['picker']
            for tries in range (len(picker) * 2):
                tactic = info[int(picker[random.randrange(len(picker))])]
                card = tactic['card']
                fallback = tactic['fallback']
                if card == 'high':
                    card = 14
                    fallback = 'L'
                    break
                if card == 'low':
                    card = 1
                    fallback = 'H'
                    break
                if cards[who][card-1]  or  fallback != 'D':
                    break
                fallback = 'C' # in case this is the last time through the loop
            cards[who][card-1] = False
            print (round, target, who, card, fallback)
    return 1
    # exit()

  @staticmethod
  def decode (internal):
    ret = [0] * GAME_SIZE
    for target in range (GAME_SIZE):
        ret [target] = {}
        picker = ""
        for item in range(3):
            info = {}
            val = 0
            for pos in range(8):
                val = val * 2 + internal[(target * 3 + item) * 8 + pos]
                new = True
                if pos == 3:
                    info ['card'] = 'low' if val == 0 else 'high' if val == 15 else val
                elif pos == 5:
                    picker += "".rjust((1, 2, 3, 5) [val], str(item))
                elif pos == 7:
                    info ['fallback'] = "LHDC"[val] # see details above
                else:
                    new = False
                if new:
                    val = 0
            ret [target][item] = info
        ret [target]['picker'] = picker
    return ret

  @staticmethod
  def parms ():
      return {'chrome_length': GAME_SIZE * 3 * 8}

class GeneticOverride (geneticgame.GeneticGame):
    def get_chromes (self):
        return self.chromes

eval_history = ''
def eval_logger (*args):
    global eval_history
    msg = ''
    for arg in args:
        msg += ', ' + str (arg)
    eval_history += msg[2:] + '\n'

game = GOPSGame()
gg = GeneticOverride (game, {'eval': {'static': 3, 'outputter': eval_logger}})
print ('--Lets Go!--')
ret = gg.optimize ()
print ('--Eval History--')
print (eval_history)
print ('--Final results--')
print (ret)
