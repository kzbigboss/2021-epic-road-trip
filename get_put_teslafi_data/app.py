import os
import requests
import json
import boto3
import base64
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    # TODO description

    ## Get data from TeslaFi
    teslafi_token = get_secret()

    teslafi_url = "https://www.teslafi.com/feed.php?" + \
                  "token=" + teslafi_token # + \
                  # "&command=lastGoodTemp"

    teslafi_data = get_teslafi_data(teslafi_url)

    ## Put data into data stream
    teslafi_stream_name = get_env_var("teslafidatastream")

    put_response = put_teslafi_data(teslafi_data, teslafi_stream_name)

    print(put_response)


def get_env_var(variable_name):
    """
    Helper to grab Lambda's env vars
    :param variable_name: string, named of
    :return: variable: string
    """

    try:
        variable = os.environ[variable_name]
    except:
        print("Environment variable name not found")
        exit()

    return variable


def get_secret():
    """
    Example AWS Python function to pull from Secrets Manager
    :return: string representing API token
    """
    secret_name = "epicroadtripteslafiapi"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])

    return json.loads(secret)['teslafiapi']


def get_teslafi_data(url):
    # TODO DESC

    r = requests.get(url)

    return r.json()


def put_teslafi_data(payload, stream_name):
    data_stream = boto3.client('kinesis')

    response = data_stream.put_record(
        StreamName=stream_name,
        Data=json.dumps(payload).encode('utf-8') + b'\n',
        PartitionKey="whatever"  # why this remains a required parameter boggles my mind
    )

    return response
