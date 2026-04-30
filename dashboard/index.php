<?php
/**
 * SPA Router Fallback para React Router
 * Redirige todas las rutas que no son archivos existentes a index.html
 * para que React Router maneje el routing en el cliente
 */

// Obtener la ruta solicitada (sin query string)
$request_uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

// Log para debugging (comentar en producción)
// error_log("REQUEST_URI: $request_uri, DIR: " . __DIR__);

// Si está pidiendo exactamente /dashboard/ o /dashboard, redirigir a /dashboard/login
if ($request_uri === '/dashboard/' || $request_uri === '/dashboard') {
    header('Location: /dashboard/login', true, 302);
    exit;
}

// Ruta del archivo solicitado (relativa al directorio actual)
$file_path = __DIR__ . $request_path;

// Si es un archivo que existe físicamente, servirlo directamente
if (is_file($file_path) && file_exists($file_path)) {
    // Determinar Content-Type basado en extensión
    $ext = strtolower(pathinfo($file_path, PATHINFO_EXTENSION));
    $mime_types = [
        'js' => 'application/javascript; charset=utf-8',
        'css' => 'text/css; charset=utf-8',
        'html' => 'text/html; charset=utf-8',
        'json' => 'application/json',
        'svg' => 'image/svg+xml',
        'png' => 'image/png',
        'jpg' => 'image/jpeg',
        'jpeg' => 'image/jpeg',
        'gif' => 'image/gif',
        'ico' => 'image/x-icon',
        'woff' => 'font/woff',
        'woff2' => 'font/woff2',
    ];

    $content_type = $mime_types[$ext] ?? 'application/octet-stream';
    header('Content-Type: ' . $content_type);
    readfile($file_path);
    exit;
}

// Si es una carpeta, intentar servir index.html de esa carpeta
if (is_dir($file_path)) {
    $index_file = rtrim($file_path, '/') . '/index.html';
    if (file_exists($index_file)) {
        header('Content-Type: text/html; charset=utf-8');
        readfile($index_file);
        exit;
    }
}

// Fallback: Para todas las rutas desconocidas, servir index.html
// para que React Router maneje el routing en el cliente
$index_file = __DIR__ . '/index.html';
if (file_exists($index_file)) {
    header('Content-Type: text/html; charset=utf-8');
    // NO cachear el index.html para que siempre cargue la versión más reciente
    header('Cache-Control: no-cache, no-store, must-revalidate');
    header('Pragma: no-cache');
    header('Expires: 0');
    readfile($index_file);
    exit;
}

// Si nada funciona, error 500
http_response_code(500);
echo "Error: index.html not found";
?>
