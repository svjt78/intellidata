#Update glue crawler

import boto3
import json

def lambda_handler(event, context):

	print (event)
	glue_client = boto3.client(service_name='glue', region_name='us-east-1',
		aws_access_key_id='AKIATENFQTYA3U4TNBFH' ,
    	aws_secret_access_key='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',
              endpoint_url='https://glue.us-east-1.amazonaws.com')

	response = glue_client.start_crawler(Name = 'ieintakemetadata')
    
