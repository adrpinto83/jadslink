<?php
/**
 * Reverse proxy + auto-heal para JADSLink (uvicorn FastAPI).
 *
 * Hostinger (LiteSpeed) no permite Passenger Python en subdirectorios ni
 * shell_exec; tampoco hay crontab por SSH. Por eso cada petición verifica
 * que uvicorn esté escuchando y, si murió, lo relanza con proc_open+setsid
 * (proceso desacoplado que sobrevive al fin del request PHP).
 */

const UVICORN_PORT = 58765;
const APP_DIR      = '/home/u938946830/jadslink-app';
const VENV_PYTHON  = APP_DIR . '/venv/bin/python3.11';
const LOG_FILE     = APP_DIR . '/uvicorn.log';
const LOCK_FILE    = APP_DIR . '/.uvicorn.lock';

function uvicorn_is_up(): bool {
    $fp = @fsockopen('127.0.0.1', UVICORN_PORT, $errno, $errstr, 1);
    if ($fp) { fclose($fp); return true; }
    return false;
}

function start_uvicorn(): void {
    // Lock para que dos peticiones simultáneas no lancen dos procesos.
    $lock = @fopen(LOCK_FILE, 'c');
    if ($lock === false) { return; }
    if (!flock($lock, LOCK_EX | LOCK_NB)) {
        // Otra petición ya está arrancando uvicorn; esperamos a que suba.
        fclose($lock);
        for ($i = 0; $i < 20; $i++) {
            usleep(300000);
            if (uvicorn_is_up()) return;
        }
        return;
    }

    // Doble chequeo dentro del lock.
    if (!uvicorn_is_up()) {
        $cmd = sprintf(
            'cd %s && exec %s -m uvicorn api.main:app --host 127.0.0.1 --port %d',
            escapeshellarg(APP_DIR),
            escapeshellarg(VENV_PYTHON),
            UVICORN_PORT
        );
        // setsid -> nuevo session leader, sobrevive al cierre del request PHP.
        $full = 'setsid /bin/bash -c ' . escapeshellarg($cmd)
              . ' >> ' . escapeshellarg(LOG_FILE) . ' 2>&1 < /dev/null &';

        $descriptors = [
            0 => ['file', '/dev/null', 'r'],
            1 => ['file', LOG_FILE, 'a'],
            2 => ['file', LOG_FILE, 'a'],
        ];
        $proc = @proc_open('/bin/bash -c ' . escapeshellarg($full), $descriptors, $pipes, APP_DIR);
        if (is_resource($proc)) {
            proc_close($proc);
        }

        // Esperar a que uvicorn quede escuchando (máx ~8s).
        for ($i = 0; $i < 27; $i++) {
            usleep(300000);
            if (uvicorn_is_up()) break;
        }
    }

    flock($lock, LOCK_UN);
    fclose($lock);
}

// --- Auto-heal ---
if (!uvicorn_is_up()) {
    start_uvicorn();
}

// --- Reverse proxy ---
$target = 'http://127.0.0.1:' . UVICORN_PORT;
$uri    = $_SERVER['REQUEST_URI'];
$method = $_SERVER['REQUEST_METHOD'];
$body   = file_get_contents('php://input');

$headers = [];
foreach (getallheaders() as $k => $v) {
    $lk = strtolower($k);
    if (in_array($lk, ['host', 'connection', 'content-length', 'transfer-encoding'])) continue;
    $headers[] = "$k: $v";
}
$headers[] = 'X-Forwarded-For: '   . ($_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR']);
$headers[] = 'X-Forwarded-Host: '  . $_SERVER['HTTP_HOST'];
$headers[] = 'X-Forwarded-Proto: https';

$ctx = stream_context_create(['http' => [
    'method'          => $method,
    'header'          => implode("\r\n", $headers),
    'content'         => $body,
    'ignore_errors'   => true,
    'follow_location' => false,
    'timeout'         => 30,
]]);

$resp = @file_get_contents($target . $uri, false, $ctx);

if ($resp === false) {
    http_response_code(502);
    header('Content-Type: application/json');
    echo json_encode(['error' => 'gateway_error', 'detail' => 'uvicorn no responde']);
    exit;
}

if (isset($http_response_header)) {
    foreach ($http_response_header as $h) {
        if (preg_match('/^HTTP\/[\d.]+ (\d+)/', $h, $m)) {
            http_response_code((int) $m[1]);
        } elseif (strpos($h, ':') !== false) {
            [$k, $v] = explode(':', $h, 2);
            $lk = strtolower(trim($k));
            if (!in_array($lk, ['connection', 'transfer-encoding', 'content-encoding'])) {
                header("$k:$v");
            }
        }
    }
}
echo $resp;
