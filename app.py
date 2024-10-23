from flask import Flask, request, jsonify
import matplotlib
matplotlib.use('Agg')
import os
from datetime import datetime
import pickle
import gymnasium as gym
import gymnasium_env
import yaml
from rule_utils import *


app = Flask(__name__)

with open('./cfg.yaml') as f:
    main_cfg = yaml.load(f, Loader=yaml.FullLoader)

legal_team_id = []
with open(main_cfg["team_id_path"]) as f:
    for l in f.readlines():
        legal_team_id.append(l.strip())
print('team_id:', legal_team_id)


def init_game(team_id, kwargs={}):
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
            print('makedirs', game_dir)
            break
    #print(datetime.now(), 'Begin game, ', kwargs)
    game_env = gym.make('gymnasium_env/GAME', **kwargs)
    obs, info = game_env.reset()
    #print(datetime.now(), 'finish reset')
    with open(f'{game_dir}/game_env.pkl', 'wb') as f:
        pickle.dump(game_env, f)
    #print(datetime.now(), 'finish dump game_env')
    return obs['image'].tolist(), obs['bag'].tolist(), obs['grid'].tolist(), game_id


def env_step(game_id, action, cls):
    #print(datetime.now(), 'begin env_step')
    game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
    with open(f'{game_dir}/game_env.pkl', 'rb') as f:
        game_env = pickle.load(f)
    #print(datetime.now(), 'finish pickle load')
    cls_penalty = 0
    if (action == 4) and (game_env.get_current_cls() != -1):
        correct = cls == game_env.get_current_cls()
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
    np.save(f'{game_dir}/cum_score.npy', game_env.get_cum_score())
    #print(datetime.now(), 'end env_step')
    return obs['bag'].tolist(), obs['grid'].tolist(), rew, term


def process_team_post(data, team_id):
    # check team id legal
    if data.get('begin', None):
        if not begin_if_can(team_id, main_cfg):
            return f'Team {team_id} has run out of game time {main_cfg["max_n"]}', 403
        param_type = data["begin"]
        if param_type not in [1, 2, 3, 4]:
            return f'begin must be in [1, 2, 3, 4], but found {param_type} with type({type(param_type)})', 400
        params = main_cfg[f'param{param_type}']
        print(f'Begin game type {data["begin"]}, team {team_id}')
        img, bag, grid, game_id = init_game(team_id, params)
        game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
        with open(f'{game_dir}/last_step_time.txt', 'w') as f:
            f.write(datetime.now().strftime('%Y%m%d %H%M%S.%f'))
        return jsonify({'is_end': False, 'img': img, 'bag':bag, 'score': 0, 'game_id': game_id, 'grid': grid})
    else:
        # continue existing game, game_id, action, cls
        game_id = data.get('game_id', None)  # str
        with open(f'{game_dir}/last_step_time.txt', 'r') as f:
            last_step_time = datetime.strptime(f.readlines()[0].strip(), '%Y%m%d %H%M%S.%f')
        time_diff = (datetime.now() - last_step_time).total_seconds()
        if game_id is None:
            print('Game id not found')
            return 'Game id not found', 400
        #print(f'Continue game, id: {game_id}')
        game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
        if os.path.exists(f'{game_dir}/finish.txt'):
            print('Game has finished')
            return 'Game has finished', 400
        action = data.get('action', None)
        if action is None:
            print('Action cannot be None')
            return 'Action cannot be None', 400
        cls = data.get('cls', None)
        if (action == 4) and (cls is None):
            print('Cls data cannot be None')
            return 'Cls data cannot be None', 401
        bag, grid, score, is_end = env_step(game_id, action, cls)
        if time_diff > float(main_cfg['max_step_seconds']):
            print(f"time_diff:{time_diff:.6f}, max_step_seconds:{float(main_cfg['max_step_seconds']):.1f}")
            score += main_cfg['timeout_penalty']
        result = {'is_end': is_end, 'bag': bag, 'score': score, 'game_id': game_id, 'grid': grid}
        return jsonify(result)


@app.route('/', methods=['POST'])
def handle_client():
    try:
        data = request.get_json()
        team_id = data.get('team_id', None)
        if team_id is None:
            return "team_id is none", 403
        elif team_id in legal_team_id:
            return process_team_post(data, team_id)
        else:
            print(f'team_id:{team_id} illegal')
            return "team_id illegal", 402
    except Exception as e:
        print(f'Error: {str(e)}')
        return jsonify({'status': e, 'message': str(e)}), 500


if __name__=="__main__":
    app.run(host='0.0.0.0', port=8081)
