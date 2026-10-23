<?php
// Shared helpers for the DRIW API. Not reachable over HTTP (see .htaccess).
//
// Connects to the PostgreSQL warehouse as `driw_web`, a member of driw_executive only:
// it can read the mart schema and nothing else, so even a bug here cannot expose detail.

declare(strict_types=1);

function config(): array
{
    // C:\xampp\htdocs\driw\api -> C:\xampp\driw-config\config.php (outside the web root)
    $path = getenv('DRIW_CONFIG') ?: dirname(__DIR__, 3) . '/driw-config/config.php';
    if (!is_file($path)) {
        fail(500, 'Server is not configured. Run ingestion/setup_web_role.py.');
    }
    return require $path;
}

function db(): PDO
{
    static $pdo = null;
    if ($pdo === null) {
        $c = config();
        $dsn = sprintf('pgsql:host=%s;port=%d;dbname=%s', $c['host'], $c['port'], $c['dbname']);
        try {
            $pdo = new PDO($dsn, $c['user'], $c['password'], [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_NUM,
            ]);
        } catch (PDOException $e) {
            error_log('DRIW API: database connection failed: ' . $e->getMessage());
            fail(503, 'Warehouse database is unavailable.');
        }
    }
    return $pdo;
}

/** Fetch all rows as associative arrays with JSON-friendly types (numeric -> number). */
function fetch_typed(PDOStatement $stmt): array
{
    $columns = [];
    for ($i = 0; $i < $stmt->columnCount(); $i++) {
        $meta = $stmt->getColumnMeta($i);
        $columns[] = [$meta['name'], $meta['native_type'] ?? 'text'];
    }
    $rows = [];
    while (($raw = $stmt->fetch()) !== false) {
        $row = [];
        foreach ($columns as $i => [$name, $type]) {
            $value = $raw[$i];
            if ($value !== null) {
                $value = match ($type) {
                    'int2', 'int4', 'int8' => (int) $value,
                    'numeric', 'float4', 'float8' => (float) $value,
                    'bool' => (bool) $value,
                    default => $value,
                };
            }
            $row[$name] = $value;
        }
        $rows[] = $row;
    }
    return $rows;
}

function require_get(): void
{
    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
        header('Allow: GET');
        fail(405, 'Only GET is supported.');
    }
}

function send_json(mixed $data, int $status = 200): never
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRESERVE_ZERO_FRACTION);
    exit;
}

function fail(int $status, string $message): never
{
    send_json(['error' => $message], $status);
}

/**
 * Run one of the project's Python tools (no shell: arguments are passed as an array) and return
 * [exit code, stdout]. stderr goes to a log file outside htdocs, so a chatty tool can never block
 * on a full pipe, and the administrator can read why a run failed.
 */
function run_tool(array $args, int $timeoutSeconds): array
{
    $c = config();
    if (empty($c['python']) || empty($c['project'])) {
        fail(500, 'Data exchange is not configured. Run ingestion/setup_web_role.py.');
    }
    $logDir = dirname(__DIR__, 3) . '/driw-config/logs';
    if (!is_dir($logDir)) {
        mkdir($logDir, 0700, true);
    }
    $log = $logDir . '/tools-' . date('Ymd') . '.log';
    $process = proc_open(
        array_merge([$c['python']], $args),
        [1 => ['pipe', 'w'], 2 => ['file', $log, 'a']],
        $pipes,
        $c['project']
    );
    if (!is_resource($process)) {
        fail(500, 'Could not start the data-exchange tool.');
    }
    stream_set_timeout($pipes[1], $timeoutSeconds);
    $stdout = stream_get_contents($pipes[1]);
    fclose($pipes[1]);
    return [proc_close($process), $stdout === false ? '' : $stdout];
}
