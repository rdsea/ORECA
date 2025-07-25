from causallearn.search.ConstraintBased.PC import pc
from causallearn.utils.cit import chisq, fisherz, gsq
from causallearn.utils.PCUtils.BackgroundKnowledge import BackgroundKnowledge

# Background knowledge for PC algorithm to forbid certain causal relationships.
# Forbids edges from memory/CPU related metrics to latency metrics.
# Forbids any incoming edges to frontend metrics.
background_knowledge = BackgroundKnowledge()
background_knowledge.add_forbidden_by_pattern(".*mem$", ".*lat50$")
background_knowledge.add_forbidden_by_pattern(".*cpu$", ".*lat50$")
background_knowledge.add_forbidden_by_pattern(".*", "frontend.*")


def pc_default(data, show_progress=False, with_bg=False, **kwargs):
    """Applies the PC (Peter-Clark) algorithm with default settings.

    Args:
        data: The input data for causal discovery.
        show_progress (bool, optional): Whether to show progress. Defaults to False.
        with_bg (bool, optional): Whether to use background knowledge. Defaults to False.

    Returns:
        The causal graph learned by the PC algorithm.
    """
    node_names = data.columns.to_list()

    cg = pc(
        data.to_numpy().astype(float),
        node_names=node_names,
        show_progress=show_progress,
        background_knowledge=background_knowledge if with_bg else None,
    )
    return cg.G.graph


def pc_fisherz(data):
    """Applies the PC algorithm using Fisher's Z-test for conditional independence.

    Args:
        data: The input data for causal discovery.

    Returns:
        The causal graph learned by the PC algorithm.
    """
    # data: pd.DataFrame
    node_names = data.columns.to_list()
    data = data.to_numpy()
    cg = pc(
        data=data,
        alpha=0.05,
        indep_test=fisherz,
        stable=False,
        uc_rule=0,
        uc_priority=-1,
        background_knowledge=None,
        show_progress=False,
        node_names=node_names,
    )
    return cg


def pc_fisherz_stable(data):
    """Applies the PC algorithm using Fisher's Z-test with stable PC variant.

    Args:
        data: The input data for causal discovery.

    Returns:
        The causal graph learned by the PC algorithm.
    """
    # data: pd.DataFrame
    node_names = data.columns.to_list()
    data = data.to_numpy()
    cg = pc(
        data=data,
        alpha=0.05,
        indep_test=fisherz,
        stable=True,
        uc_rule=0,
        uc_priority=-1,
        background_knowledge=None,
        show_progress=False,
        node_names=node_names,
    )
    return cg


def pc_gsq(data):
    """Applies the PC algorithm using G-squared test for conditional independence.

    Args:
        data: The input data for causal discovery.

    Returns:
        The causal graph learned by the PC algorithm.
    """
    # data: pd.DataFrame
    node_names = data.columns.to_list()
    data = data.to_numpy()
    cg = pc(
        data=data,
        alpha=0.05,
        indep_test=gsq,
        stable=False,
        uc_rule=0,
        uc_priority=-1,
        background_knowledge=None,
        show_progress=False,
        node_names=node_names,
    )
    return cg


def pc_gsq_stable(data):
    """Applies the PC algorithm using G-squared test with stable PC variant.

    Args:
        data: The input data for causal discovery.

    Returns:
        The causal graph learned by the PC algorithm.
    """
    # data: pd.DataFrame
    node_names = data.columns.to_list()
    data = data.to_numpy()
    cg = pc(
        data=data,
        alpha=0.05,
        indep_test=gsq,
        stable=True,
        uc_rule=0,
        uc_priority=-1,
        background_knowledge=None,
        show_progress=False,
        node_names=node_names,
    )
    return cg


def pc_chisq(data):
    """Applies the PC algorithm using Chi-squared test for conditional independence.

    Args:
        data: The input data for causal discovery.

    Returns:
        The causal graph learned by the PC algorithm.
    """
    # data: pd.DataFrame
    node_names = data.columns.to_list()
    data = data.to_numpy()
    cg = pc(
        data=data,
        alpha=0.05,
        indep_test=chisq,
        stable=False,
        uc_rule=0,
        uc_priority=-1,
        background_knowledge=None,
        show_progress=False,
        node_names=node_names,
    )
    return cg


def pc_chisq_stable(data):
    """Applies the PC algorithm using Chi-squared test with stable PC variant.

    Args:
        data: The input data for causal discovery.

    Returns:
        The causal graph learned by the PC algorithm.
    """
    # data: pd.DataFrame
    node_names = data.columns.to_list()
    data = data.to_numpy()
    cg = pc(
        data=data,
        alpha=0.05,
        indep_test=chisq,
        stable=True,
        uc_rule=0,
        uc_priority=-1,
        background_knowledge=None,
        show_progress=False,
        node_names=node_names,
    )
    return cg


def pcmci(data):
    raise NotImplementedError
