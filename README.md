[![Tests](https://github.com/fjelltopp/ckanext-who-romania/workflows/Tests/badge.svg?branch=master)](https://github.com/fjelltopp/ckanext-who-romania/actions)

# ckanext-who-romania

Provides tailored styling and features for CKAN, according to WHO Romania's requirements for their country office data library.


## Key features

The following key features are provided by this extension:

- Tailored UI styling, according to the WHO Romania branding.
- Integration with Giftless and CKAN extensions ckanext-blob-storage, ckanext-authz-service and ckanext-versions for revisioning and release management
- Template changes to streamline the UI to WHO Romania's needs.


## Configuration

To be written


## Installation

To install ckanext-who-romania:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/fjelltopp/ckanext-who-romania.git
    cd ckanext-who-romania
    pip install -e .
	pip install -r requirements.txt

3. Add `who_romania` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload


## Developer installation

To install ckanext-who-romania for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/fjelltopp/ckanext-who-romania.git
    cd ckanext-who-romania
    python setup.py develop
    pip install -r dev-requirements.txt


## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini


## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
