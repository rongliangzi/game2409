# In use

## sio.py
Main entrance of server
Run 
```
python sio.py --port 8081/8081/8083/8084
```

## stats\_team.py
Run `python stats_team.py`, and you can get `main\_cfg['save\_dir']/{team_id}/team\stats.csv`, including game\_id, cum\_score, rounds, etc.

DO NOT forget to use data on any server.


## cfg
- `cfg/chusai_eval_cfg.yaml`, Configuration for chusai eval phase.

- `cfg/chusai_test_cfg.yaml`, Configuration for chusai test phase.

- `cfg/fusai_eval_cfg.yaml`, Configuration for fusai eval phase.

- `cfg/fusai_test_cfg.yaml`, Configuration for fusai test phase.


## leaderboard

Code for leaderboard

## game\_prepare.py

Randomly generate many initial grid and loc

## adjust\_grid\_set\_cls.py
Given a set of grids for initing games, adjust the class to get the total class distribution we want.
while not get aimed distribtion:
    if class i > aimed freq, class j < aimed freq, find a grid where count\_i > count\_j, swap i and j.

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
