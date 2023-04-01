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


def lambda_handler(event, ctx) -> Response:
    query_params = event['queryParameters']
    print(query_params)

    value = ""
    if type(query_params) is dict:
        print(query_params["key"])
        value = query_params["key"]

    response = Response()

    response.body = {
        "key1": "value1",
        "key2": "value2",
        "qp": value
    }

    return response
