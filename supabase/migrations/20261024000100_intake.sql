-- Data exchange: files submitted by LGUs and agencies load alongside the synthetic extracts.
-- `origin` tells them apart, so checks that only make sense for the synthetic data (planted-defect
-- reconciliation, ground-truth matching accuracy) can be limited to synthetic batches.
alter table meta.load_batch
    add column if not exists origin text not null default 'synthetic'
    check (origin in ('synthetic', 'intake'));
