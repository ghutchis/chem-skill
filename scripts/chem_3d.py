#!/usr/bin/env python3
"""
3D Molecular Conformer Generator and Viewer

Generates 3D conformers from chemical names or SMILES and outputs
interactive HTML viewers using 3Dmol.js.

Usage:
    python chem_3d.py "caffeine" --output caffeine_3d.html
    python chem_3d.py "CCO" --input-type smiles --output ethanol_3d.html
    python chem_3d.py "aspirin" --embed --output aspirin_widget.html
"""

import argparse
import hashlib
import sys
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem

from common import get_smiles


def generate_conformer(smiles: str, num_conformers: int = 10, optimize: bool = True) -> str | None:
    """
    Generate a 3D conformer from SMILES and return as MOL block.
    
    Args:
        smiles: SMILES string
        num_conformers: Number of conformers to generate (returns lowest energy)
        optimize: Whether to run MMFF optimization
        
    Returns:
        MOL block string or None if generation fails
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    # Add hydrogens for proper 3D geometry
    mol = Chem.AddHs(mol)
    
    # Generate conformer(s)
    if num_conformers > 1:
        conf_ids = AllChem.EmbedMultipleConfs(
            mol, 
            numConfs=num_conformers,
            randomSeed=42,
            useExpTorsionAnglePrefs=True,
            useBasicKnowledge=True,
        )
        if not conf_ids:
            AllChem.EmbedMolecule(mol, randomSeed=42)
    else:
        result = AllChem.EmbedMolecule(mol, randomSeed=42)
        if result == -1:
            AllChem.EmbedMolecule(mol, useRandomCoords=True, randomSeed=42)
    
    # Optimize geometry
    if optimize and mol.GetNumConformers() > 0:
        try:
            if num_conformers > 1:
                results = AllChem.MMFFOptimizeMoleculeConfs(mol)
                if results:
                    energies = [(i, r[1]) for i, r in enumerate(results) if r[0] == 0]
                    if energies:
                        best_conf = min(energies, key=lambda x: x[1])[0]
                        return Chem.MolToMolBlock(mol, confId=best_conf)
            else:
                AllChem.MMFFOptimizeMolecule(mol)
        except Exception:
            pass
    
    if mol.GetNumConformers() > 0:
        return Chem.MolToMolBlock(mol)
    
    return None


def generate_html_viewer(
    mol_block: str,
    title: str = "Molecule",
    width: int = 500,
    height: int = 400,
    style: str = "stick",
    background: str = "white",
    show_controls: bool = True,
    embed: bool = False,
    js_path: str = None,
    inline_js_content: str = None
) -> str:
    """
    Generate HTML with 3Dmol.js viewer.
    
    Args:
        mol_block: MOL block string
        title: Display title
        width: Viewer width in pixels
        height: Viewer height in pixels
        style: Rendering style ('stick', 'sphere', 'line', 'ballstick')
        background: Background color
        show_controls: Whether to include style toggle buttons
        embed: If True, output a div snippet instead of full HTML document
        js_path: Path to local 3Dmol-min.js file (None = use CDN)
        inline_js_content: If provided, embed this JS content directly in HTML
                           (takes precedence over js_path and CDN)
        
    Returns:
        HTML string
    """
    mol_block_escaped = mol_block.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    
    # Generate unique ID for embedding multiple viewers
    viewer_id = "viewer_" + hashlib.md5(mol_block.encode()).hexdigest()[:8]
    
    controls_html = ""
    controls_js = ""
    
    if show_controls:
        controls_html = f'''
    <div style="margin-bottom: 10px;">
        <button onclick="{viewer_id}_setStyle('stick')">Stick</button>
        <button onclick="{viewer_id}_setStyle('sphere')">Sphere</button>
        <button onclick="{viewer_id}_setStyle('line')">Line</button>
        <button onclick="{viewer_id}_setStyle('ballstick')">Ball & Stick</button>
        <button onclick="{viewer_id}_toggleSpin()">Toggle Spin</button>
        <button onclick="{viewer_id}_reset()">Reset</button>
    </div>'''
        
        controls_js = f'''
        window.{viewer_id}_spinning = false;
        
        window.{viewer_id}_setStyle = function(style) {{
            const styles = {{
                stick: {{stick: {{radius: 0.15}}}},
                sphere: {{sphere: {{scale: 0.3}}}},
                line: {{line: {{}}}},
                ballstick: {{stick: {{radius: 0.1}}, sphere: {{scale: 0.25}}}}
            }};
            {viewer_id}.setStyle({{}}, styles[style] || styles.stick);
            {viewer_id}.render();
        }};
        
        window.{viewer_id}_toggleSpin = function() {{
            window.{viewer_id}_spinning = !window.{viewer_id}_spinning;
            {viewer_id}.spin(window.{viewer_id}_spinning);
        }};
        
        window.{viewer_id}_reset = function() {{
            {viewer_id}.zoomTo();
            {viewer_id}.render();
        }};'''
    
    style_obj = {
        'stick': '{stick: {radius: 0.15}}',
        'sphere': '{sphere: {scale: 0.3}}',
        'line': '{line: {}}',
        'ballstick': '{stick: {radius: 0.1}, sphere: {scale: 0.25}}'
    }.get(style, '{stick: {}}')
    
    viewer_div = f'''<div id="{viewer_id}_container" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <h3 style="margin: 0 0 10px 0; color: #333;">{title}</h3>
    {controls_html}
    <div id="{viewer_id}" style="width: {width}px; height: {height}px; position: relative;border: 1px solid #ddd; border-radius: 4px;"></div>
</div>

<script>
(function() {{
    const molData = `{mol_block_escaped}`;
    
    const {viewer_id} = $3Dmol.createViewer("{viewer_id}", {{
        backgroundColor: "{background}"
    }});
    
    {viewer_id}.addModel(molData, "sdf");
    {viewer_id}.setStyle({{}}, {style_obj});
    {viewer_id}.zoomTo();
    {viewer_id}.render();
    
    // Expose viewer globally for controls
    window.{viewer_id} = {viewer_id};
    {controls_js}
}})();
</script>'''

    if embed:
        # For embed mode with inline JS, wrap JS and viewer together
        if inline_js_content:
            return f'''<script>
{inline_js_content}
</script>
{viewer_div}'''
        return viewer_div
    
    # Determine script source: inline content, local file, or CDN
    if inline_js_content:
        script_tag = f'<script>\n{inline_js_content}\n</script>'
    elif js_path:
        script_tag = f'<script src="{js_path}"></script>'
    else:
        script_tag = '<script src="https://3dmol.org/build/3Dmol-min.js"></script>'
    
    # Full standalone HTML document
    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title} - 3D Viewer</title>
    {script_tag}
    <style>
        body {{
            margin: 20px;
            background: #f5f5f5;
        }}
        button {{
            padding: 8px 16px;
            margin-right: 5px;
            margin-bottom: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
            cursor: pointer;
            font-size: 14px;
        }}
        button:hover {{
            background: #f0f0f0;
        }}
    </style>
</head>
<body>
{viewer_div}
</body>
</html>'''


def chemical_to_3d(
    chemical: str,
    output_path: str,
    input_type: str = "name",
    width: int = 500,
    height: int = 400,
    style: str = "stick",
    num_conformers: int = 10,
    optimize: bool = True,
    show_controls: bool = True,
    embed: bool = False,
    js_path: str = None,
    inline_js_content: str = None
) -> bool:
    """
    Convert a chemical to a 3D viewer HTML file.
    
    Args:
        chemical: Chemical identifier (name or SMILES)
        output_path: Path to save the HTML
        input_type: Type of input ('name', 'smiles')
        width: Viewer width
        height: Viewer height
        style: Initial rendering style
        num_conformers: Number of conformers to generate
        optimize: Whether to optimize geometry
        show_controls: Whether to include interactive controls
        embed: Whether to output embeddable snippet vs full HTML
        js_path: Path to local 3Dmol-min.js (None = use CDN)
        inline_js_content: If provided, embed this JS content directly in HTML
        
    Returns:
        True if successful
    """
    # Get SMILES
    smiles = get_smiles(chemical, input_type)
    if not smiles:
        print(f"Could not resolve chemical: {chemical}")
        return False
    
    title = chemical.title() if input_type == "name" else "Molecule"
    
    # Generate 3D conformer
    mol_block = generate_conformer(smiles, num_conformers, optimize)
    if not mol_block:
        print(f"Could not generate 3D conformer for: {chemical}")
        return False
    
    # Generate HTML
    html = generate_html_viewer(
        mol_block, title, width, height, style,
        show_controls=show_controls, embed=embed, js_path=js_path,
        inline_js_content=inline_js_content
    )
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    return True


def get_inline_js_content(js_path: str = None) -> str | None:
    """
    Load 3Dmol.js content for inline embedding.
    
    Args:
        js_path: Path to 3Dmol-min.js file. If None, uses the bundled
                 version in the assets directory.
                 
    Returns:
        JavaScript content as string, or None if file not found
    """
    if js_path:
        path = Path(js_path)
    else:
        # Default to bundled 3Dmol-min.js in assets directory
        script_dir = Path(__file__).parent
        path = script_dir.parent / "assets" / "3Dmol-min.js"
    
    if path.exists():
        return path.read_text(encoding='utf-8')
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate 3D molecular conformers with interactive viewer"
    )
    parser.add_argument("chemical", help="Chemical name or SMILES")
    parser.add_argument("--output", "-o", default="molecule_3d.html", help="Output file path")
    parser.add_argument("--input-type", "-t", choices=["name", "smiles"], default="name")
    parser.add_argument("--width", "-W", type=int, default=500)
    parser.add_argument("--height", "-H", type=int, default=400)
    parser.add_argument("--style", "-s", choices=["stick", "sphere", "line", "ballstick"], default="stick")
    parser.add_argument("--conformers", "-c", type=int, default=10, 
                        help="Number of conformers to generate (picks lowest energy)")
    parser.add_argument("--no-optimize", action="store_true", help="Skip MMFF optimization")
    parser.add_argument("--no-controls", action="store_true", help="Hide interactive controls")
    parser.add_argument("--embed", action="store_true", 
                        help="Output embeddable snippet (no <html> wrapper, assumes 3Dmol.js loaded)")
    parser.add_argument("--use-cdn", action="store_true",
                        help="Load 3Dmol.js from CDN instead of embedding (requires network)")
    parser.add_argument("--js-path", "-j",
                        help="Path to local 3Dmol-min.js file to link (not embed)")
    parser.add_argument("--inline-js-path",
                        help="Path to 3Dmol-min.js file to embed inline (overrides bundled version)")
    
    args = parser.parse_args()
    
    # By default, embed 3Dmol.js inline (no network required)
    # Use CDN only if explicitly requested
    inline_js_content = None
    js_path = args.js_path
    
    if not args.use_cdn and not args.js_path:
        # Default: embed bundled 3Dmol.js inline
        inline_js_content = get_inline_js_content(args.inline_js_path)
        if inline_js_content is None:
            print("Warning: Could not load bundled 3Dmol-min.js, falling back to CDN")
            print("(This requires network access to 3dmol.org)")
    
    success = chemical_to_3d(
        args.chemical,
        args.output,
        input_type=args.input_type,
        width=args.width,
        height=args.height,
        style=args.style,
        num_conformers=args.conformers,
        optimize=not args.no_optimize,
        show_controls=not args.no_controls,
        embed=args.embed,
        js_path=js_path,
        inline_js_content=inline_js_content
    )
    
    if success:
        print(f"Generated: {args.output}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()