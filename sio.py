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
max_total_connect = 30
# begin step
begin_sid = []


app = Flask(__name__)
cur_ip = ''
cur_port = ''
socketio = SocketIO(app, async_mode='eventlet', ping_timeout=20)

parser = argparse.ArgumentParser()
parser.add_argument('--ip', type=str)
parser.add_argument('--port', type=str)
parser.add_argument('--cfg', type=str)
args = parser.parse_args()
print(args.cfg, args.ip, args.port)
with open(args.cfg) as f:
    main_cfg = yaml.load(f, Loader=yaml.FullLoader)

team_id_info = read_team_id(main_cfg['team_id_path'])
print('Team num:', len(team_id_info))


@app.route('/')
def index():
    return "Flask-SocketIO Server running"


def init_game2(team_id, main_cfg, begin):
    # init a game from existing game_data
    game_type = begin[0]
    param_type = type_dir = game_type_dic.get(game_type, game_type)
    game_data_id = begin[1:]
    env_args = main_cfg[f'param{param_type}']
    now = datetime.now()
    time_key = now.strftime("%Y%m%d-%H%M%S")
    game_id, game_dir = get_game_id_dir(main_cfg, team_id, time_key)
    get_init_grid_loc(env_args, main_cfg, type_dir, game_data_id)
    game_env = gym.make('gymnasium_env/GAME', **env_args)
    obs, info = game_env.reset()
    # return all -2 grid for full game when step=0
    grid = obs['grid']
    if game_type in full_game_types:
        if not game_id.startswith('l2r0ng'):
            grid = np.zeros_like(obs['grid'])-2
    return obs['image'].tolist(), obs['bag'].tolist(), grid.tolist(), obs['loc'].tolist(), game_id, game_env


def env_step2(game_env, game_id, main_cfg, action):
    # update env, send new data to client
    game_dir = os.path.join(main_cfg["save_dir"], '/'.join(game_id.rsplit('_', 1)))
    obs, rew, term, _, info = game_env.step(action)
    if term:
        with open(f'{game_dir}/finish.txt', 'w') as f:
            f.write('finish')
    return obs['bag'].tolist(), obs['grid'].tolist(), obs['loc'].tolist(), rew, term


@socketio.on('continue')
def handle_continue(data):
    sid = request.sid
    # interval from last send time to this receive time
    now = datetime.now()
    if 'last_send_time' not in sid_game[sid]:
        diff_seconds = 0.1  # float
    else:
        t_diff = now - sid_game[sid]['last_send_time']
        diff_seconds = t_diff.total_seconds()  # float
    sid_game[sid]['interval'].append(diff_seconds)
    if sid in begin_sid:
        begin_sid.remove(sid)
    team_id = data['team_id']
    game_id = data['game_id']
    action = data['action']
    #for k, v in data.items():
    #    print(f'{k}: {v}', end=' ')
    #print('\nrounds', sid_game[sid]['rounds'])
    sid_game[sid]['rounds'] += 1
    if sid_game[sid]['rounds'] == 1 and (sid_game[sid]['game_data_id'][0] in ['2', '3', '4']):
        # full game receive prediction, calculate accuracy
        grid_label = sid_game[sid]['env'].unwrapped.get_init_grid().flatten()
        if 'grid_pred' in data:
            grid_pred = np.array(data['grid_pred'], dtype=int).flatten()
            if grid_pred.size == grid_label.size:
                correct = (grid_pred == grid_label).astype(int)
                sid_game[sid]['acc'] = (correct).sum() / grid_label.size
                mask = sid_game[sid]['env'].unwrapped.get_mask()  # 1d
                sid_game[sid]['correct_n'] = (mask * correct).sum()
            else:
                print(f'grid_pred.size: {grid_pred.size} != grid_label.size: {grid_label.size}')
        else:
            print(f'No grid_pred k-v provided in data, game_id: {game_id}')
    bag, grid, loc, score, is_end = env_step2(sid_game[sid]['env'], game_id, main_cfg, action)
    send_data = {'team_id': team_id, 'game_id': game_id, 'rounds': sid_game[sid]['rounds'], 
                 'is_end': is_end, 'bag': bag, 'loc': loc}
    if is_end:
        # last round, send accuracy, calculate time penalty
        game_dir = os.path.join(main_cfg["save_dir"], '/'.join(game_id.rsplit('_', 1)))
        game_info = sid_game[sid]
        median_itv = np.median(game_info['interval'])
        time_penalty = get_time_penalty(median_itv, main_cfg, game_id)
        send_data['time_penalty'] = time_penalty
        score += time_penalty
        cum_score = game_info['env'].unwrapped.get_cum_score() + time_penalty
        send_data['acc'] = game_info.get('acc', -1.)
        print(f'[End] game_id: {game_id}, data_id: {game_info["game_data_id"]}, rounds: {game_info["rounds"]} itv: {median_itv:.2f}s, acc: {send_data["acc"]:.4f}, correct_n: {game_info.get("correct_n", 0)}')
        with open(f'{game_dir}/game_result.pkl', 'wb') as f:
            pickle.dump({'cum_score': cum_score, 
                         'acc': game_info.get('acc', -1.), 
                         'correct_n': game_info.get('correct_n', 0),
                         'begin': game_info['game_data_id'], 
                         'rounds': game_info['rounds'], 
                         'time_itv': median_itv}, f)
    send_data['score'] = score
    sid_game[sid]['last_send_time'] = datetime.now()
    emit('response', send_data)


@socketio.on('begin')
def handle_begin(data):
    print(f'[Begin] {data}')
    team_id = data['team_id']
    debug_id = ['2hl1', 'l2r0ng', '22xu', 'jhn1u']
    sid_game[request.sid] = {'team_id': team_id}
    global cur_ip, cur_port
    if (datetime.now() < datetime.strptime(main_cfg.get('starttime', '2000-01-01-01-00'), '%Y-%m-%d-%H-%M')):
        print('[Begin error] Period does not begin now')
        emit('response', {'error': 'Period does not begin now'})
    elif (datetime.now() > datetime.strptime(main_cfg.get('endtime', '2099-01-01-01-00'), '%Y-%m-%d-%H-%M')):
        print('[Begin error] Period has end now')
        emit('response', {'error': 'Period has end now'})
    elif (team_id not in team_id_info) and (not any([team_id.startswith(v) for v in debug_id])):
        print(f'[Begin error] Illegal team_id {team_id}')
        emit('response', {'error': 'Illegal team_id'})
    elif (team_id in team_id_info) and ('ip' in team_id_info[team_id]) and (team_id_info[team_id]['ip'] != cur_ip):
        # check ip only if ip info exists
        print(f'[Begin error] IP not correct, can only be {team_id_info[team_id]["ip"]}')
        emit('response', {'error': f'Error: IP not correct, can only be {team_id_info[team_id]["ip"]}'})
    elif (team_id in team_id_info) and ('port' in team_id_info[team_id]) and (team_id_info[team_id]['port'] != cur_port):
        # check port only if port info exists
        #print('check port')
        print(f'[Begin error] port not correct, can only be {team_id_info[team_id]["port"]}')
        emit('response', {'error': f'Error: port not correct, can only be {team_id_info[team_id]["port"]}'})
    #elif sum(team_connect.values()) >= max_total_connect:
    #    #print('check max total conect')
    #    emit('response', {'error': 'cannot begin because server overloading, wait'})
    elif team_connect.get(team_id, 0) >= main_cfg['team_max_connections']:
        print(f'[Begin error] Fail to check team {team_id} max connect')
        emit('response', {'error': 'cannot begin because reaching max connections'})
    elif not begin_if_can(team_id, main_cfg):
        print(f'[Begin error] Fail to check team {team_id} game n')
        emit('response', {'error': f'Team {team_id} has run out of game time {main_cfg["max_n"]}'})
    elif not begin_game_if_can(team_id, data['begin'], main_cfg):
        print(f'[Begin error] Team {team_id} has run out of time {main_cfg.get("max_n_each_game", 10000)} on game {data["begin"]}')
        emit('response', {'error': f'Team {team_id} has run out of time {main_cfg.get("max_n_each_game", 10000)} on game {data["begin"]}'})
    else:
        try:
            begin_num = sum([v.get('rounds',-1)==0 for v in sid_game.values()]) if len(sid_game) > 0 else 0
            while begin_num >= main_cfg['max_begin_num']:
                eventlet.sleep(2)
                begin_num = sum([v.get('rounds',-1)==0 for v in sid_game.values()])
                for v in sid_game.values():
                    if v.get('rounds', -1) == 0:
                        print(v['team_id'], v['game_id'], 'rounds=0')
                print(request.sid, len(sid_game), begin_num, len(begin_sid), 'waiting for begin emit')
            begin_sid.append(request.sid)
            os.makedirs(os.path.join(main_cfg["save_dir"], team_id), exist_ok=True)
            game_type = data['begin'][0]
            img, bag, grid, loc, game_id, env = init_game2(team_id, main_cfg, data['begin'])
            send_data = {'score': 0, 'bag': bag, 'loc': loc, 'game_id': game_id, 'team_id': team_id, 'rounds': 0}
            if game_type in ['2', '3', '4']:
                send_data['img'] = img
            if game_type in ['a', 'b', 'c'] or team_id.startswith('l2r0ng'):
                send_data['grid'] = grid
            game_info = {'team_id': team_id, 'game_id': game_id, 'env': env, 'game_data_id': data['begin'],
                         'rounds': 0, 'last_send_time': datetime.now(), 'interval': []}
            sid_game[request.sid] = game_info
            team_connect[team_id] = team_connect.get(team_id, 0) + 1
            emit('response', send_data)
        except Exception as e:
            print(f'[Exception] {request.sid}: {e}')
            disconnect()


@socketio.on_error()
def error_handler(e):
    print(f"[ERROR] occur: {e}")
    disconnect()


@socketio.on('connect')
def handle_connect():
    sid_game[request.sid] = {}


@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in sid_game:
        if ('team_id' in sid_game[request.sid]) and ('game_id' in sid_game[request.sid]):
            team_id = sid_game[request.sid]['team_id']
            game_id = sid_game[request.sid]['game_id']
            team_connect[team_id] -= 1
            print(f'[Disconnect] game_id: {game_id}, team current connect: {team_connect[team_id]}')
        elif ('team_id' in sid_game[request.sid]):
            print(f'[Disconnect] team_id: {team_id}')
        else:
            print(f'[Disconnect] {request.sid}, unknown team')
        del sid_game[request.sid]
    else:
        print(f'[Disconnect] Unknown or already disconnect client: {request.sid}')


def set_ip_port(args):
    global cur_ip, cur_port
    cur_ip = args.ip
    cur_port = args.port


if __name__ == '__main__':
    set_ip_port(args)
    socketio.run(app, host='0.0.0.0', port=int(args.port))
