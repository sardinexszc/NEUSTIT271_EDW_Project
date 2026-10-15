{#- SCD Type 2 lookup: the dim_location version in force on the fact's date. -#}
{% macro location_as_of(psgc_expr, date_expr, alias='loc') -%}
join {{ ref('dim_location') }} {{ alias }}
    on {{ alias }}.psgc_code = {{ psgc_expr }}
   and {{ date_expr }} between {{ alias }}.valid_from and {{ alias }}.valid_to
{%- endmacro %}

{#- Date -> dim_date key; null (not yet happened) -> the -1 member. -#}
{% macro date_key(date_expr) -%}
coalesce(to_char({{ date_expr }}, 'YYYYMMDD')::int, -1)
{%- endmacro %}
