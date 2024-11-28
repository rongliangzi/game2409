from flask import Flask, request, jsonify
import yaml
from rule_utils import *
from game_utils import *


app = Flask(__name__)

with open('./cfg/debug_cfg.yaml') as f:
    main_cfg = yaml.load(f, Loader=yaml.FullLoader)

legal_team_id = read_team_id(main_cfg['team_id_path'])
#print('team_id:', legal_team_id)


def process_team_post(data, team_id):
    # check team id legal
    os.makedirs(os.path.join(main_cfg["save_dir"], team_id), exist_ok=True)
    if data.get('begin', None):
        st = time.time()
        if not check_connections(team_id, main_cfg, data.get('refresh', False)):
            return f'Team {team_id} has reached max connections: {main_cfg["team_max_connections"]}', 400
        if not begin_if_can(team_id, main_cfg):
            return f'Team {team_id} has run out of game time {main_cfg["max_n"]}', 400
        if not check_begin(main_cfg, data['begin']):
            return f'Illegal game_type game_id param', 400
        img, bag, grid, loc, game_id = init_game(team_id, main_cfg, data['begin'])
        if time.time() - st > 1:
            print(f'Env step too long time {game_id}')
        return jsonify({'is_end': False, 'img': img, 'bag':bag, 'score': 0, 'game_id': game_id, 'grid': grid, 'loc': loc})
    else:
        # continue existing game, game_id, action, cls
        st = time.time()
        game_id = data.get('game_id', None)  # str
        if game_id is None:
            return 'Game id must be provided', 400
        game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
        if not os.path.exists(game_dir):
            return 'Game id does not exist, check if you set refresh correctly', 400
        with open(f'{game_dir}/last_step_time.txt', 'r') as f:
            last_step_time = datetime.strptime(f.readlines()[0].strip(), '%Y%m%d %H%M%S.%f')
        interval = (datetime.now() - last_step_time).total_seconds()
        action = data.get('action', None)
        cls = data.get('cls', None)
        grid_cls = data.get('grid_cls', None)
        info, code = check_step_data(game_id, game_dir, action, cls, grid_cls)
        if len(info) > 0:
            return info, code
        bag, grid, loc, score, is_end = env_step(game_id, main_cfg, action, cls, grid_cls)
        # use interval median to calculate time penalty instead
        score = update_game_result(game_dir, score, interval, is_end, main_cfg, game_id)
        result = {'is_end': is_end, 'bag': bag, 'score': score, 'game_id': game_id, 
                  'grid': grid, 
                  'loc': loc}
        if time.time() - st > 1:
            print(f'Env step too long time {game_id}')
        return jsonify(result)


@app.route('/', methods=['POST'])
def handle_client():
    try:
        data = request.get_json()
        team_id = data.get('team_id', None)
        if team_id == 'public':
            return "Test connection success", 400
        elif team_id in legal_team_id.keys():
            return process_team_post(data, team_id)
        else:
            print(f'team_id:{team_id} illegal')
            return "team_id illegal", 400
    except Exception as e:
        print(f'Error: {str(e)}')
        return jsonify({'status': e, 'message': str(e)}), 500


if __name__=="__main__":
    app.run(host='0.0.0.0', port=8081)
