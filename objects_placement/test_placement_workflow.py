#!/usr/bin/env python3
"""
Test script to demonstrate the object placement workflow
"""

import json
import os

def check_placement_config():
    """Check the current object placement configuration"""
    config_file = "object_placements.json"
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print(f"Configuration file found: {config_file}")
        print(f"Scene: {config.get('scene', 'Not specified')}")
        print(f"Number of objects: {len(config.get('objects', []))}")
        
        if config.get('objects'):
            print("\nPlaced objects:")
            for i, obj in enumerate(config['objects']):
                pos = obj['position']
                print(f"  {i+1}. {obj['name']} at ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
        else:
            print("\nNo objects placed yet.")
            
        return config
    else:
        print(f"Configuration file not found: {config_file}")
        print("Run simple_object_placement.py first to create object placements.")
        return None

def show_usage():
    """Show how to use the placement workflow"""
    print("\n" + "="*60)
    print("OBJECT PLACEMENT WORKFLOW")
    print("="*60)
    print("\n1. CREATE OBJECT PLACEMENTS:")
    print("   python simple_object_placement.py")
    print("   - Click to place objects interactively")
    print("   - Press Enter to save configuration")
    print("\n2. VIEW SCENE WITH PLACED OBJECTS:")
    print("   python enhanced_object_placement.py")
    print("   - Choose option 1 to load from config")
    print("   - Navigate the scene to see placed objects")
    print("\n3. CONFIGURATION FILE:")
    print("   - Saved as: object_placements.json")
    print("   - Contains object names and 3D positions")
    print("   - Can be edited manually if needed")

if __name__ == "__main__":
    show_usage()
    print("\n" + "="*60)
    print("CURRENT CONFIGURATION STATUS")
    print("="*60)
    check_placement_config()
