/**
 * Post-build script para corregir rutas relativas en index.html
 * Ejecutado automáticamente después de `npm run build`
 */
const fs = require('fs');
const path = require('path');

const indexPath = path.join(__dirname, 'dist', 'index.html');

try {
  let html = fs.readFileSync(indexPath, 'utf-8');

  // Reemplazar rutas absolutas con relativas
  html = html.replace(/href="\/favicon\.svg"/g, 'href="./favicon.svg"');
  html = html.replace(/src="\/assets\//g, 'src="./assets/');
  html = html.replace(/href="\/assets\//g, 'href="./assets/');

  fs.writeFileSync(indexPath, html, 'utf-8');
  console.log('✅ Rutas corregidas en index.html');
} catch (error) {
  console.error('❌ Error al corregir rutas:', error.message);
  process.exit(1);
}
