# Operational Considerations

Guidance for deploying and operating ANPR City API in production.

## Infrastructure Requirements

### Compute

#### API Server
- **Minimum**: 2 vCPU, 4GB RAM
- **Recommended**: 4 vCPU, 8GB RAM
- **Scaling**: Horizontal scaling behind load balancer
- **Autoscaling trigger**: CPU > 70% or requests > 1000/min

#### Worker Nodes (GPU-enabled)
- **Light load (1-5 cameras)**:
  - 1x NVIDIA T4 GPU
  - 4 vCPU, 16GB RAM
  - ~30 FPS processing speed

- **Medium load (5-20 cameras)**:
  - 2x NVIDIA T4 or 1x A10G GPU
  - 8 vCPU, 32GB RAM
  - ~60-100 FPS processing speed

- **Heavy load (20+ cameras)**:
  - 2+ NVIDIA A10G or V100 GPUs
  - 16+ vCPU, 64GB RAM
  - ~200+ FPS processing speed

**GPU Sizing Rule of Thumb**:
- Budget 1 GPU per 10 concurrent cameras at 15 FPS
- For higher FPS or resolution, scale proportionally

### Database

#### PostgreSQL
- **Development**: 2 vCPU, 4GB RAM, 50GB SSD
- **Production**: 4+ vCPU, 16GB+ RAM, 500GB+ SSD
- **Connection Pool**: 50-100 connections
- **Replication**: Read replica for analytics queries
- **Backup**: Daily full + WAL archiving

**Growth Estimates**:
- Events table: ~1KB per row
- 10 cameras @ 1 detection/sec = 864,000 rows/day = ~850MB/day
- 30-day retention = 25GB events + 500GB crops (with indexes)

#### Redis
- **Development**: 1GB RAM
- **Production**: 4-8GB RAM
- **Persistence**: RDB snapshots + AOF
- **Replication**: Master + 1-2 replicas
- **Use case**: Job queue only (ephemeral data)

### Storage

#### Object Storage (S3/MinIO/Supabase)
- **Raw Videos**: ~1GB/hour per camera (h264 @ 1080p, 15fps)
- **Crop Images**: ~100KB per detection (JPEG compressed)
- **Retention Example** (10 cameras, 30 days):
  - Videos: 10 × 24 × 30 × 1GB = 7.2TB
  - Crops: 10 × 3600 × 24 × 30 × 0.1MB = 2.6TB
  - **Total**: ~10TB

**Cost Optimization**:
- Compress videos: h265 codec reduces size by 50%
- Lifecycle policies: Archive old videos to glacier after 90 days
- Delete raw videos after processing (keep only crops)
- Use tiered storage: Hot (30d) → Cool (90d) → Archive (1y+)

### Network

- **Ingress**: Video uploads can be large (100MB-1GB per file)
- **Egress**: Crop image serving, API responses
- **Bandwidth Budget**:
  - 10 cameras × 1GB/hour × 24h = 240GB/day upload
  - API + crops serving: ~50GB/day
  - **Total**: ~300GB/day or 9TB/month

**Recommendations**:
- Use CDN for serving crops (CloudFront, CloudFlare)
- Implement multipart uploads for large videos
- Consider edge processing to reduce upload bandwidth

## Cost Estimates

### AWS (us-east-1)

#### Self-Hosted Stack
- **API Server**: t3.large (2vCPU, 8GB) = $60/mo
- **Worker**: g4dn.xlarge (4vCPU, 16GB, T4 GPU) × 2 = $820/mo
- **Database**: RDS db.t3.large (2vCPU, 8GB, 500GB) = $200/mo
- **Redis**: ElastiCache cache.t3.small = $25/mo
- **Storage**: S3 Standard 10TB = $240/mo
- **Data Transfer**: 10TB egress = $900/mo
- **Load Balancer**: ALB = $25/mo

**Subtotal**: ~$2,270/mo for 10-camera deployment

#### Cost Reduction Strategies
1. **Reserved Instances**: Save 30-40% on compute
2. **Spot Instances**: Use for non-critical workers (save 70%)
3. **S3 Intelligent-Tiering**: Auto-archive old data (save 40% on storage)
4. **Compress videos**: h265 codec (save 50% on storage)
5. **Delete raw videos**: Keep only crops (save 70% on storage)

**Optimized Cost**: ~$1,200/mo

### Supabase Mode

- **Supabase Pro**: $25/mo (includes 8GB DB, 100GB storage)
- **Additional Storage**: 10TB = $1,000/mo
- **Additional Bandwidth**: 10TB = TBD (check Supabase pricing)
- **Redis**: Upstash or Redis Cloud = $20-50/mo
- **Worker GPU**: Same as above = $820/mo

**Total**: ~$1,900/mo

### GCP Estimates

- **API Server**: e2-standard-2 = $50/mo
- **Worker**: n1-standard-4 + T4 GPU × 2 = $700/mo
- **Database**: Cloud SQL PostgreSQL 8GB = $150/mo
- **Redis**: Memorystore 4GB = $40/mo
- **Storage**: Cloud Storage 10TB = $200/mo
- **Egress**: 10TB = $1,200/mo

**Total**: ~$2,340/mo

### Azure Estimates

Similar to AWS, roughly $2,000-2,500/mo for equivalent setup.

## Throughput & Capacity Planning

### Processing Capacity

| Configuration | Cameras | FPS | Total Processing Capacity |
|---------------|---------|-----|---------------------------|
| 1x T4 GPU | 5-10 | 15 | 150-300 FPS |
| 2x T4 GPU | 10-20 | 15 | 300-600 FPS |
| 1x A10G GPU | 15-25 | 15 | 450-750 FPS |
| 2x A10G GPU | 30-50 | 15 | 900-1500 FPS |

**Bottlenecks**:
- GPU: Detection + OCR
- Disk I/O: Frame extraction, crop saving
- Network: Video download from storage
- Database: Event inserts (use batching)

**Optimization Tips**:
1. **Batch Processing**: Process frames in batches of 10-20
2. **Local SSD**: Download videos to local NVMe for faster I/O
3. **Database Connection Pool**: Reuse connections
4. **Crop Upload**: Async upload to storage (don't block worker)

### API Capacity

- **FastAPI + uvicorn**: ~1,000 req/sec per worker (simple queries)
- **Database queries**: 100-500 req/sec (depends on query complexity)
- **Scaling**: Horizontal scale API servers (stateless)

**Load Testing Results** (sample):
- `/api/events` search: p95 = 150ms, p99 = 300ms
- `/api/uploads` upload: p95 = 2s (depends on file size)
- `/api/auth/login`: p95 = 50ms

### Queue Throughput

- **Redis**: 10,000+ jobs/sec (not a bottleneck)
- **Worker Processing**: 1 job every 2-10 minutes (depends on video length)
- **Queue Depth Monitoring**: Alert if > 100 jobs pending

## Monitoring & Alerting

### Key Metrics

#### Application Metrics (Prometheus)
```
anpr_events_processed_total          # Total events detected
anpr_events_failed_total             # Failed detections
anpr_jobs_processed_total            # Completed video jobs
anpr_jobs_failed_total               # Failed jobs
anpr_queue_size                      # Current job backlog
```

#### System Metrics
- CPU usage (target: < 80%)
- Memory usage (target: < 85%)
- GPU utilization (target: 70-90%)
- GPU memory (target: < 90%)
- Disk I/O (watch for saturation)
- Network bandwidth

#### Database Metrics
- Connection count
- Query latency (p95, p99)
- Slow queries (> 1s)
- Table size growth
- Index usage

### Alerting Rules

**Critical (PagerDuty)**:
- API down (health check fails)
- Database down
- Queue backlog > 500 jobs
- Worker crashed (no jobs processed in 10 min)
- GPU out of memory
- Disk usage > 90%

**Warning (Slack/Email)**:
- Queue backlog > 100 jobs
- API latency p99 > 1s
- Detection accuracy drops (need custom metric)
- Failed job rate > 5%
- Disk usage > 80%

### Dashboards

**Grafana Panels**:
1. **Overview**: Events/sec, active cameras, queue depth
2. **API**: Request rate, latency, error rate
3. **Workers**: Job throughput, GPU utilization, processing time
4. **Database**: Query rate, connection pool, table sizes
5. **Storage**: Upload rate, storage used, bandwidth

## Security

### Network Security
- **API**: Behind TLS-terminating load balancer (HTTPS only)
- **Database**: Private subnet, no public access
- **Redis**: Private network only
- **Storage**: Private buckets, presigned URLs for access

### Authentication & Authorization
- **JWT**: HS256 (production: consider RS256 with key rotation)
- **Token expiry**: 7 days (configurable)
- **Password hashing**: bcrypt rounds=12
- **RBAC**: Admin vs Clerk roles

### Secrets Management
- **Development**: `.env` file (not committed)
- **Production**:
  - Kubernetes: Secrets + RBAC
  - AWS: Secrets Manager or Parameter Store
  - GCP: Secret Manager
  - Azure: Key Vault

### Data Protection
- **Encryption at rest**: Enable on database and storage
- **Encryption in transit**: TLS 1.2+ everywhere
- **PII handling**: Plate numbers may be PII depending on jurisdiction
- **Audit logs**: Track all access to sensitive data

### Compliance

#### GDPR (if applicable)
- **Right to access**: Implement data export endpoint
- **Right to erasure**: Soft delete with retention policy
- **Data minimization**: Don't store unnecessary PII
- **Retention**: Define and enforce data retention policies

#### Industry Standards
- **NIST Cybersecurity Framework**: Follow if required
- **SOC 2**: Implement controls if selling to enterprises
- **ISO 27001**: Consider certification for international customers

## Disaster Recovery

### Backup Strategy

**Database**:
- Daily full backup (automated via RDS/Cloud SQL)
- WAL archiving for point-in-time recovery
- Retention: 30 days
- Test restores: Monthly

**Storage**:
- Versioning enabled
- Cross-region replication (for critical data)
- Retention: 90 days (then archive)

**Configuration**:
- Infrastructure as Code (Terraform)
- GitOps for Kubernetes manifests

### Recovery Time Objectives

- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 1 hour

### Disaster Scenarios

1. **Database Failure**:
   - Failover to replica: < 5 minutes
   - Restore from backup: < 2 hours

2. **Storage Failure**:
   - Replication to secondary region: < 1 hour
   - Impact: New uploads fail, existing data safe

3. **Complete Region Failure**:
   - Failover to DR region: 2-4 hours
   - Requires: Multi-region setup

## Maintenance Windows

**Weekly Tasks**:
- Review logs for errors
- Check queue backlog
- Monitor storage growth
- Review slow queries

**Monthly Tasks**:
- Update dependencies (security patches)
- Database vacuum/analyze
- Review and archive old data
- Capacity planning review
- Test backup restores

**Quarterly Tasks**:
- Rotate secrets (JWT keys, API keys)
- Security audit
- Disaster recovery drill
- Performance benchmarking

## Scaling Strategy

### Vertical Scaling
- API server: t3.large → t3.xlarge → t3.2xlarge
- Database: Increase instance size
- Redis: Increase memory

**Limits**: Single instance max capacity

### Horizontal Scaling
- API servers: Add more instances behind load balancer
- Workers: Add more GPU nodes
- Database: Add read replicas (for queries)
- Redis: Cluster mode (if needed)

**Implementation**:
- Kubernetes HPA (CPU-based autoscaling)
- AWS Auto Scaling Groups
- Load balancer health checks

### Geographic Scaling
- Multi-region deployments
- Edge locations for uploads
- CDN for serving crops
- Latency-based routing

## Performance Tuning

### Database Optimization
```sql
-- Index for common queries
CREATE INDEX idx_events_camera_captured ON events(camera_id, captured_at DESC);
CREATE INDEX idx_events_plate_search ON events(normalized_plate, captured_at DESC);

-- Vacuum regularly
VACUUM ANALYZE events;

-- Partition large tables
CREATE TABLE events_2024_01 PARTITION OF events
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Worker Optimization
- Batch database inserts (50-100 events at once)
- Use connection pooling
- Local SSD cache for videos
- Async crop uploads

### API Optimization
- Redis caching for frequent queries
- Database query result caching
- Connection pooling (50-100 connections)
- Async endpoints where possible

## Troubleshooting

See `README.md` for common issues. Additional production issues:

### High Queue Backlog
1. Check worker health: `docker ps | grep worker`
2. Check GPU availability: `nvidia-smi`
3. Scale workers horizontally
4. Check for stuck jobs (> 1 hour)

### Database Slowdown
1. Check connection count: `SELECT count(*) FROM pg_stat_activity;`
2. Find slow queries: `SELECT * FROM pg_stat_statements ORDER BY total_time DESC;`
3. Check for table bloat: `SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;`
4. Run VACUUM ANALYZE

### High Storage Costs
1. Implement lifecycle policies
2. Compress old videos
3. Delete raw videos after processing
4. Archive to glacier storage

---

**Questions? See DEVELOPER_HANDOFF.md or contact infrastructure team.**
