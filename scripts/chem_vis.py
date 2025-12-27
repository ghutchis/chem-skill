#!/usr/bin/env python3
"""
Unified Chemical Visualization CLI

Generate 2D structure images or 3D interactive viewers from chemical names.

Usage:
    python chem_vis.py "caffeine" --2d --output caffeine.png
    python chem_vis.py "caffeine" --3d --output caffeine.html
    python chem_vis.py "caffeine" --both --output-dir ./caffeine/
"""

import argparse
import sys
from pathlib import Path

from chem_2d import chemical_to_image
from chem_3d import chemical_to_3d, get_inline_js_content


def main():
    parser = argparse.ArgumentParser(
        description="Generate 2D and/or 3D molecular visualizations"
    )
    parser.add_argument(
        "chemical",
        help="Chemical name, SMILES, or InChI string"
    )
    
    # Output mode
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--2d",
        dest="mode_2d",
        action="store_true",
        help="Generate 2D structure image"
    )
    mode_group.add_argument(
        "--3d",
        dest="mode_3d",
        action="store_true",
        help="Generate 3D interactive viewer"
    )
    mode_group.add_argument(
        "--both",
        action="store_true",
        help="Generate both 2D and 3D outputs"
    )
    
    # Output location
    parser.add_argument(
        "--output", "-o",
        help="Output file path (for --2d or --3d)"
    )
    parser.add_argument(
        "--output-dir", "-d",
        help="Output directory (for --both)"
    )
    
    # Common options
    parser.add_argument(
        "--input-type", "-t",
        choices=["name", "smiles", "inchi"],
        default="name",
        help="Input type (default: name)"
    )
    parser.add_argument(
        "--width", "-W",
        type=int,
        default=400,
        help="Image/viewer width in pixels (default: 400)"
    )
    parser.add_argument(
        "--height", "-H",
        type=int,
        default=400,
        help="Image/viewer height in pixels (default: 400)"
    )
    
    # 2D-specific options
    parser.add_argument(
        "--format", "-f",
        choices=["png", "svg"],
        default="svg",
        help="2D output format (default: svg)"
    )
    parser.add_argument(
        "--kekulize", "-k",
        action="store_true",
        help="Show Kekulé structure in 2D"
    )
    
    # 3D-specific options
    parser.add_argument(
        "--style", "-s",
        choices=["stick", "sphere", "line", "ballstick"],
        default="stick",
        help="3D rendering style (default: stick)"
    )
    parser.add_argument(
        "--conformers", "-c",
        type=int,
        default=10,
        help="Number of conformers to sample (default: 10)"
    )
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Output embeddable 3D snippet (no HTML wrapper)"
    )
    parser.add_argument(
        "--use-cdn",
        action="store_true",
        help="Load 3Dmol.js from CDN instead of embedding (requires network)"
    )
    
    args = parser.parse_args()
    
    # Load inline JS for 3D viewer (default: no network required)
    inline_js_content = None
    if not args.use_cdn:
        inline_js_content = get_inline_js_content()
        if inline_js_content is None:
            print("Warning: Could not load bundled 3Dmol-min.js, falling back to CDN")
    
    # Validate output arguments
    if args.both and not args.output_dir:
        parser.error("--both requires --output-dir")
    if (args.mode_2d or args.mode_3d) and not args.output:
        # Generate default output name
        safe_name = "".join(c if c.isalnum() else "_" for c in args.chemical)
        if args.mode_2d:
            args.output = f"{safe_name}.{args.format}"
        else:
            args.output = f"{safe_name}_3d.html"
    
    success = True
    
    if args.mode_2d:
        success = chemical_to_image(
            args.chemical,
            args.output,
            input_type=args.input_type,
            width=args.width,
            height=args.height,
            format=args.format,
            kekulize=args.kekulize
        )
        if success:
            print(f"Generated 2D: {args.output}")
            
    elif args.mode_3d:
        success = chemical_to_3d(
            args.chemical,
            args.output,
            input_type=args.input_type,
            width=args.width,
            height=args.height,
            style=args.style,
            num_conformers=args.conformers,
            embed=args.embed,
            inline_js_content=inline_js_content
        )
        if success:
            print(f"Generated 3D: {args.output}")
            
    elif args.both:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        safe_name = "".join(c if c.isalnum() else "_" for c in args.chemical)
        
        # Generate 2D
        path_2d = output_dir / f"{safe_name}.{args.format}"
        success_2d = chemical_to_image(
            args.chemical,
            str(path_2d),
            input_type=args.input_type,
            width=args.width,
            height=args.height,
            format=args.format,
            kekulize=args.kekulize
        )
        if success_2d:
            print(f"Generated 2D: {path_2d}")
        
        # Generate 3D
        path_3d = output_dir / f"{safe_name}_3d.html"
        success_3d = chemical_to_3d(
            args.chemical,
            str(path_3d),
            input_type=args.input_type,
            width=args.width,
            height=args.height,
            style=args.style,
            num_conformers=args.conformers,
            embed=args.embed,
            inline_js_content=inline_js_content
        )
        if success_3d:
            print(f"Generated 3D: {path_3d}")
        
        success = success_2d and success_3d
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()