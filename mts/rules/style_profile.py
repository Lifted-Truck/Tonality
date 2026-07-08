"""The style-profile bundle (Phase 4.5, gap 14 slice 2): the one genuinely new
object of the style-profile convergence.

A style has two representations: a **ruleset** (constraints — what it forbids) and
one or more **distributions** (the spread — what it does). Both already exist
(`induce_ruleset`, `build_transition_matrix`); a ``StyleProfile`` is the container
that carries them together with a **provenance** block, as one versioned,
round-trippable, MCP-portable artifact — the "assemble" step, not a re-derivation.

Provenance follows the discipline used for every versioned prior (and wont's
``tag-contrast.1`` stamps): a free-form block naming ``source`` (corpus / academic
text / per-artist) and ``method``, so a profile always says where it came from.

Cardinal-rule note: this is pure assembly of already-analyzed parts — it invents
nothing. A profile must carry **at least one** half (a bundle of nothing is not a
style); the provenance block is always present.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .schema import Ruleset, parse_ruleset, ruleset_to_payload
from .transition import TransitionMatrix

SCHEMA_VERSION = "style-profile.1"


@dataclass(frozen=True)
class StyleProfile:
    """A named style: its ruleset (constraints) + distributions (spread) + provenance.

    ``ruleset`` is the optional constraint half; ``distributions`` is a tuple of
    zero or more :class:`TransitionMatrix` (each carries its own ``state`` keying,
    so a profile can hold e.g. a degree-transition and a role-transition matrix).
    At least one half must be present. ``provenance`` is a free-form block (keys
    like ``source`` / ``method``); ``schema_version`` stamps the bundle format.
    """

    name: str
    version: str
    provenance: dict
    ruleset: Ruleset | None = None
    distributions: tuple[TransitionMatrix, ...] = ()
    description: str = ""
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        # An empty ruleset (0 rules — e.g. induction found nothing significant) is
        # not a constraint half and isn't a valid DSL payload; treat it as absent.
        if self.ruleset is not None and not self.ruleset.rules:
            object.__setattr__(self, "ruleset", None)
        if self.ruleset is None and not self.distributions:
            raise ValueError(
                "a StyleProfile must carry at least one half — a ruleset, "
                "distributions, or both (a bundle of nothing is not a style)."
            )
        if not isinstance(self.provenance, dict):
            raise ValueError(
                f"provenance must be a dict (e.g. {{'source': …, 'method': …}}), "
                f"got {type(self.provenance).__name__}."
            )

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "provenance": dict(self.provenance),
            "ruleset": ruleset_to_payload(self.ruleset) if self.ruleset is not None else None,
            "distributions": [d.to_dict() for d in self.distributions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StyleProfile":
        ruleset_payload = data.get("ruleset")
        return cls(
            name=data["name"],
            version=data["version"],
            provenance=dict(data.get("provenance", {})),
            ruleset=parse_ruleset(ruleset_payload) if ruleset_payload is not None else None,
            distributions=tuple(
                TransitionMatrix.from_dict(d) for d in data.get("distributions", ())
            ),
            description=data.get("description", ""),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )


def build_style_profile(
    name: str,
    version: str,
    *,
    provenance: dict | None = None,
    ruleset: Ruleset | dict | None = None,
    distributions: list | None = None,
    description: str = "",
) -> StyleProfile:
    """Assemble a :class:`StyleProfile` from already-built parts.

    ``ruleset`` is a parsed :class:`Ruleset` or a raw DSL payload (validated via
    ``parse_ruleset``); ``distributions`` is a list of :class:`TransitionMatrix`
    or their ``to_dict`` payloads. Pure assembly — nothing is re-derived. Raises
    if the profile would carry neither half (via ``__post_init__``).
    """

    parsed_ruleset: Ruleset | None
    if ruleset is None or isinstance(ruleset, Ruleset):
        parsed_ruleset = ruleset
    else:
        parsed_ruleset = parse_ruleset(ruleset)

    dists: list[TransitionMatrix] = []
    for d in distributions or ():
        dists.append(d if isinstance(d, TransitionMatrix) else TransitionMatrix.from_dict(d))

    return StyleProfile(
        name=name,
        version=version,
        provenance=provenance if provenance is not None else {},
        ruleset=parsed_ruleset,
        distributions=tuple(dists),
        description=description,
    )


__all__ = ["StyleProfile", "build_style_profile", "SCHEMA_VERSION"]
