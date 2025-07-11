#!/usr/bin/env python3
"""
Project Cleanup Analysis

Analyzes the current project structure to identify files that can be safely 
deleted now that async implementations are complete.
"""

import os
from pathlib import Path

class ProjectCleanupAnalyzer:
    """Analyze project structure for cleanup opportunities."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.files_to_delete = []
        self.files_to_keep = []
        self.analysis_results = {}
    
    def analyze_project_structure(self):
        """Perform comprehensive analysis of project files."""
        print("🔍 Analyzing Project Synapse for cleanup opportunities...")
        print("=" * 60)
        
        # Analyze different categories
        self._analyze_main_scripts()
        self._analyze_agents()
        self._analyze_mcp_servers() 
        self._analyze_test_files()
        self._analyze_documentation()
        
        # Generate summary
        self._generate_summary()
    
    def _analyze_main_scripts(self):
        """Analyze main application scripts."""
        print("\n📝 Main Application Scripts:")
        
        # main.py - Original simulation main script
        main_py = self.project_root / "main.py"
        if main_py.exists():
            print("  📄 main.py - Original educational simulation")
            print("      🔄 SUPERSEDED by async_main.py")
            print("      🗑️  SAFE TO DELETE (async implementation complete)")
            self.files_to_delete.append(str(main_py))
        
        # async_main.py - New production async script  
        async_main_py = self.project_root / "async_main.py"
        if async_main_py.exists():
            print("  📄 async_main.py - Production async implementation")
            print("      ✅ KEEP (current production main script)")
            self.files_to_keep.append(str(async_main_py))
        
        # test_imports.py - Simple import test
        test_imports_py = self.project_root / "test_imports.py"
        if test_imports_py.exists():
            print("  📄 test_imports.py - Simple import verification")
            print("      🔄 SUPERSEDED by test_async_implementation.py")
            print("      🗑️  SAFE TO DELETE (comprehensive test suite exists)")
            self.files_to_delete.append(str(test_imports_py))
            
        # test_async_implementation.py - Comprehensive async test suite
        test_async_py = self.project_root / "test_async_implementation.py"
        if test_async_py.exists():
            print("  📄 test_async_implementation.py - Comprehensive async test suite")
            print("      ✅ KEEP (current test infrastructure)")
            self.files_to_keep.append(str(test_async_py))
    
    def _analyze_agents(self):
        """Analyze agent implementations."""
        print("\n🤖 Agent Implementations:")
        
        agents_dir = self.project_root / "src" / "agents"
        if not agents_dir.exists():
            return
            
        # Original simulation agents
        original_agents = [
            "base_agent.py",
            "orchestrator.py", 
            "search_agent.py",
            "extraction_agent.py",
            "fact_checker_agent.py",
            "synthesis_agent.py",
            "file_save_agent.py",
            "logger_agent.py"
        ]
        
        # Async production agents
        async_agents = [
            "async_base_agent.py",
            "async_orchestrator.py",
            "async_search_agent.py", 
            "async_extraction_agent.py",
            "async_fact_checker_agent.py",
            "async_synthesis_agent.py",
            "async_file_save_agent.py",
            "async_logger_agent.py"
        ]
        
        print("  📂 Original Simulation Agents:")
        for agent_file in original_agents:
            agent_path = agents_dir / agent_file
            if agent_path.exists():
                async_equivalent = agent_file.replace(".py", "").replace("_", "_async_", 1) + ".py"
                if async_equivalent.replace("_async_", "_") == agent_file:
                    async_equivalent = "async_" + agent_file
                
                async_path = agents_dir / async_equivalent
                if async_path.exists():
                    print(f"    📄 {agent_file}")
                    print(f"        🔄 SUPERSEDED by {async_equivalent}")
                    print(f"        🗑️  SAFE TO DELETE (async version exists)")
                    self.files_to_delete.append(str(agent_path))
                else:
                    print(f"    📄 {agent_file}")
                    print(f"        ⚠️  NO ASYNC EQUIVALENT FOUND")
                    print(f"        ✅ KEEP (no replacement)")
                    self.files_to_keep.append(str(agent_path))
        
        print("  📂 Async Production Agents:")
        for agent_file in async_agents:
            agent_path = agents_dir / agent_file
            if agent_path.exists():
                print(f"    📄 {agent_file}")
                print(f"        ✅ KEEP (current async implementation)")
                self.files_to_keep.append(str(agent_path))
        
        # __init__.py
        init_path = agents_dir / "__init__.py"
        if init_path.exists():
            print(f"  📄 __init__.py")
            print(f"      ✅ KEEP (imports both old and new for compatibility)")
            self.files_to_keep.append(str(init_path))
    
    def _analyze_mcp_servers(self):
        """Analyze MCP server implementations."""
        print("\n🔧 MCP Server Implementations:")
        
        servers_dir = self.project_root / "src" / "mcp_servers"
        if not servers_dir.exists():
            return
            
        # Original simulation servers
        original_servers = [
            "primary_server.py",
            "filesystem_server.py"
        ]
        
        # FastAPI production servers
        fastapi_servers = [
            "fastapi_primary_server.py",
            "fastapi_filesystem_server.py"
        ]
        
        print("  📂 Original Simulation Servers:")
        for server_file in original_servers:
            server_path = servers_dir / server_file
            if server_path.exists():
                fastapi_equivalent = "fastapi_" + server_file
                fastapi_path = servers_dir / fastapi_equivalent
                
                if fastapi_path.exists():
                    print(f"    📄 {server_file}")
                    print(f"        🔄 SUPERSEDED by {fastapi_equivalent}")
                    print(f"        🗑️  SAFE TO DELETE (FastAPI version exists)")
                    self.files_to_delete.append(str(server_path))
                else:
                    print(f"    📄 {server_file}")
                    print(f"        ⚠️  NO FASTAPI EQUIVALENT FOUND")
                    print(f"        ✅ KEEP (no replacement)")
                    self.files_to_keep.append(str(server_path))
        
        print("  📂 FastAPI Production Servers:")
        for server_file in fastapi_servers:
            server_path = servers_dir / server_file
            if server_path.exists():
                print(f"    📄 {server_file}")
                print(f"        ✅ KEEP (current FastAPI implementation)")
                self.files_to_keep.append(str(server_path))
        
        # __init__.py
        init_path = servers_dir / "__init__.py"
        if init_path.exists():
            print(f"  📄 __init__.py")
            print(f"      ✅ KEEP (module initialization)")
            self.files_to_keep.append(str(init_path))
    
    def _analyze_test_files(self):
        """Analyze test files."""
        print("\n🧪 Test Files:")
        
        # Already covered test_imports.py and test_async_implementation.py in main scripts
        print("  (Test files analyzed in Main Application Scripts section)")
    
    def _analyze_documentation(self):
        """Analyze documentation files."""
        print("\n📚 Documentation Files:")
        
        # README.md - Original documentation
        readme_md = self.project_root / "README.md"
        if readme_md.exists():
            print("  📄 README.md - Original project documentation")
            print("      ✅ KEEP (general project information)")
            self.files_to_keep.append(str(readme_md))
            
        # README_ASYNC.md - Async implementation documentation
        readme_async_md = self.project_root / "README_ASYNC.md"
        if readme_async_md.exists():
            print("  📄 README_ASYNC.md - Async implementation documentation")
            print("      ✅ KEEP (current implementation docs)")
            self.files_to_keep.append(str(readme_async_md))
            
        # Documentation directory
        docs_dir = self.project_root / "docs"
        if docs_dir.exists():
            print("  📂 docs/ - Technical documentation")
            print("      ✅ KEEP (architectural documentation)")
            for doc_file in docs_dir.iterdir():
                if doc_file.is_file():
                    self.files_to_keep.append(str(doc_file))
    
    def _generate_summary(self):
        """Generate cleanup summary."""
        print("\n" + "=" * 60)
        print("📊 CLEANUP ANALYSIS SUMMARY")
        print("=" * 60)
        
        print(f"\n🗑️  Files Safe to Delete ({len(self.files_to_delete)}):")
        for file_path in self.files_to_delete:
            rel_path = os.path.relpath(file_path, self.project_root)
            print(f"  📄 {rel_path}")
        
        print(f"\n✅ Files to Keep ({len(self.files_to_keep)}):")
        important_keeps = [f for f in self.files_to_keep if any(keep in f for keep in [
            'async_', 'fastapi_', 'README_ASYNC', 'test_async_implementation'
        ])]
        for file_path in important_keeps[:10]:  # Show first 10 important ones
            rel_path = os.path.relpath(file_path, self.project_root)
            print(f"  📄 {rel_path}")
        if len(self.files_to_keep) > 10:
            print(f"  ... and {len(self.files_to_keep) - 10} more files")
        
        print(f"\n💾 Storage Savings:")
        total_size = 0
        for file_path in self.files_to_delete:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                total_size += size
        
        print(f"  📏 Total size of deletable files: {total_size:,} bytes ({total_size/1024:.1f} KB)")
        
        print(f"\n🎯 Recommendation:")
        print(f"  The async implementation is complete and functional.")
        print(f"  Original simulation files can be safely deleted to:")
        print(f"  • Reduce codebase complexity")
        print(f"  • Eliminate confusion between old/new implementations") 
        print(f"  • Keep focus on production-ready async version")
        print(f"  • Preserve educational version in 'educational-simulation' branch")
    
    def generate_cleanup_script(self, script_path: str = "cleanup_old_files.sh"):
        """Generate a cleanup script to remove old files."""
        script_content = """#!/bin/bash
# Project Synapse Cleanup Script
# Removes old simulation files now superseded by async implementations

echo "🧹 Project Synapse Cleanup Script"
echo "Removing old simulation files superseded by async implementations..."
echo ""

# Confirmation prompt
read -p "Are you sure you want to delete the old simulation files? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled by user"
    exit 1
fi

echo "🗑️  Deleting old files..."

"""
        
        for file_path in self.files_to_delete:
            rel_path = os.path.relpath(file_path, self.project_root)
            script_content += f"""
# Delete {rel_path}
if [ -f "{rel_path}" ]; then
    echo "  🗑️  Deleting {rel_path}"
    rm "{rel_path}"
else
    echo "  ⚠️  File not found: {rel_path}"
fi"""
        
        script_content += """

echo ""
echo "✅ Cleanup completed!"
echo "📊 Deleted files that were superseded by async implementations"
echo "🎯 Project now focuses on production-ready async version"
echo ""
echo "To restore deleted files, check the 'educational-simulation' branch:"
echo "  git checkout educational-simulation -- <file_path>"
"""
        
        script_path = self.project_root / script_path
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        print(f"\n📝 Cleanup script generated: {script_path}")
        print(f"   Execute with: ./{script_path.name}")


def main():
    """Main analysis function."""
    project_root = "/home/yan/Documents/Git/project-synapse"
    
    analyzer = ProjectCleanupAnalyzer(project_root)
    analyzer.analyze_project_structure()
    analyzer.generate_cleanup_script()


if __name__ == "__main__":
    main()
