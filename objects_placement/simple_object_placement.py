#!/usr/bin/env python3
"""
Simple Interactive Object Placement Tool
A streamlined version focused on click-to-place functionality.
"""

import habitat_sim
import numpy as np
import cv2
import os
import json
from habitat_sim.utils.common import quat_from_angle_axis
import magnum as mn

class SimpleObjectPlacer:
    def __init__(self, scene_path, ycb_base_path="/home/yidu/extraSpace_projects/Foundation_Symbolic/habitat-lab/data/objects/ycb", 
                 config_file="ycb_objects_config.json"):
        self.scene_path = scene_path
        self.ycb_base_path = ycb_base_path
        self.ycb_config_path = os.path.join(ycb_base_path, "configs")
        
        # Load object list from config file
        self.objects = self.load_objects_from_config(config_file)
        
        self.current_obj_idx = 0
        self.placed_objects = []
        self.click_positions = []
        
    def load_objects_from_config(self, config_file):
        """Load YCB objects list from configuration file"""
        try:
            # Try absolute path first, then relative to script directory
            if os.path.isabs(config_file):
                config_path = config_file
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                config_path = os.path.join(script_dir, config_file)
            
            with open(config_path, 'r') as f:
                config = json.load(f)
                objects = config.get('ycb_objects', [])
                
            print(f"Loaded {len(objects)} YCB objects from {config_path}")
            return objects
            
        except FileNotFoundError:
            print(f"Warning: Config file {config_file} not found. Using default object list.")
            # Fallback to original small list
            return [
                '002_master_chef_can',
                '003_cracker_box', 
                '013_apple',
                '025_mug',
                '077_rubiks_cube'
            ]
        except Exception as e:
            print(f"Error loading config file {config_file}: {e}")
            print("Using default object list.")
            return [
                '002_master_chef_can',
                '003_cracker_box', 
                '013_apple',
                '025_mug',
                '077_rubiks_cube'
            ]
        
    def create_sim(self):
        """Create basic simulator"""
        cfg = habitat_sim.SimulatorConfiguration()
        cfg.scene_id = self.scene_path
        cfg.enable_physics = True
        
        # RGB camera
        rgb_sensor = habitat_sim.CameraSensorSpec()
        rgb_sensor.uuid = "color"
        rgb_sensor.sensor_type = habitat_sim.SensorType.COLOR
        rgb_sensor.resolution = [720, 1280]
        rgb_sensor.position = [0.0, 1.5, 0.0]
        
        # Depth camera for 3D positioning
        depth_sensor = habitat_sim.CameraSensorSpec()
        depth_sensor.uuid = "depth"
        depth_sensor.sensor_type = habitat_sim.SensorType.DEPTH
        depth_sensor.resolution = [720, 1280]
        depth_sensor.position = [0.0, 1.5, 0.0]
        
        agent_cfg = habitat_sim.agent.AgentConfiguration()
        agent_cfg.sensor_specifications = [rgb_sensor, depth_sensor]
        
        sim = habitat_sim.Simulator(habitat_sim.Configuration(cfg, [agent_cfg]))
        return sim
    
    def mouse_click(self, event, x, y, flags, param):
        """Handle mouse clicks"""
        if event == cv2.EVENT_LBUTTONDOWN:
            print(f"Clicked at pixel ({x}, {y})")
            
            # Get 3D world position
            world_pos = self.pixel_to_world(x, y, param['sim'])
            
            if world_pos:
                # Place current object
                obj_name = self.objects[self.current_obj_idx]
                success = self.place_object(param['sim'], obj_name, world_pos)
                
                if success:
                    print(f"✓ Placed {obj_name} at {world_pos}")
                    self.placed_objects.append({
                        'name': obj_name,
                        'position': world_pos,
                        'click_pixel': [x, y]  # Store click position for debugging
                    })
                    self.current_obj_idx = (self.current_obj_idx + 1) % len(self.objects)
                    
                    # Force scene update and refresh display
                    self.update_view(param['sim'])
                    cv2.waitKey(1)  # Force window refresh
                    print(f"   Next object to place: {self.objects[self.current_obj_idx]}")
                else:
                    print(f"✗ Failed to place {obj_name}")
            else:
                print("✗ Could not get 3D position - try clicking on a visible surface")
                # Show depth information for debugging
                try:
                    obs = param['sim'].get_sensor_observations()
                    depth = obs.get("depth")
                    if depth is not None:
                        h, w = depth.shape
                        if y < h and x < w:
                            depth_val = depth[y, x]
                            print(f"  Debug: Depth at ({x}, {y}) = {depth_val:.3f}")
                            if depth_val <= 0:
                                print("  Issue: No depth data (clicking on empty space?)")
                            elif depth_val > 5.0:
                                print("  Issue: Surface too far away")
                        else:
                            print(f"  Issue: Click outside image bounds ({w}x{h})")
                except Exception as e:
                    print(f"  Debug error: {e}")
        
        elif event == cv2.EVENT_RBUTTONDOWN:
            # Right click to preview placement position
            print(f"Preview click at pixel ({x}, {y})")
            world_pos = self.pixel_to_world(x, y, param['sim'])
            if world_pos:
                print(f"  Would place object at world position: {world_pos}")
                # Show a temporary visual indicator on the image
                self.show_placement_preview(x, y, param['sim'])
            else:
                print("  No valid placement position at this pixel")
    
    def pixel_to_world(self, x, y, sim):
        """Convert pixel coordinates to 3D world position using proper unprojection"""
        try:
            obs = sim.get_sensor_observations()
            depth = obs.get("depth")
            
            if depth is None:
                return None
            
            # Debug depth statistics
            print(f"Debug: Depth image stats - min: {depth.min():.3f}, max: {depth.max():.3f}, mean: {depth.mean():.3f}")
            
            # Get depth value at clicked pixel
            h, w = depth.shape
            if y >= h or x >= w:
                return None
                
            depth_val = depth[y, x]
            print(f"Debug: Raw depth value at ({x}, {y}): {depth_val}")
            
            # Check if depth is in millimeters (common in some datasets)
            if depth_val > 100:  # If depth is very large, might be in mm
                depth_val = depth_val / 1000.0  # Convert mm to meters
                print(f"Debug: Converted depth from mm to m: {depth_val}")
            
            if depth_val <= 0 or depth_val > 10.0:  # Extended range for debugging
                print(f"Debug: Depth value {depth_val} is out of range")
                return None
            
            # Get camera intrinsics
            agent = sim.get_agent(0)
            
            # Get camera intrinsics from sensor spec
            sensor_spec = None
            for spec in agent.agent_config.sensor_specifications:
                if spec.uuid == "depth":
                    sensor_spec = spec
                    break
            
            if sensor_spec is None:
                print("Warning: Could not find depth sensor spec, using approximation")
                fov = 90.0  # degrees
                f = w / (2.0 * np.tan(np.radians(fov/2)))
            else:
                if hasattr(sensor_spec, 'hfov'):
                    hfov_deg = sensor_spec.hfov
                    # Handle Magnum Deg object - convert to float
                    if hasattr(hfov_deg, '__float__'):
                        hfov = float(hfov_deg)
                    elif hasattr(hfov_deg, 'value'):
                        hfov = hfov_deg.value
                    else:
                        hfov = float(str(hfov_deg).replace('deg', ''))
                    print(f"Debug: Using sensor HFOV = {hfov} degrees")
                else:
                    hfov = 90.0  # fallback
                    print("Debug: Using fallback HFOV = 90.0 degrees")
                f = w / (2.0 * np.tan(np.radians(hfov/2)))
            
            print(f"Debug: Focal length f = {f}")
            
            # Unproject pixel to 3D point in camera coordinates
            # Habitat-Sim camera coordinate system: X=right, Y=up, Z=BACKWARD (negative Z is forward)
            cam_x = (x - w/2) * depth_val / f
            cam_y = -(y - h/2) * depth_val / f  # Flip Y (image Y goes down, camera Y goes up)
            cam_z = -depth_val  # Depth is distance along camera's forward axis (NEGATIVE Z for forward)
            
            camera_point = np.array([cam_x, cam_y, cam_z])
            print(f"Debug: Click ({x}, {y}) at depth {depth_val:.3f} -> Camera coords {camera_point}")
            
            # Get camera pose in world coordinates
            state = agent.get_state()
            
            # Camera position: agent position + camera offset rotated by agent orientation
            camera_offset = np.array([0.0, 1.5, 0.0])  # Camera is 1.5m above agent center
            
            # Get rotation matrix from agent orientation
            rotation = state.rotation
            if hasattr(rotation, 'to_matrix'):
                rot_matrix = np.array(rotation.to_matrix())
            else:
                qw, qx, qy, qz = rotation.w, rotation.x, rotation.y, rotation.z
                rot_matrix = np.array([
                    [1 - 2*(qy*qy + qz*qz), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
                    [2*(qx*qy + qw*qz), 1 - 2*(qx*qx + qz*qz), 2*(qy*qz - qw*qx)],
                    [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx*qx + qy*qy)]
                ])
            
            print(f"Debug: Rotation matrix:\n{rot_matrix}")
            
            # Get agent position
            if hasattr(state.position, 'x'):
                agent_pos = np.array([state.position.x, state.position.y, state.position.z])
            else:
                agent_pos = np.array(state.position)
            
            # Camera position in world coordinates
            camera_world_pos = agent_pos + rot_matrix @ camera_offset
            
            # Transform camera point to world coordinates
            # This gives us the 3D point that was clicked on
            world_point = camera_world_pos + rot_matrix @ camera_point
            
            # DON'T add extra offset above surface - the depth already gives us the surface position
            # world_point[1] += 0.1  # Remove this line
            
            print(f"Debug: Agent pos {agent_pos}")
            print(f"Debug: Camera offset {camera_offset}")
            print(f"Debug: Camera world pos {camera_world_pos}")
            print(f"Debug: Transformed camera point {rot_matrix @ camera_point}")
            print(f"Debug: Final world pos {world_point}")
            print(f"Debug: Ground level should be around Y={agent_pos[1]}")
            
            return world_point.tolist()
            
        except Exception as e:
            print(f"Error in pixel_to_world: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def place_object(self, sim, obj_name, position):
        """Place object at position"""
        try:
            obj_mgr = sim.get_object_template_manager()
            rigid_mgr = sim.get_rigid_object_manager()
            
            config_file = os.path.join(self.ycb_config_path, f"{obj_name}.object_config.json")
            
            if not os.path.exists(config_file):
                print(f"Config not found: {config_file}")
                return False
            
            # Load and create object
            template_id = obj_mgr.load_configs(config_file)[0]
            obj = rigid_mgr.add_object_by_template_id(template_id)
            
            if obj is None:
                return False
            
            # Add small offset above surface to prevent embedding in the final placement
            final_position = position.copy()
            final_position[1] += 0.05  # Small 5cm offset above the clicked surface
            
            # Set position and orientation
            obj.translation = mn.Vector3(final_position[0], final_position[1], final_position[2])
            
            # Random rotation around Y axis
            angle = np.random.uniform(0, 2*np.pi)
            quat = quat_from_angle_axis(angle, np.array([0, 1, 0]))
            obj.rotation = mn.Quaternion([quat.x, quat.y, quat.z], quat.w)
            
            # Make static
            obj.motion_type = habitat_sim.physics.MotionType.STATIC
            
            print(f"Debug: Placed object at surface position {position} -> final position {final_position}")
            
            return True
            
        except Exception as e:
            print(f"Error placing object: {e}")
            return False
    
    def show_placement_preview(self, x, y, sim):
        """Show a visual preview of where the object would be placed"""
        obs = sim.get_sensor_observations()
        rgb = obs.get("color")
        
        if rgb is not None:
            # Handle different possible RGB formats from Habitat-Sim
            if rgb.dtype == np.float32 or rgb.dtype == np.float64:
                if rgb.max() <= 1.0:
                    img = (rgb * 255).astype(np.uint8)
                else:
                    img = rgb.astype(np.uint8)
            else:
                img = rgb.astype(np.uint8)
            
            # Convert from RGB to BGR for OpenCV display
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            # Draw preview crosshair at click position
            cv2.drawMarker(img_bgr, (x, y), (0, 255, 255), cv2.MARKER_CROSS, 20, 3)
            cv2.putText(img_bgr, "Preview Position", (x+10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            cv2.imshow("Object Placement - Click to place objects", img_bgr)
            cv2.waitKey(500)  # Show preview for 500ms
            
            # Refresh normal view
            self.update_view(sim)
    
    def update_view(self, sim):
        """Update the display"""
        obs = sim.get_sensor_observations()
        rgb = obs.get("color")
        
        if rgb is not None:
            # Handle different possible RGB formats from Habitat-Sim
            if rgb.dtype == np.float32 or rgb.dtype == np.float64:
                # If float, assume range [0, 1] and convert to [0, 255]
                if rgb.max() <= 1.0:
                    img = (rgb * 255).astype(np.uint8)
                else:
                    img = rgb.astype(np.uint8)
            else:
                # If already uint8, use as is
                img = rgb.astype(np.uint8)
            
            # Convert from RGB to BGR for OpenCV display
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            # Add text overlay with enhanced information
            font = cv2.FONT_HERSHEY_SIMPLEX
            next_obj = self.objects[self.current_obj_idx]
            
            # Main status
            cv2.putText(img_bgr, f"Next: {next_obj}", (10, 30), font, 0.7, (0, 255, 0), 2)
            cv2.putText(img_bgr, f"Placed: {len(self.placed_objects)}/{len(self.objects)}", (10, 60), font, 0.7, (0, 255, 0), 2)
            cv2.putText(img_bgr, f"Object {self.current_obj_idx + 1}/{len(self.objects)}", (10, 90), font, 0.6, (0, 255, 0), 2)
            
            # Show recently placed objects with their click positions
            if self.placed_objects:
                cv2.putText(img_bgr, "Recently placed:", (10, 120), font, 0.5, (255, 255, 0), 1)
                for i, obj in enumerate(self.placed_objects[-3:]):  # Show last 3 objects
                    obj_text = f"  {obj['name']}"
                    if 'click_pixel' in obj:
                        obj_text += f" (clicked {obj['click_pixel']})"
                    cv2.putText(img_bgr, obj_text, (10, 140 + i*20), font, 0.4, (255, 255, 0), 1)
                    
                    # Draw markers for recently placed objects' click positions
                    if 'click_pixel' in obj:
                        click_x, click_y = obj['click_pixel']
                        cv2.drawMarker(img_bgr, (click_x, click_y), (255, 255, 0), cv2.MARKER_DIAMOND, 10, 2)
            
            # Controls
            cv2.putText(img_bgr, "Left click: place | Right click: preview | WASD: move | N/P: next/prev obj | V: depth | ESC: exit", (10, 690), font, 0.5, (255, 255, 255), 1)
            
            cv2.imshow("Object Placement - Click to place objects", img_bgr)
            
            # Force window update
            cv2.waitKey(1)
    
    def show_depth_view(self, sim):
        """Show depth visualization to help with clicking"""
        obs = sim.get_sensor_observations()
        depth = obs.get("depth")
        
        if depth is not None:
            # Normalize depth for visualization (0-5 meters)
            depth_vis = np.clip(depth, 0, 5.0) / 5.0
            depth_vis = (depth_vis * 255).astype(np.uint8)
            depth_colored = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
            
            # Add text overlay
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(depth_colored, "Depth View - Darker = Closer", (10, 30), font, 0.6, (255, 255, 255), 2)
            cv2.putText(depth_colored, "Press V again to return to RGB", (10, 60), font, 0.6, (255, 255, 255), 2)
            
            cv2.imshow("Object Placement - Click to place objects", depth_colored)
        else:
            print("No depth data available")
    
    def show_depth_stats(self, sim):
        """Show depth statistics to understand the depth scale"""
        obs = sim.get_sensor_observations()
        depth = obs.get("depth")
        
        if depth is not None:
            print("\n=== DEPTH STATISTICS ===")
            print(f"Depth image shape: {depth.shape}")
            print(f"Depth dtype: {depth.dtype}")
            print(f"Min depth: {depth.min():.6f}")
            print(f"Max depth: {depth.max():.6f}")
            print(f"Mean depth: {depth.mean():.6f}")
            print(f"Median depth: {np.median(depth):.6f}")
            
            # Sample some specific pixel values
            h, w = depth.shape
            center_depth = depth[h//2, w//2]
            print(f"Center pixel depth: {center_depth:.6f}")
            
            # Show histogram of depth values
            valid_depths = depth[depth > 0]
            if len(valid_depths) > 0:
                print(f"Valid depth pixels: {len(valid_depths)}/{depth.size}")
                percentiles = [10, 25, 50, 75, 90]
                for p in percentiles:
                    val = np.percentile(valid_depths, p)
                    print(f"{p}th percentile: {val:.6f}")
            
            print("========================\n")
        else:
            print("No depth data available")
    
    def save_config(self):
        """Save placement configuration"""
        config = {
            'scene': self.scene_path,
            'objects': self.placed_objects
        }
        
        with open('object_placements.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("Saved placements to object_placements.json")
        print(f"Configuration contains {len(self.placed_objects)} objects:")
        for i, obj in enumerate(self.placed_objects):
            print(f"  {i+1}. {obj['name']} at {obj['position']}")
    
    def run(self):
        """Main interaction loop"""
        print("Starting Simple Object Placer")
        print(f"Loaded {len(self.objects)} YCB objects")
        print(f"First few objects: {', '.join(self.objects[:5])}{'...' if len(self.objects) > 5 else ''}")
        
        # Create simulator
        sim = self.create_sim()
        agent = sim.initialize_agent(0)
        
        # Set starting position
        nav_point = sim.pathfinder.get_random_navigable_point()
        state = habitat_sim.AgentState()
        state.position = mn.Vector3(nav_point[0], nav_point[1] + 1.5, nav_point[2])
        state.rotation = quat_from_angle_axis(0, np.array([0, 1, 0]))
        agent.set_state(state)
        
        # Setup window
        cv2.namedWindow("Object Placement - Click to place objects")
        cv2.setMouseCallback("Object Placement - Click to place objects", self.mouse_click, {'sim': sim})
        
        self.update_view(sim)
        
        print("\nControls:")
        print("- Left click: Place object at clicked position")  
        print("- Right click: Preview placement position (shows debug info)")
        print("- W: Move forward")
        print("- S: Move backward")
        print("- A: Turn left")
        print("- D: Turn right")
        print("- Q: Turn left (fine)")
        print("- E: Turn right (fine)")
        print("- N: Next object (without placing)")
        print("- P: Previous object")
        print("- V: Toggle depth view (helps see clickable surfaces)")
        print("- C: Show depth statistics")
        print("- Enter: Save and exit")
        print("- ESC: Exit")
        
        show_depth = False
        
        # Main loop
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                break
            elif key == 13:  # Enter
                self.save_config()
                break
            elif key == ord('c'):  # Show depth statistics
                self.show_depth_stats(sim)
            elif key == ord('n'):  # Next object
                self.current_obj_idx = (self.current_obj_idx + 1) % len(self.objects)
                print(f"Selected object: {self.objects[self.current_obj_idx]} ({self.current_obj_idx + 1}/{len(self.objects)})")
                if show_depth:
                    self.show_depth_view(sim)
                else:
                    self.update_view(sim)
            elif key == ord('p'):  # Previous object
                self.current_obj_idx = (self.current_obj_idx - 1) % len(self.objects)
                print(f"Selected object: {self.objects[self.current_obj_idx]} ({self.current_obj_idx + 1}/{len(self.objects)})")
                if show_depth:
                    self.show_depth_view(sim)
                else:
                    self.update_view(sim)
            elif key == ord('v'):  # Toggle depth view
                show_depth = not show_depth
                if show_depth:
                    self.show_depth_view(sim)
                    print("Switched to depth view - darker areas are closer")
                else:
                    self.update_view(sim)
                    print("Switched to RGB view")
            elif key == ord('w'):
                try:
                    agent.act("move_forward")
                    if show_depth:
                        self.show_depth_view(sim)
                    else:
                        self.update_view(sim)
                except:
                    pass
            elif key == ord('s'):
                try:
                    # Simple backward: turn around, forward, turn back
                    for _ in range(18):
                        agent.act("turn_left")
                    agent.act("move_forward") 
                    for _ in range(18):
                        agent.act("turn_left")
                    if show_depth:
                        self.show_depth_view(sim)
                    else:
                        self.update_view(sim)
                except:
                    pass
            elif key == ord('a') or key == ord('q'):
                try:
                    agent.act("turn_left")
                    if show_depth:
                        self.show_depth_view(sim)
                    else:
                        self.update_view(sim)
                except:
                    pass
            elif key == ord('d') or key == ord('e'):
                try:
                    agent.act("turn_right")
                    if show_depth:
                        self.show_depth_view(sim)
                    else:
                        self.update_view(sim)
                except:
                    pass
        
        print(f"\nSession complete! Placed {len(self.placed_objects)} objects:")
        for obj in self.placed_objects:
            print(f"- {obj['name']} at {obj['position']}")
        
        cv2.destroyAllWindows()
        sim.close()

if __name__ == "__main__":
    scene_path = "/home/yidu/extraSpace_projects/data/datasets/hm3d/train/00000-kfPV7w3FaU5/kfPV7w3FaU5.basis.glb"
    placer = SimpleObjectPlacer(scene_path)
    placer.run()
