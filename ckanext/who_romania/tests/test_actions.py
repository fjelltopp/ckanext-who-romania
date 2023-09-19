import pytest
import ckan.tests.factories as factories
from ckan.tests.helpers import call_action
import ckan.plugins.toolkit as toolkit
from ckan import model


@pytest.mark.ckan_config('ckan.plugins', "who_romania")
@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestListUsers():

    def test_empty_query(self):
        users = [factories.User(name=f"{i}01dec4a-6cc9-49cd-91ea-cc0e09ba620d") for i in range(3)]
        response = call_action(
            'user_list',
            q=''
        )
        user_ids_created = {u['id'] for u in users}
        user_ids_found = {u['id'] for u in response}
        assert user_ids_created == user_ids_found

    def test_search_by_id(self):
        users = [factories.User(name=f"{i}01dec4a-6cc9-49cd-91ea-cc0e09ba620d") for i in range(3)]
        response = call_action(
            'user_list',
            q=users[1]['id']
        )
        user_ids_found = [u['id'] for u in response]
        assert user_ids_found == [users[1]['id']]

    def test_search_by_non_id(self):
        users = [factories.User(name=f"{i}01dec4a-6cc9-49cd-91ea-cc0e09ba620d") for i in range(3)]
        response = call_action(
            'user_list',
            q=users[2]['name']
        )
        user_ids_found = [u['id'] for u in response]
        assert user_ids_found == [users[2]['id']]


@pytest.mark.ckan_config('ckan.plugins', 'who_romania')
@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestUserShowMe(object):

    def test_no_user(self):
        with pytest.raises(toolkit.NotAuthorized):
            call_action('user_show_me', {})

    def test_user(self):
        user = factories.User()
        user_obj = model.User.get(user['name'])
        response = call_action('user_show_me', {'auth_user_obj': user_obj})
        assert response['name'] == user['name']
