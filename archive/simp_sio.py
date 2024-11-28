from flask import Flask, request
from flask_socketio import SocketIO, emit
import random
import numpy as np

# request.sid: game_env
sid_game = dict()
# team_id: connect_num, restrict connect each team
team_connect = dict()


app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')


@socketio.on('continue')
def handle_continue(msg):
    sid = request.sid
    team_id = msg['team_id']
    sid_game[sid]['rounds'] += 1
    print(f'Continue {sid}', sid_game[sid]['rounds'])
    is_end = sid_game[sid]['rounds'] > 576
    if is_end:
        team_connect[team_id]-=1
    emit('response', {'team_id': team_id, 'game_id': msg['game_id'], 
                      'is_end': is_end, 'score': 0.1, 'bag': {1: 0}, 'loc': (0,0)})


@socketio.on('begin')
def handle_begin(msg):
    print(f'Begin : {msg}')
    team_id = msg['team_id']
    if team_connect.get(team_id, 0) >= 20:
        emit('response', {'error': 'cannot begin because reaching max connections'})
    else:
        grid = np.random.randint(0, 21, size=(12, 12), dtype=int)
        img = np.random.randint(0, 255, size=(600,600,3), dtype=np.uint8)
        game_id = np.random.randint(0, 999999)
        state = {'team_id': team_id, 'game_id': str(game_id), 
                 'img': img.tolist(), 'grid': grid.tolist(), 'score': 0, 'bag': {0: 0}, 'rounds': 0, 'loc': (0,0)}
        sid_game[request.sid] = state
        team_connect[team_id] = team_connect.get(team_id, 0) + 1
        emit('response', state)


@socketio.on('disconnect')
def handle_disconnect():
    try:
        del sid_game[request.sid]
        print('disconnect', request.sid, len(sid_game))
    except Exception as e:
        print('Exception', e)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8081)
