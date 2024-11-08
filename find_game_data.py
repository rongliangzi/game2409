import os
import numpy as np
import pickle
import shutil


if __name__ == "__main__":
    # dir for saving team game data
    save_dir = '/root/Desktop/hunter/game2409/team_game_data/'
    # all team id 
    team_ids = os.listdir(save_dir)
    # including special team id with '_'
    team_ids += ['zhli/nobag/', 'zhli/Iknowall/', 'zhli/walkwhilepick/']
    aim_type = 'a'  # aim game type
    valid_game_data_id = {}  # finished game data_id: {team_id: cum_score}
    valid_teams = set()  # team id with game num>=min_game_num, mean score > min_score
    min_game_num = 1800
    min_score = -200
    # game data id range
    min_gdi = 0
    max_gdi = 10000
    for tid in team_ids:
        if not any(tid.startswith(a) for a in ['lzrong', 'zhli', 'zzxu']):
            continue
        team_dir = os.path.join(save_dir, tid)
        game_ids = os.listdir(team_dir)  # game_ids
        team_game_result = dict()  # this team's score on finished games
        for game_id in game_ids:
            game_dir = os.path.join(team_dir, game_id)
            if not os.path.isdir(game_dir):
                continue
            if not os.path.exists(os.path.join(game_dir, 'finish.txt')):
                continue
            if not os.path.exists(os.path.join(game_dir, 'game_result.pkl')):
                continue
            try:
                with open(os.path.join(game_dir, 'game_result.pkl'), 'rb') as f:
                    game_result = pickle.load(f)
                game_type = game_result['begin'][0]
                if game_type != aim_type:
                    continue
                game_data_id = game_result['begin'][1:]
                if (int(game_data_id) > max_gdi) or (int(game_data_id) < min_gdi):
                    continue
                cum_score = game_result['cum_score']
                if game_data_id not in team_game_result:
                    team_game_result[game_data_id] = cum_score
                else:
                    team_game_result[game_data_id] = max(cum_score, team_game_result[game_data_id])
                if game_data_id not in valid_game_data_id:
                    valid_game_data_id[game_data_id] = {}
                valid_game_data_id[game_data_id][tid] = team_game_result[game_data_id]
            except Exception  as e:
                print(e)
        if (len(team_game_result) < min_game_num):
            continue
        scores = list(team_game_result.values())
        if np.mean(scores) > min_score:
            print(f'Team {tid}, game type {aim_type}, game id num: {len(scores)}, mean score: {np.mean(scores):.2f}')
            valid_teams.add(tid)
    valid_game_data_score = {}  # game_data_id: mean and std of all valid teams score on valid game
    for gdi, t_score in valid_game_data_id.items():
        tids = list(t_score.keys())
        # valid game: must include all valid teams
        if not valid_teams.issubset(set(tids)):
            continue
        mean_score_on_valid_teams = np.mean([t_score[vt] for vt in valid_teams])
        std_score_on_valid_teams = np.std([t_score[vt] for vt in valid_teams])
        valid_game_data_score[gdi] = [mean_score_on_valid_teams, std_score_on_valid_teams]
    # we want the games with low score and high std
    sort_game_data = sorted(valid_game_data_score.items(), key=lambda x:  0.2*x[1][0] - x[1][1])
    print(sort_game_data[:10])
    print(sort_game_data[-10:])
    # copy game data to aim dir
    def copy_game_data(src_dir, aim_dir, game_data):
        for i, gd in enumerate(game_data):
            gdi = gd[0]
            new_gdi = f'{i:05}'
            #print(gdi, new_gdi)
            os.makedirs(os.path.join(aim_dir, new_gdi), exist_ok=True)
            shutil.copy(os.path.join(src_dir, gdi, 'grid.npy'), os.path.join(aim_dir, new_gdi, 'grid.npy'))
            shutil.copy(os.path.join(src_dir, gdi, 'loc.npy'), os.path.join(aim_dir, new_gdi, 'loc.npy'))
    src_dir = '/root/Desktop/hunter/init_game_data/debug/2/'
    test_dir = '/root/Desktop/hunter/init_game_data/round0_test/2/'
    copy_game_data(src_dir, test_dir, sort_game_data[:200])
    eval_dir = '/root/Desktop/hunter/init_game_data/round0_eval/2/'
    copy_game_data(src_dir, eval_dir, sort_game_data[200:300])
