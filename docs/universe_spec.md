# UniverseSpec

UniverseSpec defines the finite, equational universe for enumeration and experiments.

Required fields:
- `logic`: must be `equational`.
- `operations`: list of operations with `name`, `arity` (1 or 2), and optional `commutative`.
- `max_vars`: maximum number of variables (named `x0`, `x1`, ...).
- `max_term_size`: maximum node count for terms.

See `docs/universe_spec.schema.json` for the formal schema.
