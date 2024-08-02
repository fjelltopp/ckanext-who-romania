import logging
from collections import OrderedDict

import ckanext.blob_storage.helpers as blobstorage_helpers

import ckan.lib.uploader as uploader
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.who_romania.actions as who_romania_actions
import ckanext.who_romania.authn as who_romania_authn
import ckanext.who_romania.upload as who_romania_upload
import ckanext.who_romania.validators as who_romania_validators
import ckanext.who_romania.helpers as who_romania_helpers
import ckanext.who_romania.blueprints as who_romania_blueprints
import ckanext.who_romania.auth as who_romania_auth
from ckan.lib.plugins import DefaultPermissionLabels

from ckan.common import config_declaration

log = logging.getLogger(__name__)


class WHORomaniaPlugin(plugins.SingletonPlugin, DefaultPermissionLabels):

    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigDeclaration)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IAuthenticator, inherit=True)
    plugins.implements(plugins.IMiddleware, inherit = True)

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'max_resource_size': uploader.get_max_resource_size,
            'get_dataset_from_id': who_romania_helpers.get_dataset_from_id,
            'blob_storage_resource_filename': blobstorage_helpers.resource_filename,
            'get_facet_items_dict': who_romania_helpers.get_facet_items_dict,
            'get_all_groups': who_romania_helpers.get_all_groups,
            'get_featured_datasets': who_romania_helpers.get_featured_datasets,
            'get_user_from_id': who_romania_helpers.get_user_from_id,
            'get_user_obj': who_romania_helpers.get_user_obj,
            'month_formatter': who_romania_helpers.month_formatter,
            'get_dates_of_weekday_in_month': who_romania_helpers.get_dates_of_weekday_in_month,
            'get_week_options': who_romania_helpers.get_week_options
        }

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "who-romania")

    # IConfigurable
    def configure(self, config):
        """
        Temporary fix to CKAN Github issue 7593.
        https://github.com/ckan/ckan/issues/7593
        This should be removed when the issue is resolved.
        """
        config_declaration.normalize(config)

    # IConfigDeclaration
    def declare_config_options(self, declaration, key):
        declaration.annotate("who_romania extension configuration")
        group = key.ckanext.who_romania
        declaration.declare(
            group.lambda_ckan_url,
            "https://wrc.fjelltopp.org"
        ).set_description("CKAN url for lambda functions to act upon")
        declaration.declare(
            group.lambda_family_medicine_function,
            ""
        ).set_description("The family medicine lambda function name")
        declaration.declare(
            group.lambda_family_medicine_template,
            ""
        ).set_description("The family medicine data reporting template")
        declaration.declare(
            group.lambda_invoke_users,
            ""
        ).set_description("Users (other than sysadmins) with permission to invoke")

    # IBlueprint
    def get_blueprint(self):
        return [
            who_romania_blueprints.lambda_blueprint
        ]

    # IFacets
    def dataset_facets(self, facet_dict, package_type):
        new_fd = OrderedDict()
        new_fd['program_area'] = plugins.toolkit._('Program Areas')
        new_fd['year'] = plugins.toolkit._('Years')
        new_fd['tags'] = plugins.toolkit._('Tags')
        return new_fd

    # IResourceController
    def before_resource_create(self, context, resource):
        who_romania_upload.handle_giftless_uploads(context, resource)
        return resource

    def before_resource_update(self, context, current, resource):
        who_romania_upload.handle_giftless_uploads(context, resource, current=current)
        return resource

    # IActions
    def get_actions(self):
        return {
            'user_list': who_romania_actions.user_list,
            'dataset_duplicate': who_romania_actions.dataset_duplicate,
            'package_create': who_romania_actions.package_create,
            'dataset_tag_replace': who_romania_actions.dataset_tag_replace,
            'user_show_me': who_romania_actions.user_show_me,
            'lambda_invoke': who_romania_actions.lambda_invoke,
            'lambda_logs': who_romania_actions.lambda_logs
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {"lambda_invoke": who_romania_auth.lambda_invoke}

    # IValidators
    def get_validators(self):
        return {
            'autogenerate_name_from_title': who_romania_validators.autogenerate_name_from_title,
            'autofill': who_romania_validators.autofill,
            'autogenerate': who_romania_validators.autogenerate,
            'isomonth': who_romania_validators.isomonth
        }

    # IPackageContoller
    def after_dataset_delete(self, context, data_dict):
        package_data = toolkit.get_action('package_show')(context, data_dict)
        if package_data.get('private'):
            package_data['state'] = 'deleted'
            context['package'].state = 'deleted'
            who_romania_upload.add_activity(context, package_data, "changed")

    def after_dataset_update(self, context, data_dict):
        if data_dict.get('private'):
            who_romania_upload.add_activity(context, data_dict, "changed")

    def after_dataset_create(self, context, data_dict):
        if data_dict.get('private'):
            who_romania_upload.add_activity(context, data_dict, "new")

    def make_middleware(self, app, config):
        @app.after_request
        def apply_owasp(response):
            response.headers['Strict-Transport-Security'] = "max-age=31536000; preload"
            response.headers['X-Content-Type-Options'] = "nosniff"
            response.headers["X-Permitted-Cross-Domain-Policies"] = "none" #not sure about this one
            response.headers["Referrer-Policy"] = "no-referrer-when-downgrade" #this is default when not set
            response.headers["Cache-Control"] = "public, max-age=0, s-maxage=43200"
            response.headers["HTTP Cross-Origin-Opener-Policy"] = "same-origin"
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
            response.headers["Cross-Origin-Resource-Policy"] = "same-site"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' https:;"
                "style-src 'self' 'unsafe-inline' https:;"
            )



            if '/view/' not in toolkit.request.path:
                response.headers['X-Frame-Options'] = 'SAMEORIGIN'

            if ("Location" in response.headers) and ('logged_out_redirect' in response.headers['Location']):
                response.headers["Clear-Site-Data"] = "\"*\""
            return response

        return app

    # IAuthenticator
    def identify(self):
        """
        Allows API requests to be sent "on behalf" of a substitute user. This is
        done by setting a HTTP Header in the requests "CKAN-Substitute-User" to be the
        username or user id of another CKAN user.
        """

        substitute_user_id = toolkit.request.headers.get('CKAN-Substitute-User')

        user_is_sysadmin = getattr(toolkit.current_user, 'sysadmin', False)
        if substitute_user_id:
            if not user_is_sysadmin:
                return {
                    "success": False,
                    "error": {
                        "__type": "Not Authorized",
                        "message": "Must be a system administrator."
                    }
                }, 403

            return who_romania_authn.substitute_user(substitute_user_id)
