#!/usr/bin/env python3
"""
Resource Analysis: Threading vs Multi-Processing Architecture
Compare resource usage for 38 concurrent users
"""

from dataclasses import dataclass
from typing import Dict, List
import json


@dataclass
class ResourceProfile:
    """Resource usage profile for an architecture"""

    architecture: str
    users: int
    processes: int
    threads: int
    memory_mb: float
    cpu_cores_needed: float
    context_switches: int
    overhead_mb: float

    def to_dict(self):
        return {
            "architecture": self.architecture,
            "users": self.users,
            "processes": self.processes,
            "threads": self.threads,
            "memory_mb": round(self.memory_mb, 1),
            "cpu_cores_needed": round(self.cpu_cores_needed, 2),
            "context_switches": self.context_switches,
            "overhead_mb": round(self.overhead_mb, 1),
            "efficiency_score": round(self.calculate_efficiency(), 2),
        }

    def calculate_efficiency(self) -> float:
        """Calculate efficiency score (higher is better)"""
        # Efficiency = useful work / total resources
        useful_work = self.users * 100  # Assume 100 units of work per user
        total_resources = self.memory_mb + (self.cpu_cores_needed * 500) + self.overhead_mb
        return useful_work / total_resources if total_resources > 0 else 0


class ResourceAnalyzer:
    """Analyze and compare different architectures"""

    def __init__(self):
        # Base resource costs
        self.PROCESS_BASE_MEMORY = 25  # MB per Python process
        self.THREAD_BASE_MEMORY = 8  # MB per thread (stack space)
        self.SERVER_BASE_MEMORY = 800  # MB for main server process

        self.PROCESS_CPU_OVERHEAD = 0.02  # CPU cost per process
        self.THREAD_CPU_OVERHEAD = 0.005  # CPU cost per thread
        self.CONTEXT_SWITCH_COST = 0.001  # CPU cost per context switch

        # Usage patterns
        self.ACTIVE_USAGE_PERCENT = 0.7  # 70% of threads/processes active at peak
        self.MEMORY_FRAGMENTATION = 1.2  # 20% memory fragmentation overhead

    def analyze_multiprocess_architecture(self, users: int) -> ResourceProfile:
        """Analyze current multi-process architecture"""

        # Each user can have: 1 script + 1 REPL + 1 file operation = 3 processes
        processes_per_user = 3
        total_processes = users * processes_per_user + 1  # +1 for server

        # Memory calculation
        server_memory = self.SERVER_BASE_MEMORY
        user_processes_memory = (total_processes - 1) * self.PROCESS_BASE_MEMORY
        total_memory = (server_memory + user_processes_memory) * self.MEMORY_FRAGMENTATION

        # CPU calculation
        active_processes = int((total_processes - 1) * self.ACTIVE_USAGE_PERCENT) + 1
        cpu_needed = (
            active_processes * self.PROCESS_CPU_OVERHEAD + active_processes * 0.15  # Assume 15% CPU per active process
        )

        # Context switches (process switches are expensive)
        context_switches = active_processes * 100  # Frequent process context switches

        return ResourceProfile(
            architecture="Multi-Process",
            users=users,
            processes=total_processes,
            threads=0,  # No explicit threading
            memory_mb=total_memory,
            cpu_cores_needed=cpu_needed,
            context_switches=context_switches,
            overhead_mb=user_processes_memory * 0.3,  # 30% overhead from process isolation
        )

    def analyze_threading_architecture(self, users: int) -> ResourceProfile:
        """Analyze proposed thread-based architecture"""

        # Each user has 1 process with multiple threads
        processes_per_user = 1  # Single Python interpreter per user
        threads_per_user = 5  # script + REPL + 3 file operations as threads

        total_processes = users * processes_per_user + 1  # +1 for server
        total_threads = users * threads_per_user

        # Memory calculation
        server_memory = self.SERVER_BASE_MEMORY
        user_processes_memory = users * self.PROCESS_BASE_MEMORY  # One process per user
        user_threads_memory = total_threads * self.THREAD_BASE_MEMORY
        total_memory = (server_memory + user_processes_memory + user_threads_memory) * 1.1  # Less fragmentation

        # CPU calculation
        active_threads = int(total_threads * self.ACTIVE_USAGE_PERCENT)
        cpu_needed = (
            total_processes * self.PROCESS_CPU_OVERHEAD
            + active_threads * self.THREAD_CPU_OVERHEAD
            + active_threads * 0.08  # Assume 8% CPU per active thread
        )

        # Context switches (thread switches are cheaper)
        context_switches = active_threads * 50  # Less frequent, cheaper thread context switches

        return ResourceProfile(
            architecture="Single-Process Multi-Thread",
            users=users,
            processes=total_processes,
            threads=total_threads,
            memory_mb=total_memory,
            cpu_cores_needed=cpu_needed,
            context_switches=context_switches,
            overhead_mb=user_threads_memory * 0.1,  # 10% overhead from thread management
        )

    def analyze_hybrid_architecture(self, users: int) -> ResourceProfile:
        """Analyze hybrid approach: fewer processes, more threads"""

        # Group users: 2-3 users share 1 Python process with isolated threads
        users_per_process = 2
        processes_needed = (users + users_per_process - 1) // users_per_process
        threads_per_user = 3  # Reduced threads per user

        total_processes = processes_needed + 1  # +1 for server
        total_threads = users * threads_per_user

        # Memory calculation
        server_memory = self.SERVER_BASE_MEMORY
        user_processes_memory = processes_needed * self.PROCESS_BASE_MEMORY
        user_threads_memory = total_threads * self.THREAD_BASE_MEMORY
        total_memory = (server_memory + user_processes_memory + user_threads_memory) * 1.15

        # CPU calculation
        active_threads = int(total_threads * self.ACTIVE_USAGE_PERCENT)
        cpu_needed = (
            total_processes * self.PROCESS_CPU_OVERHEAD
            + active_threads * self.THREAD_CPU_OVERHEAD
            + active_threads * 0.10  # Slight overhead from shared processes
        )

        context_switches = active_threads * 75  # Medium context switch cost

        return ResourceProfile(
            architecture="Hybrid Process-Thread",
            users=users,
            processes=total_processes,
            threads=total_threads,
            memory_mb=total_memory,
            cpu_cores_needed=cpu_needed,
            context_switches=context_switches,
            overhead_mb=user_processes_memory * 0.2,
        )

    def compare_architectures(self, users: int) -> Dict:
        """Compare all architectures for given user count"""

        multiprocess = self.analyze_multiprocess_architecture(users)
        threading = self.analyze_threading_architecture(users)
        hybrid = self.analyze_hybrid_architecture(users)

        comparison = {
            "user_count": users,
            "architectures": {
                "multiprocess": multiprocess.to_dict(),
                "threading": threading.to_dict(),
                "hybrid": hybrid.to_dict(),
            },
            "resource_savings": self._calculate_savings(multiprocess, threading),
            "recommendations": self._get_recommendations(multiprocess, threading, hybrid),
        }

        return comparison

    def _calculate_savings(self, baseline: ResourceProfile, optimized: ResourceProfile) -> Dict:
        """Calculate resource savings from optimization"""

        memory_savings = baseline.memory_mb - optimized.memory_mb
        cpu_savings = baseline.cpu_cores_needed - optimized.cpu_cores_needed
        process_reduction = baseline.processes - optimized.processes

        memory_savings_percent = (memory_savings / baseline.memory_mb) * 100 if baseline.memory_mb > 0 else 0
        cpu_savings_percent = (cpu_savings / baseline.cpu_cores_needed) * 100 if baseline.cpu_cores_needed > 0 else 0

        return {
            "memory_mb_saved": round(memory_savings, 1),
            "memory_percent_saved": round(memory_savings_percent, 1),
            "cpu_cores_saved": round(cpu_savings, 2),
            "cpu_percent_saved": round(cpu_savings_percent, 1),
            "processes_reduced": process_reduction,
            "efficiency_improvement": round(optimized.calculate_efficiency() - baseline.calculate_efficiency(), 2),
        }

    def _get_recommendations(
        self, multiprocess: ResourceProfile, threading: ResourceProfile, hybrid: ResourceProfile
    ) -> List[str]:
        """Get architecture recommendations"""
        recommendations = []

        # Memory efficiency
        if threading.memory_mb < multiprocess.memory_mb:
            savings_mb = multiprocess.memory_mb - threading.memory_mb
            recommendations.append(
                f"Threading saves {savings_mb:.1f}MB memory ({((savings_mb/multiprocess.memory_mb)*100):.1f}%)"
            )

        # CPU efficiency
        if threading.cpu_cores_needed < multiprocess.cpu_cores_needed:
            cpu_savings = multiprocess.cpu_cores_needed - threading.cpu_cores_needed
            recommendations.append(f"Threading reduces CPU needs by {cpu_savings:.2f} cores")

        # Process count
        process_reduction = multiprocess.processes - threading.processes
        if process_reduction > 0:
            recommendations.append(
                f"Threading reduces processes from {multiprocess.processes} to {threading.processes}"
            )

        # Best architecture
        efficiencies = {
            "multiprocess": multiprocess.calculate_efficiency(),
            "threading": threading.calculate_efficiency(),
            "hybrid": hybrid.calculate_efficiency(),
        }

        best_arch = max(efficiencies, key=efficiencies.get)
        recommendations.append(f"Most efficient architecture: {best_arch} (score: {efficiencies[best_arch]:.2f})")

        return recommendations

    def capacity_analysis_for_current_hw(self) -> Dict:
        """Analyze capacity for current 1 vCPU, 4GB RAM setup"""

        current_limits = {"cpu_cores": 1.0, "memory_mb": 4096}

        results = {}

        for users in [10, 15, 20, 25, 30, 38]:
            comparison = self.compare_architectures(users)

            # Check if each architecture fits current hardware
            for arch_name, arch_data in comparison["architectures"].items():
                cpu_fits = arch_data["cpu_cores_needed"] <= current_limits["cpu_cores"]
                memory_fits = arch_data["memory_mb"] <= current_limits["memory_mb"]

                arch_data["fits_current_hw"] = cpu_fits and memory_fits
                arch_data["bottleneck"] = []

                if not cpu_fits:
                    arch_data["bottleneck"].append(
                        f"CPU: need {arch_data['cpu_cores_needed']:.2f}, have {current_limits['cpu_cores']}"
                    )
                if not memory_fits:
                    arch_data["bottleneck"].append(
                        f"Memory: need {arch_data['memory_mb']:.1f}MB, have {current_limits['memory_mb']}MB"
                    )

            results[f"{users}_users"] = comparison

        return results


# Run analysis
if __name__ == "__main__":
    analyzer = ResourceAnalyzer()

    print("🚀 Threading vs Multi-Processing Architecture Analysis")
    print("=" * 60)

    # Analyze for 38 users (your target)
    comparison = analyzer.compare_architectures(38)

    print(f"\n📊 Resource Comparison for {comparison['user_count']} Users:")
    print("-" * 50)

    for arch_name, arch_data in comparison["architectures"].items():
        print(f"\n{arch_data['architecture']}:")
        print(f"  Processes: {arch_data['processes']}")
        print(f"  Threads: {arch_data['threads']}")
        print(f"  Memory: {arch_data['memory_mb']}MB")
        print(f"  CPU Cores: {arch_data['cpu_cores_needed']}")
        print(f"  Efficiency Score: {arch_data['efficiency_score']}")

    print(f"\n💰 Resource Savings (Threading vs Multi-Process):")
    print("-" * 50)
    savings = comparison["resource_savings"]
    for key, value in savings.items():
        print(f"  {key}: {value}")

    print(f"\n🎯 Recommendations:")
    print("-" * 50)
    for rec in comparison["recommendations"]:
        print(f"  • {rec}")

    # Current hardware capacity analysis
    print(f"\n🖥️  Current Hardware Capacity (1 vCPU, 4GB RAM):")
    print("-" * 50)

    capacity_analysis = analyzer.capacity_analysis_for_current_hw()

    for user_scenario, data in capacity_analysis.items():
        users = data["user_count"]
        print(f"\n{users} Users:")

        for arch_name, arch_data in data["architectures"].items():
            status = "✅ Fits" if arch_data["fits_current_hw"] else "❌ Exceeds limits"
            bottleneck = f" ({', '.join(arch_data['bottleneck'])})" if arch_data["bottleneck"] else ""

            print(f"  {arch_data['architecture']}: {status}{bottleneck}")

    print(f"\n🏆 Summary for Your 38 Users:")
    print("-" * 50)

    target_analysis = capacity_analysis["38_users"]

    multiprocess_fits = target_analysis["architectures"]["multiprocess"]["fits_current_hw"]
    threading_fits = target_analysis["architectures"]["threading"]["fits_current_hw"]

    print(f"Current Multi-Process: {'✅ Works' if multiprocess_fits else '❌ Cannot handle 38 users'}")
    print(f"Proposed Threading: {'✅ Works' if threading_fits else '❌ Still needs upgrade'}")

    if threading_fits and not multiprocess_fits:
        print("🎉 Threading architecture enables 38 users on current hardware!")
    elif not threading_fits:
        threading_data = target_analysis["architectures"]["threading"]
        print(f"⚠️  Threading helps but still needs: {', '.join(threading_data['bottleneck'])}")
