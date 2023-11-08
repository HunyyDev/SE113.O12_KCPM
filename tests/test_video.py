from fastapi.testclient import TestClient
from fastapi.routing import APIRoute
from app.main import app
from app import db
import os
import pytest
import requests
import json
from google.cloud.firestore_v1.base_query import FieldFilter

def endpoints():
    endpoints = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            endpoints.append(route.path)
    return endpoints
@pytest.fixture
def client():
    client = TestClient(app, "http://0.0.0.0:3000")
    yield client
@pytest.fixture
def user():
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=" + os.environ.get("FIREBASE_API_KEY")
    payload = json.dumps({
    "email": "test@gmail.com",
    "password": "testing",
    "returnSecureToken": True
    })
    headers = {
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    data = response.json()
    user = {"id": data['localId'], "token": data["idToken"]}
    yield user
class TestVideoAPI:
    @pytest.mark.skipif("/video" not in endpoints(),reason="Route not defined")
    def test_video_API(self, user, client):
        # Test when sent file is not a video
        payload = {}
        files=[
        ('file',('demo.jpg',open('demo.jpg','rb'),'application/octet-stream'))
        ]
        headers = {
        'Content-Type': 'application/json',
        }
        response = client.request("POST", 'video', headers=headers, data=payload, files=files)
        assert response.status_code == 400
        assert response.text == "File must be video"
        # Test when no token is pass to route
        payload = {}
        files=[
        ('file',('demo.mp4',open('demo.mp4','rb'),'application/octet-stream'))
        ]
        headers = {
        'Content-Type': 'application/json',
        }
        response = client.request("POST", 'video', headers=headers, data=payload, files=files)
        assert response.status_code == 400
        assert response.text == "User not found"
        # Test when all requirements have been fulfilled
        payload = {}
        files=[
        ('file',('demo.mp4',open('demo.mp4','rb'),'application/octet-stream'))
        ]
        headers = {
        'Content-Type': 'application/json',
        'Authorization': "Bearer " + user['token']
        }
        response = client.request("POST", 'video', headers=headers, data=payload, files=files)
        assert response.status_code == 200
        artifactName = response.text
        docs = db.collection("artifacts").where(filter = FieldFilter("name", '==', artifactName))
        index = 0
        for doc in docs:
            # For each document in docs. Verify name and status of the artifact
            index += 1
            data = doc.get().to_dict()
            assert data['name'] == artifactName
            assert data['status'] == 'pending'
            assert index == 1


        



        
