<?php
// Fallback para SPA routing
// Si el archivo no existe, servir index.html

$file = __DIR__ . $_SERVER['REQUEST_URI'];
$file = str_replace('/dashboard/', __DIR__ . '/', $file);

// Si es un archivo que existe, servirlo directamente
if (is_file($file) && file_exists($file)) {
    // Determinar el content-type
    $ext = pathinfo($file, PATHINFO_EXTENSION);
    $types = [
        'js' => 'application/javascript',
        'css' => 'text/css',
        'html' => 'text/html',
        'json' => 'application/json',
        'svg' => 'image/svg+xml',
        'png' => 'image/png',
        'jpg' => 'image/jpeg',
        'gif' => 'image/gif',
    ];

    if (isset($types[$ext])) {
        header('Content-Type: ' . $types[$ext]);
    }

    readfile($file);
    exit;
}

// Si es una carpeta que existe, buscar index.html
if (is_dir($file)) {
    $index = $file . '/index.html';
    if (file_exists($index)) {
        header('Content-Type: text/html');
        readfile($index);
        exit;
    }
}

// Fallback: servir index.html para SPA routing
$index = __DIR__ . '/index.html';
if (file_exists($index)) {
    header('Content-Type: text/html');
    readfile($index);
    exit;
}

// Si nada funciona, error 404
http_response_code(404);
echo "404 Not Found";
?>
