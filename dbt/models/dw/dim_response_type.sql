select * from (values
    (1, 'RESCUE',       'Search and rescue',     'Life-saving'),
    (2, 'MEDEVAC',      'Medical evacuation',    'Life-saving'),
    (3, 'EVAC_ASSIST',  'Evacuation assistance', 'Life-saving'),
    (4, 'ROAD_CLEAR',   'Road clearing',         'Access and infrastructure'),
    (5, 'RELIEF_DELIV', 'Relief delivery',       'Logistics')
) as t(response_type_key, response_type_code, response_type_name, response_cluster)
