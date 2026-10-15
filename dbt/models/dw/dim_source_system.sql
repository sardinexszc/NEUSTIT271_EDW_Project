-- Lineage: one row per load batch (source file). Every fact row points to the batch it came from.

select
    batch_id::int     as source_key,
    source_system,
    source_file,
    started_at        as loaded_at,
    row_count
from {{ source('meta', 'load_batch') }}
where status = 'succeeded'
