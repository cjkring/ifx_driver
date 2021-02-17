# -*- coding: utf-8 -*-

import logging
import time
import rd_store
import datetime
from config import read_config, validate_config
from avro_export import avroExport
import aws_connector


def backup_impl(readings,config):
    backup = readings.backup()
    now = datetime.datetime.now()
    sensor_id = config['app']['sensor_id']
    data = config['app']['data']
    
    filename = f'year={now.year}_month={now.month}_day={now.day}_hour={now.hour}_{sensor_id}.avro'
    avroExport(data, filename, backup)
    aws_connector.upload_file(config, data, filename)

def backup_thread_impl(readings,config):
    logging.warning("Backup thread started")

    while True:

        # sleep until end of the hour
        now = datetime.datetime.now()
        sleep_secs = ( 59 - now.minute ) * 60 + 60 - now.second
        time.sleep(sleep_secs)

    logging.warning("Backup thread ended")

# TEST
if  __name__ == "__main__":
    config = read_config()
    if validate_config(config) == False:
        quit()

    readings = rd_store.Readings()
    backup_impl(readings,config)