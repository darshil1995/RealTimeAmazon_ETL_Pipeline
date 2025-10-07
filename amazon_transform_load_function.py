import json
import boto3
from datetime import datetime
from io import StringIO
import pandas as pd

def products(data):
    print(f"Found {len(data)} products:")

    product_list=[]

    for product in data:
        asin = product['asin']
        title = product['product_title']
        price = product['product_price']
        product_original_price = product['product_original_price']
        rating = product['product_star_rating']
        produuct_num_ratings = product['product_num_ratings']
        product_num_offers = product['product_num_offers']
        product_original_price = product['product_original_price']
        product_minimum_offer_price = product['product_minimum_offer_price']
        product_url = product['product_url']
        product_photo = product['product_photo']
        product_prime = product['is_prime']
        product_is_best_seller = product['is_best_seller']
        product_is_amazon_choice = product['is_amazon_choice']
        product_badge = product.get('product_badge','N/A')

        # Creating Dictionary
        product_dict = {
            'asin': asin,
            'title': title,
            'price': price,
            'original_price': product_original_price,
            'minimum_offer_price': product_minimum_offer_price,
            'rating': rating,
            'num_of_ratings': produuct_num_ratings,
            'num_of_offers': product_num_offers,
            'url': product_url,
            'photo': product_photo,
            'prime': product_prime,
            'best_seller': product_is_best_seller,
            'amazon_choice': product_is_amazon_choice,
            'product_badge': product_badge
        }
        
        product_list.append(product_dict)
    
    return product_list

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    Bucket = "amazon-realtime-data-etl-pipeline"
    Key = "raw_data/to_process/"

    amazon_data=[]
    amazon_key = []

    response = s3.list_objects_v2(Bucket=Bucket, Prefix=Key)
    contents = response.get('Contents')

    for file in contents:
        file_key = file['Key']
        
        if file_key.endswith('.json'):
            response = s3.get_object(Bucket=Bucket, Key=file['Key'])
            content = response['Body']
            jsonObject = json.loads(content.read())
            
            amazon_data.append(jsonObject)
            amazon_key.append(file['Key'])

            print(f"File {file_key} processed successfully.")
            print(amazon_data)

    for data in amazon_data:
        product_list = products(data['data']["products"])
        print(len(product_list))

        product_df = pd.DataFrame.from_dict(product_list)

        # Drop Duplicates
        product_df.drop_duplicates(subset='asin', keep='first', inplace=True)

        # Clean the title by replacing newlines and tabs with a space
        product_df['title'] = product_df['title'].replace('\n', ' ').replace('\t', ' ')


        #Filling Null Values of Original price and Ratings
        product_df['original_price'] = product_df['original_price'].fillna(product_df['price'])
        product_df['rating'] = product_df['rating'].fillna(0)

        # Transforming Data
        product_df['price'] = product_df['price'].str.replace('$', '')
        product_df['minimum_offer_price'] = product_df['minimum_offer_price'].str.replace('$', '')
        product_df['original_price'] = product_df['original_price'].str.replace('$', '')

        # Saving the Transformed Data to S3 bucket
        product_key = "transformed_data/products/products_transformed_" + str(datetime.now()) + ".csv"
        product_buffer = StringIO()
        product_df.to_csv(product_buffer, index=False)
        product_content = product_buffer.getvalue()
        s3.put_object(Bucket=Bucket, Key=product_key, Body=product_content)

    # Deleting the data inside Toprcessed folder, and moving to processed folder to avoid processing again   
    s3_resource = boto3.resource('s3')
    for key in amazon_key:
        copy_source = {
                'Bucket': Bucket,
                'Key': key
            }
        s3_resource.meta.client.copy(copy_source, Bucket, "raw_data/processed/" + key.split("/")[-1])
        s3_resource.Object(Bucket, key).delete()




