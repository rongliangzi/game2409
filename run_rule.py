import gymnasium as gym
import gymnasium_env
import numpy as np
import sys
from eval_utils import *
from PIL import Image

kwargs = {'size':12, 'cls_n': 20, 'max_carry': 999, 
          'elim_n':4, 
          'img_dir': '/home/dcv-user/zhli/ubiquant/openset_20241022/dataset/train/',
          'cls_names': [30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49]
          }

class RulePolicy():
    def __init__(self, action_shape):
        self.action_shape = action_shape
    def __call__(self, obs):
        return np.random.randint(0, self.action_shape)


if __name__ =="__main__":
    env = gym.make('gymnasium_env/GAME', **kwargs)
    #env.reset()
    #sys.exit(0)
    rule_policy = RulePolicy(5)
    eval_episode_rule(rule_policy, env)
