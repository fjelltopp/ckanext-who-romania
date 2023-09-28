import logging
import random
import re
import boto3
import json

import ckan.plugins.toolkit as toolkit
from ckan.plugins.toolkit import ValidationError, _


log = logging.getLogger(__name__)


@toolkit.side_effect_free
def user_show_me(context, resource_dict):
    """
    Returns the current user object.  Raises NotAuthorized error if no user
    object found.

    No input params.

    :rtype dictionary
    :returns The user object as a dictionary, which takes the following structure:
        ```
            {
                "id": "7f88caf3-e68b-4c96-883e-b49f3d547d84",
                "name": "fjelltopp_editor",
                "fullname": "Fjelltopp Editor",
                "email": "fjelltopp_editor@fjelltopp.org",
                "created": "2021-10-29 12:51:56.277305",
                "reset_key": null,
                "about": null,
                "activity_streams_email_notifications": false,
                "sysadmin": false,
                "state": "active",
                "image_url": null,
                "plugin_extras": null
            }
        ```

    """
    model = context['model']
    auth_user_obj = context.get('auth_user_obj', model.user.AnonymousUser())
    if isinstance(auth_user_obj, model.user.AnonymousUser):
        raise toolkit.NotAuthorized
    else:
        return auth_user_obj.as_dict()


def dataset_duplicate(context, data_dict):
    dataset_id_or_name = toolkit.get_or_bust(data_dict, 'id')
    dataset = toolkit.get_action('package_show')(context, {'id': dataset_id_or_name})
    dataset_id = dataset['id']

    dataset.pop('id', None)
    dataset.pop('name', None)
    data_dict.pop('id', None)
    context.pop('package', None)

    dataset = {**dataset, **data_dict}

    for resource in dataset.get('resources', []):
        del resource['id']
        del resource['package_id']

    duplicate_dataset = toolkit.get_action('package_create')(context, dataset)
    _record_dataset_duplication(dataset_id, duplicate_dataset['id'], context)

    return toolkit.get_action('package_show')(context, {'id': duplicate_dataset['id']})


@toolkit.chained_action
def package_create(next_action, context, data_dict):
    dataset_type = data_dict.get('type', '')

    valid_types = toolkit.get_action("scheming_dataset_schema_list")(context, {})
    if 'dataset' not in valid_types:
        valid_types.append("dataset")

    if dataset_type:
        if dataset_type not in valid_types:
            raise toolkit.ValidationError(f"Type '{dataset_type}' is invalid, valid types are: '{', '.join(valid_types)}'")

    return next_action(context, data_dict)


@toolkit.chained_action
def user_list(next_action, context, data_dict):
    try:
        user_from_id = toolkit.get_action('user_show')(
            context,
            {'id': data_dict.get('q', '')}
        )
        data_dict['q'] = user_from_id.get('name')
    except toolkit.ObjectNotFound:
        pass
    return next_action(context, data_dict)


def check_id_is_unique(context, data_dict):
    """
    Validate a new user id.

    The form of this validator is taken from the ckan core validator:
        user_name_validator
    """

    if 'id' in data_dict:
        new_user_id = data_dict['id']
        model = context['model']

        if not isinstance(new_user_id, str):
            raise ValidationError({'id': [_('User IDs must be strings')]})

        user = model.User.get(new_user_id)

        if user is not None:
            raise ValidationError(_('That user ID is not available.'))


def lambda_invoke(context, data_dict):
    toolkit.check_access('lambda_invoke', context, data_dict)
    lambda_function = toolkit.get_or_bust(data_dict, 'lambda_function')
    del data_dict['lambda_function']
    data_dict['ckan_user'] = context['user']
    data_dict['ckan_url'] = toolkit.config.get('ckanext.who_romania.lambda_ckan_url')
    try:
        client = boto3.client('lambda')
        return client.invoke(
            FunctionName=lambda_function,
            InvocationType='Event',
            LogType='None',
            ClientContext='string',
            Payload=json.dumps(data_dict)
        )
    except Exception as e:
        raise toolkit.ObjectNotFound(
            f"{e} Lambda function could not be found and invoked, are "
            f"you sure access permissions are correct? {data_dict}"
        )


def lambda_logs(context, data_dict):
    lambda_function = toolkit.get_or_bust(data_dict, 'lambda_function')
    log_group = f'/aws/lambda/{lambda_function}'
    try:
        client = boto3.client('logs')
        if not data_dict.get('log_stream_name'):
            log_stream_name = client.describe_log_streams(
                logGroupName=log_group,
                orderBy='LastEventTime',
                limit=1,
                descending=True
            )['logStreams'][0]['logStreamName']
        else:
            log_stream_name = data_dict['log_stream_name']
        return client.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream_name,
            startTime=1
        )
    except Exception as e:
        raise toolkit.ObjectNotFound(f"{e} Lambda logs could not be found, are you sure "
                                     f"AWS access permissions are correct? {data_dict}")


def dataset_tag_replace(context, data_dict):
    if 'tags' not in data_dict or not isinstance(data_dict['tags'], dict):
        raise toolkit.ValidationError(toolkit._(
            "Must specify 'tags' dict of tags for update in form "
            "{'old_tag_name1': 'new_tag_name1', 'old_tag_name2': 'new_tag_name2'}"))

    tags = data_dict.pop("tags")
    package_search_params = _restrict_datasets_to_those_with_tags(data_dict, tags)

    datasets = toolkit.get_action('package_search')(context, package_search_params).get('results', [])

    _check_user_access_to_all_datasets(context, datasets)
    _update_tags(context, datasets, tags)

    return {'datasets_modified': len(datasets)}


def _check_user_access_to_all_datasets(context, datasets):
    for ds in datasets:
        toolkit.check_access('package_patch', context, {"id": ds['id']})


def _restrict_datasets_to_those_with_tags(package_search_params, tags):
    fq_tag_restriction = " OR ".join([f"tags:{key}" for key in tags])

    if 'fq' in package_search_params:
        original_fq = package_search_params['fq']
        package_search_params['fq'] = f"({original_fq}) AND ({fq_tag_restriction})"
    else:
        package_search_params['fq'] = f"({fq_tag_restriction})"

    return package_search_params


def _update_tags(context, datasets, tags_to_be_replaced):
    dataset_patch_action = toolkit.get_action('package_patch')

    for ds in datasets:
        final_tags = _prepare_final_tag_list(ds['tags'], tags_to_be_replaced)
        dataset_patch_action(context, {'id': ds['id'], 'tags': final_tags})


def _prepare_final_tag_list(original_tags, tags_to_be_replaced):
    final_tags = []
    for tag in original_tags:
        tag_name = tag['name']
        final_tags.append({"name": tags_to_be_replaced[tag_name] if tag_name in tags_to_be_replaced else tag_name})

    return final_tags


def _record_dataset_duplication(dataset_id, new_dataset_id, context):
    # We should probably use activities to record duplication in CKAN 2.10

    relationship = {
        'subject': new_dataset_id,
        'object': dataset_id,
        'type': 'child_of'
    }

    try:
        current_activity_id = toolkit.get_action('package_activity_list')(
            context,
            {'id': dataset_id}
        )[0]['id']
        relationship['comment'] = f"Duplicated from activity {current_activity_id}"
    except Exception as e:
        log.error(f"Failed to get current activity for package {dataset_id} ...")
        log.exception(e)

    try:
        toolkit.get_action('package_relationship_create')(context, relationship)
    except Exception as e:
        log.error(f"Failed to record duplication of {dataset_id} to {new_dataset_id} ...")
        log.exception(e)


def _get_random_username_from_email(email, model):
    """
    This function is copied from a CKAN core private function:
        ckan.logic.action.create._get_random_username_from_email
    Github permalink:
        https://github.com/ckan/ckan/blob/0a596b8394dbf9582902853ad91450d2c0d7959b/ckan/logic/action/create.py#L1102-L1116

    The function has been deployed and used across a plethora of CKAN
    instances, which is why we are adopting it here.

    WARNING: This logic reveals part of the user's email address
    as their username.  Fjelltopp recommends overriding this logic
    for public CKAN instances.
    """

    localpart = email.split('@')[0]
    cleaned_localpart = re.sub(r'[^\w]', '-', localpart).lower()

    # if we can't create a unique user name within this many attempts
    # then something else is probably wrong and we should give up
    max_name_creation_attempts = 100

    for i in range(max_name_creation_attempts):
        random_number = random.SystemRandom().random() * 10000
        name = '%s-%d' % (cleaned_localpart, random_number)
        if not model.User.get(name):
            return name

    return cleaned_localpart
