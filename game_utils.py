import os
from datetime import datetime
import gymnasium as gym
import gymnasium_env
import pickle


def init_game(team_id, main_cfg, kwargs={}):
    if not os.path.exists(os.path.join(main_cfg["save_dir"], team_id)):
        os.mkdir(os.path.join(main_cfg["save_dir"], team_id))
    now = datetime.now()
    time_key = now.strftime("%Y%m%d-%H%M%S")
    game_id = f'{team_id}_{time_key}'
    game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
    while True:
        try:
            os.makedirs(game_dir, exist_ok=False)
        except OSError as e:
            print(e, 'add a to game_id')
            game_id = game_id +'a'
            game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
        else:
            #print('makedirs', game_dir)
            break
    #print(datetime.now(), 'Begin game, ', kwargs)
    for k in ['img_dir', 'cls_names']:
        kwargs[k] = main_cfg[k]
    game_env = gym.make('gymnasium_env/GAME', **kwargs)
    obs, info = game_env.reset()
    #print(datetime.now(), 'finish reset')
    with open(f'{game_dir}/game_env.pkl', 'wb') as f:
        pickle.dump(game_env, f)
    #print(datetime.now(), 'finish dump game_env')
    return obs['image'].tolist(), obs['bag'].tolist(), obs['grid'].tolist(), game_id


def env_step(game_id, main_cfg, action, cls):
    #print(datetime.now(), 'begin env_step')
    game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
    with open(f'{game_dir}/game_env.pkl', 'rb') as f:
        game_env = pickle.load(f)
    #print(datetime.now(), 'finish pickle load')
    cls_penalty = 0
    if (action == 4) and (game_env.unwrapped.get_current_cls() != -1):
        correct = cls == game_env.unwrapped.get_current_cls()
        if not correct:
            cls_penalty = -0.1
    obs, rew, term, _, info = game_env.step(action)
    #print(datetime.now(), 'finish step')
    rew += cls_penalty
    with open(f'{game_dir}/game_env.pkl', 'wb') as f:
        pickle.dump(game_env, f)
    #print(datetime.now(), 'finish pickle dump')
    if term:
        with open(f'{game_dir}/finish.txt', 'w') as f:
            f.write('finish')
    #print(datetime.now(), 'end env_step')
    return obs['bag'].tolist(), obs['grid'].tolist(), rew, term
