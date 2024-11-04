from flask import Flask, request
from flask_socketio import SocketIO, emit, disconnect
#import eventlet
import numpy as np


# init Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)
connect_games = {}

init_game_state = {"score": 0, "position": [0, 0], 'grid': [[1,1,], [2,2]], 'bag': {1: 0}}

@socketio.on('connect')
def handle_connect():
    print("Client connected", request.sid)

@socketio.on('init_game')
def handle_init_game(data):
    print('init game', data)
    team_id = data['team_id']
    if team_id not in connect_games:
        connect_games[team_id] = []
    connect_games[team_id].append(request.sid)
    print(connect_games)
    socketio.emit('game_init', init_game_state)

@socketio.on('action')
def handle_action(data):
    print("Received action from client:", data)
    new_game_state = {
            "score": init_game_state["score"] + 1,
            "position": init_game_state['position'],
            'grid': init_game_state['grid'],
            'bag': init_game_state['bag']
            }
    if np.random.random() < 0.2:
        print(data['team_id'], 'game over')
        socketio.emit('game_over', new_game_state)
        disconnect()
    else:
        socketio.emit('game_update', new_game_state)


@socketio.on('disconnect')
def handle_disconnect():
    try:
        print('disconnect', request.sid)
    except Exception as e:
        print('Exception', e)


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=8081)
