# NOTICE — Tonality → consumers: field rename `rotational_symmetry_order` → `rotational_period`

> 2026-06-30, from Tonality. A **naming-only** change to a `set_class_info` field (and a
> few sibling result fields). **The value is unchanged** — only the key name moves.
> Primes the triage so you can update on your schedule; Julian is coordinating timing.

## What changed

The set-class "rotational symmetry" field is renamed to **`rotational_period`** everywhere
it surfaces. On the paths you consume:

| Surface | old key | new key |
|---|---|---|
| `set_class_info` | `rotational_symmetry_order` | **`rotational_period`** |
| `bracelet_view` node | `rotational_order` | **`rotational_period`** |
| `chord_network` node | `symmetry_order` | **`rotational_period`** |
| versioned-data export table | `rotational_symmetry_order` | **`rotational_period`** |

(Internally the same value was exposed under four inconsistent names; they are now one.)

## The value is identical — only the name moves

The number is the **rotational period**: the smallest transposition that maps the set to
itself (= 12 ÷ rotational-symmetry-group order). It was *always* the period — the old
name implied a symmetry-group order it never returned. Spot values, unchanged:

- augmented `{0,4,8}` → **4**, dim7 `{0,3,6,9}` → **3**, whole-tone → **2**
- a single pc, a major triad (no nontrivial rotational symmetry) → **12**

So if you were reading it as the period (a value `< 12` marks a symmetric "hub"), your
logic is already correct — just rename the key you read. If you were treating it as a
*symmetry count* (e.g. expecting augmented = 3), note it was never that; it is `12 ÷ that`.

## Action

- Update the key name `rotational_symmetry_order` / `rotational_order` / `symmetry_order`
  → `rotational_period` wherever you read it. No value change, no logic change.
- Lands with Tonality PR #119. There is no compatibility alias — the rename is clean
  (honest-naming pass; the misleading names are gone, not duplicated).

— Tonality
