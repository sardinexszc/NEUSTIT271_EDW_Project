<?php
// GET api/export.php[?event=TC2024-KRISTINE]
//
// The data marts as one formatted Excel workbook, generated live from the warehouse by
// ingestion/export_xlsx.py: one sheet per mart, an About sheet and a data dictionary.

declare(strict_types=1);
require __DIR__ . '/_bootstrap.php';

require_get();
set_time_limit(120);

$event = $_GET['event'] ?? null;
if ($event !== null && !preg_match('/^TC\d{4}-[A-Z]+$/', $event)) {
    fail(400, 'event must look like TC2024-KRISTINE.');
}
$args = ['ingestion/export_xlsx.py', '--out', '-'];
if ($event !== null) {
    $args[] = '--event';
    $args[] = $event;
}
[$code, $workbook] = run_tool($args, 100);
if ($code !== 0 || substr($workbook, 0, 2) !== 'PK') {   // an .xlsx is a zip file
    fail($code === 1 && $event !== null ? 404 : 500, 'The workbook could not be created.');
}
$filename = 'driw-data' . ($event !== null ? '-' . strtolower($event) : '') . '-' . date('Ymd') . '.xlsx';
header('Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
header('Content-Disposition: attachment; filename="' . $filename . '"');
header('Content-Length: ' . strlen($workbook));
header('Cache-Control: no-store');
echo $workbook;
