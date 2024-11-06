from flask import Flask, request
import eventlet
from flask_socketio import SocketIO, emit, disconnect
import random
import numpy as np
import yaml
import logging
from rule_utils import *
from game_utils import *


# request.sid: game_env
sid_game = dict()
# team_id: connect_num, restrict connect each team
team_connect = dict()
max_team_connect = 30
# begin step
begin_sid = []
max_begin_num = 40


app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', ping_timeout=30)
logging.basicConfig(level=logging.INFO)

with open('./cfg/debug_cfg.yaml') as f:
    main_cfg = yaml.load(f, Loader=yaml.FullLoader)

legal_team_id = read_team_id(main_cfg['team_id_path'])


def init_game2(team_id, main_cfg, begin):
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
    grid = np.zeros_like(obs['grid']) if game_type in full_game_types else obs['grid']
    if time.time() - st > 1:
        print(f'Env init too long time {game_id}\n', time_str)
    return obs['image'].tolist(), obs['bag'].tolist(), grid.tolist(), obs['loc'].tolist(), game_id, game_env


def env_step2(game_env, game_id, main_cfg, action):
    # update env, send new data to client
    time_str = ''
    st = time.time()
    time_str += f'{datetime.now()}, begin env_step\n'
    game_dir = os.path.join(main_cfg["save_dir"], game_id.replace("_", "/"))
    obs, rew, term, _, info = game_env.step(action)
    time_str += f'{datetime.now()} finish step\n'
    if term:
        with open(f'{game_dir}/finish.txt', 'w') as f:
            f.write('finish')
    time_str += f'{datetime.now()} end env_step\n'
    if time.time() - st > 1:
        print(f'Env step too long time {game_id}\n', time_str)
    return obs['bag'].tolist(), obs['grid'].tolist(), obs['loc'].tolist(), rew, term


@socketio.on('acc')
def handle_acc(data):
    cls = int(data.get('cls', 0))
    sid = request.sid
    if cls == label:
        sid_game[sid]['correct'] += 1
    emit('response', {})


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
    elif team_connect.get(team_id, 0) >= max_team_connect:
        emit('response', {'error': 'cannot begin because reaching max connections'})
    else:
        try:
            begin_num = sum(v['rounds']==0 for v in sid_game.values()) if len(sid_game) > 0 else 0
            while begin_num >= max_begin_num:
                eventlet.sleep(2)
                begin_num = sum(v['rounds']==0 for v in sid_game.values())
                for v in sid_game.values():
                    if v['rounds'] == 0:
                        print(v['team_id'], v['game_id'], 'rounds=0')
                print(request.sid, len(sid_game), begin_num, len(begin_sid))
                #print('waiting for begin emit')
            begin_sid.append(request.sid)
            os.makedirs(os.path.join(main_cfg["save_dir"], team_id), exist_ok=True)
            game_type = data['begin'][0]
            if game_type in ['A', 'B', 'C']:
                #img = fetch_img()
                send_data = {}
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

@socketio.event
def error_handler(e):
    logging.error(f"ERROR occur: {e}")
    disconnect()


@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in sid_game:
        team_id = sid_game[request.sid]['team_id']
        team_connect[team_id] -= 1
        del sid_game[request.sid]
        print(f'team: {team_id}, sid {request.sid} disconnect, current team connect: {team_connect[team_id]}')
    else:
        logging.warning(f'Unknown or already disconnect client: {request.sid}')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8081)
