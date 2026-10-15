{#- Use the layer schemas (staging, dq, dw, mart) as-is instead of dbt's "<target>_<custom>" naming. -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name else target.schema }}
{%- endmacro %}
