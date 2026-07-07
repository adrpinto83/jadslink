// ── Conversión de Moneda USD <-> Bs ──────────────────────────────────────────

const currencySystem = {
  exchangeRate: 36.50, // Tasa por defecto
  source: 'loading',
  lastUpdate: null,
  loading: true,

  async init() {
    await this.fetchExchangeRate();
    this.updateAllPrices();
  },

  async fetchExchangeRate() {
    try {
      const response = await fetch('/api/exchange/current');
      const data = await response.json();

      this.exchangeRate = data.rate;
      this.source = data.source;
      this.lastUpdate = data.updated_at;
      this.loading = false;

      console.log(`✓ Tasa de cambio cargada: ${this.exchangeRate} Bs/USD (${this.source})`);
    } catch (error) {
      console.error('Error cargando tasa de cambio:', error);
      this.loading = false;
      // Mantiene tasa por defecto
    }
  },

  usdToBs(usdAmount) {
    return Math.round(usdAmount * this.exchangeRate * 100) / 100;
  },

  bsToUsd(bsAmount) {
    return Math.round((bsAmount / this.exchangeRate) * 100) / 100;
  },

  formatUSD(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  },

  formatBs(amount) {
    return new Intl.NumberFormat('es-VE', {
      style: 'currency',
      currency: 'VES',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  },

  formatDualPrice(usdAmount, options = {}) {
    const showBoth = options.showBoth !== false;

    if (!showBoth) {
      return this.formatUSD(usdAmount);
    }

    const bsAmount = this.usdToBs(usdAmount);
    return `${this.formatUSD(usdAmount)} <span style="color:var(--muted);font-size:0.85em">(≈ ${this.formatBs(bsAmount)})</span>`;
  },

  updateAllPrices() {
    // Actualizar todos los elementos con data-price-usd
    const priceElements = document.querySelectorAll('[data-price-usd]');

    priceElements.forEach(el => {
      const usdAmount = parseFloat(el.getAttribute('data-price-usd'));
      const showBoth = el.getAttribute('data-show-both') !== 'false';

      el.innerHTML = this.formatDualPrice(usdAmount, { showBoth });
    });

    // Actualizar badge de tasa de cambio
    this.updateExchangeRateBadge();
  },

  updateExchangeRateBadge() {
    const badge = document.getElementById('exchange-rate-badge');
    if (!badge) return;

    if (this.loading) {
      badge.innerHTML = `
        <span style="color:var(--muted);font-size:12px">
          Cargando tasa...
        </span>
      `;
      return;
    }

    const sourceLabels = {
      'bcv_scraping': 'BCV Oficial',
      'api_fallback': 'API Internacional',
      'manual': 'Manual',
      'default': 'Tasa Base'
    };

    const sourceLabel = sourceLabels[this.source] || this.source;

    const dateStr = this.lastUpdate
      ? new Date(this.lastUpdate).toLocaleDateString('es-VE', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        })
      : '';

    badge.innerHTML = `
      <div style="display:inline-flex;align-items:center;gap:8px;padding:6px 12px;background:#ecfdf5;border:1px solid #a7f3d0;border-radius:6px;font-size:12px">
        <span style="font-weight:600;color:#059669">
          1 USD = ${this.exchangeRate.toFixed(2)} Bs
        </span>
        <span style="color:#10b981">(${sourceLabel})</span>
        ${dateStr ? `<span style="color:#6b7280">• ${dateStr}</span>` : ''}
      </div>
    `;
  }
};

// Inicializar cuando se carga la página
window.addEventListener('load', () => {
  currencySystem.init();
});
