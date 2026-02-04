# manage_db.py
import argparse
import subprocess
import sys
import os
import time

# --- Defaults ---
DEFAULT_ENV = "dev"

def load_config(env):
    """
    Determines which docker-compose file and DB settings to use.
    """
    config = {
        "compose_file": "",
        "service_name": "backend",
        "db_service": "db",
        "db_user": "postgres",  # Default fallback
        "db_name": "postgres"   # Default fallback
    }

    if env == "dev":
        config["compose_file"] = "docker-compose.dev.yml"
        config["db_name"] = "skyrocket_dev"
        config["db_user"] = "postgres"
        print(f"🔧 Mode: DEVELOPMENT (Using {config['compose_file']})")

    elif env == "prod":
        config["compose_file"] = "docker-compose.prod.yml"
        print(f"Mj Mode: PRODUCTION (Using {config['compose_file']})")
        
        # Try to load DB name from .env for Prod
        if os.path.exists(".env"):
            with open(".env") as f:
                for line in f:
                    if line.startswith("POSTGRES_DB="):
                        config["db_name"] = line.strip().split("=")[1]
                    if line.startswith("POSTGRES_USER="):
                        config["db_user"] = line.strip().split("=")[1]
        else:
            print("⚠️  Warning: .env file not found. Using default DB settings.")
            config["db_name"] = "skyrocket_prod"
            config["db_user"] = "admin"

    return config

def run_command(command, shell=False, check=True):
    """Runs a shell command and prints output."""
    try:
        cmd_str = ' '.join(command) if isinstance(command, list) else command
        print(f"🚀 Executing: {cmd_str}")
        subprocess.run(command, shell=shell, check=check)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)

def check_docker_running(config):
    """Ensures the specific environment's containers are up."""
    try:
        # Check if the backend container is running for this compose file
        result = subprocess.run(
            ["docker-compose", "-f", config["compose_file"], "ps", "-q", config["service_name"]],
            capture_output=True, text=True
        )
        if not result.stdout.strip():
            print("⚠️  Docker containers are not running.")
            print("🔄 Starting them now...")
            run_command(["docker-compose", "-f", config["compose_file"], "up", "-d"])
            print("⏳ Waiting 5 seconds for services to initialize...")
            time.sleep(5)
    except Exception as e:
        print(f"❌ Docker seems to be missing or broken: {e}")
        sys.exit(1)

def update_models(config, message):
    """Generates a migration file and applies it."""
    check_docker_running(config)
    
    print(f"1️⃣  Generating migration script: '{message}'...")
    run_command([
        "docker-compose", "-f", config["compose_file"], "exec", config["service_name"],
        "alembic", "revision", "--autogenerate", "-m", message
    ])
    
    print("2️⃣  Applying changes to Database...")
    run_command([
        "docker-compose", "-f", config["compose_file"], "exec", config["service_name"],
        "alembic", "upgrade", "head"
    ])
    print("✅ Database schema updated successfully!")

def view_data(config):
    """Opens a PostgreSQL shell."""
    check_docker_running(config)
    print(f"👀 Connecting to database '{config['db_name']}' as '{config['db_user']}'...")
    print("💡 Hint: Type '\\dt' to list tables, '\\q' to exit.")
    
    # We use 'docker-compose exec' to get inside the db container
    subprocess.run([
        "docker-compose", "-f", config["compose_file"], "exec", config["db_service"],
        "psql", "-U", config["db_user"], "-d", config["db_name"]
    ])

def delete_data(config, env):
    """Wipes the database volume. Includes safety checks for Prod."""
    if env == "prod":
        confirm = input("fwfwfw DANGER: You are about to DELETE ALL PRODUCTION DATA. Type 'DESTROY' to confirm: ")
        if confirm != "DESTROY":
            print("❌ Operation cancelled.")
            return
    else:
        confirm = input("⚠️  WARNING: This will reset the dev database. Are you sure? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Operation cancelled.")
            return

    print("fw💥 Stopping containers and removing volumes...")
    run_command(["docker-compose", "-f", config["compose_file"], "down", "-v"])
    
    print("🔄 Restarting fresh containers...")
    # For prod, we don't usually --build every restart, but for dev we do
    if env == "dev":
        run_command(["docker-compose", "-f", config["compose_file"], "up", "-d", "--build"])
    else:
        run_command(["docker-compose", "-f", config["compose_file"], "up", "-d"])
    
    print("⏳ Waiting for DB to be ready...")
    time.sleep(5)
    
    print("Mw🌱 Re-initializing Database Schema...")
    # Initialize alembic (apply migrations to the fresh DB)
    run_command([
        "docker-compose", "-f", config["compose_file"], "exec", config["service_name"],
        "alembic", "upgrade", "head"
    ])
    print("✅ Data wiped and schema reset.")

def restore_backup(config, file_path):
    """Restores database from a SQL file."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    check_docker_running(config)
    print(f"Mw📥 Restoring '{config['db_name']}' from {file_path}...")
    
    # Construct the pipe command string
    # cat file.sql | docker-compose -f file.yml exec -T db psql -U user -d db
    full_cmd = (
        f"cat {file_path} | "
        f"docker-compose -f {config['compose_file']} exec -T {config['db_service']} "
        f"psql -U {config['db_user']} -d {config['db_name']}"
    )
    
    run_command(full_cmd, shell=True)
    print("✅ Database restored successfully.")

def main():
    parser = argparse.ArgumentParser(description="Manage Skyrocket Database")
    
    # Environment Argument
    parser.add_argument(
        "--env", 
        choices=["dev", "prod"], 
        default="dev", 
        help="Target environment (default: dev)"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: update
    parser_update = subparsers.add_parser("update", help="Generate migration and upgrade DB")
    parser_update.add_argument("-m", "--message", default="update models", help="Migration message")

    # Command: view
    subparsers.add_parser("view", help="Open interactive SQL shell")

    # Command: delete
    subparsers.add_parser("delete", help="Wipe database and restart (Reset)")

    # Command: restore
    parser_restore = subparsers.add_parser("restore", help="Restore DB from a .sql file")
    parser_restore.add_argument("file", help="Path to the .sql backup file")

    args = parser.parse_args()
    
    # Load config based on selected environment
    config = load_config(args.env)

    if args.command == "update":
        update_models(config, args.message)
    elif args.command == "view":
        view_data(config)
    elif args.command == "delete":
        delete_data(config, args.env)
    elif args.command == "restore":
        restore_backup(config, args.file)

if __name__ == "__main__":
    main()