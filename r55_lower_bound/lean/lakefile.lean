import Lake
open Lake DSL

package r55 where
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩
  ]

@[default_target]
lean_lib R55 where
  srcDir := "R55"

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git"
