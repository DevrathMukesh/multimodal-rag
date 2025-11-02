#!/usr/bin/env python3
"""
Fresh Start Script for Multimodal RAG
Removes all uploaded documents, chat history, and vector database data.
"""

import os
import shutil
import sys
import subprocess
from pathlib import Path


# Colors for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_colored(message: str, color: str = Colors.RESET):
    """Print colored message."""
    print(f"{color}{message}{Colors.RESET}")


def confirm(message: str) -> bool:
    """Ask for user confirmation."""
    response = input(f"{Colors.YELLOW}{message} (y/N): {Colors.RESET}").strip().lower()
    return response in ['y', 'yes']


def delete_path(path: Path, description: str) -> bool:
    """Delete a file or directory, return True if successful."""
    try:
        if path.exists():
            if path.is_file():
                path.unlink()
                print_colored(f"  ✓ Deleted file: {description}", Colors.GREEN)
                return True
            elif path.is_dir():
                if list(path.iterdir()):  # Check if directory has contents
                    shutil.rmtree(path)
                    path.mkdir(parents=True, exist_ok=True)  # Recreate empty directory
                    print_colored(f"  ✓ Emptied directory: {description}", Colors.GREEN)
                else:
                    print_colored(f"  - Directory already empty: {description}", Colors.CYAN)
                return True
        else:
            print_colored(f"  - Not found (already deleted): {description}", Colors.CYAN)
            return False
    except Exception as e:
        print_colored(f"  ✗ Error deleting {description}: {e}", Colors.RED)
        return False


def fresh_start_local():
    """Perform fresh start for local environment."""
    print_colored("\n🔧 Fresh Start - LOCAL ENVIRONMENT", Colors.BOLD + Colors.BLUE)
    print_colored("=" * 50, Colors.BLUE)
    
    # Get project root (assume script is in project root)
    script_dir = Path(__file__).parent
    backend_dir = script_dir / "backend"
    
    if not backend_dir.exists():
        print_colored(f"❌ Error: Backend directory not found at {backend_dir}", Colors.RED)
        return False
    
    # Define paths to clean
    paths_to_clean = [
        (backend_dir / "data" / "app.db", "SQLite database"),
        (backend_dir / "data" / "app.db-journal", "SQLite journal file"),
        (backend_dir / "data" / "uploads", "Uploaded PDFs directory"),
        (backend_dir / "chroma_db", "ChromaDB vector database"),
        (backend_dir / "data" / "parents_index", "Parents index directory"),
        (backend_dir / "data" / "logs", "Logs directory"),
    ]
    
    print_colored("\n📋 The following will be deleted:", Colors.YELLOW)
    for path, desc in paths_to_clean:
        if path.exists():
            size = get_size(path)
            print_colored(f"  • {desc}: {path} ({size})", Colors.YELLOW)
        else:
            print_colored(f"  • {desc}: {path} (not found)", Colors.CYAN)
    
    if not confirm("\n⚠️  Are you sure you want to delete all data?"):
        print_colored("❌ Cancelled.", Colors.RED)
        return False
    
    print_colored("\n🗑️  Deleting files and directories...", Colors.BOLD)
    
    success_count = 0
    for path, desc in paths_to_clean:
        if delete_path(path, desc):
            success_count += 1
    
    print_colored(f"\n✅ Fresh start complete! ({success_count} items processed)", Colors.GREEN)
    print_colored("\n💡 Next steps:", Colors.CYAN)
    print_colored("   1. Restart your backend server", Colors.CYAN)
    print_colored("   2. The database and directories will be recreated automatically", Colors.CYAN)
    
    return True


def get_size(path: Path) -> str:
    """Get human-readable size of file or directory."""
    try:
        if path.is_file():
            size = path.stat().st_size
        elif path.is_dir():
            size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        else:
            return "unknown"
        
        # Convert to human-readable
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except:
        return "unknown"


def fresh_start_docker():
    """Perform fresh start for Docker environment."""
    print_colored("\n🐳 Fresh Start - DOCKER ENVIRONMENT", Colors.BOLD + Colors.BLUE)
    print_colored("=" * 50, Colors.BLUE)
    
    # Check if docker-compose is available
    try:
        subprocess.run(["docker-compose", "--version"], 
                      capture_output=True, check=True, timeout=5)
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        print_colored("❌ Error: docker-compose not found. Is Docker installed?", Colors.RED)
        return False
    
    # Get project root
    script_dir = Path(__file__).parent
    backend_dir = script_dir / "backend"
    
    # Define paths to clean (same as local)
    paths_to_clean = [
        (backend_dir / "data" / "app.db", "SQLite database"),
        (backend_dir / "data" / "app.db-journal", "SQLite journal file"),
        (backend_dir / "data" / "uploads", "Uploaded PDFs directory"),
        (backend_dir / "chroma_db", "ChromaDB vector database"),
        (backend_dir / "data" / "parents_index", "Parents index directory"),
        (backend_dir / "data" / "logs", "Logs directory"),
    ]
    
    print_colored("\n📋 The following will be deleted:", Colors.YELLOW)
    for path, desc in paths_to_clean:
        if path.exists():
            size = get_size(path)
            print_colored(f"  • {desc}: {path} ({size})", Colors.YELLOW)
        else:
            print_colored(f"  • {desc}: {path} (not found)", Colors.CYAN)
    
    print_colored("\n📋 Docker operations:", Colors.YELLOW)
    print_colored("  • Stop running containers", Colors.YELLOW)
    print_colored("  • Delete data directories", Colors.YELLOW)
    
    if confirm("\n⚠️  Also delete Docker volumes (Ollama models will need to be re-downloaded)?"):
        delete_volumes = True
        print_colored("  • Remove Docker volumes (ollama-data, backend-logs)", Colors.YELLOW)
    else:
        delete_volumes = False
    
    if not confirm("\n⚠️  Are you sure you want to proceed?"):
        print_colored("❌ Cancelled.", Colors.RED)
        return False
    
    # Step 1: Stop containers
    print_colored("\n🛑 Stopping Docker containers...", Colors.BOLD)
    try:
        result = subprocess.run(
            ["docker-compose", "down"],
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print_colored("  ✓ Containers stopped", Colors.GREEN)
        else:
            print_colored(f"  ⚠️  Warning: {result.stderr}", Colors.YELLOW)
    except Exception as e:
        print_colored(f"  ✗ Error stopping containers: {e}", Colors.RED)
    
    # Step 2: Delete volumes if requested
    if delete_volumes:
        print_colored("\n🗑️  Removing Docker volumes...", Colors.BOLD)
        try:
            result = subprocess.run(
                ["docker-compose", "down", "-v"],
                cwd=script_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print_colored("  ✓ Volumes removed", Colors.GREEN)
                print_colored("  ℹ️  Ollama model will be re-downloaded on next startup", Colors.CYAN)
            else:
                print_colored(f"  ⚠️  Warning: {result.stderr}", Colors.YELLOW)
        except Exception as e:
            print_colored(f"  ✗ Error removing volumes: {e}", Colors.RED)
    
    # Step 3: Delete data directories
    print_colored("\n🗑️  Deleting files and directories...", Colors.BOLD)
    
    success_count = 0
    for path, desc in paths_to_clean:
        if delete_path(path, desc):
            success_count += 1
    
    # Step 4: Restart containers
    print_colored("\n🚀 Restarting Docker containers...", Colors.BOLD)
    if confirm("Do you want to restart containers now?"):
        try:
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=script_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print_colored("  ✓ Containers started", Colors.GREEN)
                print_colored("\n💡 Check container status with: docker-compose ps", Colors.CYAN)
                print_colored("💡 View logs with: docker-compose logs -f", Colors.CYAN)
            else:
                print_colored(f"  ✗ Error starting containers: {result.stderr}", Colors.RED)
                print_colored("  💡 You can start manually with: docker-compose up -d", Colors.CYAN)
        except Exception as e:
            print_colored(f"  ✗ Error: {e}", Colors.RED)
            print_colored("  💡 You can start manually with: docker-compose up -d", Colors.CYAN)
    else:
        print_colored("\n💡 Start containers manually with: docker-compose up -d", Colors.CYAN)
    
    print_colored(f"\n✅ Fresh start complete! ({success_count} items processed)", Colors.GREEN)
    return True


def main():
    """Main function."""
    print_colored("\n" + "=" * 50, Colors.BOLD)
    print_colored("🔄 Multimodal RAG - Fresh Start Script", Colors.BOLD + Colors.MAGENTA)
    print_colored("=" * 50, Colors.BOLD)
    print_colored("\nThis script will delete:", Colors.YELLOW)
    print_colored("  • All uploaded documents", Colors.YELLOW)
    print_colored("  • All chat history", Colors.YELLOW)
    print_colored("  • All vector database data", Colors.YELLOW)
    print_colored("  • All processed files", Colors.YELLOW)
    print_colored("\n⚠️  This action CANNOT be undone!", Colors.RED + Colors.BOLD)
    
    print_colored("\nSelect environment:", Colors.BOLD + Colors.CYAN)
    print_colored("  1. Local environment (uvicorn/manual)", Colors.CYAN)
    print_colored("  2. Docker environment (docker-compose)", Colors.CYAN)
    print_colored("  0. Cancel", Colors.CYAN)
    
    while True:
        choice = input(f"\n{Colors.YELLOW}Enter your choice (1/2/0): {Colors.RESET}").strip()
        
        if choice == "1":
            fresh_start_local()
            break
        elif choice == "2":
            fresh_start_docker()
            break
        elif choice == "0":
            print_colored("❌ Cancelled.", Colors.RED)
            sys.exit(0)
        else:
            print_colored("❌ Invalid choice. Please enter 1, 2, or 0.", Colors.RED)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n❌ Interrupted by user.", Colors.RED)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ Unexpected error: {e}", Colors.RED)
        sys.exit(1)

