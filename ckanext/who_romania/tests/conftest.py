import pytest


@pytest.fixture(scope='package')
def vcr_config():
    return {
        "filter_post_data_parameters": [
            ('assertion', 'DUMMY')
        ],
        "filter_headers": [
            ('authorization', 'DUMMY'),
            ('Authorization', 'DUMMY')
        ],
        "ignore_hosts": [
            "127.0.0.1",
            "0.0.0.0",
            "192.168.49.2",
            "solr"
        ]
    }
