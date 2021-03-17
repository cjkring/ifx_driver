import yaml
import logging
from app_logging import test_logging

logger = logging.getLogger("ifxgui.config")

def read_config():
    try:
        with open("config.yml", "r") as ymlfile:
            cfg = yaml.safe_load(ymlfile)
            logger.info(f'Read_config: success')
            return cfg
    except Exception as e:
        logger.warn(f'Read_config: {e}')
        return {}

def validate_config(config):
    
    retval = True
    app_config = config['app']
    for key in ['sensor_id','data','annotations']:
        if key not in app_config:
            print(f'config validation: {key} does not exist in app config')
            retval = False

    aws_config = config['aws']
    for key in ['key_id','key','region','bucket','table']:
        if key not in aws_config:
            print(f'config validation: {key} does not exist in aws config')
            retval = False
    logger.info("Config validated")
    return retval
    
if  __name__ == "__main__":

    test_logging()

    config = read_config()
    validate_config(config)