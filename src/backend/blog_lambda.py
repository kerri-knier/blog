import datetime
import json
import uuid

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import (
    APIGatewayRestResolver,
    Response,
    content_types,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from dateutil.relativedelta import relativedelta

logger = Logger()
app = APIGatewayRestResolver()


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
            "PK": f"POSTID#{post_id}",
            "SK": "POST",
            "created": creation,
            "month": month,
            "text": text,
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
                IndexName="month-created-index",
                KeyConditionExpression=Key("month").eq(month),
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
            response = self.table.get_item(
                Key={"PK": f"POSTID#{post_id}", "SK": "POST"}
            )

            return response["Item"]
        except ClientError as err:
            logger.error(
                "Couldn't query for post %s: %s: %s",
                post_id,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def delete_post(self, post_id: str):
        try:
            response = self.table.delete_item(
                Key={"PK": f"POSTID#{post_id}", "SK": "POST"}
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


class AppResponse:
    def __init__(self):
        self.status_code = 200
        self.headers = {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
            "X-Custom-Header": ["My value", "My other value"],
        }
        self.body = ""

    def to_lambda_response(self) -> Response:
        Response(
            status_code=200,
            content_type=content_types.APPLICATION_JSON,
            body=self.body,
            headers=self.headers,
        )


def error_response(status: int, error: str, message: str) -> Response:
    return Response(
        status_code=status,
        content_type=content_types.TEXT_PLAIN,
        body=f"{error}: {message}",
        headers={
            "x-amzn-ErrorType": error,
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        },
    )


def lambda_handler(event: dict, ctx: LambdaContext) -> Response:
    print("EVENT", event)
    print("CONTEXT", ctx)

    return app.resolve(event, ctx)


@app.get("/post/<post_id>")
def get_post(post_id: str) -> Response:
    response = AppResponse()

    db = DB()
    db.load("blog")

    if not post_id:
        return error_response(400, "BadRequest", "cannot get empty post id")

    post = db.get_post(post_id)
    if post is None:
        return error_response(
            404,
            "NotFound",
            f"post {post_id} not found",
        )

    response.body = json.dumps(post)

    return response.to_lambda_response()


@app.get("/post")
def get_posts() -> Response:
    response = AppResponse()

    db = DB()
    db.load("blog")

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

    return response.to_lambda_response()


@app.delete("/post/<post_id>")
def delete_post(post_id: str) -> Response:
    response = AppResponse()

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

        response.body = json.dumps(post)

        return response.to_lambda_response()


def format_past_month(offset: int) -> str:
    month = datetime.date.today() - relativedelta(months=offset)

    return month.strftime("%Y-%m")


@app.post("/post")
def create_post() -> Response:
    text = app.current_event.body
    print("new post:", text)

    if not text:
        return error_response(400, "BadRequest", "cannot create empty post")

    db = DB()
    db.load("blog")
    result = db.write_post(text)

    response = AppResponse()

    response.status_code = 201
    response.body = json.dumps(result)

    return response.to_lambda_response()
