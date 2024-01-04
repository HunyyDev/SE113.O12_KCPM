from firebase_admin import messaging
from app import db
from google.cloud.firestore_v1.base_query import FieldFilter

# This function cannot be automation test because the requirement of another device to receive notification
def sendMessage(artifactId: str, message: str = None):
    token = []
    artifact = db.collection("artifacts").document(artifactId).get()
    if not artifact.exists:
        return
    artifact = artifact.to_dict()
    user_ref = db.collection("user").where(
        filter=FieldFilter("artifacts", "array_contains", "artifacts/" + artifactId)
    ).stream()
    for user in user_ref:
        token.append(user.to_dict()["deviceId"])
    if message is not None:
        msg = messaging.MulticastMessage(
            data={
                "notification": {
                    "title": message,
                    "body": "Video "
                    + artifact["name"]
                    + " has done inference. Click here to see the video",
                },
            },
            android=messaging.AndroidConfig(
                notification=messaging.AndroidNotification(
                    icon="stock_ticker_update", color="#f45342"
                ),
            ),
            tokens=token
        )
    else:
        msg = messaging.MulticastMessage(
            data={
                "notification": {
                    "title": "Video " + artifact['name'] + " has done inference.",
                    "body": "Video "
                    + artifact["name"]
                    + " has done inference. Click here to see the video",
                },
            },
            android=messaging.AndroidConfig(
                notification=messaging.AndroidNotification(
                    icon="stock_ticker_update", color="#f45342"
                ),
            ),
            tokens=token
        )
    response = messaging.send_multicast(msg)
    return response.success_count
