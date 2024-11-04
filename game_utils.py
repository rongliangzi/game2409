import os
from datetime import datetime
import time
import gymnasium as gym
import gymnasium_env
import pickle
import numpy as np
import fcntl

action_only_game_types = ['a', 'b', 'c', 'd']
full_game_types = [str(i) for i in range(10)]
all_game_types = action_only_game_types + full_game_types
game_type_dic = {'a': '2', 'b': '3', 'c': '4', 'd': '5', 'e': '5'}


def gen_game_result(game_dir, begin):
    # generate game result when initing a game
    with open(f'{game_dir}/game_result.pkl', 'wb') as f:
        pickle.dump({'cum_score': 0, 'begin': begin, 'rounds': 0, 'acc': None, 'time_itv': []}, f)


def update_acc_if_need(game_result, grid_pred, init_grid, game_dir):
    # calculate cls acc only when on step=1, update game_result
    if (game_result['rounds'] == 0) and (game_result['begin'][0] in full_game_types):
        grid_pred = np.array(grid_pred, dtype=int)
        acc = (grid_pred == init_grid).sum() / init_grid.size
        game_result['acc'] = acc
        with open(f'{game_dir}/game_result.pkl', 'wb') as f:
            pickle.dump(game_result, f)
        np.save(f'{game_dir}/grid_pred.npy', grid_pred)


def update_game_result(game_dir, score, itv, is_end, main_cfg, game_id):
    # update cum_score, rounds on every step
    with open(f'{game_dir}/game_result.pkl', 'rb') as f:
        game_result = pickle.load(f)
        game_result['rounds'] += 1
        game_result['time_itv'].append(itv)
        if is_end:
            game_result['time_itv'] = np.median(game_result['time_itv'])
            score += get_time_penalty(game_result['time_itv'], main_cfg, game_id)
        game_result['cum_score'] += score
    with open(f'{game_dir}/game_result.pkl', 'wb') as f:
        pickle.dump(game_result, f)
    return score


def get_time_penalty(time_diff, main_cfg, game_id):
    # calculate timeout penalty
    if time_diff > 2*float(main_cfg['max_step_seconds']):
        print(f"{game_id}, time_diff:{time_diff:.3f}, max_step_seconds:{float(main_cfg['max_step_seconds']):.1f}")
        return main_cfg['timeout_penalty'] * 10
    elif time_diff > float(main_cfg['max_step_seconds']):
        print(f"{game_id}, time_diff:{time_diff:.3f}, max_step_seconds:{float(main_cfg['max_step_seconds']):.1f}")
        return main_cfg['timeout_penalty']
    return 0


def check_step_data(game_id, game_dir, action, cls, grid_pred):
    # check data from client if legal
    if game_id is None:
        return 'Game id not found', 400
    if os.path.exists(f'{game_dir}/finish.txt'):
        return 'Game has finished', 400
    if action is None:
        return 'Action cannot be None', 400
    #if (action == 4) and (cls is None):
    #    return 'Cls data cannot be None', 401
    with open(f'{game_dir}/game_result.pkl', 'rb') as f:
        game_result = pickle.load(f)
    if (game_result['rounds'] == 0) and (grid_pred is None) and (game_result['begin'][0] in full_game_types):
        return 'Grid_cls not provided', 400
    return '', 200


def save_step_time(game_dir):
    # save time when ending this step, used to calculate timeout when recv next data from client
    with open(f'{game_dir}/last_step_time.txt', 'w') as f:
        f.write(datetime.now().strftime('%Y%m%d %H%M%S.%f'))


def check_begin(main_cfg, begin):
    # check begin legal
    # a~d for action only, 0~9 for full game
    if not ((len(begin) == 6) and (begin[0] in all_game_types) and (all(['0'<=b<='9' for b in begin[1:]]))):
        return False
    # check if init game data exists
    game_type = begin[0]
    type_dir = game_type_dic.get(game_type, game_type)
    game_data_id = begin[1:]
    grid_path = os.path.join(main_cfg['init_game_data_dir'], type_dir, game_data_id, 'grid.npy')
    loc_path = os.path.join(main_cfg['init_game_data_dir'], type_dir, game_data_id, 'loc.npy')
    return os.path.exists(grid_path) and os.path.exists(loc_path)


def get_init_grid_loc(cfg, main_cfg, type_dir, game_data_id):
    cfg['init_grid'] = np.load(os.path.join(main_cfg['init_game_data_dir'], type_dir, game_data_id, 'grid.npy')).astype(int)
    cfg['init_loc'] = np.load(os.path.join(main_cfg['init_game_data_dir'], type_dir, game_data_id, 'loc.npy')).astype(int)


def get_game_id_dir(main_cfg, team_id, time_key):
    # in case of multi requests at the same time
    game_id = f'{team_id}_{time_key}'
    game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
    while True:
        try:
            os.makedirs(game_dir, exist_ok=False)
        except OSError as e:
            #print(e, 'add a to game_id')
            game_id = game_id +'a'
            game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
        else:
            #print('makedirs', game_dir)
            break
    return game_id, game_dir


def init_game(team_id, main_cfg, begin):
    # init a game from existing game_data
    time_str = ''
    st = time.time()
    game_type = begin[0]
    param_type = type_dir = game_type_dic.get(game_type, game_type)
    game_data_id = begin[1:]
    #print(f'Begin game type {game_type}, team {team_id}')
    env_args = main_cfg[f'param{param_type}']
    now = datetime.now()
    time_key = now.strftime("%Y%m%d-%H%M%S")
    time_str += f'{datetime.now()}, Begin game'
    game_id, game_dir = get_game_id_dir(main_cfg, team_id, time_key)
    for k in ['img_dir', 'cls_names']:
        env_args[k] = main_cfg[k]
    get_init_grid_loc(env_args, main_cfg, type_dir, game_data_id)
    game_env = gym.make('gymnasium_env/GAME', **env_args)
    obs, info = game_env.reset()
    time_str += f'{datetime.now()}, finish reset'
    with open(f'{game_dir}/game_env.pkl', 'wb') as f:
        pickle.dump(game_env, f)
    time_str += f'{datetime.now()}, finish dump game_env'
    gen_game_result(game_dir, begin)
    save_step_time(game_dir)
    if game_type in full_game_types:
        obs['grid'] *= 0
    if time.time() - st > 1:
        print(f'Env init too long time {game_id}\n', time_str)
    return obs['image'].tolist(), obs['bag'].tolist(), obs['grid'].tolist(), obs['loc'].tolist(), game_id


def get_cls_penalty(action, label_cls, cls):
    # calculate cls acc penalty
    if (action == 4) and (label_cls !=-1) and (label_cls != cls):
        return -0.1
    return 0


def update_grid_if_need(grid, game_result, game_dir):
    # for full game, using prediction as grid
    if game_result['begin'][0] in action_only_game_types:
        return grid
    new_grid = np.load(f'{game_dir}/grid_pred.npy')
    new_grid[grid==-1] = -1
    min_pos = np.unravel_index(np.argmin(grid), grid.shape)
    new_grid[min_pos] = np.min(grid)
    return new_grid


def lock_minus_txt(fpath):
    # write count - 1
    file_desc = os.open(fpath, os.O_RDWR|os.O_CREAT)
    with os.fdopen(file_desc, 'r+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        content = f.read().strip()
        count = int(content) if content else 0
        f.seek(0)
        f.write(str(max(count-1, 0)))
        f.truncate()
        fcntl.flock(f, fcntl.LOCK_UN)


def env_step(game_id, main_cfg, action, cls, grid_pred):
    # update env, send new data to client
    time_str = ''
    st = time.time()
    time_str += f'{datetime.now()}, begin env_step\n'
    game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
    with open(f'{game_dir}/game_env.pkl', 'rb') as f:
        game_env = pickle.load(f)
    with open(f'{game_dir}/game_result.pkl', 'rb') as f:
        game_result = pickle.load(f)
    update_acc_if_need(game_result, grid_pred, game_env.unwrapped.get_init_grid(), game_dir)
    time_str += f'{datetime.now()} finish pickle load\n'
    cls_penalty = get_cls_penalty(action, game_env.unwrapped.get_current_cls(), cls)
    obs, rew, term, _, info = game_env.step(action)
    time_str += f'{datetime.now()} finish step\n'
    # since acc is logged, penalty is ignored here
    #rew += cls_penalty
    with open(f'{game_dir}/game_env.pkl', 'wb') as f:
        pickle.dump(game_env, f)
    if term:
        with open(f'{game_dir}/finish.txt', 'w') as f:
            f.write('finish')
        # release a connection
        #print(np.median(game_result['time_itv']))
        lock_minus_txt(os.path.join(main_cfg['save_dir'], game_id.split('_')[0], 'connections.txt'))
    time_str += f'{datetime.now()} end env_step\n'
    grid = update_grid_if_need(obs['grid'], game_result, game_dir)
    save_step_time(game_dir)
    if time.time() - st > 1:
        print(f'Env step too long time {game_id}\n', time_str)
    return obs['bag'].tolist(), grid.tolist(), obs['loc'].tolist(), rew, term
