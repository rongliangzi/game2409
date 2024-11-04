import os
import yaml
import numpy as np
import pandas as pd
import pickle


if __name__=="__main__":
    with open('./cfg/debug_cfg.yaml') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)
    save_dir = cfg['save_dir']
    all_teams = os.listdir(save_dir)
    for team_id in all_teams:
        team_stats = {'cum_score': [], 'game_type': [], 'game_data_id': [], 'rounds': [], 'acc': []}
        index = []
        # iterate on all teams
        team_dir = os.path.join(save_dir, team_id)
        all_game_key = os.listdir(team_dir)
        for game_key in all_game_key:
            # all games of one team
            cur_path = os.path.join(team_dir, game_key)
            if not os.path.isdir(cur_path):
                continue
            if not os.path.exists(os.path.join(cur_path, 'finish.txt')):
                continue
            game_result_path = os.path.join(team_dir, game_key, 'game_result.pkl')
            if not os.path.exists(game_result_path):
                continue
            with open(game_result_path, 'rb') as f:
                game_result = pickle.load(f)
            game_result['game_type'] = game_result['begin'][0]
            game_result['game_data_id'] = game_result['begin'][1:]
            del game_result['begin']
            for k in team_stats.keys():
                team_stats[k].append(game_result[k])
            index.append((team_id, game_key))
        df = pd.DataFrame(team_stats, index=pd.MultiIndex.from_tuples(index))
        df.to_csv(os.path.join(cur_path, f'team_stats.csv'))
