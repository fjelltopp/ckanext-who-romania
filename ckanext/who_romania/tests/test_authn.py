import pytest
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestSubstituteUser():

    def test_error_raised_for_non_sysadmin_user(self, app):
        user = factories.UserWithToken()
        response = app.get(
            toolkit.url_for('api.action', ver=3, logic_function='package_list'),
            headers={
                'Authorization': user['token'],
                'CKAN-Substitute-User': 'fjelltopp_editor'
            }
        )
        assert response.status_code == 403

    def test_error_raised_for_invalid_substitute_user(self, app):
        user = factories.UserWithToken(sysadmin=True)
        response = app.get(
            toolkit.url_for('api.action', ver=3, logic_function='package_list'),
            headers={
                'Authorization': user['token'],
                'CKAN-Substitute-User': 'non_existant_user'
            }
        )
        assert response.status_code == 400
        assert response.json == {
            "success": False,
            "error": {
                "__type": "Bad Request",
                "message": "CKAN-Substitute-User header does "
                           "not identify a valid CKAN user"
            }
        }

    @pytest.mark.parametrize("user_field", ["id", "name"])
    def test_valid_substitute_user_request(self, app, user_field):
        sysadmin_user = factories.UserWithToken(sysadmin=True)
        substitute_user = factories.User()
        dataset = factories.Dataset()
        dataset_create_url = toolkit.url_for(
            'api.action',
            ver=3,
            logic_function='package_create',
            id=dataset['id']
        )
        response = app.post(
            dataset_create_url,
            json={'name': 'test-dataset'},
            headers={
                'Authorization': sysadmin_user['token'],
                'CKAN-Substitute-User': substitute_user[user_field]
            }
        )
        assert response.status_code == 200
        assert response.json['result']['creator_user_id'] == substitute_user['id']
