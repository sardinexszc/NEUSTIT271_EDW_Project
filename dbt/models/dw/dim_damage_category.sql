select * from (values
    (1, 'Population',     'Casualties and affected population',              false),
    (2, 'Housing',        'Partially and totally damaged houses',            true),
    (3, 'Infrastructure', 'Roads, bridges, public buildings and utilities',  true),
    (4, 'Agriculture',    'Crops, livestock, fisheries and facilities',      true)
) as t(damage_category_key, damage_category, description, has_cost)
