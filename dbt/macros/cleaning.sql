{# RN-13: espacios no separables y repetidos fuera; mayúsculas intactas (etl.normalize_text). #}
{% macro normalize_text(column) -%}
    trim(regexp_replace(replace({{ column }}, chr(160), ' '), '\s+', ' ', 'g'))
{%- endmacro %}

{# RN-01: texto con coma decimal a número; lo ilegible queda NULL (etl.convert_decimal_text). #}
{% macro decimal_text(column) -%}
    try_cast(replace({{ column }}, ',', '.') as double)
{%- endmacro %}
