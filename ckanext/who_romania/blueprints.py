import logging
from flask import Blueprint, request
from ckan.plugins import toolkit
from datetime import datetime

log = logging.getLogger(__name__)
lambda_blueprint = Blueprint(
    'lambda',
    __name__,
    url_prefix="/lambda/"
)


def view_logs(lambda_function):
    try:
        toolkit.check_access('lambda_invoke', {})
    except toolkit.NotAuthorized:
        toolkit.abort(403, toolkit._('Not authorized to perform this action'))
    try:
        logs = toolkit.get_action('lambda_logs')({}, {
            'lambda_function': lambda_function
        })['events']
    except Exception as e:
        logs = [
            {'message': f"[ERROR]\t{datetime.now()}\twrc\tERROR Failed to get logs"},
            {'message': f"[ERROR]\t{datetime.now()}\twrc\t{type(e).__name__}: {e}"}
        ]
    if logs == []:
        logs = [
            {'message': f"[INFO]\t{datetime.now()}\twrc\tNothing logged yet, please "
                        "reload the page"},
        ]
    extra_vars = {
        "logs": logs,
        "lambda_function": lambda_function
    }
    return toolkit.render(
        'who_romania/lambda_logs.html', extra_vars
    )


def family_medicine(dataset_id):
    try:
        toolkit.check_access('package_update', {}, {'id': dataset_id})
        toolkit.check_access('lambda_invoke', {})
    except toolkit.NotAuthorized:
        toolkit.abort(403, toolkit._('Not authorized to perform this action'))

    lambda_function = toolkit.config.get(
        'ckanext.who_romania.lambda_family_medicine_function',
        ''
    )
    if request.method == 'POST':
        reporting_template = toolkit.config.get(
            'ckanext.who_romania.lambda_family_medicine_template',
            ''
        )
        data_dict = {
            'dataset_id': dataset_id,
            'lambda_function': lambda_function,
            'reporting_template': reporting_template
        }
        try:
            toolkit.get_action('lambda_invoke')({}, data_dict)
            toolkit.h.flash_success(toolkit._(
                "Sucessfully triggered aggregation script. The script will take no "
                "more than 5 minutes to complete.  Follow the logs below..."
            ))
        except Exception as e:
            toolkit.h.flash_error(toolkit._(
                "Failed to trigger aggregation script. Please try again and if the "
                f"problem persists, contact a system administrator ({e}). "
            ))

    return toolkit.redirect_to('lambda.view_logs', lambda_function=lambda_function)


lambda_blueprint.add_url_rule(
    '/logs/<lambda_function>',
    view_func=view_logs
)

lambda_blueprint.add_url_rule(
    '/family-medicine/<dataset_id>',
    view_func=family_medicine,
    methods=['POST', 'GET']
)
