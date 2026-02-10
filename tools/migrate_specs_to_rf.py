import os
import re

SPECS_DIR = "specs"
WORKFLOWS_DIR = "workflows/fc"

def migrate_specs():
    # 1. Get available RF workflows
    rf_workflows = set()
    if os.path.exists(WORKFLOWS_DIR):
        for f in os.listdir(WORKFLOWS_DIR):
            if f.endswith("_rf.yaml"):
                rf_workflows.add(f)
    
    print(f"Found {len(rf_workflows)} RF workflow files.")

    # 2. Process Specs
    spec_files = [f for f in os.listdir(SPECS_DIR) if f.endswith(".md")]
    
    for spec_file in spec_files:
        path = os.path.join(SPECS_DIR, spec_file)
        with open(path, "r") as f:
            content = f.read()
            
        original_content = content
        
        # Regex to find standard FC workflow references
        # Matches: workflows/fc/naohai_FC_NH_002.yaml
        # Group 1: naohai_FC_NH_002
        matches = re.findall(r"(workflows/fc/(naohai_FC_NH_\d+)\.yaml)", content)
        
        replacements = 0
        for full_path, base_name in matches:
            # Check if RF version exists
            rf_filename = f"{base_name}_rf.yaml"
            if rf_filename in rf_workflows:
                rf_full_path = f"workflows/fc/{rf_filename}"
                # Replace in content
                content = content.replace(full_path, rf_full_path)
                replacements += 1
                print(f"[{spec_file}] Replacing {base_name}.yaml -> {rf_filename}")
            else:
                print(f"[{spec_file}] No RF version found for {base_name}.yaml")

        if replacements > 0:
            with open(path, "w") as f:
                f.write(content)
            print(f"✅ Updated {spec_file} with {replacements} RF workflows.\n")
        else:
            print(f"ℹ️  No changes needed for {spec_file}.\n")

if __name__ == "__main__":
    migrate_specs()
