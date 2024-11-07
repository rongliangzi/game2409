# In use

## sio.py
Main entrance of server.
Run 
```
python sio.py --port 8081~8087 --ip 52.82.16.74/69.230.243.237
```

## stats\_team.py
Run `python stats_team.py`, and you can get `main_cfg['save_dir']/{team_id}/team_stats.csv`, columns including `game_id`, `cum_score`, `rounds`, `acc`, etc.

DO NOT forget to use data on any server.


## cfg
- `cfg/debug_cfg.yaml`, for debug

- `cfg/round0_eval_cfg.yaml`, Configuration for round0 eval phase.

- `cfg/round0_test_cfg.yaml`, Configuration for round0 test phase.

- `cfg/round1_eval_cfg.yaml`, Configuration for round1 eval phase.

- `cfg/round1_test_cfg.yaml`, Configuration for round1 test phase.


## leaderboard

Code for leaderboard

## game\_prepare.py

Randomly generate many initial grid and loc

## adjust\_grid\_set\_cls.py
Given a set of grids for initing games, adjust the class to get the total class distribution we want.
while not get aimed distribtion:
    if class i > aimed freq, class j < aimed freq, find a grid where count\_i > count\_j, swap i and j.

## assign\_img\_to\_grid.py

Assign img for each grid. Make sure that the whole grid dataset can use the whole image dataset.

# Deprecated

## app\_debug.py, app\_round0.py
Main entrance of server
Run 
```
gunicorn -w 4 -b 0.0.0.0:8081 app:app

```

## client\_post.py(Deprecated)
Client demo for posting data with app.py

## daily\_stats\_team.py(Deprecated)

Run py file without any change to get team stats **yesterday for server time**. 
Generate and save csv in `{save_dir}/{yyyymmdd}/daily_stats.csv` 

```
python daily_stats_team.py
```
Attention: time zone is different from Beijing. 
