<?php
// GET api/health.php: is the warehouse reachable, and as which (least-privilege) role?

declare(strict_types=1);
require __DIR__ . '/_bootstrap.php';

require_get();

try {
    $row = db()->query(
        "select current_database(), current_user, current_setting('server_version'), now()"
    )->fetch();
    send_json([
        'status' => 'ok',
        'database' => $row[0],
        'role' => $row[1],
        'postgres' => $row[2],
        'checked_at' => $row[3],
    ]);
} catch (PDOException $e) {
    error_log('DRIW API: health check failed: ' . $e->getMessage());
    fail(503, 'Warehouse database is unavailable.');
}
