import pytest
import mock
from freezegun import freeze_time
import datetime
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
            call_action(
                'user_show_me',
                {}
            )

    def test_anonymous_user(self):
        with pytest.raises(toolkit.NotAuthorized):
            call_action(
                'user_show_me',
                {'auth_user_obj': model.user.AnonymousUser()}
            )

    def test_user(self):
        user = factories.User()
        user_obj = model.User.get(user['name'])
        response = call_action('user_show_me', {'auth_user_obj': user_obj})
        assert response['name'] == user['name']


@pytest.mark.ckan_config('ckan.plugins', 'who_romania')
@pytest.mark.usefixtures('clean_db', 'with_plugins')
@pytest.mark.vcr
@freeze_time(datetime.datetime(2023, 9, 26, 14, 20, 0))
class TestLambda(object):

    def test_lambda_logs_success(self):
        response = call_action(
            'lambda_logs', {},
            lambda_function='WRCLambda-FamilyMedicine-8lXLORrdBUsY'
        )
        assert 'events' in response

    def test_lambda_logs_fail(self):
        with pytest.raises(toolkit.ObjectNotFound):
            call_action(
                'lambda_logs', {},
                lambda_function='Bad-Name'
            )

    def test_lambda_invoke_success(self):
        response = call_action(
            'lambda_invoke', {'user': 'jberry'},
            lambda_function='WRCLambda-FamilyMedicine-8lXLORrdBUsY',
            reporting_template=("https://wrc.fjelltopp.org/dataset/"
                                "a460606e-625d-4edf-821e-058f29fff20a/resource/"
                                "6e451aa0-9105-458f-a065-663f7e4fbed0/download/6.xlsx"),
            dataset_id="family-medicine-demo"
        )
        assert response['StatusCode'] == 202

    def test_lambda_invoke_fail(self):
        with pytest.raises(toolkit.ObjectNotFound):
            call_action(
                'lambda_invoke', {'user': 'jberry'},
                lambda_function='BadName',
                reporting_template=("https://wrc.fjelltopp.org/dataset/"
                                    "a460606e-625d-4edf-821e-058f29fff20a/resource/"
                                    "6e451aa0-9105-458f-a065-663f7e4fbed0/download/6.xlsx"),
                dataset_id="family-medicine-demo"
            )
