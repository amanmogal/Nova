# Grafana Cloud Setup for Notion Agent

## 🎯 Overview

This guide will help you set up **Grafana Cloud** for monitoring your Notion Agent with beautiful dashboards and real-time metrics.

## 🚀 Quick Start

### 1. Create Grafana Cloud Account

1. Go to [Grafana Cloud](https://grafana.com/auth/sign-up/create-user)
2. Sign up for a **free account** (includes 10k series metrics, 14 days retention)
3. Choose your **stack name** (e.g., "notion-agent-monitoring")
4. Select your **region** (closest to your deployment)

### 2. Get Your Prometheus Endpoint

After creating your stack, you'll get:
- **Prometheus URL**: `https://prometheus-prod-XX-XXXXX.grafana.net/api/prom/push`
- **Username**: Your Grafana Cloud username
- **API Key**: Generated automatically

### 3. Configure Your Agent

Your agent now exports Prometheus metrics at:
```
GET http://your-server:8000/metrics
```

### 4. Set Up Metrics Collection

#### Option A: Using Grafana Agent (Recommended)

1. **Install Grafana Agent**:
```bash
# Download Grafana Agent
wget -O grafana-agent.zip https://github.com/grafana/agent/releases/latest/download/grafana-agent-<OS>-<ARCH>.zip
unzip grafana-agent.zip
```

2. **Create config file** (`agent-config.yaml`):
```yaml
server:
  log_level: info

metrics:
  global:
    remote_write:
      - url: https://prometheus-prod-XX-XXXXX.grafana.net/api/prom/push
        basic_auth:
          username: YOUR_USERNAME
          password: YOUR_API_KEY

  configs:
    - name: notion-agent
      scrape_configs:
        - job_name: notion-agent
          static_configs:
            - targets: ['localhost:8000']
          metrics_path: /metrics
          scrape_interval: 15s
```

3. **Start Grafana Agent**:
```bash
./grafana-agent --config.file=agent-config.yaml
```

#### Option B: Using curl (Simple Testing)

```bash
# Test your metrics endpoint
curl http://localhost:8000/metrics

# Should return Prometheus format like:
# notion_agent_operation_count{operation="llm_call"} 42
# notion_agent_error_count{operation="search_tasks"} 3
# notion_agent_operation_duration_ms{operation="llm_call",success="true"} 1250.5
```

### 5. Access Grafana Dashboard

1. Go to your Grafana Cloud URL: `https://your-stack.grafana.net`
2. Login with your credentials
3. Navigate to **Explore** → **Prometheus**
4. Test queries like:
   - `notion_agent_operation_count`
   - `notion_agent_error_count`
   - `notion_agent_operation_duration_ms`

## 📊 Available Metrics

Your agent exports these Prometheus metrics:

### Counters
- `notion_agent_operation_count{operation="..."}` - Total operations by type
- `notion_agent_error_count{operation="..."}` - Total errors by operation

### Gauges
- `notion_agent_operation_duration_ms{operation="...",success="..."}` - Operation duration
- `notion_agent_token_count{operation="..."}` - Token usage per operation
- `notion_agent_cost_usd{operation="..."}` - Cost per operation
- `notion_agent_total_cost_usd` - Total cost across all operations
- `notion_agent_last_export_time` - Last metrics export timestamp

## 🎨 Create Beautiful Dashboards

### 1. Import Pre-built Dashboard

1. In Grafana, go to **Dashboards** → **Import**
2. Use dashboard ID: `1860` (Node Exporter Full)
3. Or create custom dashboard with these panels:

### 2. Recommended Dashboard Panels

#### **System Overview**
```promql
# Total Operations
sum(notion_agent_operation_count)

# Error Rate
rate(notion_agent_error_count[5m]) / rate(notion_agent_operation_count[5m]) * 100

# Average Response Time
avg(notion_agent_operation_duration_ms)
```

#### **Cost Monitoring**
```promql
# Total Cost
notion_agent_total_cost_usd

# Cost by Operation
notion_agent_cost_usd

# Cost Rate (per hour)
rate(notion_agent_cost_usd[1h])
```

#### **Performance Metrics**
```promql
# Operations per Second
rate(notion_agent_operation_count[5m])

# Token Usage
sum(notion_agent_token_count)

# Response Time Percentiles
histogram_quantile(0.95, rate(notion_agent_operation_duration_ms_bucket[5m]))
```

#### **Error Analysis**
```promql
# Error Rate by Operation
rate(notion_agent_error_count[5m])

# Top Error Operations
topk(5, rate(notion_agent_error_count[5m]))
```

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:
```bash
# Grafana Cloud Configuration
GRAFANA_CLOUD_URL=https://your-stack.grafana.net
GRAFANA_CLOUD_USERNAME=your_username
GRAFANA_CLOUD_API_KEY=your_api_key

# Metrics Configuration
ENABLE_PROMETHEUS_METRICS=true
METRICS_EXPORT_INTERVAL=15
```

### Update Your Agent

Your agent automatically exports metrics when:
- LLM calls are made
- Tool operations are performed
- Agent runs complete
- Errors occur

## 🚨 Alerts (Optional)

Set up alerts in Grafana Cloud:

### High Error Rate Alert
```promql
rate(notion_agent_error_count[5m]) / rate(notion_agent_operation_count[5m]) > 0.1
```

### High Cost Alert
```promql
rate(notion_agent_cost_usd[1h]) > 1.0
```

### Slow Response Time Alert
```promql
avg(notion_agent_operation_duration_ms) > 5000
```

## 🧪 Testing

### 1. Test Your Metrics Endpoint
```bash
# Start your server
python -m uvicorn src.server_simple:app --reload --host 0.0.0.0 --port 8000

# Test metrics endpoint
curl http://localhost:8000/metrics
```

### 2. Test Agent Operations
```bash
# Trigger some agent operations
curl -X POST http://localhost:8000/run/daily_planning

# Check metrics again
curl http://localhost:8000/metrics
```

### 3. Verify in Grafana
1. Go to Grafana Cloud
2. Navigate to **Explore** → **Prometheus**
3. Query: `notion_agent_operation_count`
4. You should see your metrics appearing

## 💡 Tips

1. **Start Simple**: Begin with basic metrics, add complexity later
2. **Use Templates**: Grafana has many dashboard templates
3. **Set Alerts**: Configure alerts for critical metrics
4. **Monitor Costs**: Keep an eye on your Grafana Cloud usage
5. **Backup Configs**: Save your agent and Grafana configurations

## 🆘 Troubleshooting

### No Metrics Appearing
- Check your `/metrics` endpoint returns data
- Verify Grafana Agent is running
- Check API keys and URLs

### High Latency
- Reduce scrape interval (default: 15s)
- Use Grafana Agent instead of direct scraping
- Check network connectivity

### Missing Metrics
- Ensure your agent is performing operations
- Check the `export_prometheus()` method
- Verify metric names match your queries

## 🎉 Success!

Once set up, you'll have:
- ✅ **Real-time monitoring** of your Notion Agent
- ✅ **Beautiful dashboards** with Grafana
- ✅ **Cost tracking** and optimization
- ✅ **Error monitoring** and alerting
- ✅ **Performance insights** and trends

Your monitoring is now production-ready! 🚀 