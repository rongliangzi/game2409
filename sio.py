from flask import Flask, request
import eventlet
from flask_socketio import SocketIO, emit, disconnect
import random
import numpy as np
import yaml
from rule_utils import *
from game_utils import *
import argparse

# request.sid: game_env
sid_game = dict()
# team_id: connect_num, restrict connect each team
team_connect = dict()
max_team_connect = 30
max_total_connect = 60
# begin step
begin_sid = []
max_begin_num = 40


app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', ping_timeout=10)

with open('./cfg/debug_cfg.yaml') as f:
    main_cfg = yaml.load(f, Loader=yaml.FullLoader)

legal_team_id = read_team_id(main_cfg['team_id_path'])
for team_id in legal_team_id:
    os.makedirs(os.path.join(main_cfg['save_cfg'], team_id), exist_ok=True)


@app.route('/')
def index():
    return "Flask-SocketIO Server running"

def init_acc(team_id, main_cfg):
    # begin acc game
    fpath = main_cfg['img_path_label_pkl']
    while True:
        try:
            with open(fpath, 'rb') as f:
                # list of (img_path, label)
                img_path_label = pickle.load(f)
            break
        except Exception as e:
            print(f'Error {e} when loading {fpath}')
    now = datetime.now()
    time_key = now.strftime("%Y%m%d-%H%M%S")
    game_id, game_dir = get_game_id_dir(main_cfg, team_id, time_key)
    return read_img(img_path_label[0][0]), img_path_label, game_id


def init_game2(team_id, main_cfg, begin):
    # init a game from existing game_data
    game_type = begin[0]
    param_type = type_dir = game_type_dic.get(game_type, game_type)
    game_data_id = begin[1:]
    #print(f'Begin game type {game_type}, team {team_id}')
    env_args = main_cfg[f'param{param_type}']
    now = datetime.now()
    time_key = now.strftime("%Y%m%d-%H%M%S")
    game_id, game_dir = get_game_id_dir(main_cfg, team_id, time_key)
    for k in ['img_dir', 'cls_names']:
        env_args[k] = main_cfg[k]
    get_init_grid_loc(env_args, main_cfg, type_dir, game_data_id)
    game_env = gym.make('gymnasium_env/GAME', **env_args)
    obs, info = game_env.reset()
    grid = np.zeros_like(obs['grid']) if game_type in full_game_types else obs['grid']
    return obs['image'].tolist(), obs['bag'].tolist(), grid.tolist(), obs['loc'].tolist(), game_id, game_env


def env_step2(game_env, game_id, main_cfg, action):
    # update env, send new data to client
    game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
    obs, rew, term, _, info = game_env.step(action)
    if term:
        with open(f'{game_dir}/finish.txt', 'w') as f:
            f.write('finish')
    return obs['bag'].tolist(), obs['grid'].tolist(), obs['loc'].tolist(), rew, term

def read_img(img_path, size):
    img = Image.open(img_path).resize((size, size))
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    img_arr = np.array(img, dtype=np.uint8)
    return img_arr


@socketio.on('acc')
def handle_acc(data):
    cls = int(data.get('cls', 0))
    sid = request.sid
    team_id = data['team_id']
    game_id = data['game_id']
    label = sid_game[sid]['img_path_cls'].pop(0)[1]
    if cls == label:
        sid_game[sid]['correct'] += 1
    sid_game[sid]['img_num'] += 1
    if len(sid_game[sid]['img_path_cls'])==0:
        send_data = {'img': None, 'team_id': team_id, 'game_id': game_id}
        game_dir = os.path.join(main_cfg['save_dir'], game_id.replace('_', '/'))
        np.save(f'{game_dir}/acc.npy', sid_game[sid]['correct'] / sid_game[sid]['img_num'])
    else:
        img = read_img(sid_game[sid]['img_path_cls'][0][0], 50)
        send_data = {'img': img.tolist(), 'team_id': team_id, 'game_id': game_id}
    emit('response', send_data)


@socketio.on('continue')
def handle_continue(data):
    sid = request.sid
    now = datetime.now()
    t_diff = now - sid_game[sid]['last_send_time']
    diff_seconds = t_diff.total_seconds()  # float
    sid_game[sid]['interval'].append(diff_seconds)
    if sid in begin_sid:
        begin_sid.remove(sid)
    team_id = data['team_id']
    game_id = data['game_id']
    action = data['action']
    sid_game[sid]['rounds'] += 1
    if sid_game[sid]['rounds'] < 1:
        print(f'Continue {sid}', sid_game[sid]['rounds'])
    if sid_game[sid]['rounds'] == 0  and sid_game[sid]['game_data_id'][0] in ['2', '3', '4']:
        grid_pred = data['grid_pred']
        cls_label = sid_game[sid]['env'].unwrapped.get_init_grid()
        sid_game[sid]['acc'] = (grid_pred == cls_label).sum() / cls_label.size
    bag, grid, loc, score, is_end = env_step2(sid_game[sid]['env'], game_id, main_cfg, action)
    if is_end:
        game_dir = os.path.join(main_cfg['save_dir'], game_id.replace('_', '/'))
        game_info = sid_game[sid]
        time_penalty = get_time_penalty(np.median(game_info['interval']), main_cfg, game_id)
        score += time_penalty
        cum_score = game_info['env'].unwrapped.get_cum_score() + time_penalty
        with open(f'{game_dir}/game_result.pkl', 'wb') as f:
            pickle.dump({'cum_score': cum_score, 
                         'acc': game_info.get('acc', 0), 
                         'begin': game_info['game_data_id'], 
                         'rounds': game_info['rounds'], 
                         'time_itv': 0}, f)
    send_data = {'team_id': team_id, 'game_id': data['game_id'], 'rounds': sid_game[sid]['rounds'], 
                 'is_end': is_end, 'score': score, 'bag': bag, 'loc': loc}
    sid_game[sid]['last_send_time'] = datetime.now()
    emit('response', send_data)


@socketio.on('begin')
def handle_begin(data):
    print(f'Begin : {data}')
    team_id = data['team_id']
    debug_id = ['zhli', 'lzrong', 'zzxu', 'jhniu']
    if team_id not in legal_team_id and (not any([team_id.startswith(v) for v in debug_id])):
        emit('response', {'error': 'Illegal team_id'})
    elif sum(team_connect.values()) >= max_total_connect:
        emit('response', {'error': 'cannot begin because server overloading, wait'})
    elif team_connect.get(team_id, 0) >= max_team_connect:
        emit('response', {'error': 'cannot begin because reaching max connections'})
    elif not begin_if_can(team_id, main_cfg):
        emit('response', {'error': f'Team {team_id} has run out of game time {main_cfg["max_n"]}'})
    else:
        try:
            begin_num = sum([v.get('rounds',-1)==0 for v in sid_game.values()]) if len(sid_game) > 0 else 0
            while begin_num >= max_begin_num:
                eventlet.sleep(2)
                begin_num = sum([v.get('rounds',-1)==0 for v in sid_game.values()])
                for v in sid_game.values():
                    if v.get('rounds', -1) == 0:
                        print(v['team_id'], v['game_id'], 'rounds=0')
                print(request.sid, len(sid_game), begin_num, len(begin_sid))
                #print('waiting for begin emit')
            begin_sid.append(request.sid)
            os.makedirs(os.path.join(main_cfg["save_dir"], team_id), exist_ok=True)
            game_type = data['begin'][0]
            if game_type in ['A', 'B', 'C']:
                #img = fetch_img()
                img_arr, img_path_label, game_id = init_acc(team_id, main_cfg)
                send_data = {'team_id': team_id, 'game_id': game_id, 'img': img_arr.tolist(), 'rounds': 0}
            else:
                img, bag, grid, loc, game_id, env = init_game2(team_id, main_cfg, data['begin'])
                send_data = {'score': 0, 'bag': bag, 'loc': loc, 'game_id': game_id, 'team_id': team_id, 'rounds': 0}
                if data['begin'][0] in ['2', '3', '4']:
                    send_data['img'] = img
                else:
                    send_data['grid'] = grid
            game_info = {'team_id': team_id, 'game_id': game_id, 'env': env, 'game_data_id': data['begin'],
                         'rounds': 0, 'last_send_time': datetime.now(), 'interval': []}
            sid_game[request.sid] = game_info
            team_connect[team_id] = team_connect.get(team_id, 0) + 1
            emit('response', send_data)
        except Exception as e:
            print(f'{request.sid} exception: {e}')
            disconnect()


@socketio.on_error()
def error_handler(e):
    print(f"ERROR occur: {e}")
    disconnect()


@socketio.on('connect')
def handle_connect():
    sid_game[request.sid] = {}


@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in sid_game:
        if 'team_id' in sid_game[request.sid]:
            team_id = sid_game[request.sid]['team_id']
            game_id = sid_game[request.sid]['game_id']
            team_connect[team_id] -= 1
            print(f'team: {team_id}, game id {game_id} disconnect, current team connect: {team_connect[team_id]}')
        else:
            print(f'{request.sid} no team disconnect')
        del sid_game[request.sid]
    else:
        print(f'Unknown or already disconnect client: {request.sid}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int)
    args = parser.parse_args()
    socketio.run(app, host='0.0.0.0', port=args.port)
