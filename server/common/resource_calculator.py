#!/usr/bin/env python3
"""
Resource Calculator for 38 concurrent users on AWS
Calculates optimal resource allocation and scaling requirements
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class ResourceRequirements:
    """Resource requirements calculation"""
    users: int
    cpu_cores: float
    memory_gb: float
    storage_gb: float
    processes: int
    
    def to_ecs_spec(self) -> Dict:
        """Convert to ECS Fargate specifications"""
        # ECS Fargate CPU/Memory combinations
        cpu_options = [0.25, 0.5, 1, 2, 4, 8, 16]
        
        # Find minimum CPU that meets requirement
        min_cpu = next(cpu for cpu in cpu_options if cpu >= self.cpu_cores)
        
        # Memory options for each CPU
        memory_options = {
            0.25: [0.5, 1, 2],           # 0.25 vCPU: 0.5-2 GB
            0.5: [1, 2, 3, 4],           # 0.5 vCPU: 1-4 GB
            1: [2, 3, 4, 5, 6, 7, 8],    # 1 vCPU: 2-8 GB
            2: list(range(4, 17)),       # 2 vCPU: 4-16 GB
            4: list(range(8, 31)),       # 4 vCPU: 8-30 GB
            8: list(range(16, 61)),      # 8 vCPU: 16-60 GB
            16: list(range(32, 121))     # 16 vCPU: 32-120 GB
        }
        
        # Find minimum memory that meets requirement
        available_memory = memory_options[min_cpu]
        min_memory_gb = next(mem for mem in available_memory if mem >= self.memory_gb)
        
        return {
            'cpu': int(min_cpu * 1024),  # Convert to CPU units (1 vCPU = 1024 units)
            'memory': int(min_memory_gb * 1024),  # Convert to MiB
            'cpu_readable': f"{min_cpu} vCPU",
            'memory_readable': f"{min_memory_gb} GB"
        }

class ResourceCalculator:
    """Calculate resource requirements for different user loads"""
    
    def __init__(self):
        # Base resource requirements per process type
        self.PROCESS_MEMORY_MB = {
            'server': 800,      # Main server process
            'script': 30,       # Script execution
            'repl': 40,         # REPL session
            'interactive': 20   # File operations
        }
        
        self.PROCESS_CPU_PERCENT = {
            'server': 15,       # Main server baseline
            'script': 8,        # Active script execution
            'repl': 3,          # REPL session (mostly idle)
            'interactive': 2    # File operations
        }
        
        # Storage requirements
        self.STORAGE_PER_USER_MB = 50   # Average per student directory
        self.BASE_STORAGE_GB = 2        # System files, logs, cache
        
    def calculate_for_users(self, concurrent_users: int, 
                           processes_per_user: int = 3) -> ResourceRequirements:
        """Calculate resource requirements for concurrent users"""
        
        total_processes = concurrent_users * processes_per_user
        
        # Memory calculation
        server_memory_mb = self.PROCESS_MEMORY_MB['server']
        
        # Assume mixed workload: 50% scripts, 30% REPL, 20% interactive
        script_processes = int(total_processes * 0.5)
        repl_processes = int(total_processes * 0.3)
        interactive_processes = total_processes - script_processes - repl_processes
        
        user_memory_mb = (
            script_processes * self.PROCESS_MEMORY_MB['script'] +
            repl_processes * self.PROCESS_MEMORY_MB['repl'] +
            interactive_processes * self.PROCESS_MEMORY_MB['interactive']
        )
        
        total_memory_gb = (server_memory_mb + user_memory_mb) / 1024
        # Add 20% buffer
        total_memory_gb *= 1.2
        
        # CPU calculation (assuming processes time-slice)
        server_cpu = self.PROCESS_CPU_PERCENT['server'] / 100
        
        user_cpu = (
            script_processes * self.PROCESS_CPU_PERCENT['script'] / 100 +
            repl_processes * self.PROCESS_CPU_PERCENT['repl'] / 100 +
            interactive_processes * self.PROCESS_CPU_PERCENT['interactive'] / 100
        )
        
        # CPU requirement is peak usage / time-slicing efficiency (assume 60%)
        total_cpu_cores = (server_cpu + user_cpu) / 0.6
        
        # Storage calculation
        user_storage_gb = (concurrent_users * self.STORAGE_PER_USER_MB) / 1024
        total_storage_gb = self.BASE_STORAGE_GB + user_storage_gb
        
        return ResourceRequirements(
            users=concurrent_users,
            cpu_cores=total_cpu_cores,
            memory_gb=total_memory_gb,
            storage_gb=total_storage_gb,
            processes=total_processes
        )
    
    def analyze_current_vs_required(self) -> Dict:
        """Compare current AWS setup vs requirements for 38 users"""
        
        current_spec = {
            'cpu_cores': 1.0,
            'memory_gb': 4.0,
            'storage_gb': 20.0  # EFS is unlimited, but this is working set
        }
        
        # Calculate for different scenarios
        scenarios = {
            'light_load': self.calculate_for_users(10, 2),  # 10 users, 2 processes each
            'normal_load': self.calculate_for_users(25, 2), # 25 users, 2 processes each
            'peak_load': self.calculate_for_users(38, 3),   # All 38 users, 3 processes each
            'stress_test': self.calculate_for_users(38, 4)  # Stress test scenario
        }
        
        analysis = {
            'current_specification': current_spec,
            'scenarios': {}
        }
        
        for scenario_name, requirements in scenarios.items():
            ecs_spec = requirements.to_ecs_spec()
            
            # Determine if current spec is sufficient
            cpu_sufficient = current_spec['cpu_cores'] >= requirements.cpu_cores
            memory_sufficient = current_spec['memory_gb'] >= requirements.memory_gb
            
            analysis['scenarios'][scenario_name] = {
                'requirements': {
                    'cpu_cores': round(requirements.cpu_cores, 2),
                    'memory_gb': round(requirements.memory_gb, 2),
                    'storage_gb': round(requirements.storage_gb, 2),
                    'processes': requirements.processes
                },
                'recommended_ecs_spec': ecs_spec,
                'current_sufficient': cpu_sufficient and memory_sufficient,
                'bottlenecks': []
            }
            
            # Identify bottlenecks
            if not cpu_sufficient:
                analysis['scenarios'][scenario_name]['bottlenecks'].append(
                    f"CPU: need {requirements.cpu_cores:.1f} cores, have {current_spec['cpu_cores']}"
                )
            
            if not memory_sufficient:
                analysis['scenarios'][scenario_name]['bottlenecks'].append(
                    f"Memory: need {requirements.memory_gb:.1f}GB, have {current_spec['memory_gb']}GB"
                )
        
        return analysis
    
    def get_scaling_recommendations(self) -> List[Dict]:
        """Get step-by-step scaling recommendations"""
        
        return [
            {
                'phase': 'Immediate Fix',
                'description': 'Fix 30-minute server crashes',
                'changes': ['Update ProcessCleanupService to exclude main server process'],
                'ecs_spec': 'Keep current: 1 vCPU, 4GB RAM',
                'supported_users': '~25 concurrent users',
                'risk': 'Low',
                'effort': '30 minutes'
            },
            {
                'phase': 'Resource Optimization',
                'description': 'Optimize for 38 users with light usage',
                'changes': [
                    'Implement process registry',
                    'Add memory limits per process',
                    'Optimize cleanup intervals'
                ],
                'ecs_spec': 'Upgrade to: 2 vCPU, 6GB RAM',
                'supported_users': '38 concurrent users (light load)',
                'risk': 'Low',
                'effort': '2-4 hours'
            },
            {
                'phase': 'Peak Load Support',
                'description': 'Handle all 38 users with heavy usage',
                'changes': [
                    'Implement resource throttling',
                    'Add database session tracking',
                    'Enhanced monitoring'
                ],
                'ecs_spec': 'Upgrade to: 2 vCPU, 8GB RAM',
                'supported_users': '38 concurrent users (peak load)',
                'risk': 'Medium',
                'effort': '1-2 days'
            },
            {
                'phase': 'Production Hardening',
                'description': 'Bulletproof system for educational use',
                'changes': [
                    'Auto-scaling based on load',
                    'Circuit breakers for overload',
                    'Comprehensive monitoring',
                    'Database connection pooling optimization'
                ],
                'ecs_spec': 'Auto-scale: 2-4 vCPU, 8-16GB RAM',
                'supported_users': '50+ concurrent users',
                'risk': 'Medium',
                'effort': '3-5 days'
            }
        ]

# Create calculator instance for analysis
calculator = ResourceCalculator()

if __name__ == "__main__":
    # Run analysis
    analysis = calculator.analyze_current_vs_required()
    
    print("=== AWS Resource Analysis for 38 Concurrent Users ===\n")
    
    for scenario, data in analysis['scenarios'].items():
        print(f"📊 {scenario.replace('_', ' ').title()}:")
        print(f"  Requirements: {data['requirements']['cpu_cores']} CPU, {data['requirements']['memory_gb']:.1f}GB RAM")
        print(f"  Recommended ECS: {data['recommended_ecs_spec']['cpu_readable']}, {data['recommended_ecs_spec']['memory_readable']}")
        print(f"  Current sufficient: {'✅ Yes' if data['current_sufficient'] else '❌ No'}")
        
        if data['bottlenecks']:
            print(f"  Bottlenecks: {', '.join(data['bottlenecks'])}")
        print()
    
    print("=== Scaling Recommendations ===\n")
    recommendations = calculator.get_scaling_recommendations()
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['phase']}")
        print(f"   {rec['description']}")
        print(f"   ECS Spec: {rec['ecs_spec']}")
        print(f"   Capacity: {rec['supported_users']}")
        print(f"   Effort: {rec['effort']} | Risk: {rec['risk']}")
        print()