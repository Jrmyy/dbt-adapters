from dbt.context.providers import generate_runtime_model_context
from dbt.tests.util import get_manifest, run_dbt
from dbt_common.exceptions import DbtRuntimeError
import pytest


@pytest.fixture(scope="class")
def models():
    return {"my_model.sql": "select 1 as fun"}


def test_basic(project):
    results = run_dbt(["run"])
    assert len(results) == 1

    manifest = get_manifest(project.project_root)
    model = manifest.nodes["model.test.my_model"]

    # Normally the context will be provided by the macro that calls the
    # get_incrmental_strategy_macro method, but for testing purposes
    # we create a runtime_model_context.
    context = generate_runtime_model_context(
        model,
        project.adapter.config,
        manifest,
    )

    macro_func = project.adapter.get_incremental_strategy_macro(context, "default")
    assert macro_func
    assert type(macro_func).__name__ == "MacroGenerator"

    macro_func = project.adapter.get_incremental_strategy_macro(context, "append")
    assert macro_func
    assert type(macro_func).__name__ == "MacroGenerator"

    macro_func = project.adapter.get_incremental_strategy_macro(context, "delete+insert")
    assert macro_func
    assert type(macro_func).__name__ == "MacroGenerator"

    # This incremental strategy only works for Postgres >= 15
    macro_func = project.adapter.get_incremental_strategy_macro(context, "merge")
    assert macro_func
    assert type(macro_func).__name__ == "MacroGenerator"

    # This incremental strategy is not valid for Postgres
    with pytest.raises(DbtRuntimeError) as excinfo:
        macro_func = project.adapter.get_incremental_strategy_macro(context, "insert_overwrite")
    assert "insert_overwrite" in str(excinfo.value)
