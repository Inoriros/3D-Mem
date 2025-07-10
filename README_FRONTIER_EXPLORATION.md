# Frontier Exploration Data Collection

This document describes the frontier exploration script that implements autonomous exploration using closest frontier selection strategy. The script is designed for collecting RGB/depth images and topdown visualization maps during exploration in different indoor environments.

## Overview

The `frontier_exploration.py` script is based on `run_aeqa_evaluation.py` but removes concept graph and object detection components to focus purely on exploration. It implements a simple but effective exploration strategy by always selecting the closest frontier point at each step.

## Key Features

- **Closest Frontier Selection**: At each step, the agent selects the nearest unexplored frontier
- **Multi-Camera Data Collection**: Records RGB and depth images from the front camera
- **Topdown Visualization**: Generates exploration maps showing agent trajectory and frontier points
- **Configurable Environments**: Supports testing multiple scenes with different start positions
- **Structured Output**: Organizes data into clear directory structure for analysis

## Installation & Setup

### Prerequisites

- Python 3.8+
- Habitat-Sim
- HM3D dataset
- Required Python packages (see main project requirements)

### Dataset Setup

Ensure the HM3D dataset is properly installed and the path is configured in `cfg/frontier_exploration.yaml`:

```yaml
scene_data_path: "/path/to/hm3d/dataset"
scene_dataset_config_path: "data/hm3d_annotated_basis.scene_dataset_config.json"
```

## Usage

### Basic Usage

Run exploration with default settings (2 environments, 2 positions each):

```bash
python frontier_exploration.py
```

### Configurable Parameters

```bash
# Test single environment with one position
python frontier_exploration.py --num_environments 1 --num_positions 1

# Test both environments with two positions each
python frontier_exploration.py --num_environments 2 --num_positions 2

# Use custom configuration file
python frontier_exploration.py --cfg_file cfg/custom_frontier_config.yaml

# Use custom scene configurations
python frontier_exploration.py --scene_config_file cfg/my_custom_scenes.json

# Test with many environments and positions
python frontier_exploration.py --num_environments 10 --num_positions 8
```

### Scene Configuration File

The script uses `cfg/frontier_scene_configs.json` to define available scenes and their start positions/rotations. This JSON file contains:

```json
{
  "scene_configurations": [
    {
      "scene_id": "00824-Dd4bFSTQ8gi",
      "description": "Scene description",
      "start_positions": [[x1, y1, z1], [x2, y2, z2], ...],
      "start_rotations": [[x1, y1, z1, w1], [x2, y2, z2, w2], ...],
      "rotation_descriptions": ["0°", "90°", ...]
    }
  ],
  "metadata": { ... }
}
```

**Creating Custom Scene Configurations:**
1. Copy `cfg/frontier_scene_configs.json` to a new file
2. Modify scene IDs, positions, and rotations as needed
3. Use `--scene_config_file` to specify your custom file

**Example Custom Configuration:**
See `cfg/example_custom_scenes.json` for a template showing how to create custom scene configurations with your own HM3D scenes and start positions.

### Scaling Beyond Predefined Configurations

The script includes 5 predefined HM3D scenes, each with 5 predefined start positions and rotations. When you request more than the available predefined configurations:

**More Environments**: The script cycles through available scenes, creating additional runs with modified scene IDs (e.g., `00824-Dd4bFSTQ8gi_run3`)

**More Positions**: The script generates additional random positions and rotations:
- New positions are created by adding random offsets (±2 meters) to existing positions
- New rotations are generated with random angles around the Y-axis
- Height (Y-coordinate) is preserved from the base positions
```

### Command Line Arguments

- `--cfg_file`: Path to configuration file (default: `cfg/frontier_exploration.yaml`)
- `--scene_config_file`: Path to scene configurations JSON file (default: `cfg/frontier_scene_configs.json`)
- `--num_environments`: Number of environments to test (default: 2, no upper limit)
- `--num_positions`: Number of start positions per environment (default: 2, no upper limit)

## Configuration

The script uses two main configuration files:

### Main Configuration (`cfg/frontier_exploration.yaml`)

Controls exploration behavior and system settings:

### Exploration Settings

```yaml
num_step: 30                    # Maximum exploration steps
init_clearance: 0.3            # Initial clearance around start position
extra_view_phase_1: 2          # Extra views during exploration
extra_view_phase_2: 6          # Extra views at start position
```

### Camera Settings

```yaml
camera_height: 1.5             # Camera height in meters
camera_tilt_deg: -30           # Camera tilt angle
img_width: 1280                # Image width
img_height: 1280               # Image height
hfov: 120                      # Horizontal field of view
```

### TSDF and Frontier Settings

```yaml
tsdf_grid_size: 0.1            # TSDF voxel size
explored_depth: 1.7            # Maximum exploration depth
planner:
  eps: 1                       # DBSCAN clustering parameter
  max_dist_from_cur_phase_1: 1 # Step size during exploration
  frontier_area_min: 8         # Minimum frontier area
```

### Scene Configuration (`cfg/frontier_scene_configs.json`)

Defines available scenes and their test configurations:

```json
{
  "scene_configurations": [
    {
      "scene_id": "00824-Dd4bFSTQ8gi",
      "description": "Residential environment from AEQA dataset",
      "start_positions": [
        [6.89, 0.07, 1.49],  // [x, y, z] in meters
        [5.0, 0.07, 0.0]     // Additional positions...
      ],
      "start_rotations": [
        [0.0, 0.0, 0.0, 1.0],      // Quaternion [x, y, z, w]
        [0.0, 0.707, 0.0, 0.707]   // 90° rotation around y-axis
      ],
      "rotation_descriptions": ["identity (0°)", "90° around y-axis"]
    }
  ]
}
```

This separation allows easy customization of test scenarios without modifying the main script.
```

## Output Structure

The script generates organized output in the following structure:

```
exploration_results/frontier_exploration/
├── exploration.log                    # Execution log with timestamps
├── scene_1_pos_1/                    # First scene, first position
│   ├── front_rgb/                     # Front camera RGB images
│   │   ├── step_000.png              # RGB at step 0
│   │   ├── step_001.png              # RGB at step 1
│   │   └── ...
│   ├── front_depth/                   # Front camera depth images
│   │   ├── step_000.png              # Depth at step 0 (viridis colormap)
│   │   ├── step_001.png              # Depth at step 1
│   │   └── ...
│   ├── map/                           # Topdown exploration maps
│   │   ├── step_000_topdown.png      # Map at step 0
│   │   ├── step_001_topdown.png      # Map at step 1
│   │   └── ...
│   └── exploration_summary.json       # Run metadata and statistics
├── scene_1_pos_2/                    # First scene, second position
│   └── ...
├── scene_2_pos_1/                    # Second scene, first position
│   └── ...
└── scene_2_pos_2/                    # Second scene, second position
    └── ...
```

### Data Description

**Front Camera Images (`front_rgb/`)**:
- High-resolution RGB images from the robot's front-facing camera
- Captured at each exploration step
- Format: PNG, RGB channels
- Resolution: 1280x1280 (configurable)

**Depth Images (`front_depth/`)**:
- Corresponding depth information for each RGB image
- Normalized and visualized using viridis colormap
- Format: PNG with color-mapped depth values
- Useful for 3D reconstruction and spatial understanding

**Exploration Maps (`map/`)**:
- Topdown view of the exploration progress
- Shows agent trajectory, current position, and frontier points
- Includes occupancy map and explored areas
- Format: PNG, high-resolution (150 DPI)

**Exploration Summary (`exploration_summary.json`)**:
- Complete metadata for each run
- Start position and rotation
- Number of steps completed
- List of explored frontiers with positions
- Final agent position
- Directory structure information

## Default Test Environments

The script includes 5 predefined HM3D scenes with diverse spatial characteristics:

### Scene 1: `00824-Dd4bFSTQ8gi`
- **5 Positions**: Starting from `[6.89, 0.07, 1.49]` with various offsets
- **5 Rotations**: Identity, 90°, 180°, -90°, 45° around Y-axis

### Scene 2: `00848-ziup5kvtCCR`
- **5 Positions**: Starting from `[1.0, 0.0, -1.0]` with different areas
- **5 Rotations**: 60°, -60°, identity, 120°, -120° around Y-axis

### Scene 3: `00829-QaAWkl8WGqw`
- **5 Positions**: Distributed across different room areas
- **5 Rotations**: Full range of orientations for comprehensive coverage

### Scene 4: `00861-GLAQ4DNUx5U`
- **5 Positions**: Strategic placement including origin and corners
- **5 Rotations**: Systematic angular distribution

### Scene 5: `00862-LT9Jq6dN3Ea`
- **5 Positions**: Cross-pattern and diagonal placements
- **5 Rotations**: 0°, 45°, 90°, 135°, 180° for thorough testing

These configurations provide diverse starting conditions to test exploration behavior across different spatial layouts, room types, and orientations. When more environments or positions are requested, the script intelligently expands the test set through cycling and random generation.

## Algorithm Details

### Exploration Strategy

1. **Multi-View Observation**: At each step, the agent captures multiple camera views
2. **TSDF Integration**: Updates occupancy map using RGB-D observations
3. **Frontier Detection**: Identifies unexplored boundary regions using DBSCAN clustering
4. **Closest Selection**: Chooses the frontier nearest to current position (Euclidean distance)
5. **Navigation**: Moves toward selected frontier using habitat pathfinding
6. **Target Reset**: Clears navigation targets after reaching destinations

### Key Differences from Original AEQA Script

- **No Concept Graph**: Removes object detection and semantic mapping
- **No VLM Queries**: Uses distance-based frontier selection instead of vision-language models
- **Simplified Scene Class**: Minimal habitat simulation without detection models
- **Pure Exploration Focus**: Optimized for spatial coverage rather than object search

## Data Analysis

The collected data can be used for:

- **Exploration Algorithm Development**: Benchmarking different frontier selection strategies
- **Visual SLAM Research**: RGB-D sequences with ground truth trajectories
- **Spatial AI Training**: Large-scale indoor navigation datasets
- **Coverage Analysis**: Quantifying exploration efficiency across environments

### Example Analysis Code

```python
import json
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

# Load exploration summary
with open('exploration_results/frontier_exploration/scene_1_pos_1/exploration_summary.json', 'r') as f:
    summary = json.load(f)

print(f"Total steps: {summary['total_steps']}")
print(f"Frontiers explored: {len(summary['explored_frontiers'])}")

# Visualize exploration trajectory
start_pos = np.array(summary['start_position'])
final_pos = np.array(summary['final_position'])
distance_traveled = np.linalg.norm(final_pos - start_pos)
print(f"Distance from start: {distance_traveled:.2f}m")
```

## Troubleshooting

### Common Issues

1. **Scene Loading Errors**: Verify HM3D dataset path and scene files exist
2. **Memory Issues**: Reduce image resolution or number of steps in config
3. **Navigation Failures**: Check start positions are valid on navigation mesh
4. **Missing Dependencies**: Ensure all required packages are installed

### Debug Mode

Enable detailed logging by modifying the script:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization

- Reduce `img_width` and `img_height` for faster execution
- Decrease `num_step` for shorter runs
- Use fewer `extra_view_phase_1/2` for less comprehensive scanning

## Citation

If you use this exploration script in your research, please cite the original 3D-Mem project:

```bibtex
@article{3dmem2024,
  title={3D-Mem: 3D Spatial Memory for Embodied AI},
  author={[Original Authors]},
  journal={[Journal/Conference]},
  year={2024}
}
```

## License

This code follows the same license as the main 3D-Mem project. See LICENSE file for details.

## Contributing

For improvements or bug reports related to frontier exploration:

1. Check existing issues in the main repository
2. Create detailed bug reports with configuration and log files
3. Submit pull requests with clear descriptions and tests

## Changelog

- **v1.2**: Improved configuration management
  - Moved scene configurations to separate JSON file (`cfg/frontier_scene_configs.json`)
  - Added `--scene_config_file` command line argument for custom scene configurations
  - Enhanced modularity and ease of customization
  - Better documentation structure for configuration files

- **v1.1**: Enhanced scalability and configurability
  - Removed limits on number of environments and start positions
  - Added 5 predefined HM3D scenes with 5 positions each
  - Automatic generation of additional positions/rotations when requested
  - Intelligent scene cycling for large-scale testing
  - Updated documentation with scaling instructions

- **v1.0**: Initial frontier exploration implementation
  - Closest frontier selection strategy
  - Multi-environment testing support
  - Structured data output with RGB/depth/maps
  - Configurable start positions and rotations
