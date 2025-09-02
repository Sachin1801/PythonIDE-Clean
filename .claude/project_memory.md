# Project Memory - PythonIDE-Clean

## Virtual Environment
- **Location**: `/server/venv/` (NOT in root directory)
- **Activation**: Always run `cd server && source venv/bin/activate` before Python commands
- **Python Path**: Set `PYTHONPATH=/home/sachinadlakha/on-campus/PythonIDE-Clean/server` when running Python scripts

## Database
- **Type**: PostgreSQL running in Docker
- **Access**: Use the database connection through the activated venv

## Important Notes
- The virtual environment is inside the server/ directory, not at project root
- Always activate venv before running migrations or Python database scripts