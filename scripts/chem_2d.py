#!/usr/bin/env python3
"""
2D Molecular Structure Image Generator

Generates 2D structure images from chemical names or SMILES.

Usage:
    python chem_2d.py "aspirin" --output aspirin.png
    python chem_2d.py "CCO" --input-type smiles --output ethanol.png
"""

import argparse
import sys
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Draw, AllChem
from rdkit.Chem.Draw import rdMolDraw2D

from common import resolve_chemical


def mol_to_image(
    mol: Chem.Mol,
    output_path: str,
    width: int = 300,
    height: int = 300,
    format: str = "png",
    kekulize: bool = False,
    show_atom_numbers: bool = False,
    highlight_atoms: list = None
) -> bool:
    """
    Generate an image from an RDKit Mol object.
    
    Args:
        mol: RDKit Mol object
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
        format: Output format ('png' or 'svg')
        kekulize: Whether to show Kekulé structure
        show_atom_numbers: Whether to display atom indices
        highlight_atoms: List of atom indices to highlight
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Generate 2D coordinates if not present
        AllChem.Compute2DCoords(mol)
        AllChem.StraightenDepiction(mol)
        
        if format.lower() == "svg":
            drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        else:
            drawer = rdMolDraw2D.MolDraw2DCairo(width, height)
        
        # Configure drawing options
        opts = drawer.drawOptions()
        opts.addAtomIndices = show_atom_numbers
        
        if kekulize:
            Chem.Kekulize(mol)
        
        # Draw the molecule
        if highlight_atoms:
            drawer.DrawMolecule(mol, highlightAtoms=highlight_atoms)
        else:
            drawer.DrawMolecule(mol)
        
        drawer.FinishDrawing()
        
        # Save to file
        output = drawer.GetDrawingText()
        
        if format.lower() == "svg":
            with open(output_path, 'w') as f:
                f.write(output)
        else:
            with open(output_path, 'wb') as f:
                f.write(output)
        
        return True
        
    except Exception as e:
        print(f"Error generating image: {e}")
        return False


def chemical_to_image(
    chemical: str,
    output_path: str,
    input_type: str = "name",
    width: int = 300,
    height: int = 300,
    format: str = "png",
    kekulize: bool = False,
    show_atom_numbers: bool = False,
    highlight_atoms: list = None
) -> bool:
    """
    Convert a chemical name/SMILES/InChI to an image.
    
    Args:
        chemical: Chemical identifier (name, SMILES, or InChI)
        output_path: Path to save the image
        input_type: Type of input ('name', 'smiles', 'inchi')
        width: Image width in pixels
        height: Image height in pixels
        format: Output format ('png' or 'svg')
        kekulize: Whether to show Kekulé structure
        show_atom_numbers: Whether to display atom indices
        highlight_atoms: List of atom indices to highlight
        
    Returns:
        True if successful, False otherwise
    """
    mol, _ = resolve_chemical(chemical, input_type)
    
    if mol is None:
        return False
    
    return mol_to_image(
        mol, output_path, width, height, format,
        kekulize, show_atom_numbers, highlight_atoms
    )


def batch_convert(
    chemicals: list,
    output_dir: str = "./",
    input_type: str = "name",
    width: int = 300,
    height: int = 300,
    format: str = "png"
) -> dict:
    """
    Convert multiple chemicals to images.
    
    Args:
        chemicals: List of chemical identifiers
        output_dir: Directory to save images
        input_type: Type of input ('name', 'smiles', 'inchi')
        width: Image width in pixels
        height: Image height in pixels
        format: Output format ('png' or 'svg')
        
    Returns:
        Dictionary mapping chemical names to success status
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    for chemical in chemicals:
        # Create safe filename
        safe_name = "".join(c if c.isalnum() else "_" for c in chemical)
        file_path = output_path / f"{safe_name}.{format}"
        
        success = chemical_to_image(
            chemical, str(file_path),
            input_type=input_type,
            width=width, height=height,
            format=format
        )
        
        results[chemical] = {
            "success": success,
            "path": str(file_path) if success else None
        }
        
        if success:
            print(f"✓ Generated: {file_path}")
        else:
            print(f"✗ Failed: {chemical}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate 2D molecular structure images"
    )
    parser.add_argument(
        "chemical",
        help="Chemical name, SMILES, or InChI string"
    )
    parser.add_argument(
        "--output", "-o",
        default="molecule.png",
        help="Output file path (default: molecule.png)"
    )
    parser.add_argument(
        "--input-type", "-t",
        choices=["name", "smiles", "inchi"],
        default="name",
        help="Input type (default: name)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["png", "svg"],
        default="png",
        help="Output format (default: png)"
    )
    parser.add_argument(
        "--width", "-W",
        type=int,
        default=300,
        help="Image width in pixels (default: 300)"
    )
    parser.add_argument(
        "--height", "-H",
        type=int,
        default=300,
        help="Image height in pixels (default: 300)"
    )
    parser.add_argument(
        "--kekulize", "-k",
        action="store_true",
        help="Show Kekulé structure (alternating single/double bonds)"
    )
    parser.add_argument(
        "--show-atom-numbers", "-n",
        action="store_true",
        help="Display atom indices"
    )
    parser.add_argument(
        "--highlight-atoms",
        type=int,
        nargs="+",
        help="Atom indices to highlight"
    )
    
    args = parser.parse_args()
    
    # Determine format from output path if not specified
    output_format = args.format
    if args.output.lower().endswith('.svg'):
        output_format = 'svg'
    elif args.output.lower().endswith('.png'):
        output_format = 'png'
    
    success = chemical_to_image(
        args.chemical,
        args.output,
        input_type=args.input_type,
        width=args.width,
        height=args.height,
        format=output_format,
        kekulize=args.kekulize,
        show_atom_numbers=args.show_atom_numbers,
        highlight_atoms=args.highlight_atoms
    )
    
    if success:
        print(f"Generated: {args.output}")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
