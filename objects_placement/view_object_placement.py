#!/usr/bin/env python3
"""
Enhanced YCB Object Placement with Interactive Configuration Support
Supports both random placement and loading from interactive placement configs.
"""

import habitat_sim
import numpy as np
import cv2
import os
import json
from habitat_sim.utils.common import quat_from_angle_axis
import magnum as mn

class EnhancedYCBPlacer:
    def __init__(self, scene_path, ycb_base_path="/home/yidu/extraSpace_projects/Foundation_Symbolic/habitat-lab/data/objects/ycb"):
        self.scene_path = scene_path
        self.ycb_base_path = ycb_base_path
        self.ycb_config_path = os.path.join(ycb_base_path, "configs")
        self.added_objects = []
    
    def create_simulator_with_hm3d(self):
        """Create simulator with HM3D scene"""
        backend_cfg = habitat_sim.SimulatorConfiguration()
        backend_cfg.scene_id = self.scene_path
        backend_cfg.enable_physics = True
        
        # Sensor setup
        sensor_specs = []
        
        # RGB sensor
        color_sensor_spec = habitat_sim.CameraSensorSpec()
        color_sensor_spec.uuid = "color_sensor"
        color_sensor_spec.sensor_type = habitat_sim.SensorType.COLOR
        color_sensor_spec.resolution = [720, 1280]
        color_sensor_spec.position = [0.0, 1.5, 0.0]
        sensor_specs.append(color_sensor_spec)
        
        # Depth sensor
        depth_sensor_spec = habitat_sim.CameraSensorSpec()
        depth_sensor_spec.uuid = "depth_sensor"
        depth_sensor_spec.sensor_type = habitat_sim.SensorType.DEPTH
        depth_sensor_spec.resolution = [720, 1280]
        depth_sensor_spec.position = [0.0, 1.5, 0.0]
        sensor_specs.append(depth_sensor_spec)
        
        # Agent configuration
        agent_cfg = habitat_sim.agent.AgentConfiguration()
        agent_cfg.sensor_specifications = sensor_specs
        agent_cfg.action_space = {
            "move_forward": habitat_sim.agent.ActionSpec(
                "move_forward", habitat_sim.agent.ActuationSpec(amount=0.25)
            ),
            "turn_left": habitat_sim.agent.ActionSpec(
                "turn_left", habitat_sim.agent.ActuationSpec(amount=10.0)
            ),
            "turn_right": habitat_sim.agent.ActionSpec(
                "turn_right", habitat_sim.agent.ActuationSpec(amount=10.0)
            ),
        }
        
        cfg = habitat_sim.Configuration(backend_cfg, [agent_cfg])
        sim = habitat_sim.Simulator(cfg)
        
        return sim
    
    def load_placement_config(self, config_file="object_placements.json"):
        """Load object placement configuration from interactive tool"""
        if not os.path.exists(config_file):
            print(f"Configuration file not found: {config_file}")
            return None
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"Loaded configuration with {len(config.get('objects', []))} objects")
            return config
        
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return None
    
    def place_objects_from_config(self, sim, config):
        """Place objects using positions from interactive configuration"""
        if not config or 'objects' not in config:
            print("No valid configuration provided")
            return []
        
        obj_template_mgr = sim.get_object_template_manager()
        rigid_obj_mgr = sim.get_rigid_object_manager()
        
        added_objects = []
        
        for obj_config in config['objects']:
            obj_name = obj_config['name']
            position = obj_config['position']
            
            obj_config_file = os.path.join(self.ycb_config_path, f"{obj_name}.object_config.json")
            
            if not os.path.exists(obj_config_file):
                print(f"Warning: Config file not found for {obj_name}")
                continue
            
            try:
                # Load object template
                obj_template_id = obj_template_mgr.load_configs(obj_config_file)[0]
                
                # Add object to scene
                obj_instance = rigid_obj_mgr.add_object_by_template_id(obj_template_id)
                
                if obj_instance is None:
                    print(f"Failed to add object {obj_name}")
                    continue
                
                # Set position from config
                obj_instance.translation = mn.Vector3(position[0], position[1], position[2])
                
                # Set rotation (random or from config if available)
                if 'rotation' in obj_config:
                    # Use saved rotation if available
                    rot = obj_config['rotation']
                    obj_instance.rotation = mn.Quaternion([rot[1], rot[2], rot[3]], rot[0])
                else:
                    # Random rotation around Y axis
                    angle = np.random.uniform(0, 2*np.pi)
                    quat = quat_from_angle_axis(angle, np.array([0, 1, 0]))
                    obj_instance.rotation = mn.Quaternion([quat.x, quat.y, quat.z], quat.w)
                
                # Make it static
                obj_instance.motion_type = habitat_sim.physics.MotionType.STATIC
                
                added_objects.append({
                    'name': obj_name,
                    'instance': obj_instance,
                    'id': obj_instance.object_id,
                    'position': position
                })
                
                print(f"✓ Placed {obj_name} at position {position}")
                
            except Exception as e:
                print(f"Error adding {obj_name}: {e}")
        
        self.added_objects = added_objects
        return added_objects
    
    def add_ycb_objects_random(self, sim, object_list=None):
        """Original random placement method"""
        obj_template_mgr = sim.get_object_template_manager()
        rigid_obj_mgr = sim.get_rigid_object_manager()
        
        if object_list is None:
            object_list = [
                '002_master_chef_can',
                '003_cracker_box',
                '005_tomato_soup_can',
                '013_apple',
                '011_banana',
                '025_mug',
                '077_rubiks_cube',
                '055_baseball',
                '006_mustard_bottle',
                '030_fork'
            ]
        
        # Get navigable points
        nav_points = []
        for _ in range(len(object_list)):
            point = sim.pathfinder.get_random_navigable_point()
            nav_points.append(point)
        
        added_objects = []
        
        for obj_name, nav_point in zip(object_list, nav_points):
            obj_config_file = os.path.join(self.ycb_config_path, f"{obj_name}.object_config.json")
            
            if not os.path.exists(obj_config_file):
                print(f"Warning: Config file not found for {obj_name}")
                continue
            
            try:
                obj_template_id = obj_template_mgr.load_configs(obj_config_file)[0]
                obj_instance = rigid_obj_mgr.add_object_by_template_id(obj_template_id)
                
                if obj_instance is None:
                    print(f"Failed to add object {obj_name}")
                    continue
                
                position = mn.Vector3(nav_point[0], nav_point[1] + 0.5, nav_point[2])
                obj_instance.translation = position
                
                angle = np.random.uniform(0, 2*np.pi)
                quat = quat_from_angle_axis(angle, np.array([0, 1, 0]))
                obj_instance.rotation = mn.Quaternion([quat.x, quat.y, quat.z], quat.w)
                
                obj_instance.motion_type = habitat_sim.physics.MotionType.STATIC
                
                added_objects.append({
                    'name': obj_name,
                    'instance': obj_instance,
                    'id': obj_instance.object_id,
                    'position': [nav_point[0], nav_point[1] + 0.5, nav_point[2]]
                })
                
                print(f"✓ Added {obj_name} at position {position}")
                
            except Exception as e:
                print(f"Error adding {obj_name}: {e}")
        
        self.added_objects = added_objects
        return added_objects
    
    def save_current_view(self, sim, filename):
        """Save current view to file with proper color conversion"""
        observations = sim.get_sensor_observations()
        if "color_sensor" in observations:
            rgb = observations["color_sensor"]
            rgb_img = (rgb * 255).astype(np.uint8)
            bgr_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filename, bgr_img)
            print(f"Saved view: {filename}")
            return True
        return False
    
    def interactive_viewer_mode(self, sim):
        """Interactive OpenCV-based viewer similar to simple_object_placement.py"""
        print("\nInteractive Viewer Mode:")
        print("Navigate the scene with your placed objects!")
        
        agent = sim.get_agent(0)
        
        # Setup OpenCV window
        window_name = "Scene Viewer - Navigate with WASD"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        # Display available controls
        print("\nControls:")
        print("- W: Move forward")
        print("- S: Move backward") 
        print("- A: Turn left")
        print("- D: Turn right")
        print("- Q: Turn left (fine)")
        print("- E: Turn right (fine)")
        print("- V: Toggle depth view")
        print("- C: Capture current view to file")
        print("- ESC: Exit viewer")
        
        show_depth = False
        capture_count = 0
        
        # Initial view update
        self.update_interactive_view(sim, show_depth)
        
        # Main interaction loop
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                print("Exiting interactive viewer...")
                break
            elif key == ord('v'):  # Toggle depth view
                show_depth = not show_depth
                if show_depth:
                    print("Switched to depth view")
                else:
                    print("Switched to RGB view")
                self.update_interactive_view(sim, show_depth)
            elif key == ord('c'):  # Capture view
                filename = f"interactive_capture_{capture_count:03d}.jpg"
                if self.save_current_view(sim, filename):
                    capture_count += 1
                    print(f"Captured view: {filename}")
            elif key == ord('w'):  # Move forward
                try:
                    agent.act("move_forward")
                    self.update_interactive_view(sim, show_depth)
                except:
                    print("Cannot move forward")
            elif key == ord('s'):  # Move backward
                try:
                    # Turn around, move forward, turn back
                    for _ in range(18):
                        agent.act("turn_left")
                    agent.act("move_forward")
                    for _ in range(18):
                        agent.act("turn_left")
                    self.update_interactive_view(sim, show_depth)
                except:
                    print("Cannot move backward")
            elif key == ord('a') or key == ord('q'):  # Turn left
                try:
                    agent.act("turn_left")
                    self.update_interactive_view(sim, show_depth)
                except:
                    print("Cannot turn left")
            elif key == ord('d') or key == ord('e'):  # Turn right
                try:
                    agent.act("turn_right")
                    self.update_interactive_view(sim, show_depth)
                except:
                    print("Cannot turn right")
        
        cv2.destroyAllWindows()
        print(f"Interactive viewing ended. Captured {capture_count} images.")
    
    def update_interactive_view(self, sim, show_depth=False):
        """Update the interactive OpenCV display"""
        obs = sim.get_sensor_observations()
        
        if show_depth:
            # Show depth view
            depth = obs.get("depth_sensor")
            if depth is not None:
                # Normalize depth for visualization (0-5 meters)
                depth_vis = np.clip(depth, 0, 5.0) / 5.0
                depth_vis = (depth_vis * 255).astype(np.uint8)
                img = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
                
                # Add text overlay
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(img, "Depth View - Press V for RGB", (10, 30), font, 0.6, (255, 255, 255), 2)
            else:
                print("No depth data available")
                return
        else:
            # Show RGB view
            rgb = obs.get("color_sensor")
            if rgb is not None:
                # Debug: Print RGB data format on first call
                if not hasattr(self, '_rgb_debug_printed'):
                    print(f"RGB Debug: shape={rgb.shape}, dtype={rgb.dtype}, min={rgb.min():.3f}, max={rgb.max():.3f}")
                    self._rgb_debug_printed = True
                
                # Handle different possible RGB formats
                if rgb.dtype == np.float32 or rgb.dtype == np.float64:
                    # RGB values are in [0, 1] range - convert to [0, 255]
                    if rgb.max() <= 1.0:
                        img = (rgb * 255).astype(np.uint8)
                    else:
                        # Already in [0, 255] range but float
                        img = rgb.astype(np.uint8)
                else:
                    # Already uint8
                    img = rgb
                
                # Convert RGB to BGR for OpenCV display
                img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                
                # Add text overlay
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(img_bgr, f"Objects: {len(self.added_objects)}", (10, 30), font, 0.7, (0, 255, 0), 2)
                cv2.putText(img_bgr, "WASD: move | V: depth | C: capture | ESC: exit", (10, 690), font, 0.5, (255, 255, 255), 1)
                
                img = img_bgr
            else:
                print("No RGB data available")
                return
        
        cv2.imshow("Scene Viewer - Navigate with WASD", img)
    
    def launch_habitat_viewer_with_objects(self, sim):
        """Try to launch external habitat-viewer with the scene and objects"""
        print("\nAttempting to launch habitat-viewer...")
        
        try:
            import subprocess
            
            # Check if habitat-viewer is available
            result = subprocess.run(['habitat-viewer', '--help'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✓ habitat-viewer found!")
                print("Note: Objects placed via code may not be visible in external viewer")
                print("The external viewer loads the base scene only")
                
                # Launch viewer with the scene
                cmd = ['habitat-viewer', '--enable-physics', self.scene_path]
                print(f"Running: {' '.join(cmd)}")
                print("Close the viewer window to return to this script")
                
                subprocess.run(cmd, check=False)
                print("habitat-viewer closed")
                
            else:
                raise FileNotFoundError("habitat-viewer not working")
                
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"✗ Could not launch habitat-viewer: {e}")
            print("Alternative: Using built-in interactive viewer...")
            self.interactive_viewer_mode(sim)

def test_enhanced_placement():
    """Test with support for both interactive configs and random placement"""
    
    scene_path = "/home/yidu/extraSpace_projects/data/datasets/hm3d/train/00000-kfPV7w3FaU5/kfPV7w3FaU5.basis.glb"
    
    print("=== Enhanced YCB Object Placement Test ===")
    print(f"Scene: {scene_path}")
    
    # Initialize manager
    manager = EnhancedYCBPlacer(scene_path)
    
    # Create simulator
    sim = manager.create_simulator_with_hm3d()
    print("Simulator created successfully")
    
    # Initialize agent
    agent = sim.initialize_agent(0)
    
    # Set agent to a good starting position
    nav_point = sim.pathfinder.get_random_navigable_point()
    agent_state = habitat_sim.AgentState()
    agent_state.position = mn.Vector3(nav_point[0], nav_point[1] + 1.5, nav_point[2])
    agent_state.rotation = quat_from_angle_axis(0, np.array([0, 1, 0]))
    agent.set_state(agent_state)
    
    # Choose placement method
    print("\n=== Object Placement Options ===")
    print("1. Load from interactive placement config (object_placements.json)")
    print("2. Random placement at navigable points")
    print("3. Skip object placement")
    
    choice = input("Choose placement method (1/2/3): ").strip()
    
    added_objects = []
    
    if choice == '1':
        print("\n=== Loading from Interactive Configuration ===")
        config = manager.load_placement_config()
        if config:
            added_objects = manager.place_objects_from_config(sim, config)
        else:
            print("Failed to load configuration, falling back to random placement")
            added_objects = manager.add_ycb_objects_random(sim, 
                ['002_master_chef_can', '003_cracker_box', '013_apple', '025_mug', '077_rubiks_cube'])
    
    elif choice == '2':
        print("\n=== Random Placement ===")
        added_objects = manager.add_ycb_objects_random(sim, 
            ['002_master_chef_can', '003_cracker_box', '013_apple', '025_mug', '077_rubiks_cube'])
    
    else:
        print("Skipping object placement")
    
    if added_objects:
        print(f"\n✓ Successfully placed {len(added_objects)} objects:")
        for i, obj in enumerate(added_objects):
            print(f"  {i+1}. {obj['name']} at {obj['position']}")
        
        # Move agent near first object for better starting view
        if len(added_objects) > 0:
            first_obj_pos = added_objects[0]['position']
            agent_state = habitat_sim.AgentState()
            agent_pos = mn.Vector3(
                first_obj_pos[0] - 2.0,
                first_obj_pos[1],
                first_obj_pos[2]
            )
            agent_state.position = agent_pos
            # Look towards the object
            direction = np.array([first_obj_pos[0] - agent_pos.x, 0, first_obj_pos[2] - agent_pos.z])
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)
                angle = np.arctan2(direction[2], direction[0])
                agent_state.rotation = quat_from_angle_axis(angle, np.array([0, 1, 0]))
            agent.set_state(agent_state)
            print(f"Positioned camera near {added_objects[0]['name']}")
        
        # Interactive viewing options
        print("\n=== Interactive Viewing Options ===")
        print("1. Built-in interactive viewer (recommended - shows objects)")
        print("2. Try external habitat-viewer (may not show placed objects)")
        print("3. Skip viewing")
        
        view_choice = input("Choose viewing method (1/2/3): ").strip()
        
        if view_choice == '1':
            print("\nStarting built-in interactive viewer...")
            manager.interactive_viewer_mode(sim)
        elif view_choice == '2':
            manager.launch_habitat_viewer_with_objects(sim)
        else:
            print("Skipping interactive viewing")
    
    else:
        print("No objects placed - nothing to view")
    
    # Print summary
    print("\n=== Summary ===")
    print(f"Scene: {scene_path}")
    print(f"Objects placed: {len(added_objects)}")
    if added_objects:
        for obj in added_objects:
            print(f"  - {obj['name']} at position {obj['position']}")
    
    sim.close()
    print("\nTest completed!")

if __name__ == "__main__":
    test_enhanced_placement()
