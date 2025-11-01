# Monitoring & Observability

## Prometheus
- Scrape targets configured in monitoring/prometheus.yml
- Custom metrics endpoints: /metrics, /metrics/business

## Grafana
- Datasource: monitoring/grafana/datasources/prometheus.yml
- Dashboards provisioned:
  - API: monitoring/grafana/dashboards/api.json
  - Worker/Runner: monitoring/grafana/dashboards/worker-runner.json

## Alerts (optional)
- Configure alert rules in Prometheus or Grafana as needed

