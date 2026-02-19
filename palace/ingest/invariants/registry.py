"""Invariant registry for managing checkers."""

from typing import List, Dict, Type, Optional
from pathlib import Path
import tomllib  # Python 3.11+ standard library
from dataclasses import dataclass, field
from palace.ingest.invariants.base import BaseInvariantChecker, CheckerConfig


@dataclass
class InvariantRuleConfig:
    """Configuration for a single invariant rule."""
    enabled: bool = True
    severity: str = "MEDIUM"
    threshold: Optional[float] = None
    patterns: List[str] = field(default_factory=list)


class InvariantRegistry:
    """
    Registry for invariant checkers.

    Manages checker instances and loads configuration from TOML files.
    """

    _instance: Optional['InvariantRegistry'] = None
    _checkers: Dict[str, Type[BaseInvariantChecker]] = {}
    _configs: Dict[str, InvariantRuleConfig] = {}

    def __new__(cls) -> 'InvariantRegistry':
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, checker_class: Type[BaseInvariantChecker]) -> None:
        """
        Register a checker class.

        Args:
            checker_class: Checker class to register
        """
        rule_name = checker_class.__name__.replace("Checker", "").lower()
        cls._checkers[rule_name] = checker_class

    @classmethod
    def load_config(cls, config_path: Path) -> None:
        """
        Load configuration from TOML file.

        Args:
            config_path: Path to invariants.toml file
        """
        if not config_path.exists():
            # Use default configuration
            return

        try:
            with open(config_path, 'rb') as f:
                config_data = tomllib.load(f)
            rules = config_data.get('rules', {})

            for rule_name, rule_config in rules.items():
                cls._configs[rule_name] = InvariantRuleConfig(
                    enabled=rule_config.get('enabled', True),
                    severity=rule_config.get('severity', 'MEDIUM'),
                    threshold=rule_config.get('threshold'),
                    patterns=rule_config.get('patterns', [])
                )
        except Exception:
            # Use defaults if TOML parsing fails
            pass

    def get_checker(self, rule_name: str) -> Optional[BaseInvariantChecker]:
        """
        Get an instance of a checker by rule name.

        Args:
            rule_name: Name of the rule (e.g., "hardcoded_secrets")

        Returns:
            Checker instance or None if not found
        """
        if rule_name not in self._checkers:
            return None

        checker_class = self._checkers[rule_name]
        config = self._configs.get(rule_name)

        if config:
            checker_config = CheckerConfig(
                enabled=config.enabled,
                severity=config.severity,
                threshold=config.threshold,
                patterns=config.patterns
            )
        else:
            checker_config = CheckerConfig()

        return checker_class(checker_config)

    def get_all_checkers(self) -> List[BaseInvariantChecker]:
        """
        Get instances of all registered checkers.

        Returns:
            List of checker instances
        """
        checkers = []

        for rule_name in self._checkers.keys():
            checker = self.get_checker(rule_name)
            if checker and checker.is_enabled():
                checkers.append(checker)

        return checkers

    def list_rules(self) -> Dict[str, dict]:
        """
        List all registered rules with their status.

        Returns:
            Dict mapping rule names to their configuration
        """
        rules = {}

        for rule_name, checker_class in self._checkers.items():
            config = self._configs.get(rule_name)

            if config:
                rules[rule_name] = {
                    'enabled': config.enabled,
                    'severity': config.severity,
                    'checker': checker_class.__name__
                }
            else:
                rules[rule_name] = {
                    'enabled': True,
                    'severity': 'MEDIUM',
                    'checker': checker_class.__name__
                }

        return rules
