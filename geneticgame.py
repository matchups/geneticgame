import copy
import json
from scipy.stats import poisson
import random
import re
import sys

def defaulter (dict, defaults):
    '''
    Utility to load defaults into a dictionary if nothing is there
    '''
    for key in defaults:
        if key not in dict:
            dict[key] = defaults[key]

class GeneticGame:
  '''
  Class to implement a genetic algorithm to optimize game play.
  '''
  def __init__ (self, _game, _parms):
    '''
    Constructor will initialize itself with game and parameters passed in, plus
    parameters specified by the game object and optionally on the command line.
    Will create a random initial collection of chromosomes.
    May also set up random opponents for static evaluation of chromosomes.
    '''
    self.game = _game
    self.parms = copy.deepcopy(_parms)
    parms_fn = getattr(self.game, "parms", None)
    if parms_fn:
        self.parms = {**self.parms, **parms_fn()}
    self.gen = 0
    eval = self.parms['eval'] if 'eval' in self.parms else False
    defaulter (self.parms, {'carryover': 0, 'chrome_length': -1, 'crossovers': 1, 'debug': 0, 'eval': {}, 'game_parms': {}, 'load': False, \
        'log': True, 'matches_per_round': 20, 'mutations': 1, 'population': 50, 'result': {}, 'rounds': 50, 'save': False, 'style': "B", 'survivor_ratio': .5, \
        'use_args': True, 'crossovers_fn': self.crossovers, 'mutations_fn': self.mutations, 'pairing_fn': self.pairing_random})
    self.chromes = {}
    defaulter (self.parms['eval'], {'end': True, 'interval': 1, 'start': True, 'style': 'A', 'top_count': 1, 'outputter': print})
    defaulter (self.parms['result'], {'score': True, 'external': True, 'internal': False, 'bitstring': False, 'count': 3, 'type': 'T'})

    # Parse arguments on command line
    if self.parms['use_args']:
        args = sys.argv
        args.append ('') # so we can always get 'next'
        skip = False
        for argpos in range (1, len (args) - 1):
            arg = args[argpos]
            argparse = re.match ("(.*)=(.*)", arg)
            fntag = ''
            if argparse:
                arg = argparse.group (1)
                next = argparse.group (2)
                equals = True
            else:
                next = args[argpos + 1]
                equals = False
            if next == 'True':
                next = True
            elif next == 'False':
                next = False
            elif re.match ("-?[0-9]+", next):
                next = int(next)
            elif re.match ("^P[0-9]+", next):
                next = int(next[1:])
                fntag = '_poisson'
            if skip:
                skip = False
            else:
                argparse = re.match ("^-(([a-z_]*)\.)?([a-z_]*)$", arg)
                if argparse:
                    main = argparse.group (2)
                    sub = argparse.group (3)
                    skip = not equals
                    if main:
                        if main not in self.parms:
                            self.parms[main] = {}
                        self.parms[main][sub] = next
                        self.parms[main]['.commandline'] = True
                    else:
                        self.parms [sub] = next
                        if fntag:
                            subfn = sub + '_fn'
                            if subfn in self.parms:
                                fnname = self.parms[subfn].__name__ + fntag
                                self.parms[subfn] = getattr (self, fnname)
                                fntag = ''
                else:
                    exit (f"Bad command line argument {arg}")
                if fntag:
                    exit (f"Function override not available for {arg}")

    if self.parms['chrome_length'] < 1:
        exit (f"Positive chromosome length must be specified")

    # Create initialset of chromosomes
    for num in range (self.parms['population']):
        self.chromes[num] = {'genes': self.initializer(), 'score': 0, 'generation': 0, 'parents': (None, None), 'id': num}
    self.max_id = self.parms['population']

    # Disable or tweak 'eval' functionality if applicable
    if not eval  and  '.commandline' not in self.parms['eval']: # All that's there are defaults
        self.parms['eval'] = False
    elif self.parms['eval']['top_count'] < 0:
            self.parms['eval']['top_count'] = self.parms['population']
    # Create a random static set of opponents
    static = self.parms['eval']['static']
    if type(static) == int:
        self.parms['eval']['static'] = [0] * static
        for opp_num in range (static):
            self.parms['eval']['static'][opp_num] = self.game.decode(self.initializer())

    # What function will be used to perform mutations?
    if 'flip_fn' not in self.parms:
        self.parms['flip_fn'] = getattr (self, 'flip' + self.parms['style'].lower())

    # Set up for a round-robin, if desired
    if self.parms['matches_per_round'] == -1:
        self.parms['matches_per_round'] = self.parms['population'] - 1
        self.parms['pairing_fn'] = self.pairing_rr

    if self.parms['debug']:
        print ('--Parameters--')
        parms = copy.deepcopy (self.parms)
        parms ['eval']['static'] = f"Array[{len(parms ['eval']['static'])}]"
        print (parms)

  '''
  Structure of chromosome objects...
  chrome[seq]
    .id
    .genes[]
    .score
    .generation
    .parents[]
  '''

  def optimize (self):
    ''' Main routine to run tournaments and do evolutionary optimization
    '''
    self.load (self.parms['load'])
    eval_res = self.eval(self.parms['eval']['start'])
    while True:
        if self.parms['log']:
            self.log ()
        self.tournament ()
        eval_res = self.eval(self.check_eval())
        self.gen += 1
        if self.check_complete (eval_res):
            break
        self.evolve ()
    self.eval(self.parms['eval']['end'])
    self.save (self.parms['save'])

    return self.final (self.parms['result'])

  def build_descendants (self, parent_genes):
      ''' Build a pair of new descendant chromosomes from the parents
      '''
      new_genes = copy.deepcopy(parent_genes)
      for cross_point in random.sample(range(self.parms['chrome_length']), k=self.parms['crossovers_fn']()):
          new_genes = [new_genes[0][:cross_point] + new_genes[1][cross_point:], new_genes[1][:cross_point] + new_genes[0][cross_point:]]
      for who in (0, 1):
          for change_point in random.sample(range(self.parms['chrome_length']), k=self.parms['mutations_fn']()):
              new_genes[who][change_point] = self.parms['flip_fn'](new_genes[who][change_point], change_point)
      return new_genes

  def check_complete (self, eval_results):
    ''' Check if it's time to stop
    '''
    return self.gen >= self.parms['rounds']

  def check_eval (self):
    ''' Check if we should run the static evaluation now
    '''
    return self.parms['eval']  and  self.parms['eval']['interval']  and  self.gen % self.parms['eval']['interval'] == 0

  def crossovers (self):
    ''' Return number of crossovers to make
    '''
    return self.parms['crossovers']

  def crossovers_poisson (self):
    ''' As above, but when it is a random variate
    '''
    return poisson.rvs(self.parms['crossovers'])

  def descendants(self, rank, chrome):
    '''
    Determine number of descendants that a chromosome should have, based on its rank in the population
    or (possibly in a child class) other information.
    '''
    return 2 if rank * 3 < self.parms['population'] else (1 if rank * 3 < self.parms['population'] * 2 else 0)

  def eval(self, whether):
    ''' Run a static evaluation to see if we are actually getting better chromosomes.
    '''
    # General initialization
    if not self.parms['eval']  or  not whether:
        return
    eval_parms = self.parms['eval']
    if 'static' not in eval_parms  or  not len (eval_parms['static']):
        raise Exception ("Nothing to evaluate")
    top_count = eval_parms['top_count']
    top_chromes = self.get_top(top_count)
    eval_res = [0.0] * top_count
    opponents = eval_parms['static']

    # Build structures to provide information on results
    if eval_parms['style'] == 'A':
        total = 0
        def a_updater (cnum, score):
            nonlocal total
            total += score
        updfn = a_updater
        retfn = lambda: total
    else:
        data = [0] * top_count
        def d_updater (cnum, score):
            data[cnum] = {'id': self.chromes[top_chromes[cnum]]['id'], 'score': score}
        updfn = d_updater
        retfn = lambda: data

    # Loop through leading chromosomes and play static opponents
    for cnum in range (top_count):
        score = 0.0
        player = self.genes (top_chromes[cnum])
        for onum in range (len(opponents)):
            res = self.game.play (player, opponents[onum], self.parms['game_parms'])
            if isinstance (res, tuple): # Get just our score and ignore opponent's
                res, dummy_opp_score = res
            score += res
        updfn (cnum, score)

    # Output results
    eval_parms['outputter'] (retfn())

  def evolve (self):
    ''' Create the next generation
    '''
    # Get a collection of parents (generally, the best-performing chromosomes of the previous generation
    counter = 0
    chrome_count = len(self.chromes)
    parents = []
    for seq in self.get_top():
        for dummy in range (self.descendants(counter, self.chromes[seq])):
            parents.append (seq)
        counter += 1

    # Add a few more if we didn't get enough
    for dummy in range (chrome_count - counter):
        parents.append (parents[random.randrange(counter)])

    new_chromes = {}
    already_survived = [False] * chrome_count
    par = [None, None]
    counter = 0
    # Loop through random pairs of parents
    for rs in random.sample(range(chrome_count), k=chrome_count):
        if par[0] != None: # Funny logic because numeric zero is okay
            par[1] = rs
            score = 0
            chrome = [0, 0]
            genes = [0, 0]
            ids = [0, 0]
            # Collect information on parents
            for who in (0, 1):
                chrome[who] = self.chromes[par[who]]
                genes [who] = chrome[who]['genes']
                ids [who] = chrome[who]['id']
                score += chrome[who]['score'] / 2
            # Build descendants and copy to next generation
            desc = self.build_descendants (genes)
            # See if one of them will survive instead of evolving, trying not to do the same one twice
            surv_now = [False, False]
            srat = self.survivor_ratio () * 2
            if srat - 1 > random.random(): # Will always be false if srat < 1; that's okay
                surv_now = [True, True]
            elif srat > random.random(): # Will always be true if srat > 1; that's okay
                surv_now [1 if already_survived[par[0]] else 0] = True
            for desc_num in (0, 1):
                if surv_now[desc_num]:
                    new_chromes[counter] = copy.deepcopy(chrome[desc_num])
                else:
                    new_chromes[counter] = {'id': self.max_id, 'genes': desc[desc_num], 'score': score, 'generation': self.gen, 'parents': ids}
                    self.max_id += 1
                counter += 1
            par[0] = None
        else:
            par[0] = rs
    self.chromes = new_chromes

  def final (self, result_parms):
    ''' Output chromosome information at the end
    '''
    msg = ''
    sep = ''
    for arg in ('all', 'bitstring', 'external', 'internal'):
        if result_parms.get(arg):
            sep = '\n'
    count = result_parms['count']
    if count < 0:
        count = len (self.chromes)
    best = []

    # Loop through best chromosomes and collect information for reporting
    for seq in self.get_top(count):
        chrome = self.chromes[seq]
        best.append (copy.deepcopy (chrome))
        genes = chrome.pop ('genes')
        score = chrome.pop ('score')
        all = result_parms.get('all')
        if msg:
            msg += sep
        if result_parms ['score']  or  all:
            if sep:
                msg += "score="
            msg += f"{score} "
        if result_parms ['bitstring']  or  all:
            msg += str (genes) + ' '
        if result_parms ['external']  or  all:
            msg += str (self.game.decode (genes)) + ' '
        if result_parms ['internal']  or  all:
            msg += str (chrome)

    return msg if result_parms['type'] == 'T' else best

  def flipf (self, oldval, pos):
      ''' Mutate a numeric value by random choice
      '''
      return random.random()

  def flipb (self, oldval, pos):
      ''' Mutate a bit by flipping it
      '''
      return 1 - oldval

  def genes (self, player_num):
    ''' Return the decoded genes for a specified player
    '''
    return self.game.decode (self.chromes[player_num]['genes'])

  def get_top (self, top_count = None):
      ''' Get the top N chromosomes
      '''
      return sorted (self.chromes, key=lambda x: self.chromes[x]['score'], reverse=True)[:top_count]

  def initializer (self):
    ''' Create a random set of initial chromosomes
    '''
    ret = [0] * self.parms['chrome_length']
    for gene in range (self.parms['chrome_length']):
      ret[gene] = random.randrange (2) if self.parms['style'] == 'B' else random.random()
    return ret

  def load (self, fn):
    ''' Load a previously-saved set of chromosomes
    '''
    if fn:
        self.chromes = json.load(open(fn, "r"))

  def log (self):
    ''' Log the current generation number
    '''
    print (self.gen)

  def mutations (self):
    ''' Return number of mutations to make
    '''
    return self.parms['mutations']

  def mutations_poisson (self):
    ''' As above, but when it is a random variate
    '''
    return poisson.rvs(self.parms['mutations'])

  def pairing_random (self, roundnum):
      ''' Create a random set of pairings for this round
      '''
      return random.sample(range(len(self.chromes)), k=len(self.chromes))

  def pairing_rr (self, roundnum):
      ''' Create a round-robin set of pairings for this round
      '''
      if not roundnum:
          self.pairing_table = self.rrpair ()
      return self.pairing_table[roundnum]

  def rrpair (self):
      ''' Create a round-robin pairing table
      '''
      chrome_count = len(self.chromes)
      table_count = int (chrome_count / 2)
      table = [0] * table_count
      ret = [0] * (chrome_count - 1)
      for col in range (table_count):
          table [col] = [col, chrome_count - 1 - col]
      for round in range (chrome_count - 1):
        round_order = [0] * chrome_count
        for col in range (table_count):
            round_order [col*2] = table [col][0]
            round_order [col*2 + 1] = table [col][1]
        ret[round] = round_order
        newtable = [0] * table_count
        for col in range (table_count):
            if col == 0:
                left = 0
            elif col == 1:
                left = table[0][1]
            else:
                left = table[col-1][0]
            if col == table_count - 1:
                right = table[col][0]
            else:
                right = table[col+1][1]
            newtable [col] = [left, right]
        table = newtable
      return ret

  def save (self, fn):
    ''' Save the chromosomes to a file
    '''
    if fn:
        json.dump(self.chromes, open(fn, "w"))

  def survivor_ratio (self):
    ''' How many of the next generation chromosomes are survivors from this round; the remainder are generated by reproduction
    '''
    return self.parms['survivor_ratio']

  def tournament (self):
      ''' Run a tournament and update each chromosome's score based on the results
      '''
      chrome_count = len(self.chromes)
      for chnum in range (chrome_count):
          self.chromes[chnum]['score'] *= self.parms['carryover']

      # Play some matches in each round of the tournament
      for roundnum in range (self.parms ['matches_per_round']):
          chlist = self.parms['pairing_fn'](roundnum) # Get pairings for this round
          for matchnum in range (0, chrome_count, 2):
              p1 = chlist[matchnum]
              p2 = chlist[matchnum+1]
              # Get results of one match from the game object
              ret = self.game.play (self.genes(p1), self.genes(p2), self.parms['game_parms'])
              if self.parms['debug']:
                  print (f"{self.gen}.{roundnum} {p1} vs {p2} -> {ret}")
              if isinstance (ret, tuple):
                  s1, s2 = ret # non-zero-sum game, so each player has their own score
              else:
                  s1 = ret # zero-sum game, so player two's score is the inverse of player one's
                  s2 = -ret
              self.chromes[p1]['score'] += s1
              self.chromes[p2]['score'] += s2
