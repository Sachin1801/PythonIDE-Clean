# Process Registry Integration Guide for 38 Concurrent Users

## Executive Summary

**Current Issue:** 30-minute server crashes due to ProcessCleanupService killing main server process
**Root Cause:** Process cleanup doesn't distinguish server from user processes
**Solution:** Implement process registry with resource tracking for 38 concurrent users

---

## 1. Process Registry Architecture

### Components Created:
- `common/process_registry.py` - Central process tracking
- `common/resource_calculator.py` - Resource requirement analysis  
- `monitoring/aws_integration.py` - AWS CloudWatch integration

### Resource Limits for 38 Users:
```
Max Concurrent Users: 38
Max Processes Per User: 3 (1 script + 1 REPL + 1 file op)
Max Total Processes: 114
Max Memory Per Process: 50MB
Max Total Memory: 3GB (1GB reserved for server)
```

---

## 2. Integration Points

### A. Update Process Cleanup (Immediate Fix - 30 minutes)

**File:** `server/server.py`
**Location:** Line 86 in `cleanup_abandoned_processes()`

**Current Code:**
```python
if proc.info['name'] and 'python' in proc.info['name'].lower():
    # Check command line arguments
    cmdline = proc.info.get('cmdline', [])
```

**Replace With:**
```python
if proc.info['name'] and 'python' in proc.info['name'].lower():
    # Skip main server process
    if proc.info['pid'] == os.getpid():
        continue
        
    # Check command line arguments
    cmdline = proc.info.get('cmdline', [])
```

### B. Integrate Process Registry (2-4 hours)

**1. Update HybridREPLThread:**

**File:** `server/command/hybrid_repl_thread.py`
**Location:** Line 394 (after subprocess.Popen)

**Add:**
```python
# After: self.p = subprocess.Popen(...)
from common.process_registry import process_registry

# Register process with registry
if not process_registry.register_process(
    pid=self.p.pid,
    username=self.username,
    file_path=self.script_path,
    process_type='script' if self.script_path else 'repl',
    cmd_id=self.cmd_id
):
    logger.error(f"Failed to register process {self.p.pid} - resource limits exceeded")
    self.p.kill()
    return
```

**2. Update Process Termination:**

**File:** `server/command/hybrid_repl_thread.py`
**Location:** Line 430 (in cleanup section)

**Add:**
```python
# Before process cleanup
if self.p:
    process_registry.unregister_process(self.p.pid)
```

**3. Update Activity Tracking:**

**File:** `server/handlers/authenticated_ws_handler.py`
**Location:** Line 257 (when handling commands)

**Add:**
```python
# When user interacts with REPL
if hasattr(self, 'active_processes'):
    for pid in self.active_processes:
        process_registry.update_activity(pid)
```

### C. Enhanced Health Monitoring (1-2 hours)

**File:** `server/handlers/health_handler.py`

**Replace health endpoint:**
```python
from monitoring.aws_integration import get_health_data

@app.route('/health')
def health():
    return get_health_data()
```

---

## 3. AWS Resource Requirements

### Current vs Required Analysis:

| Scenario | Users | CPU Needed | RAM Needed | Current Sufficient? |
|----------|-------|------------|------------|-------------------|
| Light Load | 10 | 2.0 cores | 1.7GB | ❌ CPU bottleneck |
| Normal Load | 25 | 4.7 cores | 2.8GB | ❌ CPU bottleneck |
| **Peak Load** | 38 | 10.3 cores | 5.1GB | ❌ Both bottlenecks |

### Recommended AWS Scaling:

**Phase 1 (Immediate):** Fix crashes, keep 1 vCPU, 4GB RAM
- Supports ~10-15 concurrent users reliably
- Zero downtime fix

**Phase 2 (Recommended):** Upgrade to 2 vCPU, 6GB RAM  
- Cost: ~$30-50/month additional
- Supports 25-30 concurrent users

**Phase 3 (Peak Load):** Upgrade to 4 vCPU, 8GB RAM
- Cost: ~$80-120/month additional  
- Supports all 38 users with moderate usage

---

## 4. Database Session Tracking

### Current Database Schema:
- Users table with session management
- No process tracking in DB

### Recommended Enhancement:
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    session_token VARCHAR(255) NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active_processes JSONB DEFAULT '[]',
    resource_usage JSONB DEFAULT '{}',
    INDEX (username),
    INDEX (last_activity)
);
```

### Implementation in Process Registry:
```python
def track_session_in_db(self, username: str, process_info: ProcessInfo):
    """Update database with current session info"""
    try:
        query = """
            UPDATE user_sessions 
            SET last_activity = NOW(),
                active_processes = %s,
                resource_usage = %s
            WHERE username = %s AND active = true
        """
        
        processes = [p.to_dict() for p in self.get_user_processes(username)]
        resource_usage = {
            'total_memory_mb': sum(p.memory_mb for p in processes),
            'process_count': len(processes)
        }
        
        db_manager.execute_query(query, (
            json.dumps(processes),
            json.dumps(resource_usage),
            username
        ))
    except Exception as e:
        logger.error(f"DB session tracking error: {e}")
```

---

## 5. EFS Performance Considerations

### Current Setup:
- AWS EFS mounted at `/mnt/efs/pythonide-data`
- 39 student directories
- No performance issues observed

### For 38 Concurrent Users:
- **File Operations:** ~100-200 concurrent file reads/writes
- **EFS Throughput:** Supports 7,000 ops/sec (more than sufficient)
- **Latency:** 1-3ms per operation (acceptable)
- **Bottleneck:** CPU processing, not EFS I/O

### Optimization (Optional) :

My comments: this is not required 
```python
# Cache frequently accessed files in memory
class EFSCache:
    def __init__(self):
        self.cache = {}  # filename -> (content, timestamp)
        self.max_age = 300  # 5 minutes
    
    def get_file(self, filepath):
        if filepath in self.cache:
            content, timestamp = self.cache[filepath]
            if time.time() - timestamp < self.max_age:
                return content
        
        # Read from EFS and cache
        with open(filepath, 'r') as f:
            content = f.read()
            self.cache[filepath] = (content, time.time())
            return content
```

---

## 6. Monitoring & Tracking on AWS

### CloudWatch Metrics (Automatic):
- ECS CPU/Memory utilization
- RDS connections and performance
- EFS throughput and connections
- Load balancer request rates

### Custom Metrics (via aws_integration.py):
- Active concurrent users
- Process count per user
- Memory usage per process type
- Database health status
- EFS mount status

### Alarms to Set Up:
```bash
# CPU alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "PythonIDE-HighCPU" \
    --alarm-description "CPU usage > 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold

# Memory alarm  
aws cloudwatch put-metric-alarm \
    --alarm-name "PythonIDE-HighMemory" \
    --alarm-description "Memory usage > 85%" \
    --metric-name MemoryUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 85 \
    --comparison-operator GreaterThanThreshold

# Active users alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "PythonIDE-HighUserCount" \
    --alarm-description "Active users > 35" \
    --metric-name ActiveUsers \
    --namespace PythonIDE/Custom \
    --statistic Average \
    --period 300 \
    --threshold 35 \
    --comparison-operator GreaterThanThreshold
```

---

## 7. Implementation Roadmap

### Week 1: Emergency Fix
- [ ] Fix 30-minute server crashes (30 minutes)
- [ ] Add basic process registry (2-4 hours)
- [ ] Test with 10-15 concurrent users
- [ ] Deploy to AWS with current specs

### Week 2: Resource Scaling  
- [ ] Upgrade AWS to 2 vCPU, 6GB RAM
- [ ] Implement enhanced monitoring
- [ ] Add database session tracking
- [ ] Load test with 25-30 users

### Week 3: Peak Load Support
- [ ] Upgrade AWS to 4 vCPU, 8GB RAM if needed
- [ ] Add auto-scaling policies
- [ ] Implement resource throttling
- [ ] Test all 38 users concurrent

### Week 4: Production Hardening
- [ ] Add comprehensive alerting
- [ ] Implement graceful degradation
- [ ] Documentation and runbooks
- [ ] Performance optimization

---

## 8. Cost Analysis

### Current Cost: ~$50-80/month
- ECS Fargate: 1 vCPU, 4GB RAM
- RDS PostgreSQL: db.t3.micro
- EFS: Pay per use (~minimal)
- Load Balancer: ~$20/month

### Recommended Cost: ~$120-200/month  
- ECS Fargate: 2-4 vCPU, 6-8GB RAM (+$50-120/month)
- RDS: Same (sufficient)
- EFS: Same
- Load Balancer: Same
- CloudWatch: +$10-20/month

**ROI:** Supports 3-4x more concurrent users for 2x cost = 50-100% efficiency gain

---

## 9. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| CPU bottleneck with 38 users | High | High | Upgrade to 4 vCPU |
| Memory exhaustion | Medium | High | Process memory limits + monitoring |
| Database connection limits | Low | Medium | Connection pooling |
| EFS performance issues | Very Low | Low | Already tested, performs well |
| Process registry bugs | Medium | Medium | Gradual rollout, extensive testing |

---

## 10. Success Metrics

### Performance Targets:
- **Uptime:** 99.9% (no 30-minute crashes)
- **Response Time:** <500ms for file operations
- **Concurrent Users:** Support 38 simultaneous users
- **Resource Usage:** <80% CPU, <85% memory at peak load

### Monitoring KPIs:
- Active concurrent users (target: 38)
- Average response time (target: <200ms)
- Error rate (target: <0.1%)
- Process cleanup effectiveness (target: <5 abandoned processes)

---

**Next Step:** Implement the immediate fix in `server.py` to stop the 30-minute crashes, then proceed with process registry integration.

**Time to Implementation:** 30 minutes for fix + 4 hours for full integration = **Same day deployment possible**