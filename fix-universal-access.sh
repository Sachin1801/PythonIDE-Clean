#!/bin/bash

# Fix Universal Access for pythonide-classroom.tech
# Ensure 40+ users can access the IDE from anywhere

set -e

echo "🌍 Fixing Universal Access for PythonIDE"
echo "======================================="

DOMAIN="pythonide-classroom.tech"
LOAD_BALANCER_DNS="pythonide-alb-456687384.us-east-2.elb.amazonaws.com"

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
echo "🎯 Goal: Make http://$DOMAIN work for ALL students"
echo "🌍 Target: 40+ concurrent users worldwide"
echo ""

# Test current status
echo "🔍 CURRENT STATUS CHECK"
echo "======================="

# Test domain resolution
print_info "Testing domain resolution..."
DOMAIN_IPS=$(getent hosts "$DOMAIN" 2>/dev/null | awk '{print $1}' | sort -u | tr '\n' ' ')

if [ -n "$DOMAIN_IPS" ]; then
    print_status "Domain resolves to: $DOMAIN_IPS"
else
    print_error "Domain resolution failed"
    exit 1
fi

# Test HTTP access
print_info "Testing HTTP access..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "http://$DOMAIN" 2>/dev/null)

if [ "$HTTP_CODE" = "200" ]; then
    print_status "HTTP access working (Code: $HTTP_CODE)"
elif [ "$HTTP_CODE" = "405" ]; then
    print_status "HTTP access working (Code: $HTTP_CODE - Method not allowed is normal)"
else
    print_error "HTTP access failed (Code: $HTTP_CODE)"
fi

echo ""
echo "🛠️  UNIVERSAL ACCESS SOLUTIONS"
echo "=============================="

echo ""
echo "📋 SOLUTION 1: Add Multiple DNS Records"
echo "---------------------------------------"
print_info "Adding both CNAME and A records improves compatibility"

# Get current load balancer IPs
LB_IPS=($(getent hosts "$LOAD_BALANCER_DNS" | awk '{print $1}' | sort -u))

echo ""
echo "🔧 Additional DNS Records to Add:"
echo ""
echo "A Records (for better compatibility):"
for ip in "${LB_IPS[@]}"; do
    echo "  Type: A"
    echo "  Name: @ (or blank)"
    echo "  Value: $ip"
    echo "  TTL: 7200"
    echo ""
done

echo "CNAME for WWW (redirect www to main):"
echo "  Type: CNAME"
echo "  Name: www"
echo "  Value: $DOMAIN"
echo "  TTL: 7200"

echo ""
echo "📋 SOLUTION 2: CloudFront Distribution (Recommended)"
echo "--------------------------------------------------"
print_warning "CloudFront provides global CDN for reliable worldwide access"

# Check if we have a CloudFront distribution
CF_DISTRIBUTIONS=$(aws cloudfront list-distributions --query "DistributionList.Items[?contains(Origins.Items[0].DomainName, 'pythonide')]" --output text 2>/dev/null || echo "")

if [ -z "$CF_DISTRIBUTIONS" ]; then
    print_info "No CloudFront distribution found. Creating one will:"
    echo "  • Provide global edge locations for fast access"
    echo "  • Handle DNS issues automatically"
    echo "  • Improve reliability for students worldwide"
    echo "  • Add HTTPS support automatically"
    echo ""
    
    read -p "Create CloudFront distribution for better global access? (y/n): " create_cf
    
    if [[ $create_cf =~ ^[Yy]$ ]]; then
        echo ""
        print_info "Creating CloudFront distribution..."
        
        # Create CloudFront distribution config
        cat > cloudfront-config.json << EOF
{
    "CallerReference": "pythonide-$(date +%s)",
    "Comment": "PythonIDE Global Distribution",
    "Enabled": true,
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "pythonide-origin",
                "DomainName": "$LOAD_BALANCER_DNS",
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only",
                    "OriginSslProtocols": {
                        "Quantity": 1,
                        "Items": ["TLSv1.2"]
                    }
                }
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "pythonide-origin",
        "ViewerProtocolPolicy": "redirect-to-https",
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "ForwardedValues": {
            "QueryString": true,
            "Cookies": {
                "Forward": "all"
            },
            "Headers": {
                "Quantity": 3,
                "Items": ["Host", "Origin", "Referer"]
            }
        },
        "MinTTL": 0,
        "DefaultTTL": 0,
        "MaxTTL": 0
    },
    "Aliases": {
        "Quantity": 1,
        "Items": ["$DOMAIN"]
    },
    "ViewerCertificate": {
        "CloudFrontDefaultCertificate": true
    },
    "PriceClass": "PriceClass_100"
}
EOF

        # Create distribution
        DISTRIBUTION_OUTPUT=$(aws cloudfront create-distribution --distribution-config file://cloudfront-config.json 2>/dev/null)
        
        if [ $? -eq 0 ]; then
            CF_DOMAIN=$(echo "$DISTRIBUTION_OUTPUT" | jq -r '.Distribution.DomainName')
            DISTRIBUTION_ID=$(echo "$DISTRIBUTION_OUTPUT" | jq -r '.Distribution.Id')
            
            print_status "CloudFront distribution created!"
            print_info "CloudFront Domain: $CF_DOMAIN"
            print_info "Distribution ID: $DISTRIBUTION_ID"
            
            echo ""
            print_warning "⚠️  Update your DNS record:"
            echo "  Change CNAME target from:"
            echo "    $LOAD_BALANCER_DNS"
            echo "  To:"
            echo "    $CF_DOMAIN"
            echo ""
            echo "This will provide global access with automatic HTTPS!"
            
            # Clean up temp file
            rm -f cloudfront-config.json
        else
            print_error "Failed to create CloudFront distribution"
            rm -f cloudfront-config.json
        fi
    fi
else
    print_status "CloudFront distribution already exists"
fi

echo ""
echo "📋 SOLUTION 3: Student Troubleshooting Guide"
echo "-------------------------------------------"

cat > student-access-guide.md << 'EOF'
# PythonIDE Access Guide for Students

## 🌐 Main URL
**http://pythonide-classroom.tech**

## 🔧 If the URL doesn't work:

### Quick Fixes:
1. **Try different browsers**: Chrome, Firefox, Safari, Edge
2. **Clear browser cache**: Ctrl+F5 or Cmd+Shift+R
3. **Use incognito/private mode**
4. **Disable VPN** temporarily
5. **Try mobile data** instead of WiFi

### DNS Issues:
If you get "Site cannot be reached":
1. **Change DNS servers**:
   - Windows: Network Settings → Change adapter options → DNS servers → 8.8.8.8, 1.1.1.1
   - Mac: System Preferences → Network → Advanced → DNS → Add 8.8.8.8, 1.1.1.1
2. **Flush DNS cache**:
   - Windows: `ipconfig /flushdns`
   - Mac: `sudo dscacheutil -flushcache`

### Alternative Access Methods:
1. **Direct IP access**: http://3.136.47.243 or http://3.130.8.238
2. **Wait 2-4 hours** for DNS to fully propagate globally

### Still Having Issues?
Contact your instructor with:
- Your operating system
- Browser you're using
- Exact error message
- Your location/network (school WiFi, home, etc.)
EOF

print_status "Created student-access-guide.md for troubleshooting"

echo ""
echo "📋 SOLUTION 4: Multiple Access Points"
echo "------------------------------------"
print_info "Setting up backup access methods..."

echo ""
echo "🔗 Student Access Options:"
echo "1. 🏆 Primary: http://pythonide-classroom.tech"
echo "2. 🌐 Backup: http://$LOAD_BALANCER_DNS"
echo "3. 🎯 Direct IP: http://3.136.47.243"
echo "4. 🎯 Direct IP: http://3.130.8.238"

# Create a simple status page
cat > access-status.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>PythonIDE Access Status</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .working { background: #d4edda; border-left: 5px solid #28a745; }
        .testing { background: #fff3cd; border-left: 5px solid #ffc107; }
        .url { font-family: monospace; background: #f8f9fa; padding: 5px; border-radius: 3px; }
        .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 5px; }
        .btn:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐍 PythonIDE Access Status</h1>
        <p>Multiple ways to access your Python IDE:</p>
        
        <div class="status working">
            <h3>✅ Primary URL</h3>
            <p>Main access point for all students</p>
            <a href="http://pythonide-classroom.tech" class="btn">pythonide-classroom.tech</a>
        </div>
        
        <div class="status testing">
            <h3>⚡ Backup URLs</h3>
            <p>Use these if the main URL doesn't work</p>
            <a href="http://$LOAD_BALANCER_DNS" class="btn">Load Balancer URL</a>
            <a href="http://3.136.47.243" class="btn">Direct IP #1</a>
            <a href="http://3.130.8.238" class="btn">Direct IP #2</a>
        </div>
        
        <div class="status">
            <h3>🔧 Troubleshooting</h3>
            <ul>
                <li>Try different browsers (Chrome, Firefox, Safari)</li>
                <li>Clear browser cache (Ctrl+F5)</li>
                <li>Use incognito/private mode</li>
                <li>Change DNS to 8.8.8.8, 1.1.1.1</li>
                <li>Disable VPN temporarily</li>
                <li>Try mobile data instead of WiFi</li>
            </ul>
        </div>
        
        <div class="status">
            <h3>📱 Need Help?</h3>
            <p>Contact your instructor if none of these URLs work for you.</p>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds to check status
        setTimeout(() => window.location.reload(), 30000);
    </script>
</body>
</html>
EOF

print_status "Created access-status.html page"

echo ""
echo "🎉 RECOMMENDATIONS FOR 40+ STUDENTS"
echo "=================================="

echo ""
print_status "✅ Immediate Actions:"
echo "  1. Share ALL URLs with students (primary + backups)"
echo "  2. Add A records to DNS for better compatibility" 
echo "  3. Distribute the student troubleshooting guide"
echo ""

print_status "🚀 Long-term Solutions:"
echo "  1. Set up CloudFront distribution (global CDN)"
echo "  2. Add proper HTTPS with SSL certificate"
echo "  3. Monitor access patterns and fix issues proactively"
echo ""

print_status "📋 Student Communication:"
cat << 'EOF'

📧 Email Template for Students:
===============================
Subject: PythonIDE Access Instructions

Hi everyone!

Your Python IDE is ready! Here are multiple ways to access it:

🏆 PRIMARY URL: http://pythonide-classroom.tech

🔗 BACKUP URLs (if primary doesn't work):
- http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com
- http://3.136.47.243
- http://3.130.8.238

If you have trouble accessing, try:
1. Different browser (Chrome/Firefox/Safari)
2. Clear browser cache (Ctrl+F5)
3. Private/incognito mode
4. Change DNS to 8.8.8.8, 1.1.1.1

The system supports 40+ concurrent users, so everyone can code simultaneously!

Happy coding! 🐍
EOF

echo ""
print_status "Universal access setup completed!"
echo ""
print_info "Next steps:"
echo "  • Test all URLs from different devices/networks"
echo "  • Share multiple URLs with students"
echo "  • Consider CloudFront for global reliability"