#!/usr/bin/env python3
"""
Auto-patcher script to replace OpenAI API calls with Ollama in evaluation files
"""

import os
import sys
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a backup of the original file"""
    backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"  ✓ Backup created: {backup_path}")
    return backup_path

def patch_file(filepath, replacements):
    """Apply replacements to a file"""
    print(f"Patching {filepath}...")
    
    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Create backup
    backup_file(filepath)
    
    # Apply replacements
    modified = False
    for old_text, new_text in replacements:
        if old_text in content:
            content = content.replace(old_text, new_text)
            modified = True
            print(f"  ✓ Replaced: {old_text[:50]}...")
    
    if modified:
        # Write the modified content
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✓ File patched successfully")
    else:
        print(f"  - No changes needed")
    
    return modified

def patch_aeqa_file():
    """Patch the AEQA evaluation file"""
    filepath = "src/eval_utils_gpt_aeqa.py"
    
    replacements = [
        # Replace the main API calls with Ollama
        ('response = call_openai_api(prefiltering_sys, prefiltering_content)', 
         'response = call_ollama_api(prefiltering_sys, prefiltering_content)'),
        
        ('full_response = call_openai_api(sys_prompt, content)',
         'full_response = call_ollama_api(sys_prompt, content)'),
        
        # Update error messages
        ('print("call_openai_api returns None, retrying")',
         'print("call_ollama_api returns None, retrying")')
    ]
    
    return patch_file(filepath, replacements)

def patch_goatbench_file():
    """Patch the GoatBench evaluation file"""
    filepath = "src/eval_utils_gpt_goatbench.py"
    
    replacements = [
        # Replace the main API calls with Ollama  
        ('response = call_openai_api(prefiltering_sys, prefiltering_content)',
         'response = call_ollama_api(prefiltering_sys, prefiltering_content)'),
        
        ('response = call_openai_api(sys_prompt, content)',
         'response = call_ollama_api(sys_prompt, content)'),
        
        # Update error messages
        ('print("call_openai_api returns None, retrying")',
         'print("call_ollama_api returns None, retrying")')
    ]
    
    return patch_file(filepath, replacements)

def patch_const_file():
    """Patch the constants file to enable Ollama by default"""
    filepath = "src/const.py"
    
    replacements = [
        ('USE_OLLAMA = False', 'USE_OLLAMA = True')
    ]
    
    return patch_file(filepath, replacements)

def patch_smart_api():
    """Alternative patching that uses the smart API function"""
    print("Patching files to use smart API function...")
    
    files_to_patch = [
        "src/eval_utils_gpt_aeqa.py",
        "src/eval_utils_gpt_goatbench.py"
    ]
    
    replacements = [
        ('response = call_openai_api(prefiltering_sys, prefiltering_content)',
         'response = call_api_smart(prefiltering_sys, prefiltering_content)'),
        
        ('full_response = call_openai_api(sys_prompt, content)',
         'full_response = call_api_smart(sys_prompt, content)'),
        
        ('response = call_openai_api(sys_prompt, content)',
         'response = call_api_smart(sys_prompt, content)')
    ]
    
    modified_files = []
    for filepath in files_to_patch:
        if os.path.exists(filepath):
            modified = patch_file(filepath, replacements)
            if modified:
                modified_files.append(filepath)
    
    return modified_files

def restore_backups():
    """Restore files from backups"""
    print("Looking for backup files...")
    
    backup_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if '.backup.' in file:
                backup_files.append(os.path.join(root, file))
    
    if not backup_files:
        print("No backup files found.")
        return
    
    print(f"Found {len(backup_files)} backup files:")
    for i, backup in enumerate(backup_files, 1):
        print(f"  {i}. {backup}")
    
    choice = input("\nRestore all backups? [y/N]: ").lower()
    if choice in ['y', 'yes']:
        for backup in backup_files:
            original = backup.split('.backup.')[0]
            if os.path.exists(original):
                shutil.copy2(backup, original)
                print(f"  ✓ Restored: {original}")
            else:
                print(f"  ⚠ Original file not found: {original}")
    else:
        print("Backup restoration cancelled.")

def main():
    print("Ollama Integration Auto-Patcher")
    print("=" * 40)
    print()
    
    if not os.path.exists("src/eval_utils_gpt_aeqa.py"):
        print("Error: Not in the correct directory. Please run from the 3D-Mem root directory.")
        sys.exit(1)
    
    print("Choose patching method:")
    print("1. Direct replacement (call_openai_api → call_ollama_api)")
    print("2. Smart API (call_openai_api → call_api_smart)")
    print("3. Enable Ollama in config only")
    print("4. Restore from backups")
    print("5. Exit")
    
    choice = input("\nEnter your choice [1-5]: ").strip()
    
    if choice == "1":
        print("\nApplying direct Ollama replacements...")
        modified = []
        if patch_aeqa_file():
            modified.append("AEQA evaluation file")
        if patch_goatbench_file():
            modified.append("GoatBench evaluation file")
        
        if modified:
            print(f"\n✓ Successfully patched: {', '.join(modified)}")
            print("Note: Make sure to set USE_OLLAMA = True in src/const.py")
        else:
            print("\n- No files were modified (already patched or no matching patterns found)")
    
    elif choice == "2":
        print("\nApplying smart API replacements...")
        modified = patch_smart_api()
        if modified:
            print(f"\n✓ Successfully patched: {', '.join(modified)}")
            print("You can now control the provider using USE_OLLAMA in src/const.py")
        else:
            print("\n- No files were modified")
    
    elif choice == "3":
        print("\nEnabling Ollama in configuration...")
        if patch_const_file():
            print("\n✓ Configuration updated to use Ollama by default")
            print("Use call_api_smart() function to respect this setting")
        else:
            print("\n- Configuration already set or file not found")
    
    elif choice == "4":
        restore_backups()
    
    elif choice == "5":
        print("Exiting...")
        sys.exit(0)
    
    else:
        print("Invalid choice. Exiting...")
        sys.exit(1)
    
    print("\nNext steps:")
    print("1. Test the integration: python test_ollama_integration.py")
    print("2. Run your evaluation scripts as usual")
    print("3. Check the results and compare with OpenAI if needed")

if __name__ == "__main__":
    main()
