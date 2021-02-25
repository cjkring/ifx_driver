from fastavro import writer, schemaless_writer, reader, parse_schema
from rd_store import Readings, Reading
import numpy as np
import os
from time import time
from config import read_config, validate_config

schema = {
    'name': 'Reading',
    'type': 'record',
    'namespace': 'test',
    'fields': [
        {'name': 'timestamp', 'type': 'double'},
        {'name': 'seqno', 'type': 'int'},
        {'name': 'count', 'type': 'int'},
        {'name': 'data_i', 'type': {'type': 'array','items':'int'}},
        {'name': 'data_q', 'type': {'type': 'array','items':'int'}},
        {'name': 'magnitude', 'type': {'type': 'array','items':'float'}},
        {'name': 'phase', 'type': {'type': 'array','items':'float'}},
        {'name': 'phase_velocity', 'type': {'type': 'array','items':'float'}},
        {'name': 'phase_unrolled', 'type': {'type': 'array','items':'float'}},
    ]
}
parsed_schema = parse_schema(schema)
def avroExport(filename, readings):
    count = readings.head
    prev = round( time(), 3 )
    try:
        with open(fullpathname, 'wb') as f:
            # write the schema and headers with the first on
            writer(f, parsed_schema, readings)
    except Exception as e:
        print(f'AvroExport: {e}')
    now = round( time(), 3 )
    print(f'AvroExport:{count} readings in {now-prev} seconds')

def avroImport(filename, readings):
    now = round( time(), 3 )
    count = 0
    try:
        # reset readings,  the io_thread was stopped by the calling function
        readings.backup()
        with open(filename, 'rb') as f:
            for record in reader(f):
                reading = Reading( record["seqno"], record["count"], record["data_i"], record["data_q"])
                reading["timestamp"] = record["timestamp"]
                reading["magnitude"] = record["magnitude"]
                reading["phase"] = record["phase"]
                reading["phase_velocity"] = record["phase_velocity"]
                reading["phase_unrolled"] = record["phase_unrolled"]
                readings.put(reading)
                count += 1
        print(f'AvroImport: {count} readings imported')
    except Exception as e:
        print(f'AvroImport: {e}')
    now = round( time(), 3 )
    print(f'AvroImport:{count} readings in {now-prev} seconds')
    return readings

# TEST CODE

def printReadings(readings):
    for reading in readings:
        data = reading["data_i"] + reading["data_q"] * 1j
        print(f'reading: ts= {reading["timestamp"]}, seqno = {reading["seqno"]}, count = {reading["count"]}, data = {data[0]} ... {data[255]}')

def compareReadings(readings,new_readings):
    if readings.head != new_readings.head:
        print(f'compareReadings: readings.head does not match - {readings.head} != {new_readings.head}')
        return
    for i in range (readings.head + 1):
        reading = readings.readings[i]
        new_reading = new_readings.readings[i]
        for item in ['timestamp','seqno','count']:
            if new_reading[item] != reading[item]:
                print(f'compareReadings: {item} does not match - {reading[item]} != {new_reading[item]}')
                return
        for item in ['data_i','data_q']:
            if np.array_equal(reading[item],new_reading[item]) == False:
                print(f'compareReadings: {item} does not match')
                return
        # avro import/export generates non-material differences in float values
        for item in ['magnitude','phase','phase_velocity','phase_unrolled']:
            if np.allclose(reading[item],new_reading[item],atol=0.001 ) == False:
                print(f'compareReadings: {item} does not match')
                return

    print('compareReadings: success')

if  __name__ == "__main__":

    from frame_process import process_frame

    config = read_config()
    if validate_config(config) == False:
        quit()

    prev = round( time(), 3 )
    readings = Readings()
    for seqno in range(10000):
        reading = Reading( seqno, 256, np.random.randint(-2500,2500,256), np.random.randint(-2500,2500,256))
        readings.put(reading)
        process_frame(readings, readings.head, reading)
    now = round( time(), 3 )
    print(f'Avro Test: generated data in {now-prev} seconds')
    prev = now

    fullpathname = os.path.join(config['app']['data'], 'test.avro')
    avroExport(fullpathname, readings)

    now = round( time(), 3 )
    print(f'Avro Test: exported data in {now-prev} seconds')
    prev = now

    old_readings = readings.backup()

    new_readings = avroImport(fullpathname,readings)

    now = round( time(), 3 )
    print(f'Avro Test: imported data in {now-prev} seconds')
    prev = now

    compareReadings(old_readings, new_readings)