# JADSlink Monitoring and Observability

Complete guide for setting up monitoring, logging, and alerting.

## Architecture

```
┌─────────────────┐
│   JADSlink API  │
│                 │
│ • Structured    │
│   JSON Logging  │
│ • Prometheus    │
│   Metrics       │
│ • Health Checks │
└────────┬────────┘
         │
    ┌────┴─────┬──────────────┐
    ▼          ▼              ▼
 Logs       Metrics        Health
  │            │              │
  ▼            ▼              ▼
 Loki      Prometheus    Load Balancer
  │            │
  └─────┬──────┘
        ▼
     Grafana
    (Dashboards)
```

## Components

### 1. Structured Logging

All logs are emitted as JSON with contextual information:

```json
{
  "timestamp": "2026-04-21T10:30:45.123456",
  "level": "INFO",
  "logger": "jadslink.routers.auth",
  "message": "User login successful",
  "environment": "production",
  "request_id": "abc123",
  "user_id": "uuid",
  "duration_ms": 45
}
```

**Features:**
- Structured JSON format for easy parsing
- Timestamp in ISO 8601 format
- Environment metadata
- Request tracing support
- Compatible with ELK, Loki, Datadog, etc.

### 2. Prometheus Metrics

Metrics exposed at `/metrics` endpoint for Prometheus scraping.

**Available Metrics:**

| Metric | Type | Description |
|--------|------|-------------|
| `jadslink_requests_total` | Counter | Total API requests by method/endpoint/status |
| `jadslink_request_duration_seconds` | Histogram | Request latency distribution |
| `jadslink_active_sessions_total` | Gauge | Current active sessions |
| `jadslink_nodes_total` | Gauge | Total nodes by status |
| `jadslink_nodes_offline_total` | Gauge | Number of offline nodes |
| `jadslink_tickets_generated_total` | Counter | Tickets created by plan tier |
| `jadslink_stripe_subscription_created_total` | Counter | Stripe subscriptions created |
| `jadslink_errors_total` | Counter | Total errors by type/endpoint |
| `jadslink_rate_limit_exceeded_total` | Counter | Rate limit violations |
| `jadslink_db_query_duration_seconds` | Histogram | Database query latency |

**Example Query (PromQL):**

```promql
# Average request duration (last 5 minutes)
rate(jadslink_request_duration_seconds_sum[5m]) / rate(jadslink_request_duration_seconds_count[5m])

# Error rate
rate(jadslink_errors_total[5m]) / rate(jadslink_requests_total[5m])

# Offline nodes
jadslink_nodes_offline_total

# P95 latency
histogram_quantile(0.95, jadslink_request_duration_seconds)
```

### 3. Health Checks

**GET `/health`** - Basic health check
- Returns 200 if database is accessible
- Checks: database connectivity

**GET `/health/ready`** - Readiness probe
- Used by load balancers
- Returns 200 when ready for traffic

**GET `/health/nodes`** - Node health status
- Online/offline/stale counts
- Updates `jadslink_nodes_offline_total` metric
- Stale = not seen in > 5 minutes

**GET `/metrics`** - Prometheus metrics
- Scraped by Prometheus
- All application metrics
- Update interval configurable

## Setup

### Option 1: Prometheus Only (Lightweight)

Add to `docker-compose.yml`:

```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: jadslink_prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'

volumes:
  prometheus_data:
```

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'jadslink-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

Start:
```bash
docker compose up prometheus
# Access: http://localhost:9090
```

### Option 2: Full Stack (Prometheus + Grafana + Loki)

See `docker-compose.monitoring.yml` for complete setup with:
- Prometheus (metrics)
- Loki (logs)
- Grafana (visualization)

Start:
```bash
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up
```

Access:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- API: http://localhost:8000

### Option 3: Cloud Providers

**AWS CloudWatch:**
```python
# Install: pip install watchtower
import watchtower
logging.handlers.append(watchtower.CloudWatchLogHandler())
```

**Google Cloud Logging:**
```python
# Install: pip install google-cloud-logging
from google.cloud import logging as cloud_logging
cloud_logging.Client().setup_logging()
```

**Datadog:**
```python
# Install: pip install ddtrace
import ddtrace
ddtrace.patch_all()
```

## Alerts

### Node Offline Alert

Triggered when a node hasn't reported in > 5 minutes.

**Prometheus Alert Rule:**

```yaml
groups:
  - name: jadslink
    rules:
      - alert: NodeOffline
        expr: jadslink_nodes_offline_total > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $value }} nodes offline"
          description: "Nodes have not reported for > 5 minutes"
```

### High Error Rate

Triggered when error rate exceeds 5%.

```yaml
- alert: HighErrorRate
  expr: |
    (rate(jadslink_errors_total[5m]) / rate(jadslink_requests_total[5m])) > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
```

### High Latency

Triggered when P95 latency exceeds 1 second.

```yaml
- alert: HighLatency
  expr: |
    histogram_quantile(0.95, rate(jadslink_request_duration_seconds[5m])) > 1
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High API latency"
```

## Dashboards

### Grafana Dashboard

Import dashboard from `grafana/dashboards/jadslink.json` or create manually:

**System Health**
- Request rate
- Error rate
- Latency (P50, P95, P99)
- Active sessions

**Business Metrics**
- Tickets generated (per plan)
- Subscriptions created
- Node status distribution
- Tenant usage

**Resource Usage**
- Database query latency
- API response times
- Rate limit events

**Errors & Issues**
- Error count by type
- Offline nodes
- Failed webhooks
- Rate limit violations

## Logging Configuration

**Environment Variables:**

```bash
# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# Environment: development, staging, production
ENVIRONMENT=production
```

**Log Output:**

Development:
```
INFO:jadslink.routers.auth:User login successful
```

Production (JSON):
```json
{"timestamp":"2026-04-21T10:30:45.123456","level":"INFO","logger":"jadslink.routers.auth","message":"User login successful","environment":"production"}
```

## Integration Examples

### ELK Stack (Elasticsearch, Logstash, Kibana)

Logstash configuration:

```logstash
input {
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  mutate {
    add_field => { "[@metadata][index_name]" => "jadslink-%{+YYYY.MM.dd}" }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "%{[@metadata][index_name]}"
  }
}
```

### Loki (Grafana Logs)

Promtail configuration:

```yaml
scrape_configs:
  - job_name: jadslink
    static_configs:
      - targets:
          - localhost
        labels:
          job: jadslink
          __path__: /var/log/jadslink/*.json
```

### Datadog

```python
from datadog import initialize, api
from pythonjsonlogger import jsonlogger
import logging

# Configure Datadog handler
options = {
    'api_key': os.getenv('DATADOG_API_KEY'),
    'app_key': os.getenv('DATADOG_APP_KEY')
}
initialize(**options)

# Logs are automatically sent via JSON format
```

## Troubleshooting

### Metrics endpoint returns 404

- Check `/metrics` route is registered
- Verify MetricsMiddleware is added
- Look at logs for import errors

### No data in Prometheus

- Check `prometheus.yml` configuration
- Verify API `/metrics` endpoint is accessible
- Check Prometheus targets: http://localhost:9090/targets
- Increase `scrape_interval` if needed

### High memory usage

- Reduce Prometheus retention: `--storage.tsdb.retention.time=30d`
- Adjust metric cardinality (number of label combinations)
- Use Prometheus relabel_configs to drop unnecessary labels

### Missing logs

- Check LOG_LEVEL environment variable
- Verify logging_config.py is imported
- Check file permissions if writing to disk
- Verify JSON formatter is working

## Performance

**Overhead:**
- Metrics collection: < 1% CPU overhead
- Logging (JSON): < 2% CPU overhead
- Health checks: < 1% requests

**Best Practices:**
- Scrape interval: 15-30 seconds
- Retention: 15-30 days
- Alert evaluation: 15-60 seconds
- Sample regularly (don't query every second)

## Security

⚠️ **Important:**
- `/metrics` endpoint is public (no auth)
  - Can expose sensitive information
  - Restrict IP access in production
  - Use reverse proxy with authentication
- Logs may contain sensitive data
  - Implement log scrubbing for passwords, tokens
  - Use data masking in log aggregators
- Monitor access to monitoring systems
  - Protect Prometheus/Grafana with strong passwords
  - Use network ACLs
  - Enable audit logging

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [Python JSON Logger](https://github.com/madzak/python-json-logger)
- [FastAPI Monitoring](https://fastapi.tiangolo.com/deployment/concepts/)

## Support

For issues:
1. Check logs: `docker compose logs api`
2. Verify Prometheus scrape: `http://localhost:9090/targets`
3. Test metrics endpoint: `curl http://localhost:8000/metrics`
4. Check health: `curl http://localhost:8000/health`
