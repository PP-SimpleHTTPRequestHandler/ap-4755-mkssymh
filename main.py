import json
from http.server import HTTPServer, BaseHTTPRequestHandler

USERS_LIST = [
    {
        "id": 1,
        "username": "theUser",
        "firstName": "John",
        "lastName": "James",
        "email": "john@email.com",
        "password": "12345",
    }
]

DEFAULT_USERS_LIST = [
    {
        "id": 1,
        "username": "theUser",
        "firstName": "John",
        "lastName": "James",
        "email": "john@email.com",
        "password": "12345",
    }
]

REQUIRED_USER_FIELDS = {"id": int, "username": str, "firstName": str, "lastName": str, "email": str, "password": str}
REQUIRED_PUT_FIELDS = {"username": str, "firstName": str, "lastName": str, "email": str, "password": str}


def is_valid_user(data):
    if not isinstance(data, dict):
        return False
    for field, ftype in REQUIRED_USER_FIELDS.items():
        if field not in data or not isinstance(data[field], ftype):
            return False
    return True


def is_valid_put(data):
    if not isinstance(data, dict):
        return False
    for field, ftype in REQUIRED_PUT_FIELDS.items():
        if field not in data or not isinstance(data[field], ftype):
            return False
    return True


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def _set_response(self, status_code=200, body=None):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(body if body is not None else {}).encode('utf-8'))

    def _parse_body(self):
        content_length = int(self.headers['Content-Length'])
        return json.loads(self.rfile.read(content_length).decode('utf-8'))

    def do_GET(self):
        global USERS_LIST

        if self.path == '/reset':
            USERS_LIST = [dict(u) for u in DEFAULT_USERS_LIST]
            self._set_response(200, {})

        elif self.path == '/users':
            self._set_response(200, USERS_LIST)

        elif self.path.startswith('/user/'):
            username = self.path.split('/')[-1]
            user = next((u for u in USERS_LIST if u['username'] == username), None)
            if user:
                self._set_response(200, user)
            else:
                self._set_response(400, {"error": "User not found"})

        else:
            self._set_response(404, {})

    def do_POST(self):
        body = self._parse_body()

        if self.path == '/user':
            if not is_valid_user(body):
                self._set_response(400, {})
                return
            if any(u['id'] == body['id'] for u in USERS_LIST):
                self._set_response(400, {})
                return
            USERS_LIST.append(body)
            self._set_response(201, body)

        elif self.path == '/user/createWithList':
            if not isinstance(body, list) or not all(is_valid_user(u) for u in body):
                self._set_response(400, {})
                return
            existing_ids = {u['id'] for u in USERS_LIST}
            if any(u['id'] in existing_ids for u in body):
                self._set_response(400, {})
                return
            USERS_LIST.extend(body)
            self._set_response(201, body)

        else:
            self._set_response(404, {})

    def do_PUT(self):
        if self.path.startswith('/user/'):
            user_id = self.path.split('/')[-1]
            try:
                user_id = int(user_id)
            except ValueError:
                self._set_response(400, {"error": "not valid request data"})
                return

            body = self._parse_body()

            if not is_valid_put(body):
                self._set_response(400, {"error": "not valid request data"})
                return

            user = next((u for u in USERS_LIST if u['id'] == user_id), None)
            if not user:
                self._set_response(404, {"error": "User not found"})
                return

            user.update(body)
            self._set_response(200, user)

        else:
            self._set_response(404, {})

    def do_DELETE(self):
        global USERS_LIST

        if self.path.startswith('/user/'):
            user_id = self.path.split('/')[-1]
            try:
                user_id = int(user_id)
            except ValueError:
                self._set_response(404, {"error": "User not found"})
                return

            user = next((u for u in USERS_LIST if u['id'] == user_id), None)
            if not user:
                self._set_response(404, {"error": "User not found"})
                return

            USERS_LIST = [u for u in USERS_LIST if u['id'] != user_id]
            self._set_response(200, {})

        else:
            self._set_response(404, {})


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, host='localhost', port=8000):
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


if __name__ == '__main__':
    from sys import argv
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
