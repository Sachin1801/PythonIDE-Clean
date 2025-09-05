#!/bin/bash

# Setup pythonide-classroom.tech Domain
# Configure custom domain for PythonIDE AWS deployment

set -e

echo "🌐 Setting Up pythonide-classroom.tech for PythonIDE"
echo "===================================================="

# Configuration
DOMAIN="pythonide-classroom.tech"
REGION="us-east-2"
LOAD_BALANCER_ARN="arn:aws:elasticloadbalancing:us-east-2:653306034507:loadbalancer/app/pythonide-alb/2dcd02db57a7616c"
LOAD_BALANCER_DNS="pythonide-alb-456687384.us-east-2.elb.amazonaws.com"
TARGET_GROUP_ARN="arn:aws:elasticloadbalancing:us-east-2:653306034507:targetgroup/pythonide-targets/7ecb2c257c437e2e"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }

echo ""
echo "🎯 Target Setup:"
echo "  Domain: $DOMAIN"
echo "  Load Balancer: $LOAD_BALANCER_DNS"
echo "  Final URL: https://$DOMAIN"
echo ""

# Step 1: DNS Configuration
echo "📋 STEP 1: DNS Configuration"
echo "============================"
echo ""
print_info "You need to add DNS records for $DOMAIN"
echo ""
echo "🔧 DNS Records to Add:"
echo ""
echo "Record 1 - Main Domain (A Record or CNAME):"
echo "  Type: CNAME"
echo "  Name: @ (or blank for root domain)"
echo "  Value: $LOAD_BALANCER_DNS"
echo "  TTL: 300 (5 minutes)"
echo ""
echo "Record 2 - WWW Subdomain (Optional):"
echo "  Type: CNAME" 
echo "  Name: www"
echo "  Value: $LOAD_BALANCER_DNS"
echo "  TTL: 300"
echo ""

# Check where domain was registered
echo "🌍 Common Domain Management Locations:"
echo ""
echo "• GitHub Student Pack domains → Usually managed at:"
echo "  - Namecheap (most common)"
echo "  - Name.com"
echo "  - Check your GitHub Student Pack dashboard"
echo ""
echo "• Freenom domains → Freenom.com DNS Management"
echo "• Other registrars → Check your domain registrar's DNS panel"
echo ""

read -p "Have you added the DNS records? (y/n): " dns_added

if [[ ! $dns_added =~ ^[Yy]$ ]]; then
    print_warning "⏸️  Please add the DNS records first, then run this script again"
    echo ""
    echo "📋 Quick Guide:"
    echo "1. Log into your domain registrar"
    echo "2. Find DNS Management / DNS Records"
    echo "3. Add CNAME record: @ → $LOAD_BALANCER_DNS"
    echo "4. Save changes (may take 5-60 minutes to propagate)"
    echo "5. Test with: nslookup $DOMAIN"
    echo ""
    exit 0
fi

# Step 2: Test DNS Resolution
echo ""
echo "🔍 STEP 2: Testing DNS Resolution"
echo "================================="
echo ""

print_info "Testing DNS resolution for $DOMAIN..."

# Wait a moment for DNS to settle
sleep 2

# Test DNS resolution
DNS_RESULT=$(getent hosts "$DOMAIN" 2>/dev/null | awk '{print $1}' | head -n1)

if [ -n "$DNS_RESULT" ]; then
    print_status "DNS resolution successful: $DOMAIN → $DNS_RESULT"
    DNS_WORKING=true
    
    # Test if it resolves to our load balancer IPs
    LB_IPS=$(getent hosts "$LOAD_BALANCER_DNS" 2>/dev/null | awk '{print $1}' | sort)
    DOMAIN_IPS=$(getent hosts "$DOMAIN" 2>/dev/null | awk '{print $1}' | sort)
    
    if [ "$LB_IPS" = "$DOMAIN_IPS" ]; then
        print_status "Domain correctly points to load balancer!"
    else
        print_warning "Domain IPs don't match load balancer IPs yet (DNS propagation in progress)"
        echo "  Load Balancer IPs: $LB_IPS"
        echo "  Domain IPs: $DOMAIN_IPS"
    fi
else
    print_error "DNS resolution failed for $DOMAIN"
    print_warning "DNS propagation can take 5-60 minutes. Try again later."
    DNS_WORKING=false
fi

# Step 3: Test HTTP Access
if [ "$DNS_WORKING" = true ]; then
    echo ""
    echo "🌐 STEP 3: Testing HTTP Access"
    echo "=============================="
    echo ""
    
    HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "http://$DOMAIN" 2>/dev/null || echo "FAILED")
    
    if [ "$HTTP_RESPONSE" = "200" ] || [ "$HTTP_RESPONSE" = "405" ]; then
        print_status "HTTP access working: http://$DOMAIN (Code: $HTTP_RESPONSE)"
        HTTP_WORKING=true
    else
        print_error "HTTP access failed: $HTTP_RESPONSE"
        HTTP_WORKING=false
    fi
fi

# Step 4: SSL Certificate Setup
echo ""
echo "🔒 STEP 4: SSL Certificate Setup"
echo "================================"
echo ""

if [ "$DNS_WORKING" = true ] && [ "$HTTP_WORKING" = true ]; then
    print_info "Requesting SSL certificate for $DOMAIN..."
    
    # Request SSL certificate from AWS Certificate Manager
    CERT_ARN=$(aws acm request-certificate \
        --domain-name "$DOMAIN" \
        --subject-alternative-names "www.$DOMAIN" \
        --validation-method DNS \
        --region $REGION \
        --query 'CertificateArn' \
        --output text 2>/dev/null)
    
    if [ $? -eq 0 ] && [ "$CERT_ARN" != "None" ]; then
        print_status "SSL certificate requested successfully!"
        print_info "Certificate ARN: $CERT_ARN"
        echo ""
        
        # Save certificate ARN
        echo "$CERT_ARN" > .certificate-arn
        
        print_warning "⚠️  IMPORTANT: Certificate validation required!"
        echo ""
        echo "You need to add DNS validation records:"
        echo ""
        
        # Wait a moment for certificate to be processed
        print_info "Getting validation records (this may take 30-60 seconds)..."
        
        for i in {1..12}; do
            sleep 5
            
            VALIDATION_RECORDS=$(aws acm describe-certificate \
                --certificate-arn "$CERT_ARN" \
                --region $REGION \
                --query 'Certificate.DomainValidationOptions[].ResourceRecord' \
                --output table 2>/dev/null)
            
            if echo "$VALIDATION_RECORDS" | grep -q "Name"; then
                echo "$VALIDATION_RECORDS"
                break
            else
                echo -n "."
            fi
        done
        
        echo ""
        echo "📋 Add these CNAME records to your DNS:"
        echo "  • Copy the Name and Value from the table above"
        echo "  • Add as CNAME records in your domain's DNS management"
        echo "  • This proves you own the domain"
        echo ""
        
        echo "💾 Certificate ARN saved to .certificate-arn file"
        echo ""
        
        echo "⏳ After adding validation records, wait for certificate approval (5-30 minutes)"
        echo ""
        echo "🔄 Check certificate status with:"
        echo "aws acm describe-certificate --certificate-arn $CERT_ARN --region $REGION --query 'Certificate.Status'"
        
    else
        print_error "Failed to request SSL certificate"
        print_info "You can request manually in AWS Console: https://console.aws.amazon.com/acm/"
    fi
else
    print_warning "Skipping SSL setup - fix DNS issues first"
fi

# Step 5: HTTPS Listener Setup (conditional)
echo ""
echo "🎧 STEP 5: HTTPS Listener Setup"
echo "==============================="
echo ""

if [ -f ".certificate-arn" ]; then
    CERT_ARN=$(cat .certificate-arn)
    
    print_info "Checking if certificate is validated..."
    
    CERT_STATUS=$(aws acm describe-certificate \
        --certificate-arn "$CERT_ARN" \
        --region $REGION \
        --query 'Certificate.Status' \
        --output text 2>/dev/null || echo "UNKNOWN")
    
    if [ "$CERT_STATUS" = "ISSUED" ]; then
        print_status "Certificate is validated and issued!"
        
        # Check if HTTPS listener already exists
        EXISTING_HTTPS=$(aws elbv2 describe-listeners \
            --load-balancer-arn "$LOAD_BALANCER_ARN" \
            --region $REGION \
            --query 'Listeners[?Port==`443`].Protocol' \
            --output text 2>/dev/null)
        
        if [ "$EXISTING_HTTPS" = "HTTPS" ]; then
            print_status "HTTPS listener already exists"
        else
            print_info "Adding HTTPS listener to load balancer..."
            
            LISTENER_ARN=$(aws elbv2 create-listener \
                --load-balancer-arn "$LOAD_BALANCER_ARN" \
                --protocol HTTPS \
                --port 443 \
                --certificates CertificateArn="$CERT_ARN" \
                --default-actions Type=forward,TargetGroupArn="$TARGET_GROUP_ARN" \
                --region $REGION \
                --query 'Listeners[0].ListenerArn' \
                --output text 2>/dev/null)
            
            if [ $? -eq 0 ]; then
                print_status "HTTPS listener added successfully!"
                print_status "Listener ARN: $LISTENER_ARN"
            else
                print_error "Failed to add HTTPS listener"
            fi
        fi
    else
        print_warning "Certificate status: $CERT_STATUS"
        echo ""
        echo "Certificate is not yet validated. Please:"
        echo "1. Add the DNS validation records shown above"
        echo "2. Wait 5-30 minutes for validation"
        echo "3. Run this script again to add HTTPS listener"
        echo ""
        echo "🔄 Check status: aws acm describe-certificate --certificate-arn $CERT_ARN --region $REGION"
    fi
else
    print_warning "No certificate ARN file found - run this script again after DNS is working"
fi

# Final Status and Instructions
echo ""
echo "🎉 SETUP STATUS SUMMARY"
echo "======================="
echo ""

if [ "$DNS_WORKING" = true ]; then
    print_status "✅ DNS Resolution: Working"
else
    print_error "❌ DNS Resolution: Failed"
fi

if [ "$HTTP_WORKING" = true ]; then
    print_status "✅ HTTP Access: http://$DOMAIN"
else
    print_error "❌ HTTP Access: Failed"
fi

if [ "$CERT_STATUS" = "ISSUED" ] && [ -f ".certificate-arn" ]; then
    print_status "✅ HTTPS Access: https://$DOMAIN"
    echo ""
    print_status "🎯 SUCCESS! Your IDE is now available at:"
    echo ""
    echo "    🌐 https://$DOMAIN"
    echo ""
    echo "Share this URL with all your students! 🎓"
else
    print_warning "⏳ HTTPS: Pending certificate validation"
    echo ""
    echo "🎯 Current Status:"
    echo "  • HTTP: http://$DOMAIN (working)"
    echo "  • HTTPS: Pending (add DNS validation records)"
    echo ""
    echo "📋 Next Steps:"
    echo "  1. Add certificate validation DNS records"
    echo "  2. Wait for certificate approval"
    echo "  3. Run this script again to enable HTTPS"
fi

echo ""
echo "💡 Pro Tips:"
echo "  • Bookmark: https://$DOMAIN"
echo "  • Share with students: https://$DOMAIN"  
echo "  • Test from different devices/networks"
echo ""

print_status "Domain setup completed!"