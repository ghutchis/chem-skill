#!/usr/bin/env python3
"""
Common utilities for chemical visualization.

Shared functions for name resolution, SMILES parsing, and molecule handling.
"""

import sys
from pathlib import Path

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
except ImportError:
    print("Error: RDKit is required. Install with: pip install rdkit --break-system-packages")
    sys.exit(1)

# Try to import local common_molecules dictionary
try:
    # Check if common_molecules.py is in the same directory as this script
    script_dir = Path(__file__).parent
    if (script_dir / "common_molecules.py").exists():
        sys.path.insert(0, str(script_dir))
    from common_molecules import get_smiles as get_common_smiles
    HAS_COMMON_MOLECULES = True
except ImportError:
    get_common_smiles = None
    HAS_COMMON_MOLECULES = False

try:
    import py2opsin
    HAS_OPSIN = True
except ImportError:
    py2opsin = None
    HAS_OPSIN = False

try:
    import pubchempy as pcp
    HAS_PUBCHEM = True
except ImportError:
    pcp = None
    HAS_PUBCHEM = False


def name_to_smiles(chemical_name: str) -> str | None:
    """
    Convert a chemical name to SMILES.
    
    Resolution order (prioritizing offline sources):
    1. Local common_molecules dictionary (no network, instant)
    2. py2opsin / OPSIN (no network, local IUPAC parser)
    3. PubChem (requires network)
    
    Args:
        chemical_name: Common name or IUPAC name of the chemical
        
    Returns:
        SMILES string or None if not found
    """
    # 1. First, try the local common_molecules dictionary (fastest, no network)
    if HAS_COMMON_MOLECULES:
        try:
            smiles = get_common_smiles(chemical_name)
            if smiles:
                return smiles
        except Exception:
            pass  # Fall through to other methods
    
    # 2. Try OPSIN since it's local (no network required)
    if HAS_OPSIN:
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                smiles = py2opsin.py2opsin(chemical_name)
            # Check if we got a valid result
            if smiles and isinstance(smiles, str) and smiles.strip():
                return smiles.strip()
        except Exception:
            pass  # Fall through to PubChem
    
    # 3. Fall back to PubChem (requires network)
    if HAS_PUBCHEM:
        try:
            compounds = pcp.get_compounds(chemical_name, 'name')
            if compounds:
                # Use .smiles property (isomeric SMILES with stereochemistry)
                smiles = compounds[0].smiles
                if smiles:
                    return smiles
        except Exception as e:
            print(f"PubChem lookup failed: {e}")
            return None
    
    # No methods available or all failed
    if not HAS_COMMON_MOLECULES and not HAS_PUBCHEM and not HAS_OPSIN:
        print("Warning: No chemical name resolution available.")
        print("Options:")
        print("  - Place common_molecules.py in the scripts directory")
        print("  - Install pubchempy: pip install pubchempy --break-system-packages")
        print("  - Install py2opsin: pip install py2opsin --break-system-packages")
    
    return None


def smiles_to_mol(smiles: str) -> Chem.Mol | None:
    """
    Convert SMILES string to RDKit Mol object.
    
    Args:
        smiles: SMILES string
        
    Returns:
        RDKit Mol object or None if parsing fails
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        print(f"Error: Could not parse SMILES: {smiles}")
        return None
    return mol


def inchi_to_mol(inchi: str) -> Chem.Mol | None:
    """
    Convert InChI string to RDKit Mol object.
    
    Args:
        inchi: InChI string
        
    Returns:
        RDKit Mol object or None if parsing fails
    """
    mol = Chem.MolFromInchi(inchi)
    if mol is None:
        print(f"Error: Could not parse InChI: {inchi}")
        return None
    return mol


def resolve_chemical(
    chemical: str,
    input_type: str = "name"
) -> tuple[Chem.Mol | None, str]:
    """
    Resolve a chemical identifier to an RDKit Mol object.
    
    Args:
        chemical: Chemical identifier (name, SMILES, or InChI)
        input_type: Type of input ('name', 'smiles', 'inchi')
        
    Returns:
        Tuple of (Mol object or None, title string)
    """
    title = chemical.title() if input_type == "name" else "Molecule"
    
    if input_type == "name":
        smiles = name_to_smiles(chemical)
        if smiles is None:
            print(f"Could not find chemical: {chemical}")
            print("Try using SMILES directly with --input-type smiles")
            return None, title
        mol = smiles_to_mol(smiles)
        
    elif input_type == "smiles":
        mol = smiles_to_mol(chemical)
        
    elif input_type == "inchi":
        mol = inchi_to_mol(chemical)
        
    else:
        print(f"Unknown input type: {input_type}")
        return None, title
    
    return mol, title


def get_smiles(chemical: str, input_type: str = "name") -> str | None:
    """
    Get SMILES string from a chemical identifier.
    
    Args:
        chemical: Chemical identifier (name, SMILES, or InChI)
        input_type: Type of input ('name', 'smiles', 'inchi')
        
    Returns:
        SMILES string or None
    """
    if input_type == "name":
        return name_to_smiles(chemical)
    elif input_type == "smiles":
        return chemical
    elif input_type == "inchi":
        mol = inchi_to_mol(chemical)
        if mol:
            return Chem.MolToSmiles(mol)
    return None


def get_available_methods() -> list[str]:
    """
    Get list of available name resolution methods.
    
    Returns:
        List of available method names
    """
    methods = []
    if HAS_COMMON_MOLECULES:
        methods.append("common_molecules (local dictionary)")
    if HAS_OPSIN:
        methods.append("py2opsin (local IUPAC parser)")
    if HAS_PUBCHEM:
        methods.append("pubchempy (network)")
    return methods


if __name__ == "__main__":
    # Test the module
    print("Chemical name resolution methods available:")
    for method in get_available_methods():
        print(f"  - {method}")
    print()
    
    # Test some lookups
    test_names = ["caffeine", "aspirin", "glucose", "benzene", "2-butanol"]
    print("Test lookups:")
    for name in test_names:
        smiles = name_to_smiles(name)
        if smiles:
            has_stereo = "@" in smiles
            stereo_note = " [stereo]" if has_stereo else ""
            print(f"  {name}: {smiles}{stereo_note}")
        else:
            print(f"  {name}: NOT FOUND")
