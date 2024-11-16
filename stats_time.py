import time
from datetime import datetime
import os
import pickle
import numpy as np


if __name__ == "__main__":
    team_game_data = './team_game_data/'
    teams = os.listdir(team_game_data)
    type_team_time = {'2': {}, 'a': {}}
    for team_id in teams:
        if not os.path.isdir(os.path.join(team_game_data, team_id)):
            continue
        if team_id.startswith('2024'):
            continue
        if any(spid in team_id for spid in ['lzrong', 'zzxu', 'zhli']):
            continue
        print('team_id', team_id)
        game_ids = os.listdir(os.path.join(team_game_data, team_id))
        for game_id in game_ids:
            if game_id == 'public':
                continue
            game_dir = os.path.join(team_game_data, team_id, game_id)
            if not os.path.isdir(game_dir):
                continue
            #print(game_id)
            if 'a' in game_id:
                game_id = game_id[:game_id.index('a')]
            game_st_time = datetime.strptime(game_id, "%Y%m%d-%H%M%S")
            finish_path = os.path.join(game_dir, 'finish.txt')
            game_result_path = os.path.join(game_dir, 'game_result.pkl')
            if not os.path.exists(finish_path) or (not os.path.exists(game_result_path)):
                continue
            try:
                with open(game_result_path, 'rb') as f:
                    game_result = pickle.load(f)
                game_type = game_result['begin'][0]
                mtime = os.path.getmtime(game_result_path)
                game_ed_time = datetime.fromtimestamp(mtime)
                game_time = (game_ed_time - game_st_time).total_seconds()
                if team_id not in type_team_time[game_type]:
                    type_team_time[game_type][team_id] = []
                type_team_time[game_type][team_id].append(game_time)
            except Exception as e:
                pass
            finally:
                #break
                pass
    for k in type_team_time.keys():
        print('type', k)
        team_avg = [np.mean(v) for v in type_team_time[k].values()]
        print('Calculate avg on each team')
        for p in range(10, 100, 20):
            print(f'percentile {p} time: {np.percentile(team_avg, p):.2f}s')
        print('On all teams')
        all_time = [t for v in type_team_time[k].values() for t in v]
        for p in range(10, 100, 20):
            print(f'percentile {p} time: {np.percentile(all_time, p):.2f}s')
