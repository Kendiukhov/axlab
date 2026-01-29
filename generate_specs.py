
import json
from pathlib import Path

def generate_spec(vars, num_binary_ops, num_unary_ops):
    """Generates a UniverseSpec JSON object."""
    spec = {
        "version": "v0",
        "logic": "equational",
        "operations": [],
        "max_vars": vars,
        "max_term_size": 5
    }

    for i in range(num_binary_ops):
        spec["operations"].append({
            "name": f"f{i}",
            "arity": 2,
            "commutative": False
        })

    for i in range(num_unary_ops):
        spec["operations"].append({
            "name": f"g{i}",
            "arity": 1
        })
    
return spec

def main():
    """Generates a series of UniverseSpec files."""
    specs_dir = Path("specs")
    specs_dir.mkdir(exist_ok=True)

    for v in range(1, 4):
        for b in range(1, 3):
            for u in range(0, 2):
                spec = generate_spec(v, b, u)
                filename = f"spec_v{v}_b{b}_u{u}_c0.json"
                with open(specs_dir / filename, "w") as f:
                    json.dump(spec, f, indent=2)
    
    print(f"Generated spec files in {specs_dir}")

if __name__ == "__main__":
    main()
