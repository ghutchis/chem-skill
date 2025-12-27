#!/usr/bin/env python3
"""
Common utilities for chemical visualization.

Shared functions for name resolution, SMILES parsing, and molecule handling.
"""

import sys

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
except ImportError:
    print("Error: RDKit is required. Install with: pip install rdkit --break-system-packages")
    sys.exit(1)

try:
    import pubchempy as pcp
    HAS_PUBCHEM = True
except ImportError:
    pcp = None
    HAS_PUBCHEM = False

try:
    import py2opsin
    HAS_OPSIN = True
except ImportError:
    py2opsin = None
    HAS_OPSIN = False


def name_to_smiles(chemical_name: str) -> str | None:
    """
    Convert a chemical name to SMILES using OPSIN (local) or PubChem (network).
    
    Tries py2opsin first since it doesn't require network access,
    then falls back to PubChem if OPSIN fails or returns no result.
    
    Args:
        chemical_name: Common name or IUPAC name of the chemical
        
    Returns:
        SMILES string or None if not found
    """
    if not HAS_PUBCHEM and not HAS_OPSIN:
        print("Warning: pubchempy and py2opsin are not installed.")
        print("Install with: pip install pubchempy py2opsin --break-system-packages")
        return None
    
    # First, try OPSIN since it's local (no network required)
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
    
    # Fall back to PubChem (requires network)
    if HAS_PUBCHEM:
        try:
            compounds = pcp.get_compounds(chemical_name, 'name')
            if compounds and compounds[0].smiles:
                return compounds[0].smiles
        except Exception as e:
            print(f"PubChem lookup failed: {e}")
            return None
    
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