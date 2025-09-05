#!/bin/bash

# Debug URL Access Issues
# Help diagnose why the deployment URL works on some devices but not others

echo "🔍 Debugging PythonIDE URL Access Issues"
echo "======================================="

URL="http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com"
DOMAIN="pythonide-alb-456687384.us-east-2.elb.amazonaws.com"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

echo ""
echo "Testing URL: $URL"
echo "Domain: $DOMAIN"
echo ""

# Test 1: Basic HTTP connectivity
echo "🌐 Test 1: Basic HTTP Connectivity"
echo "--------------------------------"

HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$URL" 2>/dev/null)
if [ "$HTTP_RESPONSE" = "200" ] || [ "$HTTP_RESPONSE" = "405" ] || [ "$HTTP_RESPONSE" = "302" ]; then
    print_status "HTTP connection successful (Code: $HTTP_RESPONSE)"
    HTTP_WORKS=true
else
    print_error "HTTP connection failed (Code: $HTTP_RESPONSE)"
    HTTP_WORKS=false
fi

# Test 2: DNS Resolution
echo ""
echo "🔍 Test 2: DNS Resolution"
echo "------------------------"

# Try to resolve IP addresses
IP_ADDRESSES=$(getent hosts "$DOMAIN" 2>/dev/null | awk '{print $1}' | sort -u)
if [ -n "$IP_ADDRESSES" ]; then
    print_status "DNS resolution successful:"
    echo "$IP_ADDRESSES" | while read ip; do
        echo "  → $ip"
    done
    DNS_WORKS=true
else
    print_error "DNS resolution failed"
    DNS_WORKS=false
fi

# Test 3: Direct IP Access (if DNS worked)
if [ "$DNS_WORKS" = true ]; then
    echo ""
    echo "🎯 Test 3: Direct IP Access"
    echo "---------------------------"
    
    FIRST_IP=$(echo "$IP_ADDRESSES" | head -n1)
    print_info "Testing direct access to IP: $FIRST_IP"
    
    IP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "http://$FIRST_IP" -H "Host: $DOMAIN" 2>/dev/null)
    if [ "$IP_RESPONSE" = "200" ] || [ "$IP_RESPONSE" = "405" ] || [ "$IP_RESPONSE" = "302" ]; then
        print_status "Direct IP access works (Code: $IP_RESPONSE)"
        IP_WORKS=true
    else
        print_error "Direct IP access failed (Code: $IP_RESPONSE)"
        IP_WORKS=false
    fi
fi

# Test 4: Port Connectivity
echo ""
echo "🔌 Test 4: Port Connectivity"
echo "----------------------------"

if command -v nc >/dev/null 2>&1; then
    if echo "" | timeout 5 nc -w 3 "$DOMAIN" 80 2>/dev/null; then
        print_status "Port 80 is reachable"
        PORT_80_WORKS=true
    else
        print_error "Port 80 is not reachable"
        PORT_80_WORKS=false
    fi
else
    print_warning "netcat (nc) not available - skipping port test"
fi

# Test 5: Load Balancer Health Check
echo ""
echo "❤️  Test 5: Load Balancer Status"
echo "-------------------------------"

print_info "Checking AWS Load Balancer status..."

# Check if AWS CLI is configured
if aws sts get-caller-identity >/dev/null 2>&1; then
    LB_STATE=$(aws elbv2 describe-load-balancers \
        --load-balancer-arns "arn:aws:elasticloadbalancing:us-east-2:653306034507:loadbalancer/app/pythonide-alb/2dcd02db57a7616c" \
        --query 'LoadBalancers[0].State.Code' \
        --output text --region us-east-2 2>/dev/null)
    
    if [ "$LB_STATE" = "active" ]; then
        print_status "Load Balancer status: active"
        LB_HEALTHY=true
    else
        print_error "Load Balancer status: $LB_STATE"
        LB_HEALTHY=false
    fi
    
    # Check target health
    TARGET_HEALTH=$(aws elbv2 describe-target-health \
        --target-group-arn "arn:aws:elasticloadbalancing:us-east-2:653306034507:targetgroup/pythonide-targets/7ecb2c257c437e2e" \
        --query 'TargetHealthDescriptions[0].TargetHealth.State' \
        --output text --region us-east-2 2>/dev/null)
    
    if [ "$TARGET_HEALTH" = "healthy" ]; then
        print_status "Target health: healthy"
        TARGET_HEALTHY=true
    else
        print_error "Target health: $TARGET_HEALTH"
        TARGET_HEALTHY=false
    fi
else
    print_warning "AWS CLI not configured - skipping AWS checks"
fi

# Test 6: Traceroute (if available)
echo ""
echo "🛤️  Test 6: Network Path"
echo "----------------------"

if command -v traceroute >/dev/null 2>&1; then
    print_info "Tracing network path (first 5 hops)..."
    timeout 15 traceroute -m 5 "$DOMAIN" 2>/dev/null | head -n 8
elif command -v mtr >/dev/null 2>&1; then
    print_info "Using MTR for network path analysis..."
    timeout 10 mtr -r -c 3 "$DOMAIN" 2>/dev/null
else
    print_warning "No traceroute tools available"
fi

# Summary and Recommendations
echo ""
echo "📋 DIAGNOSIS SUMMARY"
echo "==================="
echo ""

if [ "$HTTP_WORKS" = true ] && [ "$DNS_WORKS" = true ]; then
    print_status "✅ URL is accessible from this location"
    echo ""
    print_info "If the URL doesn't work on your other laptop, the issue might be:"
    echo ""
    echo "🏠 Network-related issues:"
    echo "  • Different WiFi network with restrictions"
    echo "  • Corporate firewall blocking AWS domains"
    echo "  • ISP-level blocking or filtering"
    echo "  • VPN interfering with connections"
    echo ""
    echo "💻 Device-related issues:"
    echo "  • DNS settings (try 8.8.8.8, 1.1.1.1)"
    echo "  • Browser cache/cookies"
    echo "  • Antivirus/security software blocking"
    echo "  • Proxy settings"
    echo ""
    echo "🔧 Troubleshooting steps for the other laptop:"
    echo "  1. Try different browsers"
    echo "  2. Clear browser cache and cookies"
    echo "  3. Try incognito/private mode"
    echo "  4. Check DNS settings"
    echo "  5. Disable VPN temporarily"
    echo "  6. Try mobile hotspot instead of WiFi"
    echo "  7. Test direct IP access: http://$FIRST_IP (add Host header)"
    
else
    print_error "❌ URL is not accessible from this location either"
    echo ""
    print_info "This suggests a server-side issue:"
    echo ""
    if [ "$DNS_WORKS" = false ]; then
        echo "  • DNS resolution problems"
    fi
    if [ "$LB_HEALTHY" = false ]; then
        echo "  • Load balancer is not healthy"
    fi
    if [ "$TARGET_HEALTHY" = false ]; then
        echo "  • ECS service is not healthy"
    fi
    echo ""
    echo "🔧 Server-side fixes needed:"
    echo "  1. Check ECS service status"
    echo "  2. Review load balancer configuration"
    echo "  3. Check target group health"
    echo "  4. Review security group rules"
fi

echo ""
echo "🌐 Alternative access methods:"
echo "  • Share the IP address: $FIRST_IP (if DNS is the issue)"
echo "  • Set up a custom domain with proper DNS"
echo "  • Use AWS CloudFront for better global access"

echo ""
print_status "Diagnosis complete!"