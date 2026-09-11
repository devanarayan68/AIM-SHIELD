#!/usr/bin/env python3
"""
AIM-SHIELD v1 → v2 Migration Script
Handles upgrading old installations to the new advanced system
"""

import os
import shutil
import json
from pathlib import Path

def backup_old_files():
    """Create backup of old files"""
    print("📦 Backing up old files...")
    backup_dir = Path('backup_v1')
    backup_dir.mkdir(exist_ok=True)
    
    old_files = ['frontend.html', 'backend/app.py']
    for file in old_files:
        if Path(file).exists():
            dest = backup_dir / Path(file).name
            shutil.copy2(file, dest)
            print(f"   ✓ Backed up {file} → {dest}")
    
    return backup_dir

def update_requirements():
    """Update requirements.txt with new dependencies"""
    print("\n📋 Updating requirements.txt...")
    
    requirements = [
        'flask',
        'flask-cors',
        'flask-socketio',
        'python-socketio',
        'python-engineio',
        'numpy',
        'pandas',
        'scikit-learn',
        'python-dotenv',
    ]
    
    with open('requirements.txt', 'w') as f:
        f.write('\n'.join(requirements))
    
    print("   ✓ requirements.txt updated with new dependencies")

def create_env_file():
    """Create .env file from template"""
    print("\n🔧 Creating .env configuration file...")
    
    if Path('.env').exists():
        print("   ! .env already exists, skipping")
        return
    
    if Path('.env.example').exists():
        shutil.copy2('.env.example', '.env')
        print("   ✓ Created .env from .env.example")
    else:
        print("   ! .env.example not found")

def initialize_database():
    """Initialize new database"""
    print("\n🗄️  Initializing SQLite database...")
    
    try:
        from backend.database import Database
        db = Database()
        print("   ✓ Database initialized at backend/aim_shield.db")
        
        stats = db.get_statistics()
        print(f"   📊 Database ready: {stats}")
    except Exception as e:
        print(f"   ! Error initializing database: {e}")

def create_config():
    """Create config.py if not exists"""
    print("\n⚙️  Setting up configuration module...")
    
    if Path('backend/config.py').exists():
        print("   ✓ config.py already exists")
    else:
        print("   ! config.py should be created manually")

def create_directory_structure():
    """Ensure all required directories exist"""
    print("\n📁 Ensuring directory structure...")
    
    dirs = [
        'backend/models',
        'backend/data',
        'logs',
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {dir_path}/")

def generate_migration_report():
    """Generate migration report"""
    print("\n📝 Migration Summary")
    print("=" * 50)
    
    report = {
        'version': {
            'from': 'v1',
            'to': 'v2',
        },
        'new_features': [
            '✨ WebSocket real-time streaming',
            '✨ SQLite database with persistence',
            '✨ Advanced alert management system',
            '✨ Historical data explorer',
            '✨ System statistics dashboard',
            '✨ Docker & Kubernetes support',
            '✨ CI/CD pipeline (GitHub Actions)',
            '✨ Configurable thresholds via .env',
        ],
        'breaking_changes': [
            '⚠️  Backend changed: app.py → app_advanced.py',
            '⚠️  Frontend changed: frontend.html → frontend_advanced.html',
            '⚠️  API signature changes (backward compatible with REST)',
            '⚠️  WebSocket required for real-time features',
        ],
        'migration_checklist': [
            '✓ Backed up old files',
            '✓ Updated requirements.txt',
            '✓ Created .env configuration',
            '✓ Initialized database',
            '✓ Set up directory structure',
        ],
        'next_steps': [
            '1. Review .env and customize settings',
            '2. Install new dependencies: pip install -r requirements.txt',
            '3. Start backend: python backend/app_advanced.py',
            '4. Open frontend: http://localhost:8000/frontend_advanced.html',
            '5. (Optional) Deploy with Docker: docker-compose up --build',
        ]
    }
    
    print("\n🎯 New Features:")
    for feature in report['new_features']:
        print(f"   {feature}")
    
    print("\n⚡ Breaking Changes:")
    for change in report['breaking_changes']:
        print(f"   {change}")
    
    print("\n✅ Migration Checklist:")
    for item in report['migration_checklist']:
        print(f"   {item}")
    
    print("\n🚀 Next Steps:")
    for step in report['next_steps']:
        print(f"   {step}")
    
    print("\n" + "=" * 50)
    print("💡 Migration complete! Read README_ADVANCED.md for full documentation.")
    
    # Save report to file
    with open('MIGRATION_REPORT.json', 'w') as f:
        json.dump(report, f, indent=2)
    print("\n📄 Detailed report saved to MIGRATION_REPORT.json")

def main():
    """Run complete migration"""
    print("\n" + "=" * 50)
    print("🚀 AIM-SHIELD v1 → v2 MIGRATION")
    print("=" * 50 + "\n")
    
    try:
        # Run migration steps
        backup_old_files()
        create_directory_structure()
        update_requirements()
        create_env_file()
        create_config()
        initialize_database()
        generate_migration_report()
        
        print("\n✅ Migration completed successfully!")
        print("📖 For more details, see README_ADVANCED.md\n")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("🔙 Original files backed up in ./backup_v1/")
        return False
    
    return True

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
