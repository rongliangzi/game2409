## app.py
Main entrance of server
Run 
```
gunicorn -w 4 -b 0.0.0.0:8081 app:app
```
## daily_stats_team.py

Run py file without any change to get team stats ::yesterday::. 
```
python daily_stats_team.py
```
## client_type4.py
Client demo

## cfg
- chusai_eval_cfg.yaml
Configuration for chusai eval phase.

- chusai_test_cfg.yaml
Configuration for chusai test phase.

- fusai_eval_cfg.yaml
Configuration for fusai eval phase.

- fusai_test_cfg.yaml
Configuration for fusai test phase.

