import copy
import random

import geneticgame

GAME_SIZE = 4
GROUPS = (GAME_SIZE * (GAME_SIZE + 1)) // 2 - 2
BITS_PER_GROUP = 3
DIR_NAMES = 'NWSE'
DIR_CODES = [[0, -1], [-1, 0], [0, 1], [1, 0]]

last_ten = [0] * 10
which = 0
totcount = 0

class chaseGame ():
  '''
  For coordinates 0,1 0,2 0,3 1,1 1,2 1,3 2,2 2,3, three bits each: preferred direction
  as N W S E in two bits and the third bit as to whether to be -1 or +1 in the
  perpendicular direction if it is blocked
  '''

  @staticmethod
  def play (p1, p2, game_parms):
    ret = 0
    pos = [2, 2]
    px = [p1, p2]
    who = 0
    last = 99
    count = 0
    game_log = "22 "
    while True:
        tactic = px[who][pos[0]][pos[1]]
        dir = tactic [0]
        if dir == 'X':
            winner = int (tactic[1])
            game_log += f"-->{winner}"
            break
        if abs(dir - last) == 2: # We are trying to backtrack
            dir = (dir + tactic[1]) % 2
        codes = DIR_CODES [dir]
        for coord in (0, 1):
            pos[coord] += codes[coord]
            if pos[coord] < 0:
                pos[coord] = 2
                dir += 2
            elif pos[coord] > 3:
                pos[coord] = 1
                dir -= 2
        game_log += f"{who}{DIR_NAMES[dir]}{pos[0]}{pos[1]} "
        last = dir
        who = 1 - who
        count += 1
        if count > 20:
            winner = .5
            game_log += "-->T"
            break
    return {'score': 1 - winner * 2, 'log': game_log} # 0 -> 1, 1 -> -1

  @staticmethod
  def decode (internal):
    index = [['X0', 0, 1, 2], [0, 3, 4, 5], [1, 4, 6, 7], [2, 5, 7, 'X1']]
    ret = [0] * GAME_SIZE
    for x in range (GAME_SIZE):
      ret[x] = [0] * GAME_SIZE
      for y in range (GAME_SIZE):
          sub = index[x][y]
          if isinstance (sub, int):
              bits = internal[sub * 3: (sub+1) * 3]
              dir, alt = bits[0]*2 + bits[1], bits[2]*2 - 1
              if y > x:
                  dir = (1, 0, 3, 2)[dir]
              ret[x][y] = [dir, alt]
          else:
              ret[x][y] = sub
    return ret

  @staticmethod
  def display (internal):
    if 'genes' in internal:
        decoded = chaseGame.decode (internal['genes'])
    elif len (internal) == 24:
        decoded = chaseGame.decode (internal)
    else:
        decoded = internal
    ret = ''
    for x in range (GAME_SIZE):
      for y in range (GAME_SIZE):
          sub = decoded[x][y]
          if isinstance (sub, str):
              ret += '!!'
          else:
              ret += DIR_NAMES[sub[0]] + '<.>'[sub[1]+1]
      ret += ' '
    return ret + f" {chaseGame.quality(decoded)}"

  @staticmethod
  def quality (decoded):
    count = 0
    for x in range (GAME_SIZE):
      for y in range (GAME_SIZE):
          move = decoded[x][y][0]
          if isinstance (move, int):
              count += ((move > 1) * 2 - 1) * (((x + y) % 2) * 2 - 1)
    return count

  @staticmethod
  def parms ():
      return {'chrome_length': GROUPS * BITS_PER_GROUP}

class GeneticOverride (geneticgame.GeneticGame):
    def get_chromes (self):
        return self.chromes

    def log (self):
        if self.gen % 5 == 0:
            global totcount
            print (self.gen, totcount / self.parms['matches_per_round'])
        totcount = 0

    def eval_logger (self, results, logs):
        global last_ten, which
        last_ten [which] = results
        which = (which + 1) % 10
        tot = 0
        for lt in last_ten:
            tot += lt
        print (results, tot / 10.0)
        if logs:
            fn = open (f"evallogs{self.gen}.log", "w")
            for game in logs:
                fn.write (f"{game} {logs[game]}\n")
            fn.close()

    def evolve (self):
        desc_count = {}
        for temp in range(2):
            if self.gen == 25:
                print ('After' if temp else 'Before')
                counter = 0
                for seq in self.get_top():
                    chrome = self.chromes[seq]
                    id = chrome['id']
                    if temp:
                        parents = [0, 0]
                        for p in range(2):
                            who = chrome['parents'][p]
                            parents[p] = f"{who} ({desc_count.get(who, 0)})"
                    else:
                        desc_count[id] = dc = self.descendants(counter, chrome)
                    dmsg = f"*{dc}" if not temp else ''
                    msg = f"{seq:2}{dmsg} score= {chrome['score']}"
                    gen = chrome['generation']
                    msg += (f" parent={parents}" if gen==self.gen else f" gen={gen}") if temp else f" id={id}"
                    counter += 1
                    print (msg, self.game.display(chrome))

            if temp == 0:
                super().evolve ()

    def pregame (self, p1, p2):
        global oldscore
        px = [p1, p2]
        for n in range(2):
            oldscore[n] = self.chromes[px[n]]['score']
    def postgame (self, p1, p2):
        global oldscore, totcount
        px = [p1, p2]
        for n in range(2):
            qual = self.game.quality(self.game.decode(self.chromes[px[n]]['genes']))
            totcount += qual
            # print (self.game.display(self.chromes[px[n]]), qual, oldscore[n], '-->', self.chromes[px[n]]['score'])

game = chaseGame()
gg = GeneticOverride (game, {'eval': {'static': 3, 'outputter': "eval_logger"}})
oldscore = [0, 0]
print ('--Lets Go!--')
ret = gg.optimize ()
print ('--Final results--')
print (ret)
