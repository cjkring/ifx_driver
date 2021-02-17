from fastavro import writer, schemaless_writer, reader, parse_schema
import rd_store
import numpy as np
import os
from config import read_config, validate_config

schema = {
    'name': 'reading.Reading',
    'type': 'record',
    'namespace': 'test',
    'fields': [
        {'name': 'timestamp', 'type': 'double'},
        {'name': 'seqno', 'type': 'int'},
        {'name': 'count', 'type': 'int'},
        {'name': 'data_i', 'type': {'type': 'array','items':'int'}},
        {'name': 'data_q', 'type': {'type': 'array','items':'int'}},
    ]
}
parsed_schema = parse_schema(schema)
def avroExport(filename, readings):
    try:
        with open(fullpathname, 'wb') as f:
            # write the schema and headers with the first on
            writer(f, parsed_schema, readings)
    except Exception as e:
        print(f'AvroExport: {e}')

def avroImport(filename, readings):
    try:
        # reset readings,  the io_thread was stopped by the calling function
        count = 0
        readings.backup()
        with open(filename, 'rb') as f:
            for record in reader(f):
                reading = rd_store.Reading( record["seqno"], record["count"], record["data_i"], record["data_q"])
                reading["timestamp"] = record["timestamp"]
                readings.put(reading)
                count += 1
        print(f'AvroImport: {count} readings inported')
    except Exception as e:
        print(f'AvroImport: {e}')
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
        if np.array_equal(reading['data_i'],new_reading['data_i']) == False:
            print(f'compareReadings: data_i does not match')
            return
        if np.array_equal(reading['data_q'],new_reading['data_q']) == False:
            print(f'compareReadings: data_q does not match')
            return
    print('compareReadings: success')

if  __name__ == "__main__":

    config = read_config()
    if validate_config(config) == False:
        quit()

    readings = rd_store.Readings()
    for seqno in range(10000):
        reading = rd_store.Reading( seqno, 256, np.random.randint(-2500,2500,256), np.random.randint(-2500,2500,256))
        readings.put(reading)

    fullpathname = os.path.join(config['app']['data'], 'test.avro')
    avroExport(fullpathname, readings)

    new_readings = avroImport(fullpathname,readings)

    compareReadings(readings, new_readings)