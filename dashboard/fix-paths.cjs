/**
 * Post-build script para corregir rutas relativas en index.html
 * y agregar cache busting timestamp
 * Ejecutado automáticamente después de `npm run build`
 */
const fs = require('fs');
const path = require('path');

const indexPath = path.join(__dirname, 'dist', 'index.html');
const timestamp = Math.floor(Date.now() / 1000);

try {
  let html = fs.readFileSync(indexPath, 'utf-8');

  // Mantener favicon como ruta absoluta (importante para que funcione en subrutas como /admin/)
  html = html.replace(/href="\/favicon\.png"/g, 'href="/favicon.png"');
  html = html.replace(/href="\/favicon\.svg"/g, 'href="/favicon.png"'); // Convertir .svg a .png
  // Assets como relativas
  html = html.replace(/src="\/assets\//g, 'src="./assets/');
  html = html.replace(/href="\/assets\//g, 'href="./assets/');

  // Agregar cache busting query string con timestamp
  html = html.replace(/src="\.\/assets\/([^"]+)"/g, `src="./assets/$1?v=${timestamp}"`);
  html = html.replace(/href="\.\/assets\/([^"]+)"/g, `href="./assets/$1?v=${timestamp}"`);

  fs.writeFileSync(indexPath, html, 'utf-8');
  console.log(`✅ Rutas corregidas en index.html (cache bust: v=${timestamp})`);
} catch (error) {
  console.error('❌ Error al corregir rutas:', error.message);
  process.exit(1);
}
