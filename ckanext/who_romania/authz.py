import ckan.authz as authz
import ckan.logic.auth as logic_auth
import ckan.plugins.toolkit as toolkit


@toolkit.chained_auth_function
def creators_manage_collaborators(next_auth, context, data_dict):
    """
    Explicitly ensures that dataset creators can always edit collaborators.
    """
    user = context['user']
    model = context['model']

    package = model.Package.get(data_dict['id'])
    user_obj = model.User.get(user)

    if package.creator_user_id == user_obj.id:
        return {'success': True}

    else:
        return next_auth(context, data_dict)

