#!/bin/bash

echo "Checking available regions for your Azure Student subscription..."
echo "================================================================"

# Check which regions are available for App Service
echo ""
echo "✅ Regions where you can deploy App Services:"
az provider show --namespace Microsoft.Web --query "resourceTypes[?resourceType=='sites'].locations[]" -o tsv | sort | uniq | head -10

echo ""
echo "🌍 Recommended regions for students (usually work):"
echo "  • Central US (centralus)"
echo "  • West US 2 (westus2)"
echo "  • South Central US (southcentralus)"
echo "  • North Central US (northcentralus)"
echo "  • West US (westus)"

echo ""
echo "Now run: ./azure-student-deploy-fixed.sh"
echo "It will let you choose from available regions!"