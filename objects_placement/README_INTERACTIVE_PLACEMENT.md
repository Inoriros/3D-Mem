# Interactive Object Placement Tools

This directory contains two tools for interactively placing YCB objects in Habitat-Sim HM3D scenes by clicking on desired positions.

## Tools Overview

### 1. `simple_object_placement.py` - Streamlined version  
- Simpler interface, easier to use
- Basic camera controls
- Click-to-place with automatic object cycling
- Lightweight and fast

## How It Works

1. **Load HM3D Scene**: The tool loads your specified HM3D scene file
2. **Navigate**: Use keyboard controls to move around and find good positions
3. **Click to Place**: Left-click on the scene image to place objects at that 3D location
4. **Depth Calculation**: Uses the depth sensor to convert 2D clicks to 3D world positions
5. **Object Placement**: Places YCB objects at the calculated positions with random orientations

## Usage
### In the objects placement tool directory
```bash
cd objects_placement
```
### Place the objects in interaction mode and save the objects-scene config
```bash
python simple_object_placement.py
```

### Load the config and view and explore the env in interaction mode
```bash
python view_object_placement.py
```

## Controls

### Camera Movement
- **W**: Move forward
- **S**: Move backward  
- **A/Q**: Turn left
- **D/E**: Turn right

### Object Placement
- **Left Click**: Place object at clicked position
- **Enter**: Save placements and exit
- **ESC**: Exit without saving

### Additional (Full Version)
- **R**: Clear all placed objects
- **H**: Show help

## Configuration

Edit the scene path in the scripts:
```python
scene_path = "/path/to/your/hm3d/scene.glb"
```

Available YCB objects (you can modify these lists):
- 002_master_chef_can
- 003_cracker_box
- 013_apple
- 025_mug
- 077_rubiks_cube
- And more...

## Output

The tools save placement configurations to `object_placements.json`:
```json
{
  "scene": "/path/to/scene.glb",
  "objects": [
    {
      "name": "002_master_chef_can",
      "position": [x, y, z]
    }
  ]
}
```

## Requirements

- habitat-sim
- opencv-python
- numpy
- magnum (included with habitat-sim)

## Tips

1. **Navigate First**: Move around to find good placement spots before clicking
2. **Click on Surfaces**: Click on floors, tables, or other flat surfaces for best results
3. **Depth Matters**: Objects are placed at the depth of the clicked surface
4. **Save Frequently**: Use Enter to save configurations as you work
5. **Start Simple**: Try the simple version first to understand the workflow

## Troubleshooting

- **No depth at click**: Click on visible surfaces, not empty space
- **Object placement fails**: Ensure YCB object configs are available
- **Display issues**: Make sure X11 forwarding is enabled if using SSH
- **Navigation problems**: Use small movements, avoid collisions with walls

## Integration with Existing Code

You can use the saved configurations with your existing test code:

```python
# Load placements
with open('object_placements.json', 'r') as f:
    config = json.load(f)

# Apply to your scene
for obj_config in config['objects']:
    place_object_at_position(sim, obj_config['name'], obj_config['position'])
```
