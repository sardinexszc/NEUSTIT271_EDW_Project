{#- Matching key for place names: case, spacing, accents, "City of"/"City", Sto./Sta., punctuation. -#}
{% macro norm_name(col) -%}
trim(regexp_replace(regexp_replace(regexp_replace(regexp_replace(regexp_replace(regexp_replace(
    regexp_replace(translate(lower(trim({{ col }})), 'ñ', 'n'),
    '\(.*?\)', '', 'g'),
    '^city of ', ''),
    ' city$', ''),
    '^sto\.? ', 'santo '),
    '^sta\.? ', 'santa '),
    '[^a-z0-9 ]', '', 'g'),
    '\s+', ' ', 'g'))
{%- endmacro %}

{#- Letters and digits only: makes typos that move a space ("Cityo f Legazpi") comparable. -#}
{% macro loose_key(col) -%}
regexp_replace(translate(lower({{ col }}), 'ñ', 'n'), '[^a-z0-9]', '', 'g')
{%- endmacro %}

{#- Text -> numeric. Missing-value tokens become null; thousands separators are removed. -#}
{% macro clean_number(col) -%}
case
    when replace(trim({{ col }}), ',', '') ~ '^-?[0-9]+(\.[0-9]+)?$'
        then replace(trim({{ col }}), ',', '')::numeric
end
{%- endmacro %}

{#- Date written in any of the formats DSWD field offices use. -#}
{% macro date_format_of(col) -%}
case
    when {{ col }} ~ '^\d{4}-\d{2}-\d{2}$' then 'iso'
    when {{ col }} ~ '^\d{1,2}/\d{1,2}/\d{4}$' then 'us'
    when {{ col }} ~ '^\d{1,2}-[A-Za-z]{3}-\d{4}$' then 'dmy'
    when {{ col }} ~ '^\d{5}$' then 'excel'
end
{%- endmacro %}

{% macro parse_any_date(col) -%}
case {{ date_format_of(col) }}
    when 'iso' then to_date({{ col }}, 'YYYY-MM-DD')
    when 'us' then to_date({{ col }}, 'MM/DD/YYYY')
    when 'dmy' then to_date({{ col }}, 'DD-Mon-YYYY')
    when 'excel' then date '1899-12-30' + {{ col }}::int
end
{%- endmacro %}

{#- Overall row status from its issue codes ("RULE" or "RULE:field"). -#}
{% macro dq_status(issues, reject_rules, warning_rules) -%}
case
    when exists (select 1 from unnest({{ issues }}) i
                 where split_part(i, ':', 1) in ('{{ reject_rules | join("', '") }}')) then 'rejected'
    when exists (select 1 from unnest({{ issues }}) i
                 where split_part(i, ':', 1) in ('{{ warning_rules | join("', '") }}')) then 'warning'
    else 'valid'
end
{%- endmacro %}

{#- Lateral join that resolves a free-text event reference within the event's time window. -#}
{% macro event_lookup(ref_expr, date_expr, alias) -%}
left join lateral (
    select a.event_key
    from {{ ref('stg_event_alias') }} a
    where a.alias = lower(trim({{ ref_expr }}))
      and {{ date_expr }} between a.start_date - 3 and a.end_date + 90
    order by a.start_date desc
    limit 1
) {{ alias }} on true
{%- endmacro %}
