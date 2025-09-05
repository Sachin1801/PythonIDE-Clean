#!/bin/bash

# Setup Custom Domain for PythonIDE
# Provides consistent URL access for all users

set -e

echo "🌐 Setting Up Custom Domain for PythonIDE"
echo "========================================="

# Configuration
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

show_options() {
    echo ""
    echo "🎯 Domain Options for PythonIDE Access:"
    echo ""
    echo "1. 🏆 AWS Route 53 Domain (Recommended)"
    echo "   • Professional: pythonide.yourname.com"
    echo "   • Automatic DNS management"
    echo "   • Free SSL certificate"
    echo "   • Cost: ~$12-15/year"
    echo ""
    echo "2. 💰 Budget Option: Use Existing Domain"  
    echo "   • If you already own a domain"
    echo "   • Create subdomain: ide.yourdomain.com"
    echo "   • Just need to add CNAME record"
    echo ""
    echo "3. 🎓 Education/Free Options:"
    echo "   • Freenom (.tk, .ml, .ga domains) - Free"
    echo "   • GitHub Student Pack (.tech domain) - Free"
    echo "   • University domain (if available)"
    echo ""
    echo "4. 🚀 Quick Fix: Subdomain Services"
    echo "   • No domain needed"
    echo "   • Use services like ngrok, localtunnel"
    echo "   • Good for testing/demos"
}

setup_route53_domain() {
    echo ""
    print_info "Setting up Route 53 domain..."
    
    read -p "Enter desired domain name (e.g., pythonide-classroom): " domain_base
    
    echo ""
    echo "Available TLDs:"
    echo "  • .com ($12/year) - Most professional"
    echo "  • .org ($12/year) - Good for education" 
    echo "  • .net ($12/year) - Alternative to .com"
    echo "  • .dev ($12/year) - Perfect for development"
    echo "  • .edu (special requirements)"
    echo ""
    
    read -p "Enter TLD (e.g., com, org, dev): " tld
    domain_name="${domain_base}.${tld}"
    
    echo ""
    print_info "Checking domain availability: $domain_name"
    
    # Check domain availability
    availability=$(aws route53domains check-domain-availability \
        --domain-name "$domain_name" \
        --region us-east-1 \
        --query 'Availability' \
        --output text 2>/dev/null || echo "ERROR")
    
    if [ "$availability" = "AVAILABLE" ]; then
        print_status "Domain $domain_name is available!"
        echo ""
        
        read -p "Purchase this domain for ~$12-15? (y/n): " purchase
        if [[ $purchase =~ ^[Yy]$ ]]; then
            echo ""
            print_info "Purchasing domain $domain_name..."
            
            # Note: This requires contact information
            echo "⚠️  You'll need to provide contact information for domain registration"
            echo "Run this command to complete purchase:"
            echo ""
            echo "aws route53domains register-domain \\"
            echo "  --domain-name $domain_name \\"
            echo "  --duration-in-years 1 \\"
            echo "  --admin-contact '{...}' \\"
            echo "  --registrant-contact '{...}' \\"
            echo "  --tech-contact '{...}' \\"
            echo "  --region us-east-1"
            echo ""
            echo "Or purchase through AWS Console: https://console.aws.amazon.com/route53/domains/home"
        fi
    elif [ "$availability" = "UNAVAILABLE" ]; then
        print_error "Domain $domain_name is not available"
        echo "Try: ${domain_base}ide.${tld}, ${domain_base}app.${tld}, or different TLD"
    else
        print_error "Could not check domain availability (AWS CLI issue)"
    fi
}

setup_existing_domain() {
    echo ""
    read -p "Enter your existing domain (e.g., yourdomain.com): " existing_domain
    read -p "Enter subdomain name (e.g., ide, pythonide): " subdomain
    
    full_domain="${subdomain}.${existing_domain}"
    
    echo ""
    print_info "Setting up subdomain: $full_domain"
    echo ""
    echo "📋 DNS Configuration Required:"
    echo "  Record Type: CNAME"
    echo "  Name: $subdomain"
    echo "  Value: $LOAD_BALANCER_DNS"
    echo "  TTL: 300 (5 minutes)"
    echo ""
    echo "🔧 Add this record in your domain's DNS management:"
    echo "  • GoDaddy: DNS Management → Add Record"
    echo "  • Namecheap: Advanced DNS → Add New Record"
    echo "  • Cloudflare: DNS → Add Record"
    echo ""
    
    setup_ssl_for_domain "$full_domain"
}

setup_ssl_for_domain() {
    local domain=$1
    
    echo ""
    print_info "Setting up SSL certificate for $domain..."
    
    # Request SSL certificate
    CERT_ARN=$(aws acm request-certificate \
        --domain-name "$domain" \
        --validation-method DNS \
        --region $REGION \
        --query 'CertificateArn' \
        --output text 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        print_status "SSL certificate requested: $CERT_ARN"
        echo ""
        echo "📋 Certificate Validation Required:"
        echo ""
        
        # Get validation records
        sleep 10  # Wait for certificate to be processed
        
        aws acm describe-certificate \
            --certificate-arn "$CERT_ARN" \
            --region $REGION \
            --query 'Certificate.DomainValidationOptions[0].ResourceRecord' \
            --output table 2>/dev/null || {
                echo "⏳ Certificate is being processed..."
                echo "Check validation records with:"
                echo "aws acm describe-certificate --certificate-arn $CERT_ARN --region $REGION"
            }
        
        echo ""
        print_warning "⚠️  You must add the DNS validation record to prove domain ownership!"
        echo ""
        echo "After validation completes, add HTTPS listener:"
        echo ""
        echo "aws elbv2 create-listener \\"
        echo "  --load-balancer-arn $LOAD_BALANCER_ARN \\"
        echo "  --protocol HTTPS \\"
        echo "  --port 443 \\"
        echo "  --certificates CertificateArn=$CERT_ARN \\"
        echo "  --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN \\"
        echo "  --region $REGION"
        
        # Save certificate ARN for later use
        echo "$CERT_ARN" > .certificate-arn
        print_status "Certificate ARN saved to .certificate-arn file"
    else
        print_error "Failed to request SSL certificate"
    fi
}

setup_free_options() {
    echo ""
    echo "🎓 Free Domain Options:"
    echo ""
    echo "1. Freenom (Free TLDs):"
    echo "   • Visit: https://freenom.com"
    echo "   • Get .tk, .ml, .ga, .cf domains for free"
    echo "   • Add CNAME: $LOAD_BALANCER_DNS"
    echo ""
    echo "2. GitHub Student Pack:"
    echo "   • Visit: https://education.github.com/pack"
    echo "   • Free .tech domain (if you're a student)"
    echo "   • Many other developer tools included"
    echo ""
    echo "3. University Domain:"
    echo "   • Ask your IT department"
    echo "   • Often: username.university.edu"
    echo "   • Requires university approval"
}

setup_quick_tunnel() {
    echo ""
    print_info "Quick tunnel setup (temporary solution)..."
    echo ""
    echo "🚀 Tunnel Services (No domain needed):"
    echo ""
    echo "Option A: ngrok (Recommended)"
    echo "  1. Sign up at: https://ngrok.com"
    echo "  2. Install: npm install -g @ngrok/ngrok"
    echo "  3. Run: ngrok http $LOAD_BALANCER_DNS:80 --host-header=$LOAD_BALANCER_DNS"
    echo ""
    echo "Option B: Cloudflare Tunnel"
    echo "  1. Install cloudflared"
    echo "  2. Run: cloudflared tunnel --url http://$LOAD_BALANCER_DNS"
    echo ""
    echo "⚠️  These provide temporary URLs that change frequently"
    echo "💡 Better for testing than production use"
}

# Main menu
show_options

echo ""
read -p "Choose option (1-4): " choice

case $choice in
    1)
        setup_route53_domain
        ;;
    2)
        setup_existing_domain
        ;;
    3)
        setup_free_options
        ;;
    4)
        setup_quick_tunnel
        ;;
    *)
        print_error "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "🎯 NEXT STEPS SUMMARY:"
echo "====================="
echo ""
echo "1. ✅ Choose and register your domain"
echo "2. 🔧 Add DNS records (CNAME or A record)"
echo "3. 🔒 Set up SSL certificate"
echo "4. 🌐 Add HTTPS listener to load balancer"
echo "5. 🎉 Share single URL with all students!"
echo ""
print_status "Domain setup guide completed!"