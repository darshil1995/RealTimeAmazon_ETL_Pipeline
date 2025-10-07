import http.client
import json
import pandas as pd
import boto3
from datetime import datetime
import os

def lambda_handler(event, context):
    conn = http.client.HTTPSConnection("real-time-amazon-data.p.rapidapi.com")

    headers = {
        'x-rapidapi-key': os.environ["x-rapidapi-key"],
        'x-rapidapi-host': "real-time-amazon-data.p.rapidapi.com"
    }

    search_term = "phone"

    conn.request("GET", "/search?query="+search_term+"&page=1&country=US&sort_by=RELEVANCE&product_condition=ALL&is_prime=false&deals_and_discounts=NONE", headers=headers)

    res = conn.getresponse()
    api_response_bytes = res.read()

    api_response_string = api_response_bytes.decode("utf-8")

    data_dict = json.loads(api_response_string)

    
    # Convert the dictionary back to a JSON string before uploading

    client = boto3.client('s3')
    file_name = "amazon_raw_" + str(datetime.now()) + ".json"
    client.put_object(
        Bucket='amazon-realtime-data-etl-pipeline',
        Key='raw_data/to_process/' + file_name,
        Body=json.dumps(data_dict)
    )

    
