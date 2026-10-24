-- Lifelines tracked in NDRRMC sitreps (critical infrastructure and basic services).
select * from (values
    (1, 'ROAD',   'Road sections not passable',         'Transport', 'road sections'),
    (2, 'BRIDGE', 'Bridges not passable',               'Transport', 'bridges'),
    (3, 'POWER',  'Power interruption',                 'Utilities', 'barangays'),
    (4, 'WATER',  'Water supply interruption',          'Utilities', 'barangays'),
    (5, 'COMMS',  'Communication lines down',           'Utilities', 'barangays')
) as t(lifeline_key, lifeline_code, lifeline_name, lifeline_sector, unit_of_measure)
