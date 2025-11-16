# Development Checklist

Tasks for completing and enhancing the ANPR City API.

## Immediate Tasks (Week 1)

### Detector Integration
- [ ] Replace stub in `src/detectors/yolo_easyocr_adapter.py` with actual YOLO model
- [ ] Add EasyOCR integration for plate text extraction
- [ ] Test detector on sample videos and verify accuracy
- [ ] Add confidence threshold tuning
- [ ] Implement plate deduplication logic (same plate in consecutive frames)

### Storage & Infrastructure
- [ ] Test Supabase storage integration end-to-end
- [ ] Verify MinIO bucket creation and access
- [ ] Configure CORS for storage buckets
- [ ] Set up signed URL generation for crop images
- [ ] Add storage quota monitoring

### Testing
- [ ] Add integration tests for upload → detection → event workflow
- [ ] Add tests for BOLO matching logic
- [ ] Test correction workflow and export generation
- [ ] Load test with multiple concurrent uploads
- [ ] Verify worker can handle job failures gracefully

## Near-term Enhancements (Weeks 2-3)

### Features
- [ ] Implement export worker for labeled dataset generation (ZIP creation)
- [ ] Add email notification support for BOLO matches
- [ ] Add webhook retry logic with exponential backoff
- [ ] Implement plate deduplication across short time windows
- [ ] Add camera health monitoring (RTSP stream checks)
- [ ] Implement rate limiting on API endpoints
- [ ] Add pagination for large result sets

### Security
- [ ] Implement API key authentication (alternative to JWT)
- [ ] Add IP whitelisting for admin endpoints
- [ ] Implement audit log cleanup/archival strategy
- [ ] Add input validation and sanitization everywhere
- [ ] Implement CSRF protection (if web UI added)
- [ ] Add SQL injection prevention audit

### Performance
- [ ] Add Redis caching for frequently accessed data
- [ ] Optimize database queries (add composite indexes)
- [ ] Implement connection pooling tuning
- [ ] Add batch processing for events (reduce DB roundtrips)
- [ ] Profile detector performance and optimize bottlenecks

## Medium-term Goals (Month 2)

### Advanced Features
- [ ] Implement live RTSP stream processing (not just uploads)
- [ ] Add vehicle make/model detection (optional)
- [ ] Implement geographic search (find events near location)
- [ ] Add time-series analytics dashboard
- [ ] Implement automatic model retraining pipeline
- [ ] Add A/B testing for detector models

### Integration
- [ ] Add Stripe integration for licensing/payments
- [ ] Implement SMTP provider for email notifications (SendGrid/Mailgun)
- [ ] Add Slack integration for BOLO alerts
- [ ] Implement Datadog/New Relic APM integration
- [ ] Add Sentry error tracking

### DevOps
- [ ] Create Helm chart for Kubernetes deployment
- [ ] Add Terraform configurations for AWS/GCP/Azure
- [ ] Implement blue-green deployment strategy
- [ ] Set up automated database backups
- [ ] Create runbooks for common incidents
- [ ] Add auto-scaling policies for workers

## Long-term Roadmap (Months 3-6)

### Scalability
- [ ] Implement horizontal scaling for API servers
- [ ] Add database read replicas for analytics queries
- [ ] Implement distributed tracing (Jaeger/Zipkin)
- [ ] Add message queue alternatives (RabbitMQ/Kafka)
- [ ] Optimize storage with tiered archival (S3 → Glacier)

### Machine Learning
- [ ] Implement active learning pipeline
- [ ] Add model versioning and A/B testing
- [ ] Build confidence calibration system
- [ ] Implement anomaly detection for suspicious patterns
- [ ] Add automated quality metrics tracking

### Compliance & Governance
- [ ] Implement GDPR compliance (data export/deletion)
- [ ] Add data retention policies automation
- [ ] Implement encryption at rest
- [ ] Add compliance reporting dashboard
- [ ] Implement role-based data access controls

## Technical Debt

### Code Quality
- [ ] Increase test coverage to >80%
- [ ] Add type hints to all functions
- [ ] Refactor large functions (>50 lines)
- [ ] Document all public APIs with docstrings
- [ ] Add OpenAPI examples for all endpoints

### Documentation
- [ ] Create architecture decision records (ADRs)
- [ ] Write deployment guide for each cloud provider
- [ ] Create troubleshooting playbooks
- [ ] Add video tutorials for common workflows
- [ ] Document API rate limits and quotas

### Dependencies
- [ ] Audit and update all dependencies
- [ ] Add Dependabot for automated updates
- [ ] Remove unused dependencies
- [ ] Pin all dependency versions
- [ ] Add security scanning (Snyk/Trivy)

## Performance Benchmarks

Target metrics to achieve:

- **API Latency**: p95 < 200ms, p99 < 500ms
- **Upload Processing**: < 2x realtime (10min video in <20min)
- **Detection Throughput**: 30+ FPS per GPU
- **Database Queries**: < 100ms for simple queries
- **Queue Processing**: < 5 second delay from enqueue to start
- **System Uptime**: 99.9% (8.76 hours downtime/year)

## Known Issues

1. **Worker Crash on Large Videos**: Need to add memory limits and chunking
2. **BOLO Pattern Matching**: Only supports basic regex, needs fuzzy matching
3. **Export Generation**: Synchronous and blocks, needs async worker
4. **Storage Cleanup**: No automated cleanup of old uploads/crops
5. **License Validation**: No online validation endpoint implemented

## Resources Needed

- **GPU Instances**: For production detector workload
- **CDN**: For serving crop images at scale
- **Redis Cluster**: For high-availability queue
- **S3/GCS**: For cost-effective long-term storage
- **Monitoring**: Prometheus + Grafana stack

## Questions for Product Team

1. What is the target number of cameras per deployment?
2. What is the expected video retention period?
3. Are there specific compliance requirements (GDPR, CCPA, etc.)?
4. What is the priority: accuracy vs. throughput?
5. Do we need real-time processing or is batch OK?
6. What is the budget for infrastructure?

---

Last Updated: 2024-01-01
Maintainer: Engineering Team
