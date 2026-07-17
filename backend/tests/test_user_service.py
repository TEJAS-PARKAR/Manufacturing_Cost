from backend.services.user_service import UserService


class FakeCollection:
    def __init__(self):
        self.documents = {}
        self.inserted = []

    def find_one(self, filter, *args, **kwargs):
        username = filter.get("username")
        return self.documents.get(username)

    def insert_one(self, document):
        self.inserted.append(document)
        self.documents[document["username"]] = document
        return type("InsertResult", (), {"inserted_id": document["username"]})()

    def create_index(self, *args, **kwargs):
        return "index-created"


def test_register_and_authenticate_user_with_fake_collection():
    collection = FakeCollection()
    service = UserService(collection=collection, users_collection_name="users")

    created = service.register_user("alice", "secret123")
    assert created["username"] == "alice"
    assert created["password_hash"] != "secret123"

    authenticated = service.authenticate_user("alice", "secret123")
    assert authenticated is True

    rejected = service.authenticate_user("alice", "wrong-password")
    assert rejected is False
