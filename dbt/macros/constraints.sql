{#- Physical keys so ERD tools (pgAdmin, DBeaver) draw the star schema.
    Constraint names are left to Postgres: dbt swaps tables by renaming, and auto-generated
    names avoid clashing with the old table's index until dbt drops it.
    Rebuilding a dimension alone drops its facts' foreign keys (dbt drops the old table
    with CASCADE); a full `dbt build` recreates them. -#}

{% macro primary_key(column) -%}
alter table {{ this }} add primary key ({{ column }})
{%- endmacro %}

{% macro foreign_keys(mapping) -%}
{%- for column, target in mapping.items() %}
alter table {{ this }} add foreign key ({{ column }}) references {{ ref(target[0]) }} ({{ target[1] }});
{%- endfor %}
{%- endmacro %}
