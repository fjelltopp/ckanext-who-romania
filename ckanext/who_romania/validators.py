from ckanext.scheming.validation import scheming_validator
from ckanext.who_romania.helpers import (
    comma_swap_formatter,
    lower_formatter,
    month_formatter
)
from ckan.logic.validators import package_name_validator
from ckan.plugins.toolkit import ValidationError, _
from string import ascii_lowercase
from random import choice
import copy
import slugify


@scheming_validator
def autogenerate_name_from_title(field, schema):

    def validator(key, data, errors, context):

        # Preserve the name when editing an existing package
        if context.get('package'):
            data[key] = context['package'].name
            return

        # Use the exact name given by the user if it exists
        if data[key]:
            return

        if not data[('title',)]:
            raise ValidationError({'title': ['Missing value']})

        title_slug = slugify.slugify(data[('title',)])
        data[key] = title_slug

        # Multiple attempts so alpha_id can be as short as possible
        for counter in range(10):
            package_name_errors = copy.deepcopy(errors)
            package_name_validator(key, data, package_name_errors, context)
            dataset_name_valid = package_name_errors[key] == errors[key]

            if dataset_name_valid:
                break

            alpha_id = ''.join(choice(ascii_lowercase) for i in range(3))
            new_dataset_name = "{}-{}".format(title_slug, alpha_id)
            data[key] = new_dataset_name
        else:
            raise ValidationError({'name': [_('Could not autogenerate a unique name.')]})

    return validator


@scheming_validator
def autogenerate(field, schema):
    template = field[u'template']
    template_args = field[u'template_args']
    template_formatters = field.get(u'template_formatters', dict())
    formatters = {
        "lower": lower_formatter,
        "slugify": slugify.slugify,
        "comma_swap": comma_swap_formatter,
        "month_formatter": month_formatter
    }
    f_list = []
    for f in template_formatters:
        if f in formatters.keys():
            f_list.append(formatters[f])

    def validator(key, data, errors, context):
        str_args = []
        key_base = key[:-1]  # Needed for resource editing
        for t_arg in template_args:
            arg_value = data[(*key_base, t_arg)]
            for f in f_list:
                arg_value = f(arg_value)
            str_args.append(arg_value)
        auto_text = template.format(*str_args)
        data[key] = auto_text
        pass

    return validator


@scheming_validator
def autofill(field, schema):
    field_value = field.get(u'field_value', field.get('default', ''))

    def validator(key, data, errors, context):
        if not data.get(key):
            data[key] = field_value

    return validator


@scheming_validator
def isomonth(field, schema):
    def validator(key, data, errors, context):
        if data.get(key):
            try:
                month_formatter(data[key])
            except ValueError:
                raise ValidationError({'name': [_('Month should be of the form yyyy-mm')]})
    return validator
