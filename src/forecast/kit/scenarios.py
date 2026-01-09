import asyncio
import logging
from typing import Any, Dict, Generic, TypeVar

from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.graph import BaseGraphState
from forecast.core.utils.state_ops import clone_state

logger = logging.getLogger(__name__)

StateT = TypeVar("StateT", bound=BaseGraphState)


class ScenarioManager(Generic[StateT]):
    """
    Manages the execution of parallel scenarios (counterfactuals) from a common base state.

    This implements the "Scenario Branching" pattern where a single initial state
    is cloned and mutated into multiple branches (e.g., "Control", "Treatment A", "Treatment B")
    which are then executed concurrently.
    """

    def __init__(self, orchestrator: Orchestrator[StateT]):
        """
        Args:
            orchestrator: The orchestrator instance (graph definition) to use for execution.
                          The same graph topology is used for all branches.
        """
        self.orchestrator = orchestrator
        self.branches: Dict[str, Dict[str, Any]] = {}

    def add_branch(self, name: str, overrides: Dict[str, Any] | None = None) -> None:
        """
        Registers a new branch for execution.

        Args:
            name: Unique identifier for the branch (e.g., "control", "no_search").
            overrides: Dictionary of state fields to override for this branch.
        """
        if name in self.branches:
            raise ValueError(f"Branch '{name}' already exists.")

        self.branches[name] = overrides or {}

    async def run_all(self, initial_state: StateT) -> Dict[str, StateT]:
        """
        Executes all registered branches in parallel using the orchestrator.

        Args:
            initial_state: The common starting state for all branches.

        Returns:
            A dictionary mapping branch names to their final states.
        """
        if not self.branches:
            logger.warning("No branches registered. Returning empty result.")
            return {}

        logger.info(f"Preparing to run {len(self.branches)} scenarios: {list(self.branches.keys())}")

        # 1. Prepare tasks
        tasks = []
        branch_names = []

        for name, overrides in self.branches.items():
            # Clone and mutate state
            try:
                branch_state = clone_state(initial_state, overrides)
                logger.debug(f"Created state clone for branch '{name}' with overrides: {overrides}")
            except Exception as e:
                logger.error(f"Failed to prepare branch '{name}': {e}")
                raise

            # Create coroutine for this branch
            # We assume orchestrator.run() is stateless regarding the orchestrator instance itself
            # (i.e. it relies only on the passed state), which is true for our design.
            task = self.orchestrator.run(branch_state)
            tasks.append(task)
            branch_names.append(name)

        # 2. Execute in parallel
        # return_exceptions=False ensures we fail fast if a critical error occurs,
        # or we could use True to allow partial success. For research, seeing the error is usually better.
        results = await asyncio.gather(*tasks)

        # 3. Zip results
        # Mypy doesn't infer that asyncio.gather returns List[StateT] automatically here
        final_states: Dict[str, StateT] = dict(zip(branch_names, results))  # type: ignore

        logger.info("All scenarios completed.")
        return final_states
