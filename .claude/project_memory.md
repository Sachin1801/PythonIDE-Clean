# Project Memory - PythonIDE-Clean

## Virtual Environment
- **Location**: `/server/venv/` (NOT in root directory)
- **Activation**: Always run `cd server && source venv/bin/activate` before Python commands
- **Python Path**: Set `PYTHONPATH=/home/sachinadlakha/on-campus/PythonIDE-Clean/server` when running Python scripts

## Database
- **Type**: PostgreSQL running in Docker
- **Access**: Use the database connection through the activated venv

## New feature development
- **Testing**
    - **Step 1**: All the new features made will be tested locally using docker build and running the local docker. 
    - **Step 2**: Then the next testing will always be done on the aws staging environment for correct functioning of the new feature developed.
    - **Step 3**: Once confirmed working in both steps 1 and 2, then we will create a PR to `main` branch which will trigger new deployment on the main ide on aws. We have to make sure all the changes work on the main ide and the exam ide running on aws.


## Important Notes
- The virtual environment is inside the server/ directory, not at project root
- Always activate venv before running migrations or Python database scripts