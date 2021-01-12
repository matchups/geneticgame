import random

import geneticgame

GAME_SIZE = 14
GROUPS = 3
BITS_PER_GROUP = 8

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
    cards = [[True] * GAME_SIZE, [True] * GAME_SIZE]
    strats = [p1, p2]
    targets = random.sample(range(GAME_SIZE), k=GAME_SIZE)
    score = [0, 0]
    final = [0, 0]
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
            if cards[who][card-1]:
                testers = [card]
            else:
                if fallback == 'L': # next lowest, if possible
                    testers = list(reversed(range(1, card))) + list (range (card+1, GAME_SIZE+1))
                elif fallback == 'H': # next highest
                    testers = list(range (card+1, GAME_SIZE+1)) + list(reversed(range(1, card)))
                elif fallback == 'C': # closest
                    testers = sorted (range(1, GAME_SIZE+1), key=lambda x: abs(card-x) + random.random() / 2) # randomness so we don't always start
                    # with lower or always with higher
                else:
                    raise Exception ("bad fallback method")
            for good_card in testers:
                if cards[who][good_card-1]:
                    break
            # print (round, target, who, card, fallback, testers, good_card)
            cards[who][good_card-1] = False
            final[who] = good_card
        if (final[0] > final[1]):
            score[0] += target + 1
        elif (final[1] > final[0]):
            score[1] += target + 1
        # print ('...', score)
        diff = score[0] - score[1]
        return (diff + 20) if diff > 0 else ((diff - 20) if diff < 0 else 0)

  @staticmethod
  def decode (internal):
    ret = [0] * GAME_SIZE
    for target in range (GAME_SIZE):
        ret [target] = {}
        picker = ""
        for item in range(GROUPS):
            info = {}
            val = 0
            for pos in range(BITS_PER_GROUP):
                val = val * 2 + internal[(target * GROUPS + item) * BITS_PER_GROUP + pos]
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
  def display (internal):
      ret = ''
      for target in range (GAME_SIZE):
          if target:
              ret += ' '
          for item in range(GROUPS):
              val = 0
              if item:
                  ret += '|'
              for pos in range(BITS_PER_GROUP):
                  val = val * 2 + internal[(target * GROUPS + item) * BITS_PER_GROUP + pos]
                  new = True
                  if pos == 3:
                      ret += 'L' if val == 0 else 'H' if val == 15 else str(val) if val < 10 else chr(val+55) # 10 -> A
                  elif pos == 5:
                      ret += str ((1, 2, 3, 5) [val])
                  elif pos == 7:
                      ret += "LHDC"[val] # see details above
                  else:
                      new = False
                  if new:
                      val = 0
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
gg = GeneticOverride (game, {'eval': {'static': 3, 'xoutputter': eval_logger}})
print ('--Lets Go!--')
ret = gg.optimize ()
print ('--Eval History--')
print (eval_history)
print ('--Final results--')
print (ret)
