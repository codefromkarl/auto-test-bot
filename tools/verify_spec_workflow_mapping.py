import os
import re
import glob

SPECS_DIR = "specs"
WORKFLOWS_DIR = "workflows"

def get_all_workflows():
    """Get a set of all actual workflow files."""
    workflows = set()
    for root, _, files in os.walk(WORKFLOWS_DIR):
        for file in files:
            if file.endswith(".yaml") or file.endswith(".yml"):
                # Store relative path matches spec convention
                rel_path = os.path.relpath(os.path.join(root, file), ".")
                workflows.add(rel_path)
    return workflows

def verify_specs(existing_workflows):
    """Scan specs and verify references."""
    
    spec_map = {} # Spec -> [Referenced Workflows]
    missing_refs = {} # Spec -> [Missing Workflows]
    referenced_workflows = set()

    spec_files = glob.glob(os.path.join(SPECS_DIR, "*.md"))
    
    print(f"Checking {len(spec_files)} spec files against {len(existing_workflows)} workflow files...\n")

    for spec_path in sorted(spec_files):
        if os.path.basename(spec_path) == "README.md":
            continue
            
        with open(spec_path, "r") as f:
            content = f.read()
            
        # Regex to find workflow paths mentioned in markdown
        # Matches: workflows/xxx/yyy.yaml
        refs = re.findall(r"(workflows/[\w\-\./]+\.yaml)", content)
        
        # Deduplicate
        refs = sorted(list(set(refs)))
        
        spec_name = os.path.basename(spec_path)
        spec_map[spec_name] = refs
        
        print(f"📄 {spec_name}")
        if not refs:
            print(f"   ⚠️  No workflows referenced!")
        
        for ref in refs:
            referenced_workflows.add(ref)
            if ref in existing_workflows:
                print(f"   ✅ {ref}")
            else:
                print(f"   ❌ {ref} (FILE NOT FOUND)")
                if spec_name not in missing_refs:
                    missing_refs[spec_name] = []
                missing_refs[spec_name].append(ref)
        print("")

    # Check for Orphan Workflows
    orphans = sorted(list(existing_workflows - referenced_workflows))
    
    print("-" * 40)
    print("🔍 Summary")
    print("-" * 40)
    
    if missing_refs:
        print("\n🚩 BROKEN LINKS (Spec references missing files):")
        for spec, missing in missing_refs.items():
            print(f"  {spec}:")
            for m in missing:
                print(f"    - {m}")
    else:
        print("\n✅ All referenced workflows exist.")

    if orphans:
        print(f"\n👻 ORPHAN WORKFLOWS ({len(orphans)} files not referenced by any Spec):")
        # Group by folder for cleaner output
        orphan_map = {}
        for o in orphans:
            folder = os.path.dirname(o)
            if folder not in orphan_map:
                orphan_map[folder] = []
            orphan_map[folder].append(os.path.basename(o))
            
        for folder, files in sorted(orphan_map.items()):
            print(f"  📂 {folder}/\n")
            if len(files) > 5:
                print(f"    - {len(files)} files (e.g., {files[0]}, {files[1]}...)")
            else:
                for f in files:
                    print(f"    - {f}")
    else:
        print("\n🎉 100% Workflow Coverage! (No orphans)")

if __name__ == "__main__":
    all_wfs = get_all_workflows()
    verify_specs(all_wfs)
