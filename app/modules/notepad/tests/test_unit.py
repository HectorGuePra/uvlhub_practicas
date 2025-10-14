import pytest

from app import db
from app.modules.auth.models import User
from app.modules.conftest import login, logout
from app.modules.profile.models import UserProfile
from app.modules.notepad.models import Notepad

# @pytest.fixture(scope='module')
# def test_client(test_client):
#     """
#     Extends the test_client fixture to add additional specific data for module testing.
#     """
#     with test_client.application.app_context():
#         # Add HERE new elements to the database that you want to exist in the test context.
#         # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.

#         user_test = User(email="test@example.com", password="test1234")
#         db.session.add(user_test)
#         db.session.commit()

#         profile = UserProfile(user_id=user_test.id, name="Name", surname="Surname")
#         db.session.add(profile)
#         db.session.commit()

#     yield test_client


# ==================== GET ==========================================
def test_sample_assertion(test_client):
    greeting = "Hello, World!"
    assert greeting == "Hello, World!"

def test_list_empty_notepad_get(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get("/notepad")
    assert response.status_code == 200
    assert b"You have no notepads." in response.data

    logout(test_client)

def test_list_notepad_unauthenticated_get(test_client):
    response = test_client.get("/notepad", follow_redirects=True)
    assert response.status_code == 200
    assert b"login" in response.data.lower() or b"please log in" in response.data.lower()

def test_view_notepad_authorized(test_client):
    login(test_client, "test@example.com", "test1234")
    test_client.post("/notepad/create", data={"title": "Show OK", "body": "..."}, follow_redirects=True)
    with test_client.application.app_context():
        note = Notepad.query.filter_by(title="Show OK").first()
    response = test_client.get(f"/notepad/{note.id}")
    assert response.status_code == 200
    assert b"Show OK" in response.data
    logout(test_client)
    
def test_view_notepad_unauthorized(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200
    create_response = test_client.post(
        "/notepad/create",
        data={"title": "Privado", "body": "Solo test@example.com"},
        follow_redirects=True
    )
    assert create_response.status_code == 200
    with test_client.application.app_context():
        notepad = Notepad.query.filter_by(title="Privado").first()
        notepad_id = notepad.id

    logout(test_client)
    login_response = login(test_client, "hacker@example.com", "test1234")
    assert login_response.status_code == 200
    response = test_client.get(f"/notepad/{notepad_id}", follow_redirects=False)
    assert response.status_code == 302
    assert "/notepad" in response.headers["Location"]

#==================== CREATE ==========================================
def test_create_notepad(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    create_response = test_client.post(
        "/notepad/create",
        data={"title": "Test Notepad", "body": "Contenido de prueba"},
        follow_redirects=True
    )
    assert create_response.status_code == 200
    assert b"Notepad created successfully!" in create_response.data or b"Test Notepad" in create_response.data

def test_notepad_appears_in_list(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    test_client.post(
        "/notepad/create",
        data={"title": "Test Notepad", "body": "Contenido de prueba"},
        follow_redirects=True
    )

    response = test_client.get("/notepad", follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Notepad" in response.data

def test_create_notepad_invalid_form(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    create_response = test_client.post(
        "/notepad/create",
        data={"title": "", "body": "Contenido sin título"},
        follow_redirects=True
    )
    assert create_response.status_code == 200
    assert b"create" in create_response.data.lower() or b"title" in create_response.data.lower()

# ==================== UPDATE ==========================================
def test_edit_notepad(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    create_response = test_client.post(
        "/notepad/create",
        data={"title": "Original Title", "body": "Texto original"},
        follow_redirects=True
    )
    assert create_response.status_code == 200

    with test_client.application.app_context():
        notepad = Notepad.query.filter_by(title="Original Title").first()
        assert notepad is not None
        notepad_id = notepad.id

    edit_response = test_client.post(
        f"/notepad/edit/{notepad_id}",
        data={"title": "Updated Title", "body": "Texto actualizado"},
        follow_redirects=True
    )
    assert edit_response.status_code == 200
    assert b"Notepad updated successfully!" in edit_response.data or b"Updated Title" in edit_response.data

    response_after = test_client.get("/notepad", follow_redirects=True)
    assert b"Updated Title" in response_after.data

def test_edit_notepad_unauthorized(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200
    create_response = test_client.post(
        "/notepad/create",
        data={"title": "Edit Privado", "body": "Solo test@example.com"},
        follow_redirects=True
    )
    assert create_response.status_code == 200
    with test_client.application.app_context():
        notepad = Notepad.query.filter_by(title="Edit Privado").first()
        notepad_id = notepad.id

    logout(test_client)
    login_response = login(test_client, "hacker@example.com", "test1234")
    assert login_response.status_code == 200
    response = test_client.post(
        f"/notepad/edit/{notepad_id}",
        data={"title": "Hack", "body": "Intento hackear"},
        follow_redirects=False
    )
    assert response.status_code == 302
    assert "/notepad" in response.headers["Location"]

def test_edit_notepad_invalid_form(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200
    create_response = test_client.post(
        "/notepad/create",
        data={"title": "Edit Test", "body": "Texto original"},
        follow_redirects=True
    )
    assert create_response.status_code == 200
    with test_client.application.app_context():
        notepad = Notepad.query.filter_by(title="Edit Test").first()
        notepad_id = notepad.id

    edit_response = test_client.post(
        f"/notepad/edit/{notepad_id}",
        data={"title": "", "body": "Texto actualizado"},
        follow_redirects=True
    )
    assert edit_response.status_code == 200
    assert b"edit" in edit_response.data.lower() or b"title" in edit_response.data.lower()

# ==================== DELETE ==========================================
def test_delete_notepad(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    create_response = test_client.post(
        "/notepad/create",
        data={"title": "To Be Deleted", "body": "Texto a borrar"},
        follow_redirects=True
    )
    assert create_response.status_code == 200

    with test_client.application.app_context():
        notepad = Notepad.query.filter_by(title="To Be Deleted").first()
        assert notepad is not None
        notepad_id = notepad.id

    delete_response = test_client.post(
        f"/notepad/delete/{notepad_id}",
        follow_redirects=True
    )
    assert delete_response.status_code == 200

    response_after = test_client.get("/notepad", follow_redirects=True)
    assert b"To Be Deleted" not in response_after.data

def test_delete_notepad_unauthorized(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200
    create_response = test_client.post(
        "/notepad/create",
        data={"title": "Delete Privado", "body": "Solo test@example.com"},
        follow_redirects=True
    )
    assert create_response.status_code == 200
    with test_client.application.app_context():
        notepad = Notepad.query.filter_by(title="Delete Privado").first()
        notepad_id = notepad.id

    logout(test_client)
    login_response = login(test_client, "hacker@example.com", "test1234")
    assert login_response.status_code == 200
    response = test_client.post(
        f"/notepad/delete/{notepad_id}",
        follow_redirects=False
    )
    assert response.status_code == 302
    assert "/notepad" in response.headers["Location"]

def test_delete_notepad_error(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200
    response = test_client.post(
        "/notepad/delete/999999",  # ID que no existe
        follow_redirects=False
    )
    assert response.status_code == 404