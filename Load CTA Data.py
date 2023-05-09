
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from shapely.geos import lgeos
from google.cloud import bigquery
from bs4 import BeautifulSoup
import time
import datetime as dt
import re
import json
import os
import sys
import datetime


# Set up BigQuery client and credentials
client = bigquery.Client.from_service_account_json('PATH TO BIGQUERY CREDENTIALS')

# Route Mapping Dict to transform parameter variables into corresponding line name
route_map = {'y': 'Yellow Line',
 'org': 'Orange Line',
 'pink': 'Pink Line',
 'brn': 'Brown Line',
 'g': 'Green Line',
 'red': 'Red Line',
 'blue': 'Blue Line',
 'p': 'Purple Line'}


# Define function to get data from CTA API and create dataframe
def get_cta_data():
    url = 'http://lapi.transitchicago.com/api/1.0/ttpositions.aspx'
    params = {'key': 'CTA API KEY', 'rt': ['red,blue,brn,g,org,p,pink,y'], 'outputType': 'xml'}
    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.content, 'xml')
    train_data = []
    time = pd.Timestamp.now().floor('s')
    for route in soup.find_all('route'):
        for train in route.find_all('train'):
            train_dict = {'time': time,
                          'route': str(route_map[route['name']]),
                          'run_number': int(train.rn.text),
                          'destination_station_id': int(train.destSt.text),
                          'destination_station_name': str(train.destNm.text),
                          'train_direction': int(train.trDr.text),
                          'next_station_id': int(train.nextStaId.text),
                          'next_stop_id': int(train.nextStpId.text),
                          'next_station_name': str(train.nextStaNm.text),
                          'timestamp': dt.datetime.strptime(train.prdt.text, '%Y%m%d %H:%M:%S'),
                          'arrival_time': dt.datetime.strptime(train.arrT.text, '%Y%m%d %H:%M:%S'),
                          'is_approaching': int(train.isApp.text),
                          'is_delayed': int(train.isDly.text),
                          'latitude': float(train.lat.text),
                          'longitude': float(train.lon.text),
                          'heading': float(train.heading.text)}
            train_data.append(train_dict)
    df = pd.DataFrame(train_data)
    return df

# Define function to upload snapshot dataframe to BigQuery
def upload_snapshot_to_bigquery(df):
    table_id = 'BIGQUERY TABLE ID'
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField('route', 'STRING'),
            bigquery.SchemaField('run_number', 'INTEGER'),
            bigquery.SchemaField('destination_station_id', 'INTEGER'),
            bigquery.SchemaField('destination_station_name', 'STRING'),
            bigquery.SchemaField('train_direction', 'INTEGER'),
            bigquery.SchemaField('next_station_id', 'INTEGER'),
            bigquery.SchemaField('next_stop_id', 'INTEGER'),
            bigquery.SchemaField('next_station_name', 'STRING'),
            bigquery.SchemaField('timestamp', 'DATETIME'),
            bigquery.SchemaField('arrival_time', 'DATETIME'),
            bigquery.SchemaField('is_approaching', 'INTEGER'),
            bigquery.SchemaField('is_delayed', 'INTEGER'),
            bigquery.SchemaField('latitude', 'FLOAT'),
            bigquery.SchemaField('longitude', 'FLOAT'),
            bigquery.SchemaField('heading', 'FLOAT')
        ],
        write_disposition='WRITE_TRUNCATE'
    )
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for job to complete
    print('Uploaded {} rows to BigQuery table {}'.format(len(df), table_id))
    
# Create a dataframe that holds each individual train that runs on the CTA system
# Every 30 seconds see if that train is at the next stop, and add that stop and time to the dataframe
# Ultimately will track a trains progress and times as it makes its run
def update_route_times(to_ingest, route_times):
    for index, row in to_ingest.iterrows():

        # Check if run_number, route, and destination_station_name already exist in route_times
        mask = (route_times['run_number'] == row['run_number']) & \
               (route_times['route'] == row['route']) & \
               (route_times['destination_station_name'] == row['destination_station_name'])
        matching_rows = route_times[mask]
        if matching_rows.empty:
            # Create new row in route_times with empty lists
            new_row = pd.DataFrame({'run_number': [row['run_number']],
                                    'route': [row['route']],
                                    'destination_station_name': [row['destination_station_name']],
                                    'list_of_stations': [[str(row['next_station_name'])]],
                                    'list_of_arrival_times': [[row['arrival_time']]],
                                    'Running': [True]})
            route_times = pd.concat([route_times, new_row], ignore_index=True)
            # Update the matching_rows variable to include the new row
            matching_rows = new_row
        # Append the next_station_name and arrival_time to the existing lists in the matching rows
        for i, matching_row in matching_rows.iterrows():
            last_station_index = len(matching_row['list_of_stations']) - 1
            if matching_row['list_of_stations'] and row['next_station_name'] == matching_row['list_of_stations'][last_station_index]:
                continue
            matching_row['list_of_stations'].append(str(row['next_station_name']))
            matching_row['list_of_arrival_times'].append(row['arrival_time'])
            if row['next_station_name'] == row['destination_station_name']:
                matching_row['Running'] = False
        # If the run has ended, and a new row with the same run_number, route, and destination_station_name is found, create a new row with running set to True
        if matching_rows['Running'].all() == False:
            new_row = pd.DataFrame({'run_number': [row['run_number']],
                                    'route': [row['route']],
                                    'destination_station_name': [row['destination_station_name']],
                                    'list_of_stations': [[str(row['next_station_name'])]],
                                    'list_of_arrival_times': [[row['arrival_time']]],
                                    'Running': [True]})
            route_times = pd.concat([route_times, new_row], ignore_index=True)
    return route_times

# Define function to upload run dataframe to BigQuery
def upload_run_to_bigquery(df):
    df['list_of_stations'].apply(lambda x: json.dumps(x))
    df['date'] = (datetime.date.today())
    table_id = 'BIGQUERY TABLE ID'
    job_config = bigquery.LoadJobConfig(
        schema = [
            bigquery.SchemaField('date', 'DATE', mode='REQUIRED'),
            bigquery.SchemaField('run_number', 'INTEGER', mode='REQUIRED'),
            bigquery.SchemaField('route', 'STRING', mode='REQUIRED'),
            bigquery.SchemaField('destination_station_name', 'STRING', mode='REQUIRED'),
            bigquery.SchemaField('list_of_stations', 'STRING', mode='REPEATED'),
            bigquery.SchemaField('list_of_arrival_times', 'TIMESTAMP', mode='REPEATED'),
            bigquery.SchemaField('Running', 'BOOLEAN', mode='REQUIRED')
        ],
        write_disposition='WRITE_APPEND'
    )
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for job to complete
    print('Uploaded {} rows to BigQuery table {}'.format(len(df), table_id))

def main():
    # Loop to get data and upload to BigQuery every 30 seconds
    route_times_df = pd.DataFrame(columns=['run_number', 'route', 'destination_station_name',
                                        'list_of_stations', 'list_of_arrival_times', 'Running'])

    while True:
        if (pd.Timestamp.now().hour == 15 and pd.Timestamp.now().minute == 24):
            print('the time is now bitch')
            upload_run_to_bigquery(route_times_df)
            route_times_df = pd.DataFrame(columns=['run_number', 'route', 'destination_station_name',
                                    'list_of_stations', 'list_of_arrival_times', 'Running'])
            time.sleep(60)
            
        start_time = pd.Timestamp.now().floor('s')

        df = get_cta_data()
        upload_snapshot_to_bigquery(df)

        to_ingest = df[df.is_approaching == 1][['run_number', 'route', 'destination_station_name', 'next_station_name', 'arrival_time']]
        route_times_df = update_route_times(to_ingest, route_times_df)
        

        end_time = pd.Timestamp.now().floor('s')
        time_diff = (end_time - start_time).total_seconds()

        time.sleep(30 - time_diff)


if __name__ == "__main__":
    main()



