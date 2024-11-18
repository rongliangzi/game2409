import time
from datetime import datetime
import os
import pickle
import numpy as np


if __name__ == "__main__":
    team_game_data = './team_game_data/'
    teams = os.listdir(team_game_data)
    type_team_time = {'2': {}, 'a': {}}
    min_cum_score = 0
    start_date = 20241115
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
            game_date = int(game_id.split('-')[0])
            if game_date < start_date:
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
                if game_result['cum_score'] < min_cum_score:
                    continue
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
        print('='*20, 'Game type', k, '='*20)
        print(f'Only consider games after {start_date}, cum_score > {min_cum_score}')
        #print('teams', type_team_time[k].keys())
        team_avg = [np.mean(v) for v in type_team_time[k].values()]
        print(f'Calculate avg on each team, total {len(team_avg)} teams')
        for p in range(10, 100, 20):
            print(f'percentile {p} time: {np.percentile(team_avg, p):.2f}s')
        all_time = [t for v in type_team_time[k].values() for t in v]
        print(f'On all teams, total {len(all_time)} games')
        for p in range(10, 100, 20):
            print(f'percentile {p} time: {np.percentile(all_time, p):.2f}s')
