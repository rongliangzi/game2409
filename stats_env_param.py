import os
import yaml
import numpy as np
import pandas as pd
import pickle
from datetime import datetime
import shutil

def diff_of_strategies(save_dir, teams):
    # stats diff for strategies on the same game under one parameter
    game_id_score = {}
    for team_id in teams:
        team_dir = os.path.join(save_dir, team_id)
        all_game_key = os.listdir(team_dir)
        for game_key in all_game_key:
            # all games of one team
            if game_key == 'public':
                continue
            cur_path = os.path.join(team_dir, game_key)
            if not os.path.isdir(cur_path):
                continue
            game_result_path = os.path.join(team_dir, game_key, 'game_result.pkl')
            try:
                with open(game_result_path, 'rb') as f:
                    game_result = pickle.load(f)
                game_type = game_result['begin'][0]
                game_data_id = game_result['begin'][1:]
                if game_type not in game_id_score:
                    game_id_score[game_type] = dict()
                if game_data_id not in game_id_score[game_type]:
                    game_id_score[game_type][game_data_id] = []
                game_id_score[game_type][game_data_id].append(game_result['cum_score'])
            except Exception as e:
                pass
    for game_type in sorted(game_id_score.keys()):
        print('game_type:', game_type)
        type_result = game_id_score[game_type]
        type_std = []
        for game_id in type_result.keys():
            if len(type_result[game_id]) < 5:
                continue
            std = np.std(type_result[game_id])
            type_std.append(std)
        print(f'Score std of diff strategies: {np.mean(type_std):.2f}, game num: {len(type_std)}')


if __name__=="__main__":
    with open('./cfg/debug_cfg.yaml') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)
    save_dir = cfg['save_dir']
    all_teams = os.listdir(save_dir)
    par_teams =[['1dcalve12jo8', 'lloc4npi17p3', 'ktfg1ixijy85', 'mz7f6f3xzdes', '3y8tbt7ih2dt', 'lpax2ja8immg', 'libms897ww51', 'n75ifpwrkmps'], 
                ['1h6b90wb6cvq', 'nfxrw4v95lck', 'nhroo94ub0bx', 'nmzq7vqawuej', '99g7zr35sdb1', 'd82sbx0oao6g', 'aceim54318b0'], 
                ['', ]]
    par = ['carry_k=1', 'carry_k=1.5', 'carry_k=0.5']
    for p, teams in zip(par, par_teams):
        print('\nParam:', p)
        diff_of_strategies(save_dir, teams)
