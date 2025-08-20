#!/bin/bash
echo "Streaming logs from Azure..."
az webapp log tail --name pythonide-3d84299d --resource-group PythonIDE-RG
