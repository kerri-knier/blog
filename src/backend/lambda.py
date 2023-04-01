from typing import Optional

class Response:
    statusCode = 200
    headers = {
        "content-type": "application/json"
    }
    isBase64Encoded = False
    multiValueHeaders = {
        "X-Custom-Header": ["My value", "My other value"]
    }
    body = ""


def lambda_handler(event: dict, ctx) -> Response:
    print(event)

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

    return response
