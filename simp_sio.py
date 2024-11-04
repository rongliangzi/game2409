from flask import Flask
from flask_socketio import SocketIO, emit
import random
import numpy as np


app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

@socketio.on('continue')
def handle_continue(msg):
    print(f'Continue Received message: {msg}')
    num = np.random.random()
    emit('response', {'is_end': num>0.99, 'score': 0.1, 'bag': {1: 0}})


@socketio.on('begin')
def handle_begin(msg):
    print(f'Begin : {msg}')
    num = np.random.random()
    grid = np.random.randint(0, 21, size=(12, 12))
    emit('response', {'is_end': num>0.999, 'grid': grid.tolist(), 'score': 0, 'bag': {0: 0}})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8081)

