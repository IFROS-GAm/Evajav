USERS = [
    {"username": "999", "password": "ADMIN_MJAVIERA", "redirect": "/administrador"},
    {"username": "10", "password": "M", "redirect": "/seleccionatuprofesor"},
]


def authenticate(username: str, password: str):
    for user in USERS:
        if user["username"] == username and user["password"] == password:
            return user["redirect"]
    return None
