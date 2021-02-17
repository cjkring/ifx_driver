import yaml

def read_config():
    try:
        with open("config.yml", "r") as ymlfile:
            cfg = yaml.safe_load(ymlfile)
            return cfg
    except Exception as e:
        print(f'Read_config: {e}')
        return {}

def validate_config(config):
    
    retval = True
    app_config = config['app']
    for key in ['sensor_id','data']:
        if key not in app_config:
            print(f'config validation: {key} does not exist in app config')
            retval = False

    aws_config = config['aws']
    for key in ['key_id','key','region','bucket','table']:
        if key not in aws_config:
            print(f'config validation: {key} does not exist in aws config')
            retval = False
    return retval