import pytest
import json 
import requests
@pytest.fixture
def token_inviter():
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyArSoK9Wx9Hpe1R9ZywuLEIMVjCtHjO8Os"

    payload = json.dumps({
    "email": "test@gmail.com",
    "password": "testing",
    "returnSecureToken": True
    })
    headers = {
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    token = response.json()["idToken"]
    yield token
@pytest.fixture()
def token_invitee():
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyArSoK9Wx9Hpe1R9ZywuLEIMVjCtHjO8Os"

    payload = json.dumps({
    "email": "test2@gmail.com",
    "password": "testing2",
    "returnSecureToken": True
    })
    headers = {
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    token = response.json()["idToken"]
    yield token
