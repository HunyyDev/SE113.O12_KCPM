from fastapi.testclient import TestClient
import mmcv
from app.main import app
import pytest
import json
import os
import site
import shutil
from fastapi.routing import APIRoute
from app import firebase_app
from firebase_admin import firestore
def get_site_packages():
    # Get the list of directories 
    site_packages_dirs = site.getsitepackages()

    # Find the "site-packages" directory in the list
    for dir in site_packages_dirs:
        if dir.endswith("site-packages"):
            target_dir = dir
            break
        else:
            target_dir=None
    return target_dir

def endpoints():
    endpoints = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            endpoints.append(route.path)
    return endpoints
@pytest.fixture(autouse=True)
def modify_mmcv_image():
    site_packages_path = get_site_packages()
    dirList = os.listdir(site_packages_path)
    if "mmcv" in dirList:
        shutil.copyfile("libs/image.py", os.path.join(site_packages_path, "mmcv/visualization/image.py"))
    else:
        pytest.exit('Error: Cannot modified mmcv.Image')
        
@pytest.fixture
def client():
    client = TestClient(app, "http://0.0.0.0:3000")
    yield client
@pytest.fixture
def token():
    token = ""
    yield token
class TestFireBaseAPI():
    def test_get_me(self, client, token):
        if "/me" not in endpoints():
            pytest.skip("This route isn't defined")
        else:
            if token != "":
                payload = ""
                headers = {
                    'accept': 'application/json',
                    "Authorization":"Bearer " + token
                }
                response = client.request("get", 'me', headers=headers, data=payload)
                assert response.status_code == 200
            payload = ""
            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json',
            }
            response = client.request("get", 'me', headers=headers, data=payload)
            assert response.status_code == 403
    def test_invitation(self,client, token):
        if"/invitation" not in endpoints():
            pytest.skip("This route isn't defined")
        else:
            payload = ''
            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json',
                "Authorization": "Bearer " + token
            }
            response = client.request("post", 'invitation', headers=headers, data=payload)
            assert response.status_code == 200
            result = mmcv.imfrombytes(response.read())
            assert result.shape[0] == 3
            