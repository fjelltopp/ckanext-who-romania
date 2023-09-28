from ckan.plugins import toolkit


def lambda_invoke(context, data_dict):
    authorized_users = toolkit.config.get('ckanext.who_romania.lambda_invoke_users', " ")
    authorized_users = authorized_users.split(" ")
    if context['user'] in authorized_users:
        return {'success': True}
    else:
        return {
            'success': False,
            'msg': 'You are not authorized to carry out this action'
        }
