import datetime
import json
import logging
import uuid

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from humps import camelize

logger = logging.getLogger(__name__)


class DB:
    def __init__(self):
        self.resource = boto3.resource("dynamodb")
        self.table = None

    def exists(self, table_name: str):
        try:
            table = self.resource.Table(table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response['Error']['Code'] == 'ResourceNotFoundException':
                exists = False
            else:
                logger.error(
                    "Couldn't check for existence of %s: %s: %s",
                    table_name,
                    err.response['Error']['Code'], err.response['Error']['Message'])
                raise
        else:
            self.table = table
        return exists

    def write_post(self, text: str):
        now = datetime.datetime.now()
        creation = now.strftime("%Y-%m-%dT%H:%M:%S%z")
        month = now.strftime("%Y-%m")
        post_id = str(uuid.uuid1())
        try:
            self.table.put_item(
                Item={
                    'PK': f"POSTMONTH#{month}",
                    'SK': f"POSTTIME#{creation}",
                    'id': post_id,
                    'text': text,
                }
            )
        except ClientError as err:
            logger.error(
                "Couldn't add post: %s: %s",
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

    def get_posts(self, month: str):
        try:
            response = self.table.query(KeyConditionExpression=Key('PK').eq(f"POSTMONTH#{month}"))
        except ClientError as err:
            logger.error(
                "Couldn't query for posts in %s: %s: %s", month,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Items']


class Response:
    def __init__(self):
        self.status_code = 200
        self.headers = {
            "content-type": "application/json",
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        }
        self.is_base64_encoded = False
        self.multi_value_headers = {
            "X-Custom-Header": ["My value", "My other value"]
        }
        self.body = ""

    def to_json_dict(self) -> dict:
        return {camelize(k): v for k, v in vars(self).items()}


def error_response(status: int, error: str, message: str) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "text/plain",
            "x-amzn-ErrorType": error,
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        "isBase64Encoded": False,
        "body": f"{error}: {message}"
    }


def lambda_handler(event, ctx) -> dict:
    print(event)
    print(ctx)

    path: str = event.get("path")
    verb: str = event.get("httpMethod")
    resource = event.get('resource')

    print(verb, path)

    if type(path) is not str:
        return error_response(404, "NotFound", f"bad path {path} resource {resource} event {type(event)} {event}")

    if not path.startswith("/post"):
        return error_response(404, "NotFound", f"bad path {path} resource {resource} event {type(event)} {event}")

    if verb == "GET":
        return get_posts()

    if verb == "POST":
        body = event.get("body")

        if body is None or body == "":
            return error_response(400, "BadRequest", "cannot create empty post")

        return create_post(body)

    return error_response(404, "NotFound", f"bad path {path} resource {resource} event {type(event)} {event}")


def get_posts() -> dict:
    response = Response()

    db = DB()
    db.exists("blog")
    print("posts:", db.get_posts(current_month()))

    posts = [
        "stored first post",
        "stored second post",
        "stored third post",
        "stored fourth and extra long post about anything and everything because now its making sense",
        "stored fifth post",
        "stored sixth post",
        "stored seventh post",
        "stored eighth post",
        "stored ninth post",
        "stored tenth post",
    ]

    response.body = json.dumps(posts)

    return response.to_json_dict()


def current_month() -> str:
    return datetime.date.today().strftime("%Y-%m")


def create_post(text) -> dict:
    print("new post:", text)

    db = DB()
    db.exists("blog")
    db.write_post(text)

    response = Response()

    response.status_code = 201

    return response.to_json_dict()
