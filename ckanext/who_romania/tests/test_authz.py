import pytest

from ckan.plugins import toolkit
from ckan.tests import factories
from ckan.tests.helpers import call_auth, call_action
from ckanext.who_romania.tests import get_context


@pytest.fixture
def users():
    return [
        factories.User(),
        factories.User()
    ]


@pytest.fixture(params=["editor", "admin"])
def organisation(request, users):

    return factories.Organization(
        users=[
            {'name': users[0]['name'], 'capacity': request.param},
            {'name': users[1]['name'], 'capacity': request.param}
        ]
    )


@pytest.fixture
def datasets(organisation, users):
    return [
        factories.Dataset(
            owner_org=organisation['id'],
            private=True,
            user=users[0]
        ),
        factories.Dataset(
            owner_org=organisation['id'],
            private=True,
            user=users[1]
        ),
        factories.Dataset(
            owner_org=organisation['id'],
            private=False,
            user=users[1]
        )
    ]


@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestAuth():

    def test_users_cant_see_private_datasets(self, users, datasets):
        with pytest.raises(toolkit.NotAuthorized):
            call_auth(
                'package_show',
                get_context(users[0]),
                id=datasets[1]['id']
            )

    def test_users_cant_edit_private_datasets(self, users, datasets):
        with pytest.raises(toolkit.NotAuthorized):
            call_auth(
                'package_update',
                get_context(users[0]),
                id=datasets[1]['id']
            )

    def test_users_can_edit_own_datasets(self, users, datasets):
        assert call_auth(
            'package_update',
            get_context(users[0]),
            id=datasets[0]['id']
        )

    def test_users_can_see_own_datasets(self, users, datasets):
        assert call_auth(
            'package_show',
            get_context(users[0]),
            id=datasets[0]['id']
        )

    def test_collaborators_can_see_datasets(self, users, datasets):
        call_action(
            'package_collaborator_create',
            id=datasets[0]['id'],
            user_id=users[1]['id'],
            capacity='member'
        )
        assert call_auth(
            'package_show',
            get_context(users[1]),
            id=datasets[0]['id'],
        )

    def test_collaborators_can_edit_datasets(self, users, datasets):
        call_action(
            'package_collaborator_create',
            id=datasets[0]['id'],
            user_id=users[1]['id'],
            capacity='editor'
        )
        assert call_auth(
            'package_update',
            get_context(users[1]),
            id=datasets[0]['id'],
        )

    def test_users_can_see_public_datasets(self, users, datasets):
        assert call_auth(
            'package_show',
            get_context(users[0]),
            id=datasets[2]['id'],
        )

    def test_users_cant_edit_public_datasets(self, users, datasets):
        with pytest.raises(toolkit.NotAuthorized):
            call_auth(
                'package_update',
                get_context(users[0]),
                id=datasets[2]['id']
            )

    def test_creator_can_list_collaborators(self, users, datasets):
        assert call_auth(
            'package_collaborator_list',
            get_context(users[0]),
            id=datasets[0]['id']
        )

    def test_creator_can_add_collaborators(self, users, datasets):
        assert call_auth(
            'package_collaborator_create',
            get_context(users[0]),
            id=datasets[0]['id'],
            user_id=users[1]['id'],
            capacity='editor'
        )

    def test_creator_can_delete_collaborators(self, users, datasets):
        call_action(
            'package_collaborator_create',
            id=datasets[0]['id'],
            user_id=users[1]['id'],
            capacity='editor'
        )
        assert call_auth(
            'package_collaborator_delete',
            get_context(users[0]),
            id=datasets[0]['id'],
            user_id=users[1]['id']
        )
