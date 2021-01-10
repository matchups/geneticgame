import geneticgame

class TestGame ():
  @staticmethod
  def play (p1, p2, game_parms):
    ret = 0
    for foo in range (10):
        p1v, p2v = p1[foo], p2[foo]
        if p1v != p2v:
            ret += p2v - p1v + (10 if p1v > p2v else -10)
    if ret < 3:
        return ret
    return ret, -3

  @staticmethod
  def decode (internal):
    ret = [0] * 10
    for foo in range (10):
        val = 0
        for bar in range (5):
            val = val * 2 + internal[foo*5 + bar]
        ret[foo] = val
    return ret

class GeneticOverride (geneticgame.GeneticGame):
    def get_parms (self):
        return self.parms

eval_history = ''
def eval_logger (*args):
    global eval_history
    msg = ''
    for arg in args:
        msg += ', ' + str (arg)
    eval_history += msg[2:] + '\n'

gg = GeneticOverride (TestGame(), {'eval': {'static': 3, 'outputter': eval_logger}})
print ('--Parameters--')
print (gg.get_parms())
print ('--Lets Go!--')
ret = gg.optimize ()
print ('--Eval History--')
print (eval_history)
print ('--Final results--')
print (ret)
