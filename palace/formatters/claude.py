"""
Claude Formatter - Structured Markdown generator for Claude Code.
Formats architectural context into Markdown optimized for Claude Code.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional


class ContextBundle:
    """
    Enriched context bundle with all relevant information.
    """

    def __init__(
        self,
        seed_file: str,
        total_activation: float,
        risk_score: float,
        invariants: List['Invariant'],
        topological_neighbors: List['Artifact'],
        active_concepts: List['Concept'],
        relevant_decisions: List['Decision']
    ):
        self.seed_file = seed_file
        self.total_activation = total_activation
        self.risk_score = risk_score
        self.invariants = invariants
        self.topological_neighbors = topological_neighbors
        self.active_concepts = active_concepts
        self.relevant_decisions = relevant_decisions

    def has_violations(self) -> bool:
        """Check if any invariants are in FAIL state."""
        return any(inv.check_result is False for inv in self.invariants if inv.check_result is not None)


class Invariant:
    """Invariant (architectural rule) with context."""

    def __init__(
        self,
        id: str,
        rule: str,
        severity: str,
        distance: int,
        affected_file: Optional[str] = None,
        check_result: Optional[bool] = None
    ):
        self.id = id
        self.rule = rule
        self.severity = severity
        self.distance = distance
        self.affected_file = affected_file
        self.check_result = check_result


class Artifact:
    """Artifact (code file) with relationship information."""

    def __init__(
        self,
        path: str,
        language: str,
        distance: int,
        relation_type: str
    ):
        self.path = path
        self.language = language
        self.distance = distance
        self.relation_type = relation_type  # "depends_on", "depended_by", "related"


class Concept:
    """Concept with activation and evidence."""

    def __init__(
        self,
        name: str,
        activation: float,
        evidence: Optional[List[str]] = None
    ):
        self.name = name
        self.activation = activation
        self.evidence = evidence or []


class Decision:
    """Architectural decision record (ADR)."""

    def __init__(
        self,
        title: str,
        timestamp: Optional[str],
        status: str,
        rationale: Optional[str],
        relevance: float
    ):
        self.title = title
        self.timestamp = timestamp
        self.status = status
        self.rationale = rationale
        self.relevance = relevance


class ClaudeFormatter:
    """
    Formats architectural context into Markdown optimized for Claude Code.

    Generates a structured format that Claude can easily parse
    and use to make informed decisions.
    """

    SEVERITY_EMOJIS = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🔵"
    }

    def format(self, bundle: ContextBundle) -> str:
        """
        Generates the complete context markdown.

        Args:
            bundle: ContextBundle with context information

        Returns:
            Formatted Markdown string
        """
        lines = []

        # Main header
        lines.append("## 🏛️ Architectural Context (Palace Mental)")
        lines.append(f"**Seed**: `{bundle.seed_file}` | **Total Activation**: {bundle.total_activation:.2f} | **Risk**: {bundle.risk_score:.2f}")
        lines.append("")

        # Invariants section
        lines.extend(self._format_invariants(bundle.invariants))

        # Topology section
        lines.extend(self._format_topology(bundle.topological_neighbors))

        # Active concepts section
        lines.extend(self._format_concepts(bundle.active_concepts))

        # Historical memory section
        lines.extend(self._format_decisions(bundle.relevant_decisions))

        # Risk assessment section
        lines.extend(self._format_risk_assessment(bundle))

        # Footer
        lines.append("---")
        lines.append(f"*Palace v2.0 | {datetime.now().isoformat()} | Last sleep: recent*")

        return "\n".join(lines)

    def _format_invariants(self, invariants: List[Invariant]) -> List[str]:
        """Formats the invariants section."""
        lines = []

        if not invariants:
            lines.append("### ⚠️ Active Invariants")
            lines.append("*No active invariants for this file.*")
            lines.append("")
            return lines

        # Group by severity
        critical = [inv for inv in invariants if inv.severity == "CRITICAL"]
        high = [inv for inv in invariants if inv.severity == "HIGH"]
        others = [inv for inv in invariants if inv.severity not in ("CRITICAL", "HIGH")]

        lines.append("### ⚠️ Active Invariants")

        if critical:
            lines.append(f"**🚨 CRITICAL ({len(critical)}):**")
            for inv in critical:
                lines.extend(self._format_single_invariant(inv))

        if high:
            lines.append(f"**⚡ HIGH ({len(high)}):**")
            for inv in high:
                lines.extend(self._format_single_invariant(inv))

        if others:
            lines.append(f"**📋 Others ({len(others)}):**")
            for inv in others[:3]:  # Limit to 3
                lines.extend(self._format_single_invariant(inv))

        lines.append("")
        return lines

    def _format_single_invariant(self, inv: Invariant) -> List[str]:
        """Formats a single invariant."""
        emoji = self.SEVERITY_EMOJIS.get(inv.severity, "⚪")
        lines = []

        lines.append(f"- [{emoji}] `{inv.id}`: {inv.rule}")
        lines.append(f"  ↳ Distance: {inv.distance} hops | File: `{inv.affected_file or 'N/A'}`")

        if inv.check_result is not None:
            status = "✅ PASS" if inv.check_result else "❌ FAIL"
            lines.append(f"  ↳ Validation: {status}")

        return lines

    def _format_topology(self, neighbors: List[Artifact]) -> List[str]:
        """Formats the topology section."""
        lines = []
        lines.append("### 🔗 Local Topology (Cognitive Neighborhood)")

        if not neighbors:
            lines.append("*No topological neighbors found.*")
            lines.append("")
            return lines

        # Group by relation type
        depends = [a for a in neighbors if a.relation_type == "depends_on"]
        depended = [a for a in neighbors if a.relation_type == "depended_by"]
        related = [a for a in neighbors if a.relation_type not in ("depends_on", "depended_by")]

        if depends:
            lines.append("**📥 Depends on:**")
            for art in depends[:5]:
                lines.append(f"- `{art.path}` ({art.language}) - dist: {art.distance}")

        if depended:
            lines.append("**📤 Impacts:**")
            for art in depended[:5]:
                lines.append(f"- `{art.path}` ({art.language}) - dist: {art.distance}")

        if related:
            lines.append("**🔗 Related:**")
            for art in related[:3]:
                lines.append(f"- `{art.path}` ({art.language})")

        lines.append("")
        return lines

    def _format_concepts(self, concepts: List[Concept]) -> List[str]:
        """Formats the active concepts section."""
        lines = []
        lines.append("### 🧠 Active Concepts")

        if not concepts:
            lines.append("*No active concepts detected.*")
            lines.append("")
            return lines

        # Show top concepts
        for concept in concepts[:8]:
            activation_bar = "█" * int(concept.activation * 10) + "░" * (10 - int(concept.activation * 10))
            lines.append(f"- **{concept.name}** `{activation_bar}` {concept.activation:.2f}")

            if concept.evidence:
                evidence_str = ", ".join(concept.evidence[:2])
                lines.append(f"  ↳ Evidence: {evidence_str[:80]}")

        lines.append("")
        return lines

    def _format_decisions(self, decisions: List[Decision]) -> List[str]:
        """Formats the architectural decisions section."""
        lines = []
        lines.append("### 📜 Relevant Historical Memory")

        if not decisions:
            lines.append("*No relevant historical decisions found.*")
            lines.append("")
            return lines

        for decision in decisions[:5]:
            lines.append(f"**[{decision.timestamp[:10] if decision.timestamp else 'N/A'}] {decision.title}**")

            if decision.rationale:
                rationale = decision.rationale[:150] + "..." if len(decision.rationale) > 150 else decision.rationale
                lines.append(f"  ↳ {rationale}")

            lines.append(f"  ↳ Status: `{decision.status}` | Relevance: {decision.relevance:.2f}")
            lines.append("")

        return lines

    def _format_risk_assessment(self, bundle: ContextBundle) -> List[str]:
        """Formats the risk assessment section."""
        lines = []
        lines.append("### 🎯 Risk Assessment")

        # Risk bar
        risk_emoji = "🟢" if bundle.risk_score < 0.3 else "🟡" if bundle.risk_score < 0.6 else "🔴"
        risk_level = "Low" if bundle.risk_score < 0.3 else "Medium" if bundle.risk_score < 0.6 else "High"

        lines.append(f"**{risk_emoji} Risk Level: {risk_level} ({bundle.risk_score:.2f})**")

        # Risk factors
        factors = []

        critical_invariants = [inv for inv in bundle.invariants if inv.severity == "CRITICAL"]
        if critical_invariants:
            factors.append(f"{len(critical_invariants)} CRITICAL invariants active")

        if len(bundle.topological_neighbors) > 10:
            factors.append(f"High connectivity ({len(bundle.topological_neighbors)} neighbors)")

        if bundle.has_violations():
            factors.append("Invariants in FAIL state")

        if factors:
            lines.append("**Risk factors:**")
            for factor in factors:
                lines.append(f"- ⚠️ {factor}")
        else:
            lines.append("*No significant risk factors detected.*")

        # Recommendations
        lines.append("")
        lines.append("**💡 Recommendations:**")

        if bundle.risk_score > 0.5:
            lines.append("- Carefully review CRITICAL invariants before modifying")
            lines.append("- Consider impact on dependent files")

        if len(bundle.topological_neighbors) > 5:
            lines.append(f"- This file has {len(bundle.topological_neighbors)} connections - changes may have domino effects")

        if not factors and bundle.risk_score < 0.3:
            lines.append("- ✅ File is safe to modify")

        lines.append("")
        return lines

    def format_compact(self, bundle: ContextBundle) -> str:
        """
        Compact version of context (for short prompts).
        """
        lines = []

        lines.append(f"🏛️ Context: `{bundle.seed_file}` (risk: {bundle.risk_score:.2f})")

        # Critical invariants
        critical = [inv for inv in bundle.invariants if inv.severity == "CRITICAL"]
        if critical:
            lines.append(f"🚨 CRITICAL: {', '.join(inv.id for inv in critical[:3])}")

        # Key concepts
        if bundle.active_concepts:
            top_concepts = [c.name for c in bundle.active_concepts[:3]]
            lines.append(f"🧠 Concepts: {', '.join(top_concepts)}")

        # Important neighbors
        if bundle.topological_neighbors:
            deps = [a.path for a in bundle.topological_neighbors if a.relation_type == "depends_on"][:3]
            if deps:
                lines.append(f"📥 Depends on: {', '.join(deps)}")

        return " | ".join(lines)
