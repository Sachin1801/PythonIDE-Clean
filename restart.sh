#!/bin/bash
echo "Restarting web app..."
az webapp restart --name pythonide-3d84299d --resource-group PythonIDE-RG
echo "Web app restarted!"
