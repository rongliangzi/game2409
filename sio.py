from flask import Flask
from flask_socketio import SocketIO, emit
import eventlet

# init Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

initial_game_state = {"score": 0, "position": [0, 0], "health": 100}

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit('game_data', initial_game_state)

@socketio.on('player_action')
def handle_player_action(data):
    print("Received action from client:", data)
    new_game_state = {
            "score": initial_game_state["score"] + 1,  
            "position": [data.get("x"), data.get("y")],
            "health": initial_game_state["health"] - data.get("damage", 0)
            }
    emit('game_data', new_game_state)

def check_game_over(state):
    return state["health"] <= 0

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=8081)
