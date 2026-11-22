# Keep generated flows separate from deterministic execution

DeepSeek generates a bounded, typed flow and a plain-English explanation; a Python validator and interpreter own structural checks and simulation. This requires explicit node semantics rather than asking the model to improvise each execution step, but makes branching, failures, and regression tests reproducible. The flow format uses Wati vocabulary without claiming native Wati import compatibility.

DeepSeek calls are real. Business API calls, team assignments, and waits are explicitly simulated: API fixtures can succeed or fail, assignments are recorded, and time advances virtually. This preserves an interactive demonstration without requiring external business accounts or producing real side effects. Production execution is outside the agreed MVP.
