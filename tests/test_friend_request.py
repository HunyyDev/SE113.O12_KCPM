import os
import pytest
import json
import cv2
import mmcv
import requests
from fastapi.testclient import TestClient
from app.main import app
from app import db
from app.constants import deviceId
from fastapi.routing import APIRoute
from app import db
from google.cloud.firestore_v1.base_query import FieldFilter
import time

def endpoints():
    endpoints = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            endpoints.append(route.path)
    return endpoints


def read_qr_code(filename):
    """Read an image and read the QR code.

    Args:
        filename (string): Path to file

    Returns:
        qr (string): Value from QR code
    """
    try:
        img = cv2.imread(filename)
        detect = cv2.QRCodeDetector()
        value, points, straight_qrcode = detect.detectAndDecode(img)
        return value
    except:
        return


@pytest.fixture
def client():
    client = TestClient(app)
    yield client


@pytest.fixture
def inviter():
    url = (
        "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key="
        + os.environ.get("FIREBASE_API_KEY")
    )

    payload = json.dumps(
        {"email": "test@gmail.com", "password": "testing", "returnSecureToken": True}
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    data = response.json()
    inviter = {"id": data["localId"], "token": data["idToken"]}
    yield inviter


@pytest.fixture()
def invitee():
    url = (
        "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key="
        + os.environ.get("FIREBASE_API_KEY")
    )

    payload = json.dumps(
        {"email": "test2@gmail.com", "password": "testing2", "returnSecureToken": True}
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    data = response.json()
    invitee = {"id": data["localId"], "token": data["idToken"]}
    yield invitee


class TestFriendRequest:
    @pytest.mark.skipif(
        "/friend_request" not in endpoints(), reason="Route not defined"
    )
    def test_post_friend(self, client, inviter, invitee):
        # Call the firebase database
        friend_request_ref = db.collection("friend_request")
        # Remove all the friend_request use for testing in the past
        query = friend_request_ref.where(
            filter=FieldFilter("inviter", "==", inviter["id"])
        )
        docs = query.stream()
        for doc in docs:
            doc.reference.delete()
        # Delete the user for safety-check
        user_ref = db.collection("user")
        user_ref.document(inviter["id"]).delete()
        # Send request with no token
        payload = ""
        headers = {
            "Content-Type": "application/json",
        }
        response = client.request(
            "POST", "friend_request", headers=headers, data=payload
        )
        assert response.status_code == 403
        # Send request with false token
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer amksckmasckmafvqnwfniqoniofv",
        }
        response = client.request(
            "POST", "friend_request", headers=headers, data=payload
        )
        assert response.status_code == 401
        # Send request with unknown user
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + inviter["token"],
        }
        flag = False
        for i in range(5):
            response = client.request(
                "POST", "friend_request", headers=headers, data=payload
            )
            if response.status_code == 200:
                flag = True
                break
            else:
                time.sleep(2)
        # Create request and re-send
        user_ref.document(inviter["id"]).set({"deviceId": deviceId})
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + inviter["token"],
        }
        response = client.request(
            "POST", "friend_request", headers=headers, data=payload
        )
        assert response.status_code == 200
        result = mmcv.imfrombytes(response.read())
        # Check returned QR image
        assert result.shape[2] == 3
        # Write image for later read
        mmcv.imwrite(result, "qrcode.jpg")
        request_id = read_qr_code("qrcode.jpg")
        ## Send request again (accept friend request when no invitee)
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + inviter["token"],
        }
        response = client.request(
            "PATCH", "friend_request/" + request_id, headers=headers, data=payload
        )
        assert response.status_code == 409
        # Now test for the invitee aka the one that scan QR code
        # Delete invitee user (if existed)
        user_ref.document(invitee["id"]).delete()
        # Test when the invitee is unknow user (no user entity in database)
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + invitee["token"],
        }
        response = client.request(
            "PATCH", "friend_request/" + request_id, headers=headers, data=payload
        )
        assert response.status_code == 403

        # Create invitee user
        user_ref.document(invitee["id"]).set({"deviceId": deviceId})
        # Send request
        ## Send request with false token 
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + "xxxxxx",
        }
        response = client.request(
            "PATCH", "friend_request/" + request_id, headers=headers, data=payload
        )
        assert response.status_code == 401
        ## Send request
        request_id = read_qr_code("qrcode.jpg")
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + invitee["token"],
        }
        response = client.request(
            "PATCH", "friend_request/" + request_id, headers=headers, data=payload
        )
        assert response.status_code == 200
        ## Send request again (false)
        request_id = read_qr_code("qrcode.jpg")
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + invitee["token"],
        }
        response = client.request(
            "PATCH", "friend_request/" + request_id, headers=headers, data=payload
        )
        assert response.status_code == 409
        ## Send request again (accept friend request from invitee)
        request_id = read_qr_code("qrcode.jpg")
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + inviter["token"],
        }
        response = client.request(
            "PATCH", "friend_request/" + request_id, headers=headers, data=payload
        )
        assert response.status_code == 200
        # Delete entity for next time test
        user_ref.document(inviter["id"]).delete()
        user_ref.document(invitee["id"]).delete()
    def test_delete_requestF(self, client, inviter, invitee):
        # Call the firebase database
        friend_request_ref = db.collection("friend_request")
        # Remove all the friend_request use for testing in the past
        query = friend_request_ref.where(
            filter=FieldFilter("inviter", "==", inviter["id"])
        )
        docs = query.stream()
        for doc in docs:
            doc.reference.delete()
        # Delete the user for safety-check
        user_ref = db.collection("user")
        user_ref.document(inviter["id"]).delete()
        # Create request and re-send
        user_ref.document(inviter["id"]).set({"deviceId": deviceId})
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + inviter["token"],
        }
        flag = False
        for i in range(5):
            response = client.request(
                "POST", "friend_request", headers=headers, data=payload
            )
            if(response.status_code == 200):
                flag = True
                break
            else:
                time.sleep(2)
        assert flag == True
        result = mmcv.imfrombytes(response.read())
        # Check returned QR image
        assert result.shape[2] == 3
        # Write image for later read
        mmcv.imwrite(result, "qrcode.jpg")
        request_id = read_qr_code("qrcode.jpg")
        #Check with unknowed invitee
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + invitee["token"],
        }
        response = client.request(
            "DELETE", "friend_request/" + request_id, headers=headers, data=payload
        )
        #Delete invitee for safety check
        user_ref.document(invitee["id"]).delete()
        # Create invitee user
        user_ref.document(invitee["id"]).set({"deviceId": deviceId})
        # check DELETE route
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + inviter["token"],
        }
        response = client.request(
            "DELETE", "friend_request/" + "xxxx", headers=headers, data=payload
        )
        assert response.status_code == 404
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + invitee["token"],
        }
        response = client.request(
            "DELETE", "friend_request/" + request_id, headers=headers, data=payload
        )
        assert response.status_code == 403
        #Correct Request
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + inviter["token"],
        }
        response = client.request(
            "DELETE", "friend_request/" + request_id, headers=headers, data=payload
        )
        assert response.status_code == 200

        # Delete entity for next time test
        user_ref.document(inviter["id"]).delete()
        user_ref.document(invitee["id"]).delete()