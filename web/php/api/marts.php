<?php
// GET api/marts.php?name=mart_event_summary[&event=TC2024-KRISTINE]
//
// Returns one data mart as a JSON array, in the same column types and row order as the
// static snapshot (ingestion/export_marts.py), so the dashboards can use either.

declare(strict_types=1);
require __DIR__ . '/_bootstrap.php';

require_get();

// Allow-list: the name is never interpolated unless it is one of these.
const MARTS = [
    'mart_event_summary' => true,           // value: has an event_code column
    'mart_impact_cube' => false,
    'mart_province_event_impact' => true,
    'mart_evacuation_daily' => true,
    'mart_response_performance' => true,
    'mart_relief_by_org_category' => true,
    'mart_displacement_daily' => true,
    'mart_lifeline_restoration' => true,
];

$name = $_GET['name'] ?? '';
if (!array_key_exists($name, MARTS)) {
    fail(400, 'Unknown mart. Use one of: ' . implode(', ', array_keys(MARTS)));
}

$event = $_GET['event'] ?? null;
if ($event !== null) {
    if (!MARTS[$name]) {
        fail(400, "$name has no event_code column.");
    }
    if (!preg_match('/^TC\d{4}-[A-Z]+$/', $event)) {
        fail(400, 'event must look like TC2024-KRISTINE.');
    }
}

$pdo = db();
try {
    // order by every column, exactly as the snapshot export does
    $columnCount = $pdo->query("select * from mart.$name limit 0")->columnCount();
    $orderBy = implode(', ', range(1, $columnCount));
    $sql = "select * from mart.$name" . ($event !== null ? ' where event_code = :event' : '') . " order by $orderBy";
    $stmt = $pdo->prepare($sql);
    $stmt->execute($event !== null ? ['event' => $event] : []);
    send_json(fetch_typed($stmt));
} catch (PDOException $e) {
    error_log("DRIW API: query on $name failed: " . $e->getMessage());
    fail(500, 'Query failed.');
}
