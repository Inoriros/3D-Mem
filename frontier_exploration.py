"""
Frontier Exploration Script

This script implements frontier-based exploration using the closest frontier selection strategy.
It is based on run_aeqa_evaluation.py but removes concept graph and object detection components
to focus purely on exploration.

Key features:
- Selects closest frontier to current position at each step
- Records RGB/depth images from front camera and topdown visualization maps
- Can test multiple environments and start positions
- Configurable number of exploration steps

Usage:
    python frontier_exploration.py --num_environments 2 --num_positions 2

The script will create a directory structure like:
exploration_results/frontier_exploration/
├── exploration.log
├── scene_1_pos_1/
│   ├── front_rgb/                  # Front camera RGB images
│   │   ├── step_000.png
│   │   ├── step_001.png
│   │   └── ...
│   ├── front_depth/                # Front camera depth images
│   │   ├── step_000.png
│   │   ├── step_001.png
│   │   └── ...
│   ├── map/                        # Top-down exploration maps
│   │   ├── step_000_topdown.png
│   │   ├── step_001_topdown.png
│   │   └── ...
│   └── exploration_summary.json
└── scene_1_pos_2/
    └── ...
"""

import os

os.environ["TRANSFORMERS_VERBOSITY"] = "error"  # disable warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HABITAT_SIM_LOG"] = (
    "quiet"  # https://aihabitat.org/docs/habitat-sim/logging.html
)
os.environ["MAGNUM_LOG"] = "quiet"

# Disable OpenGL to prevent context issues
os.environ["MPLBACKEND"] = "Agg"
os.environ["DISPLAY"] = ""  # Disable display
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["PYOPENGL_PLATFORM"] = "osmesa"  # Use offscreen rendering
os.environ["MESA_GL_VERSION_OVERRIDE"] = "3.3"
os.environ["MESA_GLSL_VERSION_OVERRIDE"] = "330"

import argparse
from omegaconf import OmegaConf
import random
import numpy as np
import torch
import time
import json
import logging

# Set matplotlib backend to prevent OpenGL issues
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

# Additional matplotlib safety configurations
plt.ioff()  # Turn off interactive mode
plt.rcParams['figure.max_open_warning'] = 0  # Disable max open figures warning
plt.rcParams['agg.path.chunksize'] = 10000  # Prevent path chunking issues
plt.rcParams['font.size'] = 8  # Reduce font size to prevent rendering issues
import gc  # For garbage collection

from src.habitat import pose_habitat_to_tsdf
from src.geom import get_cam_intr, get_scene_bnds
from src.tsdf_planner import TSDFPlanner, Frontier
from src.scene_aeqa import Scene
from src.utils import resize_image, get_pts_angle_aeqa
from src.const import *


def select_closest_frontier(tsdf_planner, current_pts):
    """
    Select the closest frontier to the current position
    """
    if not tsdf_planner.frontiers:
        return None
    
    current_voxel = tsdf_planner.habitat2voxel(current_pts)[:2]
    min_distance = float('inf')
    closest_frontier = None
    
    for frontier in tsdf_planner.frontiers:
        distance = np.linalg.norm(frontier.position - current_voxel)
        if distance < min_distance:
            min_distance = distance
            closest_frontier = frontier
    
    return closest_frontier


def main(cfg, scene_configs):
    # Configure matplotlib for stability
    plt.rcParams['figure.max_open_warning'] = 0  # Disable max figure warning
    
    # load the default concept graph config
    cfg_cg = OmegaConf.load(cfg.concept_graph_config_path)
    OmegaConf.resolve(cfg_cg)

    img_height = cfg.img_height
    img_width = cfg.img_width
    cam_intr = get_cam_intr(cfg.hfov, img_height, img_width)

    random.seed(cfg.seed)
    np.random.seed(cfg.seed)

    # Create output directory for exploration results
    output_dir = os.path.join(cfg.output_parent_dir, cfg.exp_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Run exploration for each configuration
    for config_idx, scene_config in enumerate(scene_configs):
        scene_id = scene_config['scene_id']
        start_positions = scene_config['start_positions']
        start_rotations = scene_config['start_rotations']
        
        logging.info(f"\n========\nScene {config_idx + 1}: {scene_id}")
        
        for pos_idx, (start_pos, start_rot) in enumerate(zip(start_positions, start_rotations)):
            run_id = f"scene_{config_idx + 1}_pos_{pos_idx + 1}"
            logging.info(f"\nRun {run_id}: Position {start_pos}, Rotation {start_rot}")
            
            # Create run-specific directories
            run_dir = os.path.join(output_dir, run_id)
            front_rgb_dir = os.path.join(run_dir, "front_rgb")
            front_depth_dir = os.path.join(run_dir, "front_depth")
            map_dir = os.path.join(run_dir, "map")
            
            for dir_path in [run_dir, front_rgb_dir, front_depth_dir, map_dir]:
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
            
            # Convert position and rotation to expected format
            pts = np.array(start_pos, dtype=float)
            # Convert quaternion to angle for habitat usage
            # For simplicity, we'll use a fixed angle for now and adjust as needed
            angle = 0.0  # Can be modified to extract angle from quaternion if needed
            
            # Load scene (without concept graph and object detection components)
            try:
                del scene
            except:
                pass
            
            # Create a simplified scene without detection models
            scene = SimpleScene(scene_id, cfg)
            
            # Initialize the TSDF
            tsdf_planner = TSDFPlanner(
                vol_bnds=get_scene_bnds(scene.pathfinder, floor_height=pts[1])[0],
                voxel_size=cfg.tsdf_grid_size,
                floor_height=pts[1],
                floor_height_offset=0,
                pts_init=pts,
                init_clearance=cfg.init_clearance * 2,
                save_visualization=cfg.save_visualization,
            )
            
            logging.info(f"Run {run_id} initialization successful!")
            
            # Run exploration steps
            cnt_step = -1
            explored_frontiers = []
            
            while cnt_step < cfg.num_step - 1:
                cnt_step += 1
                logging.info(f"Step: {cnt_step}")
                
                # (1) Observe the surroundings and update occupancy map
                # Determine the viewing angles for the current step
                if cnt_step == 0:
                    angle_increment = cfg.extra_view_angle_deg_phase_2 * np.pi / 180
                    total_views = 1 + cfg.extra_view_phase_2
                else:
                    angle_increment = cfg.extra_view_angle_deg_phase_1 * np.pi / 180
                    total_views = 1 + cfg.extra_view_phase_1
                    
                all_angles = [
                    angle + angle_increment * (i - total_views // 2)
                    for i in range(total_views)
                ]
                # Let the main viewing angle be the last one
                main_angle = all_angles.pop(total_views // 2)
                all_angles.append(main_angle)
                
                rgb_views = []
                for view_idx, ang in enumerate(all_angles):
                    # Get observation
                    obs, cam_pose = scene.get_observation(pts, ang)
                    rgb = obs["color_sensor"]
                    depth = obs["depth_sensor"]
                    
                    # Only save front camera RGB and depth images
                    is_front_camera = (view_idx == len(all_angles) - 1)  # Main view is last
                    
                    if is_front_camera:
                        # Save front camera images
                        rgb_path = os.path.join(front_rgb_dir, f"step_{cnt_step:03d}.png")
                        depth_path = os.path.join(front_depth_dir, f"step_{cnt_step:03d}.png")
                        
                        plt.imsave(rgb_path, rgb)
                        # Save depth as a normalized grayscale image
                        depth_normalized = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
                        plt.imsave(depth_path, depth_normalized, cmap='viridis')
                    
                    rgb_views.append(rgb)
                    
                    # Update depth map and occupancy map
                    tsdf_planner.integrate(
                        color_im=rgb,
                        depth_im=depth,
                        cam_intr=cam_intr,
                        cam_pose=pose_habitat_to_tsdf(cam_pose),
                        obs_weight=1.0,
                        margin_h=int(cfg.margin_h_ratio * img_height),
                        margin_w=int(cfg.margin_w_ratio * img_width),
                        explored_depth=cfg.explored_depth,
                    )
                
                # (2) Update the Frontier Map
                try:
                    update_success = tsdf_planner.update_frontier_map(
                        pts=pts,
                        cfg=cfg.planner,
                        scene=scene,
                        cnt_step=cnt_step,
                        save_frontier_image=False,  # Don't save frontier images, only topdown maps
                        eps_frontier_dir=map_dir,
                        prompt_img_size=(cfg.prompt_h, cfg.prompt_w),
                    )
                except Exception as e:
                    logging.error(f"Error in update_frontier_map: {e}")
                    update_success = False
                
                if not update_success:
                    logging.info("Warning! Update frontier map failed!")
                    if cnt_step == 0:
                        logging.info(f"Run {run_id} invalid: update_frontier_map failed!")
                        break
                
                # (3) Choose the closest frontier
                # First, reset any existing navigation target
                if tsdf_planner.max_point is not None or tsdf_planner.target_point is not None:
                    tsdf_planner.max_point = None
                    tsdf_planner.target_point = None
                
                closest_frontier = select_closest_frontier(tsdf_planner, pts)
                
                if closest_frontier is None:
                    logging.info(f"No frontiers available. Exploration complete for {run_id}")
                    break
                
                # Set the closest frontier as the navigation target
                update_success = tsdf_planner.set_next_navigation_point(
                    choice=closest_frontier,
                    pts=pts,
                    objects={},  # No objects since we're not using concept graph
                    cfg=cfg.planner,
                    pathfinder=scene.pathfinder,
                    random_position=False,
                )
                
                if not update_success:
                    logging.info(f"Run {run_id} invalid: set_next_navigation_point failed!")
                    break
                
                # (4) Agent navigate to the target point for one step
                try:
                    return_values = tsdf_planner.agent_step(
                        pts=pts,
                        angle=angle,
                        objects={},  # No objects
                        snapshots={},  # No snapshots
                        pathfinder=scene.pathfinder,
                        cfg=cfg.planner,
                        path_points=None,
                        save_visualization=cfg.save_visualization,
                    )
                except Exception as e:
                    logging.error(f"Error in agent_step: {e}")
                    return_values = [None]
                
                if return_values[0] is None:
                    logging.info(f"Run {run_id} invalid: agent_step failed!")
                    break
                
                # Update agent's position and rotation
                pts, angle, pts_voxel, fig, _, target_arrived = return_values
                logging.info(f"New position: {pts}")
                
                # Save visualization if enabled
                if cfg.save_visualization and fig is not None:
                    try:
                        viz_path = os.path.join(map_dir, f"step_{cnt_step:03d}_topdown.png")
                        fig.savefig(viz_path, dpi=150, bbox_inches='tight')
                        plt.close(fig)
                    except Exception as e:
                        logging.warning(f"Failed to save visualization at step {cnt_step}: {e}")
                        try:
                            plt.close(fig)
                        except:
                            pass
                
                # Cleanup matplotlib to prevent memory leaks and context issues
                try:
                    plt.close('all')  # Close all figures
                    plt.clf()         # Clear the current figure
                    plt.cla()         # Clear the current axes
                    gc.collect()      # Force garbage collection
                except Exception as e:
                    logging.warning(f"Error cleaning up matplotlib: {e}")
                
                # Record explored frontier
                if target_arrived:
                    explored_frontiers.append({
                        'step': cnt_step,
                        'frontier_position': closest_frontier.position.tolist(),
                        'agent_position': pts.tolist(),
                    })
                    logging.info(f"Reached frontier at step {cnt_step}")
                    # Reset navigation targets after reaching frontier
                    # (Note: agent_step should already do this, but ensure it's done)
                    if tsdf_planner.max_point is not None or tsdf_planner.target_point is not None:
                        tsdf_planner.max_point = None
                        tsdf_planner.target_point = None
                
                # Check if no more frontiers to explore
                if not tsdf_planner.frontiers:
                    logging.info(f"All frontiers explored for {run_id}")
                    break
            
            # Save exploration summary
            summary = {
                'run_id': run_id,
                'scene_id': scene_id,
                'start_position': start_pos,
                'start_rotation': start_rot,
                'total_steps': cnt_step + 1,
                'explored_frontiers': explored_frontiers,
                'final_position': pts.tolist() if 'pts' in locals() else None,
                'output_structure': {
                    'front_rgb': f"{front_rgb_dir}",
                    'front_depth': f"{front_depth_dir}",
                    'map': f"{map_dir}",
                    'description': {
                        'front_rgb': 'Front camera RGB images at each exploration step',
                        'front_depth': 'Front camera depth images at each exploration step',
                        'map': 'Top-down exploration maps showing agent position and frontiers'
                    }
                }
            }
            
            summary_path = os.path.join(run_dir, 'exploration_summary.json')
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logging.info(f"Run {run_id} completed. Total steps: {cnt_step + 1}")
            logging.info(f"Explored {len(explored_frontiers)} frontiers")
            
            # Complete cleanup between runs to prevent resource accumulation
            try:
                if 'scene' in locals():
                    del scene.simulator
                    del scene
                if 'tsdf_planner' in locals():
                    del tsdf_planner
                plt.close('all')
                gc.collect()
                logging.info(f"Cleanup completed for {run_id}")
            except Exception as e:
                logging.warning(f"Error during cleanup: {e}")

    logging.info("All exploration runs completed!")


class SimpleScene:
    """Simplified scene class without concept graph and object detection"""
    
    def __init__(self, scene_id, cfg):
        import habitat_sim
        from src.habitat import make_simple_cfg
        import os
        
        self.scene_id = scene_id
        self.cfg = cfg
        
        # Set up scene paths based on scene_id
        split = "train" if int(scene_id.split("-")[0]) < 800 else "val"
        scene_mesh_path = os.path.join(
            cfg.scene_data_path, split, scene_id, scene_id.split("-")[1] + ".basis.glb"
        )
        navmesh_path = os.path.join(
            cfg.scene_data_path,
            split,
            scene_id,
            scene_id.split("-")[1] + ".basis.navmesh",
        )
        
        # Initialize Habitat simulator with proper settings
        sim_settings = {
            "scene": scene_mesh_path,
            "default_agent": 0,
            "sensor_height": cfg.camera_height,
            "width": cfg.img_width,
            "height": cfg.img_height,
            "hfov": cfg.hfov,
            "scene_dataset_config_file": cfg.scene_dataset_config_path,
            "camera_tilt": cfg.camera_tilt_deg * np.pi / 180,
        }
        
        sim_cfg = make_simple_cfg(sim_settings)
        self.simulator = habitat_sim.Simulator(sim_cfg)
        self.pathfinder = self.simulator.pathfinder
        self.pathfinder.seed(cfg.seed)
        self.pathfinder.load_nav_mesh(navmesh_path)
        self.agent = self.simulator.get_agent(0)
        
        # Store observations for later use
        self.all_observations = {}
    
    def get_observation(self, pts, angle):
        """Get RGB and depth observation at given position and angle"""
        import habitat_sim
        import quaternion
        from src.habitat import get_quaternion
        
        # Set agent state
        agent_state = habitat_sim.AgentState()
        agent_state.position = pts
        agent_state.rotation = get_quaternion(angle, 0)
        self.agent.set_state(agent_state)
        
        # Get observation
        obs = self.simulator.get_sensor_observations()
        
        # Get camera pose for TSDF integration
        sensor = self.agent.get_state().sensor_states["depth_sensor"]
        quaternion_0 = sensor.rotation
        translation_0 = sensor.position
        cam_pose = np.eye(4)
        cam_pose[:3, :3] = quaternion.as_rotation_matrix(quaternion_0)
        cam_pose[:3, 3] = translation_0
        
        # Convert RGBA to RGB if needed
        if obs["color_sensor"].shape[-1] == 4:
            obs["color_sensor"] = obs["color_sensor"][..., :3]
        
        return obs, cam_pose
    
    def get_frontier_observation(self, pts, view_direction):
        """Get frontier observation (simplified version)"""
        # For simplified exploration, just return current observation
        obs, _ = self.get_observation(pts, 0)  # Use angle 0 for simplicity
        return obs


if __name__ == "__main__":
    # Get config path
    parser = argparse.ArgumentParser()
    parser.add_argument("-cf", "--cfg_file", help="cfg file path", default="cfg/frontier_exploration.yaml", type=str)
    parser.add_argument("--scene_config_file", help="scene configurations JSON file", default="cfg/frontier_scene_configs.json", type=str)
    parser.add_argument("--num_environments", help="number of environments to test", default=2, type=int)
    parser.add_argument("--num_positions", help="number of start positions per environment", default=2, type=int)
    args = parser.parse_args()
    cfg = OmegaConf.load(args.cfg_file)
    OmegaConf.resolve(cfg)
    
    # Override some settings for frontier exploration
    cfg.save_visualization = True  # Disable visualization to avoid OpenGL issues completely
    
    # Set up logging
    cfg.output_dir = os.path.join(cfg.output_parent_dir, cfg.exp_name)
    if not os.path.exists(cfg.output_dir):
        os.makedirs(cfg.output_dir, exist_ok=True)
    
    logging_path = os.path.join(cfg.output_dir, "exploration.log")
    
    class ElapsedTimeFormatter(logging.Formatter):
        def __init__(self, fmt=None, datefmt=None):
            super().__init__(fmt, datefmt)
            self.start_time = time.time()

        def formatTime(self, record, datefmt=None):
            elapsed_seconds = record.created - self.start_time
            hours, remainder = divmod(elapsed_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    formatter = ElapsedTimeFormatter(fmt="%(asctime)s - %(message)s")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            logging.FileHandler(logging_path, mode="w"),
            logging.StreamHandler(),
        ],
    )
    
    for handler in logging.getLogger().handlers:
        handler.setFormatter(formatter)
    
    # Load scene configurations from JSON file
    with open(args.scene_config_file, 'r') as f:
        scene_config_data = json.load(f)
    
    all_scene_configs = scene_config_data['scene_configurations']
    logging.info(f"Loaded {len(all_scene_configs)} scene configurations from {args.scene_config_file}")
    
    # Handle user requests for environments and positions
    # If user requests more environments than predefined, repeat/cycle through available ones
    if args.num_environments > len(all_scene_configs):
        logging.info(f"Requested {args.num_environments} environments, but only {len(all_scene_configs)} are predefined.")
        logging.info("Cycling through available environments to meet the request.")
        scene_configs = []
        for i in range(args.num_environments):
            config_idx = i % len(all_scene_configs)
            config_copy = all_scene_configs[config_idx].copy()
            config_copy['scene_id'] = f"{config_copy['scene_id']}_run{i+1}"
            scene_configs.append(config_copy)
    else:
        scene_configs = all_scene_configs[:args.num_environments]
    
    # Handle user requests for positions per environment
    for config in scene_configs:
        available_positions = len(config['start_positions'])
        available_rotations = len(config['start_rotations'])
        
        if args.num_positions > available_positions:
            logging.info(f"Requested {args.num_positions} positions for scene {config['scene_id']}, but only {available_positions} are predefined.")
            logging.info("Generating additional random positions and rotations.")
            
            # Generate additional random positions around existing ones
            base_positions = config['start_positions'].copy()
            base_rotations = config['start_rotations'].copy()
            
            for i in range(args.num_positions - available_positions):
                # Generate random position near existing ones
                base_pos = base_positions[i % len(base_positions)]
                random_offset = np.random.uniform(-2.0, 2.0, 3)  # Random offset within 2 meters
                random_offset[1] = 0  # Keep y-coordinate (height) the same
                new_position = [base_pos[0] + random_offset[0], base_pos[1], base_pos[2] + random_offset[2]]
                config['start_positions'].append(new_position)
                
                # Generate random rotation
                random_angle = np.random.uniform(0, 2 * np.pi)
                new_rotation = [0.0, np.sin(random_angle/2), 0.0, np.cos(random_angle/2)]
                config['start_rotations'].append(new_rotation)
        else:
            # Limit to requested number of positions
            config['start_positions'] = config['start_positions'][:args.num_positions]
            config['start_rotations'] = config['start_rotations'][:args.num_positions]
    
    # Run exploration
    logging.info(f"***** Starting Frontier Exploration *****")
    logging.info(f"Testing {len(scene_configs)} environments with {args.num_positions} positions each")
    main(cfg, scene_configs)
