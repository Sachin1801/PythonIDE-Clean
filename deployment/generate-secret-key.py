#!/usr/bin/env python3
"""
Generate a secure IDE_SECRET_KEY and update the ECS task definition
"""
import os
import json
import secrets
import string

def generate_secure_key(length=64):
    """Generate a cryptographically secure random key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def update_task_definition():
    """Update the ECS task definition with a new secret key"""
    task_def_path = os.path.join(os.path.dirname(__file__), 'ecs-task-definition.json')
    
    # Generate new secret key
    new_secret = generate_secure_key()
    print(f"Generated new IDE_SECRET_KEY: {new_secret}")
    
    # Read current task definition
    with open(task_def_path, 'r') as f:
        task_def = json.load(f)
    
    # Update the IDE_SECRET_KEY in environment variables
    container = task_def['containerDefinitions'][0]
    for env_var in container['environment']:
        if env_var['name'] == 'IDE_SECRET_KEY':
            old_key = env_var['value']
            env_var['value'] = new_secret
            print(f"✅ Updated IDE_SECRET_KEY in task definition")
            print(f"   Old: {old_key}")
            print(f"   New: {new_secret}")
            break
    else:
        # Add IDE_SECRET_KEY if not found
        container['environment'].append({
            "name": "IDE_SECRET_KEY",
            "value": new_secret
        })
        print(f"✅ Added IDE_SECRET_KEY to task definition")
    
    # Write back the updated task definition
    with open(task_def_path, 'w') as f:
        json.dump(task_def, f, indent=2)
    
    print(f"✅ Task definition updated: {task_def_path}")
    
    # Also update the region placeholder if needed
    if 'REGION' in container['image']:
        container['image'] = container['image'].replace('REGION', 'us-east-2')
        print(f"✅ Fixed region in image URL: {container['image']}")
        
        # Write again with region fix
        with open(task_def_path, 'w') as f:
            json.dump(task_def, f, indent=2)

if __name__ == '__main__':
    print("🔐 Generating secure IDE_SECRET_KEY...")
    update_task_definition()
    print("🎉 Secret key generation complete!")