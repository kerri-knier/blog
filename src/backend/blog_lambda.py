import json
from typing import Optional


class Response:
    def __init__(self):
        self.status_code = 200
        self.headers = {
            "content-type": "application/json"
        }
        self.is_base64_encoded = False
        self.multi_value_headers = {
            "X-Custom-Header": ["My value", "My other value"]
        }
        self.body = ""


def lambda_handler(event: dict, ctx) -> dict:
    print(event)
    print(ctx)

    query_params: Optional[dict] = event.get("queryStringParameters")
    print(query_params)

    value = ""
    if type(query_params) is dict:
        value = query_params.get('key')
        print(value)

    response = Response()

    response.body = {
        "key1": "value1",
        "key2": "value2",
        "qp": value
    }

    return vars(response)
