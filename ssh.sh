#!/bin/bash
echo "Opening SSH connection to Azure container..."
az webapp ssh --name pythonide-3d84299d --resource-group PythonIDE-RG
