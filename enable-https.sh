#!/bin/bash

# Enable HTTPS for PythonIDE Load Balancer
# This script adds SSL certificate and HTTPS listener

set -e

echo "🔒 Enabling HTTPS for PythonIDE"
echo "================================"

# Configuration
REGION="us-east-2"
LOAD_BALANCER_ARN="arn:aws:elasticloadbalancing:us-east-2:653306034507:loadbalancer/app/pythonide-alb/2dcd02db57a7616c"
TARGET_GROUP_ARN="arn:aws:elasticloadbalancing:us-east-2:653306034507:targetgroup/pythonide-targets/7ecb2c257c437e2e"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

echo ""
echo "Current Load Balancer: pythonide-alb-456687384.us-east-2.elb.amazonaws.com"
echo ""

# Option 1: Use a custom domain with AWS Certificate Manager
echo "📋 HTTPS Setup Options:"
echo ""
echo "1. 🏆 Custom Domain + AWS Certificate (Recommended)"
echo "   - Get a domain name (e.g., pythonide.yourdomain.com)"
echo "   - Request free SSL certificate from AWS"
echo "   - Professional setup"
echo ""
echo "2. ⚡ Self-Signed Certificate (Development Only)"
echo "   - Works immediately but shows security warnings"
echo "   - Not recommended for production"
echo ""
echo "3. 🔧 Manual Certificate Upload"
echo "   - Upload your own certificate"
echo ""

read -p "Choose option (1/2/3): " choice

case $choice in
    1)
        echo ""
        print_warning "For Option 1, you need a domain name first."
        echo ""
        echo "Steps to complete this setup:"
        echo "1. Purchase a domain (e.g., from Route53, GoDaddy, etc.)"
        echo "2. Create a CNAME record pointing to: pythonide-alb-456687384.us-east-2.elb.amazonaws.com"
        echo "3. Request SSL certificate for your domain"
        echo "4. Add HTTPS listener to load balancer"
        echo ""
        
        read -p "Do you have a domain name ready? (y/n): " has_domain
        
        if [[ $has_domain =~ ^[Yy]$ ]]; then
            read -p "Enter your domain name (e.g., pythonide.example.com): " domain_name
            
            echo ""
            echo "🔄 Requesting SSL certificate for $domain_name..."
            
            # Request certificate
            CERT_ARN=$(aws acm request-certificate \
                --domain-name "$domain_name" \
                --validation-method DNS \
                --region $REGION \
                --query 'CertificateArn' \
                --output text)
            
            if [ $? -eq 0 ]; then
                print_status "SSL certificate requested: $CERT_ARN"
                echo ""
                print_warning "IMPORTANT: You must validate the certificate!"
                echo ""
                echo "Next steps:"
                echo "1. Check your DNS validation records:"
                echo "   aws acm describe-certificate --certificate-arn $CERT_ARN --region $REGION"
                echo ""
                echo "2. Add the CNAME records to your domain's DNS"
                echo ""
                echo "3. Wait for validation (can take a few minutes to hours)"
                echo ""
                echo "4. Once validated, run this command to add HTTPS listener:"
                echo "   aws elbv2 create-listener \\"
                echo "     --load-balancer-arn $LOAD_BALANCER_ARN \\"
                echo "     --protocol HTTPS \\"
                echo "     --port 443 \\"
                echo "     --certificates CertificateArn=$CERT_ARN \\"
                echo "     --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN \\"
                echo "     --region $REGION"
            else
                print_error "Failed to request certificate"
                exit 1
            fi
        else
            echo ""
            print_warning "You need a domain name first. Here's how to get one:"
            echo ""
            echo "AWS Route 53 (Recommended):"
            echo "  aws route53domains search-domains --domain-name pythonide --region us-east-1"
            echo ""
            echo "Or use any domain registrar (GoDaddy, Namecheap, etc.)"
        fi
        ;;
        
    2)
        echo ""
        print_warning "Creating self-signed certificate (development only)..."
        echo ""
        
        # Create self-signed certificate
        openssl req -x509 -newkey rsa:2048 -keyout private.key -out certificate.crt -days 365 -nodes \
            -subj "/C=US/ST=NY/L=NYC/O=PythonIDE/OU=Dev/CN=pythonide-alb-456687384.us-east-2.elb.amazonaws.com"
        
        if [ $? -eq 0 ]; then
            print_status "Self-signed certificate created"
            
            # Upload certificate to AWS
            echo "🔄 Uploading certificate to AWS IAM..."
            CERT_ARN=$(aws iam upload-server-certificate \
                --server-certificate-name pythonide-self-signed-$(date +%s) \
                --certificate-body file://certificate.crt \
                --private-key file://private.key \
                --query 'ServerCertificateMetadata.Arn' \
                --output text)
            
            if [ $? -eq 0 ]; then
                print_status "Certificate uploaded: $CERT_ARN"
                
                # Add HTTPS listener
                echo "🔄 Adding HTTPS listener..."
                aws elbv2 create-listener \
                    --load-balancer-arn $LOAD_BALANCER_ARN \
                    --protocol HTTPS \
                    --port 443 \
                    --certificates CertificateArn=$CERT_ARN \
                    --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN \
                    --region $REGION
                
                if [ $? -eq 0 ]; then
                    print_status "HTTPS listener added successfully!"
                    echo ""
                    print_warning "⚠️  Browser will show security warnings (certificate not trusted)"
                    echo ""
                    echo "🌐 You can now access:"
                    echo "  HTTP:  http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com"
                    echo "  HTTPS: https://pythonide-alb-456687384.us-east-2.elb.amazonaws.com"
                    echo ""
                    echo "For production, use Option 1 with a real domain and AWS certificate."
                else
                    print_error "Failed to add HTTPS listener"
                fi
            else
                print_error "Failed to upload certificate"
            fi
            
            # Clean up certificate files
            rm -f private.key certificate.crt
        else
            print_error "Failed to create self-signed certificate"
        fi
        ;;
        
    3)
        echo ""
        print_warning "Manual certificate upload option selected."
        echo ""
        echo "You need to provide:"
        echo "1. Certificate file (.crt or .pem)"
        echo "2. Private key file (.key)"
        echo "3. Certificate chain file (optional)"
        echo ""
        echo "Place these files in the current directory and run:"
        echo "  aws iam upload-server-certificate \\"
        echo "    --server-certificate-name pythonide-custom \\"
        echo "    --certificate-body file://certificate.crt \\"
        echo "    --private-key file://private.key"
        ;;
        
    *)
        print_error "Invalid option selected"
        exit 1
        ;;
esac

echo ""
print_status "HTTPS setup script completed"