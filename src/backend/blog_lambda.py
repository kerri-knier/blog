from humps import camelize


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

    def to_json_dict(self) -> dict:
        return camelize(vars(self))


def error_response(status: int, error: str, message: str) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "text/plain",
            "x-amzn-ErrorType": error
        },
        "isBase64Encoded": False,
        "body": f"{error}: {message}"
    }


def lambda_handler(event: dict, ctx) -> dict:
    print(event)
    print(ctx)

    path: str = event.get("path")
    verb: str = event.get("httpMethod")
    resource = event.get('resource')

    print(verb, path)

    if type(path) is not str:
        return error_response(404, "NotFound", f"bad path {path} resource {resource} event {event}")

    if not path.startswith("/post"):
        return error_response(404, "NotFound", f"bad path {path} resource {resource} event {event}")

    if verb == "GET":
        return get_posts()

    if verb == "POST":
        body = event.get("body")

        if body is None or body == "":
            return error_response(400, "BadRequest", "cannot create empty post")

        return create_post(body)

    return error_response(404, "BadRequest", f"bad path {path} resource {resource} event {event}")


def get_posts() -> dict:
    response = Response()

    response.body = [
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

    return response.to_json_dict()


def create_post(text) -> dict:
    print("new post:", text)

    response = Response()

    response.status_code = 201

    return response.to_json_dict()
