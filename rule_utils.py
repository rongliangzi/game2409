import os
from datetime import datetime
import numpy as np
import fcntl
import shutil
import time


def read_team_id_txt(team_id_path):
    # line in txt has format: {team_id}: {team_name}
    legal_team_id = dict()
    with open(team_id_path) as f:
        for l in f.readlines():
            if ': ' not in l:
                continue
            team_id, team_name = l.strip().split(': ')
            legal_team_id[team_id] = team_name
    return legal_team_id


def lock_rw_txt(fpath, max_n):
    # not exist: create, write 1, return 0
    # count >= max_n, not change, return count
    # count <max_n, write count + 1, return count
    file_desc = os.open(fpath, os.O_RDWR|os.O_CREAT)
    with os.fdopen(file_desc, 'r+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        content = f.read().strip()
        count = int(content) if content else 0
        f.seek(0)
        f.write(str(min(count+1, max_n)))
        f.truncate()
        fcntl.flock(f, fcntl.LOCK_UN)
        return count

def check_connections(team_id, cfg, refresh=False):
    # check if current connection reach up limit
    connect_fpath = os.path.join(cfg['save_dir'], team_id, 'connections.txt')
    if refresh:
        #  remove all unfinished games before and clear connections
        try:
            st = time.time()
            os.remove(connect_fpath)
            game_dir = os.listdir(os.path.join(cfg['save_dir'], team_id))
            for gd in game_dir:
                cur_dir = os.path.join(cfg['save_dir'], team_id, gd)
                if not os.path.exists(os.path.join(cur_dir, 'finish.txt')):
                    shutil.rmtree(cur_dir)
            print(f'Finish refresh, time:{time.time()-st:.1f}s')
        except Exception as e:
            print(f'Exception {e} when remove {connect_fpath}')
        finally:
            pass
    connect_n = lock_rw_txt(connect_fpath, cfg['team_max_connections'])
    print(team_id, 'connection_n', connect_n)
    return connect_n < cfg['team_max_connections']


def begin_if_can(team_id, cfg):
    # check if team_id has run out game time, update txt
    now = datetime.now()
    yymmdd = now.strftime("%Y%m%d")
    day_dir = os.path.join(cfg['save_dir'], yymmdd)
    os.makedirs(day_dir, exist_ok=True)
    team_day_fpath = os.path.join(day_dir, f'{team_id}_game_n.txt')
    team_day_n = lock_rw_txt(team_day_fpath, cfg['max_n'])
    return team_day_n < cfg['max_n']
