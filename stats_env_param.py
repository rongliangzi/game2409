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
                game_id_score[game_type][game_data_id].append((game_result['cum_score'], game_key))
                game_keys = {}
            except Exception as e:
                pass
    for game_type in sorted(game_id_score.keys()):
        print('game_type:', game_type)
        type_result = game_id_score[game_type]
        type_std = []
        type_mean = []
        for game_data_id in type_result.keys():
            if len(type_result[game_data_id]) < 5:
                continue
            arr = [v[0] for v in type_result[game_data_id]]
            std = np.std(arr)
            type_std.append(std)
            type_mean.append(np.mean(arr))
        print(f'Score of diff strategies: mean:{np.mean(type_mean):.2f} std:{np.mean(type_std):.2f}, game num: {len(type_std)}')
    type_team_score = {}
    for game_type in sorted(game_id_score.keys()):
        if game_type not in type_team_score:
            type_team_score[game_type] = dict()
        for game_data_id in game_id_score[game_type].keys():
            for team_id in teams:
                if team_id not in type_team_score[game_type]:
                    type_team_score[game_type][team_id] = []
                team_dir = os.path.join(save_dir, team_id)
                for v in game_id_score[game_type][game_data_id]:
                    game_result_path = os.path.join(team_dir, v[1], 'game_result.pkl')
                    if not os.path.exists(game_result_path):
                        continue
                    with open(game_result_path, 'rb') as f:
                        game_result = pickle.load(f)
                    type_team_score[game_type][team_id].append(game_result['cum_score'])
    for game_type in sorted(game_id_score.keys()):
        print('game_type', game_type)
        team_scores = [np.mean(v) for v in type_team_score[game_type].values() if len(v) > 0]
        for i, v in enumerate(type_team_score[game_type].values()):
            if len(v) > 0:
                print(f'Team{i}: mean:{np.mean(v):.2f}, std:{np.std(v):.2f}')
        qufendu = np.std(team_scores)
        mean_score = np.mean(team_scores)
        print(f'Team score mean: {mean_score:.2f}, std: {qufendu:.2f}')


if __name__=="__main__":
    with open('./cfg/debug_cfg.yaml') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)
    save_dir = cfg['save_dir']
    all_teams = os.listdir(save_dir)
    par_teams =[['1dcalve12jo8', 'lloc4npi17p3', 'ktfg1ixijy85', 'mz7f6f3xzdes', '3y8tbt7ih2dt', 'lpax2ja8immg', 'libms897ww51', 'n75ifpwrkmps'], 
                ['1h6b90wb6cvq', 'nfxrw4v95lck', 'nhroo94ub0bx', 'nmzq7vqawuej', '99g7zr35sdb1', 'd82sbx0oao6g', 'aceim54318b0'], 
                ['250uviu3cdh1', 'nobiq17o5wcw', 'o5hc7rhdftac', 'otxka1kf3jlu', 'cw34w2oi2vzk', 'fspr27sgu487', 'ilmunas6bpn1']]
    par = ['carry_k=1', 'carry_k=1.5', 'carry_k=0.5']
    for p, teams in zip(par, par_teams):
        print('\nParam:', p)
        diff_of_strategies(save_dir, teams)
