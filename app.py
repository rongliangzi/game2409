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
from game_utils import *


app = Flask(__name__)

with open('./cfg.yaml') as f:
    main_cfg = yaml.load(f, Loader=yaml.FullLoader)

legal_team_id = []
with open(main_cfg["team_id_path"]) as f:
    for l in f.readlines():
        legal_team_id.append(l.strip())
print('team_id:', legal_team_id)


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
        img, bag, grid, game_id = init_game(team_id, main_cfg, params)
        game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
        with open(f'{game_dir}/last_step_time.txt', 'w') as f:
            f.write(datetime.now().strftime('%Y%m%d %H%M%S.%f'))
        with open(f'{game_dir}/game_result.pkl', 'wb') as f:
            pickle.dump({'cum_score': 0, 'game_type': param_type}, f)
        return jsonify({'is_end': False, 'img': img, 'bag':bag, 'score': 0, 'game_id': game_id, 'grid': grid})
    else:
        # continue existing game, game_id, action, cls
        game_id = data.get('game_id', None)  # str
        game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
        with open(f'{game_dir}/last_step_time.txt', 'r') as f:
            last_step_time = datetime.strptime(f.readlines()[0].strip(), '%Y%m%d %H%M%S.%f')
        time_diff = (datetime.now() - last_step_time).total_seconds()
        if game_id is None:
            print('Game id not found')
            return 'Game id not found', 400
        #print(f'Continue game, id: {game_id}')
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
        bag, grid, score, is_end = env_step(game_id, main_cfg, action, cls)
        if time_diff > float(main_cfg['max_step_seconds']):
            print(f"{game_id}, time_diff:{time_diff:.6f}, max_step_seconds:{float(main_cfg['max_step_seconds']):.1f}")
            score += main_cfg['timeout_penalty']
        game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
        with open(f'{game_dir}/game_result.pkl', 'rb') as f:
            game_result = pickle.load(f)
            game_result['cum_score'] += score
        with open(f'{game_dir}/game_result.pkl', 'wb') as f:
            pickle.dump(game_result, f)
        result = {'is_end': is_end, 'bag': bag, 'score': score, 'game_id': game_id, 'grid': grid}
        with open(f'{game_dir}/last_step_time.txt', 'w') as f:
            f.write(datetime.now().strftime('%Y%m%d %H%M%S.%f'))
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
