# -*- coding: utf-8 -*-

import logging
import time
import rd_store
import datetime
from avro_export import avroExport

def backup_thread_impl(readings):
    logging.warning("Backup thread started")

    while True:

        # sleep until end of the hour
        now = datetime.datetime.now()
        sleep_secs = ( 59 - now.minute ) * 60 + 60 - now.second
        time.sleep(sleep_secs)

        # do backup
        backup = readings.backup()
        now = datetime.datetime.now()
        filename = f'{now.year}_{now.month}_{now.day}_{now.hour}.avro'
        avroExport(filename, backup)

    logging.warning("Backup thread ended")

# testing
if  __name__ == "__main__":
    readings = rd_store.Readings()
    backup_thread_impl(readings)