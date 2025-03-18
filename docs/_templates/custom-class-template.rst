.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

..
    Credit to https://github.com/JamesALeedham/Sphinx-Autosummary-Recursion for the custom templates.
..
{{ fullname | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}
   :members:
   :show-inheritance:
   :inherited-members: BaseModel
   :exclude-members: model_computed_fields, model_config, model_fields
   :special-members: __init__, __call__, __add__, __mul__

   {% block methods %}
   {% if methods %}
   .. rubric:: {{ _('Methods') }}

   .. autosummary::
      :nosignatures:
   {% for item in methods %}
      {%- if not item.startswith('_') and item not in [
         'construct', 'copy', 'dict', 'from_orm', 'json', 'model_construct',
         'model_copy', 'model_dump', 'model_dump_json', 'model_json_schema',
         'model_parametrized_name', 'model_post_init', 'model_rebuild', '',
         'model_validate', 'model_validate_json', 'model_validate_strings',
         'parse_file', 'parse_obj', 'parse_raw', 'schema', 'schema_json',
         'update_forward_refs', 'validate',
      ] %}
      ~{{ name }}.{{ item }}
      {%- endif -%}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes %}
   .. rubric:: {{ _('Attributes') }}

   .. autosummary::
   {% for item in attributes %}
      {%- if not item.startswith('_') and item not in [
         'model_computed_fields', 'model_config', 'model_extra', 'model_fields',
         'model_fields_set',
      ] %}
      ~{{ name }}.{{ item }}
      {%- endif -%}
   {%- endfor %}
   {% endif %}
   {% endblock %}
