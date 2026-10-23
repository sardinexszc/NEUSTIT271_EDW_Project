<?php
// POST api/intake.php   (multipart form)
//   action  = validate | submit
//   type    = dromic | ndrrmc | lgu | pagasa | ngo
//   profile = standard | <layout profile id>
//   file    = the report (.xlsx or .csv, up to 10 MB)
//
// Validate checks every row against the warehouse's data-quality rules in a sandbox and returns
// a per-row report (JSON). Submit does the same, saves the rows in the standard layout under
// data/intake/ and reloads the warehouse. The work is done by ingestion/intake.py.
//
// Uploads are accepted from this computer only (config 'intake_allow_remote'), until the site
// has sign-in: an open upload form must not be reachable from the network.

declare(strict_types=1);
require __DIR__ . '/_bootstrap.php';

const REPORT_TYPES = ['dromic', 'ndrrmc', 'lgu', 'pagasa', 'ngo'];
const ACTIONS = ['validate', 'submit'];
const MAX_BYTES = 10 * 1024 * 1024;

set_time_limit(300);   // a submit reloads the warehouse (about half a minute)
$c = config();
$client = $_SERVER['REMOTE_ADDR'] ?? '';
if (empty($c['intake_allow_remote']) && !in_array($client, ['127.0.0.1', '::1'], true)) {
    fail(403, 'Uploads are accepted on the DRIW server itself only.');
}
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    fail(405, 'Use POST with a file.');
}

$action = $_POST['action'] ?? 'validate';
$type = $_POST['type'] ?? '';
$profile = $_POST['profile'] ?? 'standard';
if (!in_array($action, ACTIONS, true)) {
    fail(400, 'action must be validate or submit.');
}
if (!in_array($type, REPORT_TYPES, true)) {
    fail(400, 'Unknown report type.');
}
if (!preg_match('/^[a-z0-9-]{1,64}$/', $profile)) {
    fail(400, 'Unknown layout.');
}

$file = $_FILES['file'] ?? null;
if (!is_array($file) || ($file['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_OK) {
    fail(400, 'Choose a file to upload.');
}
if ($file['size'] > MAX_BYTES) {
    fail(413, 'The file is larger than 10 MB.');
}
$extension = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
if (!in_array($extension, ['xlsx', 'csv'], true)) {
    fail(415, 'Upload an Excel workbook (.xlsx) or a CSV file.');
}
// the original name is only shown back and used for the stored file's name; keep it plain
$name = preg_replace('/[^A-Za-z0-9 ._()-]+/', '_', basename($file['name']));
$name = substr($name, 0, 120);

$uploads = dirname(__DIR__, 3) . '/driw-config/uploads';   // outside htdocs: never served
if (!is_dir($uploads)) {
    mkdir($uploads, 0700, true);
}
$stored = $uploads . '/' . bin2hex(random_bytes(12)) . '.' . $extension;
if (!move_uploaded_file($file['tmp_name'], $stored)) {
    fail(500, 'The upload could not be saved.');
}

try {
    [$code, $out] = run_tool(['ingestion/intake.py', $action, '--type', $type, '--profile', $profile,
                              '--file', $stored, '--name', $name], 280);
} finally {
    @unlink($stored);
}
$report = json_decode($out, true);
if (!is_array($report)) {
    error_log("DRIW intake: tool exited $code without a report");
    fail(500, 'The check could not run. The administrator can see the reason in driw-config/logs.');
}
send_json($report, $report['ok'] ? 200 : 422);
