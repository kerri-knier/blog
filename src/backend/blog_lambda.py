import datetime
import json
import logging
import uuid
from dateutil.relativedelta import relativedelta

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from humps import camelize

logger = logging.getLogger(__name__)


class DB:
    def __init__(self):
        self.resource = boto3.resource("dynamodb")
        self.table = None

    def load(self, table_name: str):
        try:
            table = self.resource.Table(table_name)
            table.load()
            self.table = table
        except ClientError as err:
            logger.error(
                "Couldn't load dynamodb table %s: %s: %s",
                table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

        return

    def write_post(self, text: str):
        now = datetime.datetime.now()
        creation = now.strftime("%Y-%m-%dT%H:%M:%S%z")
        month = now.strftime("%Y-%m")
        post_id = str(uuid.uuid1())
        new_post = {
                    'PK': f"POSTMONTH#{month}",
                    'SK': f"POSTTIME#{creation}",
                    'id': post_id,
                    'text': text,
                }
        try:
            self.table.put_item(Item=new_post)
            return new_post
        except ClientError as err:
            logger.error(
                "Couldn't add post: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def get_posts(self, month: str):
        try:
            response = self.table.query(
                KeyConditionExpression=Key("PK").eq(f"POSTMONTH#{month}")
            )

            return response["Items"]
        except ClientError as err:
            logger.error(
                "Couldn't query for posts in %s: %s: %s",
                month,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def get_post(self, post_id: str):
        try:
            response = self.table.query(
                IndexName="id-index", KeyConditionExpression=Key("id").eq(post_id)
            )

            items = response["Items"]
            return items[0] if len(items) > 0 else None
        except ClientError as err:
            logger.error(
                "Couldn't query for post %s: %s: %s",
                post_id,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise


class Response:
    def __init__(self):
        self.status_code = 200
        self.headers = {
            "content-type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        }
        self.is_base64_encoded = False
        self.multi_value_headers = {"X-Custom-Header": ["My value", "My other value"]}
        self.body = ""

    def to_json_dict(self) -> dict:
        return {camelize(k): v for k, v in vars(self).items()}


def error_response(status: int, error: str, message: str) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "text/plain",
            "x-amzn-ErrorType": error,
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        },
        "isBase64Encoded": False,
        "body": f"{error}: {message}",
    }


def lambda_handler(event: dict, ctx) -> dict:
    print("EVENT", event)
    print("CONTEXT", ctx)

    path: str = event.get("path")
    pathParams: dict = event.get("pathParameters")
    post_id: str = pathParams.get("postid") if pathParams else None
    verb: str = event.get("httpMethod")
    resource = event.get("resource")

    print(verb, path, pathParams)

    if type(path) is not str:
        return error_response(
            404,
            "NotFound",
            f"bad path {path} resource {resource} event {type(event)} {event}",
        )

    if not path.startswith("/post"):
        return error_response(
            404,
            "NotFound",
            f"bad path {path} resource {resource} event {type(event)} {event}",
        )

    if verb == "GET":
        return get_posts(post_id)

    if verb == "POST":
        body = event.get("body")
        text = None

        if body:
            text = json.loads(body)

        if not text:
            return error_response(400, "BadRequest", "cannot create empty post")

        return create_post(text)

    return error_response(
        404,
        "NotFound",
        f"bad path {path} resource {resource} event {type(event)} {event}",
    )


def get_posts(post_id: str) -> dict:
    response = Response()

    db = DB()
    db.load("blog")

    if post_id:
        post = db.get_post(post_id)
        if post is None:
            return error_response(
                404,
                "NotFound",
                f"post {post_id} not found",
            )

        response.body = json.dumps(posts)

        return response.to_json_dict()

    posts = []
    for i in range(12):
        month_posts = db.get_posts(format_past_month(i))
        month_posts.sort(key=lambda post: post["SK"], reverse=True)

        posts += month_posts

        if len(posts) > 10:
            posts = posts[:10]
            break

    print("POSTS")
    i = 0
    for post in posts:
        print(i, post)
        i += 1

    response.body = json.dumps(posts)

    return response.to_json_dict()


def format_past_month(offset: int) -> str:
    month = datetime.date.today() - relativedelta(months=offset)

    return month.strftime("%Y-%m")


def create_post(text) -> dict:
    print("new post:", text)

    db = DB()
    db.load("blog")
    result = db.write_post(text)

    response = Response()

    response.status_code = 201
    response.body = json.dumps(result)

    return response.to_json_dict()
